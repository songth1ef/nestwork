#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# nestwork recent-activity digest (protocol 3.2)
#
# Generates a small, git-derived "what moved recently" summary that the
# SessionStart hook lists as a resident file for every agent. It is one
# nest-level, git-ignored artefact (local/recent.md), rebuilt every session from
# synced git history -- so every machine computes the same content, it cannot go
# stale in git, and it never needs human maintenance.
#
# Sources (no LLM, no network):
#   - projects/*.md touched within --project-days: Current Goal / Next Action /
#     Last Verified fields (AGENTS.md §10.1)
#   - memory / workflow / project markdown touched within --days: the topic's
#     front-matter `description`, else its first heading
#
# Output is capped at --max-bytes (UTF-8). Encrypted files that are still
# locked (git-crypt header) are skipped rather than printed as noise.
#
# Usage:
#   recent-digest.py [--nest PATH] [--days 7] [--project-days 30]
#                    [--max-bytes 2048] [--out FILE]
# Without --out, prints to stdout. Always exits 0 on content problems so a
# startup hook is never blocked.
# -----------------------------------------------------------------------------

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path

SCAN_DIRS = ("projects", "shared", "agents", "workflow")
SKIP_NAMES = {"memory.md", "resident.md", "README.md", "index.md"}
LINE_MAX = 200
GITCRYPT_MAGIC = b"\x00GITCRYPT"


def git(nest: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(nest), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return result.stdout if result.returncode == 0 else ""


def read_text(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError:
        return ""
    if raw.startswith(GITCRYPT_MAGIC):
        return ""
    return raw.decode("utf-8", errors="replace")


def clip(text: str, limit: int = LINE_MAX) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def front_matter_description(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    for line in text[3:end].splitlines():
        m = re.match(r"\s*description:\s*(.+)", line)
        if m:
            return m.group(1).strip().strip("\"'")
    return ""


def first_heading(text: str) -> str:
    m = re.search(r"(?m)^#\s+(.+)$", text)
    return m.group(1).strip() if m else ""


def section(text: str, name: str) -> str:
    """First non-empty, non-placeholder line under `## <name>`."""
    m = re.search(rf"(?m)^##\s+{re.escape(name)}\s*$", text)
    if not m:
        return ""
    for line in text[m.end():].splitlines():
        if line.startswith("#"):
            break
        line = line.strip().lstrip("-*").strip()
        if line and not line.startswith(">"):
            return line
    return ""


def commits(nest: Path, days: int) -> list:
    """Newest-first [(author date, subject, [paths])] within the window."""
    out = git(nest, "log", f"--since={days} days ago", "--name-only",
              "--format=%x00%as%x01%s", "--", *SCAN_DIRS)
    result = []
    for line in out.splitlines():
        if line.startswith("\x00"):
            date, _, subject = line[1:].partition("\x01")
            result.append((date.strip(), subject.strip(), []))
        elif line.strip() and result:
            result[-1][2].append(line.strip())
    return result


def recent_changes(nest: Path, days: int) -> dict:
    """Map repo-relative path -> latest author date (YYYY-MM-DD) within window."""
    latest: dict = {}
    for date, _, paths in commits(nest, days):
        for path in paths:
            latest.setdefault(path, date)
    return latest


def eligible(rel: str) -> bool:
    parts = rel.split("/")
    if not rel.endswith(".md") or "local" in parts:
        return False
    name = parts[-1]
    return not (name in SKIP_NAMES or name.startswith("_"))


def project_lines(nest: Path, changes: dict, limit: int = 6) -> list:
    lines = []
    for rel, date in changes.items():
        if not (rel.startswith("projects/") and rel.count("/") == 1 and eligible(rel)):
            continue
        text = read_text(nest / rel)
        if not text:
            continue
        name = Path(rel).stem
        goal = section(text, "Current Goal")
        nxt = section(text, "Next Action")
        verified = section(text, "Last Verified")
        if not (goal or nxt):
            continue
        parts = [f"**{name}** ({date})"]
        if goal:
            parts.append(f"goal: {goal}")
        if nxt:
            parts.append(f"next: {nxt}")
        if verified:
            parts.append(f"verified: {verified}")
        lines.append("- " + clip(" · ".join(parts), LINE_MAX + 100))
        if len(lines) >= limit:
            break
    return lines


def memory_lines(nest: Path, days: int, limit: int = 12, bulk: int = 5) -> list:
    """One line per recently changed topic; a commit touching more than `bulk`
    topics (a split, migration or distillation) collapses into one line so it
    cannot crowd out individual updates."""
    lines, seen = [], set()
    for date, subject, paths in commits(nest, days):
        topics = [p for p in paths
                  if not p.startswith("projects/") and eligible(p) and p not in seen]
        seen.update(topics)
        if len(topics) > bulk:
            lines.append(f"- {date[5:]} {clip(subject)} ({len(topics)} files)")
        else:
            for rel in topics:
                text = read_text(nest / rel)
                if not text:
                    continue
                desc = front_matter_description(text) or first_heading(text) or Path(rel).stem
                lines.append(f"- {date[5:]} `{rel}` — {clip(desc)}")
        if len(lines) >= limit:
            break
    return lines[:limit]


def build(nest: Path, days: int, project_days: int, max_bytes: int) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    header = [
        "# Recent activity (generated)",
        "",
        f"> {now} by scripts/maintenance/recent-digest.py from git history. "
        "Orientation only: verify dated state before acting; "
        "past work is not a current assignment.",
    ]
    body = []
    projects = project_lines(nest, recent_changes(nest, project_days))
    if projects:
        body += ["", f"## Projects touched in the last {project_days} days", *projects]
    memory = memory_lines(nest, days)
    if memory:
        body += ["", f"## Memory updated in the last {days} days", *memory]
    if not body:
        body = ["", f"No project or memory changes in the last {project_days} days."]

    text = "\n".join(header)
    budget_note = "\n- … (truncated to fit the resident budget)"
    for line in body:
        candidate = text + "\n" + line
        if len((candidate + budget_note).encode("utf-8")) > max_bytes:
            text += budget_note
            break
        text = candidate
    return text + "\n"


def main() -> int:
    default_nest = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nest", type=Path, default=default_nest)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--project-days", type=int, default=30)
    ap.add_argument("--max-bytes", type=int, default=2048)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    text = build(args.nest, args.days, args.project_days, args.max_bytes)
    if args.out is None:
        sys.stdout.write(text)
        return 0
    out = args.out if args.out.is_absolute() else args.nest / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

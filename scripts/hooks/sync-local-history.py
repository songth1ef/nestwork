#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# hivequeen local-history sync
#
# Captures selected Claude Code runtime artefacts into the agent's memory dir
# so they can be versioned in git alongside distilled memory.
#
# Scope (opt-in via ~/.hivequeen/settings.json → {"sync_local_history": true}):
#   - ~/.claude/history.jsonl  -> local/history.jsonl  (redacted)
#   - ~/.claude/plans/         -> local/plans/         (mirror)
#
# Not captured (signal too sparse — UUID-per-session bookkeeping):
#   - ~/.claude/todos/   (>99% files are empty "[]")
#   - ~/.claude/tasks/   (subagent mid-flight state)
#
# Usage:
#   sync-local-history.py <hivequeen_path> <host> <agent_id>
#
# Redaction applied to history.jsonl:
#   - pastedContents field dropped
#   - user home path normalised to <HOME>
#   - obvious token patterns (sk-*, ghp_*, Bearer ...) replaced with <REDACTED>
# -----------------------------------------------------------------------------

import json
import re
import shutil
import sys
from pathlib import Path


TOKEN_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"gho_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9\._\-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
]


def home_variants() -> list[str]:
    """All string forms of $HOME we want to replace with <HOME>."""
    home = str(Path.home())
    variants = {home, home.replace("\\", "/"), home.replace("/", "\\")}
    return sorted(variants, key=len, reverse=True)


def redact_text(text: str, homes: list[str]) -> str:
    for h in homes:
        text = text.replace(h, "<HOME>")
    for pat in TOKEN_PATTERNS:
        text = pat.sub("<REDACTED>", text)
    return text


def redact_history(src: Path, dst: Path) -> int:
    """Read src jsonl, drop pastedContents, redact inline, write to dst."""
    if not src.exists():
        return 0
    homes = home_variants()
    dst.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with src.open("r", encoding="utf-8", errors="replace") as fin, \
         dst.open("w", encoding="utf-8", newline="\n") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(entry, dict):
                entry.pop("pastedContents", None)
                if "project" in entry and isinstance(entry["project"], str):
                    entry["project"] = redact_text(entry["project"], homes)
                if "display" in entry and isinstance(entry["display"], str):
                    entry["display"] = redact_text(entry["display"], homes)
            fout.write(json.dumps(entry, ensure_ascii=False) + "\n")
            n += 1
    return n


def mirror_dir(src: Path, dst: Path) -> int:
    """Mirror src tree into dst. Deletes dst first for a clean snapshot."""
    if not src.exists():
        if dst.exists():
            shutil.rmtree(dst)
        return 0
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return sum(1 for _ in dst.rglob("*") if _.is_file())


def load_settings() -> dict:
    """Read ~/.hivequeen/settings.json. Missing / malformed -> empty dict."""
    path = Path.home() / ".hivequeen" / "settings.json"
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def main() -> int:
    settings = load_settings()
    if not settings.get("sync_local_history"):
        return 0
    if len(sys.argv) < 4:
        print(
            "usage: sync-local-history.py <hivequeen_path> <host> <agent_id>",
            file=sys.stderr,
        )
        return 2

    hivequeen_path = Path(sys.argv[1])
    host = sys.argv[2]
    agent_id = sys.argv[3]
    claude_home = Path.home() / ".claude"
    local_dir = hivequeen_path / "agents" / host / agent_id / "local"
    local_dir.mkdir(parents=True, exist_ok=True)

    n_hist = redact_history(claude_home / "history.jsonl", local_dir / "history.jsonl")
    n_plans = mirror_dir(claude_home / "plans", local_dir / "plans")

    # Purge previously-captured todos/tasks so old mirrors don't linger.
    for stale in ("todos", "tasks"):
        stale_path = local_dir / stale
        if stale_path.exists():
            shutil.rmtree(stale_path)

    print(
        f"[ok] sync-local-history -> {local_dir} "
        f"(history={n_hist} plans={n_plans})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

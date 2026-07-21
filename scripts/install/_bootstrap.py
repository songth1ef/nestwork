#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# nestwork bootstrap injector (shared by install-claude / install-gemini / ...)
#
# Idempotently writes a nestwork startup protocol block into a tool-specific
# markdown (e.g. ~/.claude/CLAUDE.md, ~/.gemini/GEMINI.md). Uses HTML-comment
# markers so the user's own content in the same file is preserved across
# re-installs and upstream protocol bumps.
#
# Behaviour:
#   - File does not exist          -> create with just the nestwork block
#   - File exists, no markers      -> append block after existing content
#   - File exists, markers present -> replace content between markers only
#
# Usage:
#   _install-bootstrap.py <output_md> <nestwork_path> <host> <agent_id> [--tool=<tool>]
#
# --tool=kimi produces a Kimi Code-specific bootstrap that does not assume
# additionalContext injection (Kimi Code currently only runs SessionStart hooks).
# -----------------------------------------------------------------------------

import os
import re
import sys

BEGIN = "<!-- nestwork:begin -->"
END   = "<!-- nestwork:end -->"
LEGACY_BEGIN = "<!-- " + "hive" + "queen:begin -->"
LEGACY_END = "<!-- " + "hive" + "queen:end -->"

LEGACY_CODEX_BOOTSTRAP_RE = re.compile(
    r"^\s*# Global Startup Protocol\b.*?(?:\.codex[\\/]+repos[\\/]+codex[\\/]+bootstrap\.md|/root/github/agents/bootstrap\.md).*$",
    re.DOTALL,
)

BLOCK_TEMPLATE = """\
{begin}
# Nestwork Startup Protocol

Before any analysis, planning, or implementation in a fresh session, ensure
nestwork context is loaded.

On Claude Code, the SessionStart hook auto-runs `git pull` and inlines
`agent-rules.md` plus a `READ-ON-START` manifest with absolute paths
(because hook stdout is truncated near 2KB, only `agent-rules.md` fits
inline -- the rest you Read via the listed paths). On Codex / Gemini /
other agents there is no SessionStart hook; you must do every step below
yourself.

Required at session start:

1. Pull: `git -C {hp} pull --rebase`
2. Read each of the following (use your Read tool; on Claude Code,
   `agent-rules.md` is already inlined, but you still must Read items 2-4):
   - `{hp}/queen/agent-rules.md`
   - `{hp}/queen/strategy.md`
   - `{hp}/shared/memory.md`
   - `{hp}/agents/{host}/{aid}/memory.md`
3. Read on demand when task-relevant:
   - `{hp}/workflow/*.md` (portable methodology)
   - `{hp}/projects/<name>.md` (current task scope)

Skipping step 2 is a protocol violation: `agent-rules.md` requires you to
"say so -- do not guess" when context is missing, and step 2 is what
prevents the missing-context state.

## After loading -- self-direct, do not ask

You have enough signal to pick a next action without user prompting.
Before your first reply:

1. `git -C {hp} log --oneline -10 -- agents/` -- recent activity across
   every instance
2. `git -C {hp} log --oneline -5` -- recent protocol / shared changes
3. Cross-reference with `queen/strategy.md` **Current Priorities** and
   the latest entries in `shared/memory.md` / `agents/{host}/{aid}/memory.md`

Open with: **(a) state summary** (2-3 bullets on what's in flight, what
priorities say, what's blocking) and **(b) one concrete proposal** for
the next action (plus a short alternative if meaningful).

FORBIDDEN first replies: "What would you like me to do?" / "How can I
help?" / "Tell me what to do." Only if every source above is empty may
you ask -- and you must state that you checked and found nothing.

## Write protocol

- Only write to `{hp}/agents/{host}/{aid}/`
- When the session ends and memory changed:

```bash
git -C {hp} add agents/{host}/{aid}/
git -C {hp} diff --cached --quiet -- agents/{host}/{aid}/ || \
  git -C {hp} commit -m "memory: update {host}/{aid}" -- agents/{host}/{aid}/
git -C {hp} push
```

See full protocol: `{hp}/AGENTS.md`
{end}
"""

KIMI_BLOCK_TEMPLATE = """\
{begin}
# Nestwork Startup Protocol

Before any analysis, planning, or implementation in a fresh session, ensure
nestwork context is loaded.

Kimi Code's SessionStart hook runs `git -C {hp} pull --rebase` for you, but
it does not inject additionalContext. Therefore you MUST Read the files
below yourself with your Read tool before your first reply.

Required at session start:

1. Pull: `git -C {hp} pull --rebase` (already done by the SessionStart hook)
2. Read each of the following (use your Read tool):
   - `{hp}/queen/agent-rules.md`
   - `{hp}/queen/strategy.md`
   - `{hp}/shared/memory.md`
   - `{hp}/agents/{host}/{aid}/memory.md`
3. Read on demand when task-relevant:
   - `{hp}/workflow/*.md` (portable methodology)
   - `{hp}/projects/<name>.md` (current task scope)

Skipping step 2 is a protocol violation: `agent-rules.md` requires you to
"say so -- do not guess" when context is missing, and step 2 is what
prevents the missing-context state.

## After loading -- self-direct, do not ask

You have enough signal to pick a next action without user prompting.
Before your first reply:

1. `git -C {hp} log --oneline -10 -- agents/` -- recent activity across
   every instance
2. `git -C {hp} log --oneline -5` -- recent protocol / shared changes
3. Cross-reference with `queen/strategy.md` **Current Priorities** and
   the latest entries in `shared/memory.md` / `agents/{host}/{aid}/memory.md`

Open with: **(a) state summary** (2-3 bullets on what's in flight, what
priorities say, what's blocking) and **(b) one concrete proposal** for
the next action (plus a short alternative if meaningful).

FORBIDDEN first replies: "What would you like me to do?" / "How can I
help?" / "Tell me what to do." Only if every source above is empty may
you ask -- and you must state that you checked and found nothing.

## Write protocol

- Only write to `{hp}/agents/{host}/{aid}/`
- PreToolUse / PostToolUse hooks handle commit+push for every Write/Edit
  under `agents/{host}/{aid}/`. If hooks are unavailable, run manually:

```bash
git -C {hp} add agents/{host}/{aid}/
git -C {hp} diff --cached --quiet -- agents/{host}/{aid}/ ||   git -C {hp} commit -m "memory: update {host}/{aid}" -- agents/{host}/{aid}/
git -C {hp} push
```

See full protocol: `{hp}/AGENTS.md`
{end}
"""


def strip_legacy_codex_bootstrap(content: str) -> str:
    if not LEGACY_CODEX_BOOTSTRAP_RE.search(content):
        return content
    if BEGIN in content:
        return content[content.index(BEGIN):].lstrip()
    if LEGACY_BEGIN in content:
        return content[content.index(LEGACY_BEGIN):].lstrip()
    return ""


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: _install-bootstrap.py <output_md> <nestwork_path> <host> <agent_id> [--tool=<tool>]",
            file=sys.stderr,
        )
        return 2

    out_path       = sys.argv[1]
    nestwork_path = sys.argv[2].replace("\\", "/").rstrip("/")
    host           = sys.argv[3]
    agent_id       = sys.argv[4]

    tool = ""
    if len(sys.argv) >= 6 and sys.argv[5].startswith("--tool="):
        tool = sys.argv[5][len("--tool="):].strip().lower()

    template = KIMI_BLOCK_TEMPLATE if tool == "kimi" else BLOCK_TEMPLATE
    block = template.format(
        begin=BEGIN, end=END, hp=nestwork_path, host=host, aid=agent_id
    )

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    existing = ""
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            existing = f.read()
    existing = strip_legacy_codex_bootstrap(existing)

    marker_pattern = re.compile(
        re.escape(BEGIN) + r".*?" + re.escape(END), re.DOTALL
    )
    legacy_marker_pattern = re.compile(
        re.escape(LEGACY_BEGIN) + r".*?" + re.escape(LEGACY_END), re.DOTALL
    )

    if marker_pattern.search(existing):
        # Replace only the marker block; keep user content outside intact.
        new_content = marker_pattern.sub(block.strip(), existing)
    elif legacy_marker_pattern.search(existing):
        # Upgrade older installed blocks to the new marker name.
        new_content = legacy_marker_pattern.sub(block.strip(), existing)
    elif existing.strip():
        # User already has unrelated content -- append the block after it.
        new_content = existing.rstrip() + "\n\n" + block
    else:
        new_content = block

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    mode = (
        "updated block" if marker_pattern.search(existing)
        else "updated legacy block" if legacy_marker_pattern.search(existing)
        else "appended block" if existing.strip()
        else "created"
    )
    print(f"nestwork bootstrap ({mode}) in {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

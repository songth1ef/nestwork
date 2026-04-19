#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# hivequeen bootstrap injector (shared by install-claude / install-gemini / ...)
#
# Idempotently writes a hivequeen startup protocol block into a tool-specific
# markdown (e.g. ~/.claude/CLAUDE.md, ~/.gemini/GEMINI.md). Uses HTML-comment
# markers so the user's own content in the same file is preserved across
# re-installs and upstream protocol bumps.
#
# Behaviour:
#   - File does not exist          -> create with just the hivequeen block
#   - File exists, no markers      -> append block after existing content
#   - File exists, markers present -> replace content between markers only
#
# Usage:
#   _install-bootstrap.py <output_md> <hivequeen_path> <host> <agent_id>
# -----------------------------------------------------------------------------

import os
import re
import sys

BEGIN = "<!-- hivequeen:begin -->"
END   = "<!-- hivequeen:end -->"

BLOCK_TEMPLATE = """\
{begin}
# Hivequeen Startup Protocol

Before starting analysis, planning, or implementation, run:

```bash
git -C {hp} pull --rebase
```

Then load context from hivequeen in this order:

1. `{hp}/queen/agent-rules.md`
2. `{hp}/queen/strategy.md`
3. `{hp}/shared/memory.md`
4. `{hp}/agents/{host}/{aid}/memory.md`
5. Relevant `{hp}/projects/*.md` for current task

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


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: _install-bootstrap.py <output_md> <hivequeen_path> <host> <agent_id>",
            file=sys.stderr,
        )
        return 2

    out_path       = sys.argv[1]
    hivequeen_path = sys.argv[2].replace("\\", "/").rstrip("/")
    host           = sys.argv[3]
    agent_id       = sys.argv[4]

    block = BLOCK_TEMPLATE.format(
        begin=BEGIN, end=END, hp=hivequeen_path, host=host, aid=agent_id
    )

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    existing = ""
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            existing = f.read()

    marker_pattern = re.compile(
        re.escape(BEGIN) + r".*?" + re.escape(END), re.DOTALL
    )

    if marker_pattern.search(existing):
        # Replace only the marker block; keep user content outside intact.
        new_content = marker_pattern.sub(block.strip(), existing)
    elif existing.strip():
        # User already has unrelated content -- append the block after it.
        new_content = existing.rstrip() + "\n\n" + block
    else:
        new_content = block

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    mode = (
        "updated block" if marker_pattern.search(existing)
        else "appended block" if existing.strip()
        else "created"
    )
    print(f"hivequeen bootstrap ({mode}) in {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

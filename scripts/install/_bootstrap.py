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
# Nestwork Startup Protocol — resident and on-demand context

At session start, pull `{hp}` with `git pull --rebase` unless a startup
hook already refreshed it. If unavailable, report the limitation and use local context.
Read only these resident files (skip a missing optional resident file):
- `{hp}/queen/agent-rules.md`
- `{hp}/shared/resident.md`
- `{hp}/agents/{host}/{aid}/resident.md`

A hook may provide a READ-ON-START manifest; read those paths unless their
contents are already supplied. Missing resident files do not make historical
memory mandatory. Do not recursively load links from resident files.

On demand: search headings/keywords before reading relevant sections of
`{hp}/shared/memory.md`, `{hp}/agents/{host}/{aid}/memory.md`,
`{hp}/projects/`, and `{hp}/workflow/`. Read `{hp}/queen/strategy.md`
when prioritizing work or discussing direction. Check recent git activity only
when resuming work, coordinating agents, or maintaining Nestwork.
Follow the user's current task; unrelated project history is not an assignment.

Within the Nestwork repository, ordinary memory writes belong only in
`{hp}/agents/{host}/{aid}/`. This restriction does not govern files in other
projects or user-requested artifacts. Protocol/shared changes need task-specific
authorization. Read `{hp}/AGENTS.md` and `{hp}/docs/context-loading.md`
when maintaining Nestwork or changing shared context.

If memory changed and no sync hooks handle it, sync only your agent directory:
```bash
git -C {hp} add agents/{host}/{aid}/
git -C {hp} diff --cached --quiet -- agents/{host}/{aid}/ || \
  git -C {hp} commit -m "memory: update {host}/{aid}" -- agents/{host}/{aid}/
git -C {hp} push
```
{end}
"""

# Kimi runs SessionStart but does not inject additionalContext; the explicit
# file reads in the common bootstrap work with and without injected context.
KIMI_BLOCK_TEMPLATE = BLOCK_TEMPLATE


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

#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# hivequeen memory distiller (LLM-oriented variant of compile.sh)
#
# Walks every agents/<id>/memory.md, reads the current shared/memory.md, and
# prints a single prompt suitable for an LLM agent to merge into a new
# shared/memory.md per AGENTS.md section 7.
#
# Piggyback a compile step:
#
#   bash scripts/maintenance/compile.sh        # mechanical concat (fast, no LLM)
#   python3 scripts/maintenance/distill.py     # LLM prompt (run the output
#                                              # through a Claude/Gemini/etc.
#                                              # session, commit the result)
#
# Attribution: originally drafted by a Codex agent in myhivequeen
# (commit a1e5713) and ported into the shared template here.
# -----------------------------------------------------------------------------

import io
import os
import sys
from datetime import datetime, timezone


def read_file_robust(path: str) -> str | None:
    """Read a memory file, tolerating a handful of plausible encodings.

    Agent memories are written by many different tools on many different
    machines; a single utf-8 read can blow up on Windows-authored files
    saved as utf-16 / gbk / utf-8-sig. Fail silently and return None so
    the caller can skip the file rather than abort the whole distill.
    """
    for enc in ("utf-8-sig", "utf-16", "gbk", "utf-8", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read().strip()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def main() -> int:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    hp = os.path.abspath(os.path.join(script_dir, "..", "..")).replace("\\", "/")
    agents_dir  = f"{hp}/agents"
    shared_file = f"{hp}/shared/memory.md"

    if not os.path.exists(agents_dir):
        print(f"Error: agents/ not found at {agents_dir}", file=sys.stderr)
        return 1

    memory_data = []
    for agent_id in sorted(os.listdir(agents_dir)):
        m_path = f"{agents_dir}/{agent_id}/memory.md"
        if os.path.isfile(m_path):
            content = read_file_robust(m_path)
            if content and "_No memory yet._" not in content:
                memory_data.append({"id": agent_id, "content": content})

    if not memory_data:
        print("No meaningful agent memory found to distill.")
        return 0

    current_shared = read_file_robust(shared_file) or ""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Force utf-8 stdout on Windows so the printed prompt round-trips through
    # a file redirect (`python3 distill.py > prompt.md`) without mojibake.
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("--- DISTILLATION PROMPT BEGIN ---")
    print(f"Date: {now}")
    print("\n# TASK: Distill Agent Memories into Shared Memory")
    print("\nYou are the Hive Queen distiller. Your goal is to merge individual "
          "agent observations into the central `shared/memory.md` according to "
          "the protocol in `AGENTS.md` section 7.")
    print("\n## Rules:")
    print("1. Merge cross-agent stable facts (user identity, tech stack, preferences).")
    print("2. Keep divergent observations if they are consistent (different machines / tools).")
    print("3. Filter out temporary task details or one-off debugging notes.")
    print("4. NEVER delete facts from shared memory; only add, update, or unify.")
    print("5. Use clean Markdown structure.")

    print("\n## Current shared/memory.md:")
    print("```markdown")
    print(current_shared if current_shared else "(Empty)")
    print("```")

    for m in memory_data:
        print(f"\n## Private memory from agent: {m['id']}")
        print("```markdown")
        print(m["content"])
        print("```")

    print("\n## Instruction:")
    print("Analyze the content above. Output the FULL contents for the new "
          "`shared/memory.md`. Wrap your output in a single markdown block.")
    print("--- DISTILLATION PROMPT END ---")

    return 0


if __name__ == "__main__":
    sys.exit(main())

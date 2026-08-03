#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# nestwork hook remover for Codex CLI (inverse of scripts/install/_codex_hooks.py)
#
# Deletes the nestwork hook from Stop or SessionEnd, matching with the installer's
# own predicate so any command the installer would supersede gets removed.
# `hooksPath` in config.toml is left in place: it is a generic pointer to
# hooks.json, which may still hold the user's own hooks.
#
# Usage:
#   _codex_unhooks.py <hooks.json>
# -----------------------------------------------------------------------------

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir, "install"))
from _codex_hooks import is_nestwork_hook  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: _codex_unhooks.py <hooks_json>", file=sys.stderr)
        return 2

    hooks_path = sys.argv[1]
    if not os.path.exists(hooks_path):
        print(f"nestwork Codex hook: {hooks_path} does not exist (nothing to remove)")
        return 0

    with open(hooks_path, encoding="utf-8") as f:
        data = json.load(f)

    removed = 0
    events = data.get("hooks") or {}
    for event in ("Stop", "SessionEnd"):
        kept = []
        for entry in events.get(event, []):
            commands = [
                hook.get("command", "")
                for hook in entry.get("hooks", [])
                if isinstance(hook, dict)
            ]
            if any(is_nestwork_hook(c) for c in commands):
                removed += 1
            else:
                kept.append(entry)
        if kept:
            events[event] = kept
        else:
            events.pop(event, None)

    if not removed:
        print(f"nestwork Codex hook: none found in {hooks_path} (nothing to remove)")
        return 0

    with open(hooks_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"removed {removed} nestwork Codex hook(s) from {hooks_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

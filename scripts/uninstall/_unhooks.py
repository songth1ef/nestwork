#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# nestwork hook remover for Claude Code (inverse of scripts/install/_hooks.py)
#
# Deletes every nestwork-installed hook entry from settings.json across all
# five events (SessionStart / PreToolUse / PostToolUse / Stop / SessionEnd),
# using the same matcher the installer uses to supersede prior installs --
# so anything the installer would replace, the uninstaller removes.
# User-defined hooks in the same file are preserved untouched.
#
# Usage:
#   _unhooks.py <settings.json> <host> <agent_id>
#
# host / agent_id may be empty strings: the matcher then falls back to the
# nestwork script-name patterns, which cover every standard install.
# -----------------------------------------------------------------------------

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir, "install"))
from _hooks import is_nestwork_hook  # noqa: E402

EVENTS = ["SessionStart", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"]


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: _unhooks.py <settings_path> <host> <agent_id>",
              file=sys.stderr)
        return 2

    settings_path = sys.argv[1]
    host          = sys.argv[2]
    agent_id      = sys.argv[3]

    if not os.path.exists(settings_path):
        print(f"nestwork hooks: {settings_path} does not exist (nothing to remove)")
        return 0

    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)

    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        print(f"nestwork hooks: no hooks in {settings_path} (nothing to remove)")
        return 0

    removed = 0
    for event in EVENTS:
        entries = hooks.get(event)
        if not isinstance(entries, list):
            continue
        kept = []
        for e in entries:
            inner = (e.get("hooks") or [{}])[0].get("command", "")
            if is_nestwork_hook(inner, host, agent_id):
                removed += 1
            else:
                kept.append(e)
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    if not hooks:
        settings.pop("hooks", None)

    if not removed:
        print(f"nestwork hooks: none found in {settings_path} (nothing to remove)")
        return 0

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

    print(f"removed {removed} nestwork hook(s) from {settings_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

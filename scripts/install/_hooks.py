#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# nestwork hook installer (shared by install-claude.sh and install-claude.ps1)
#
# Merges SessionStart / PreToolUse / PostToolUse / Stop / SessionEnd hooks
# into Claude Code settings.json.
# Safe to re-run: removes prior nestwork entries before inserting new ones.
#
# Usage:
#   _install-hooks.py <settings.json> <nestwork_path> <host> <agent_id>
#
# Why a separate script: PowerShell's ConvertTo-Json mishandles single-element
# nested arrays (serializes them as objects), and repeating the merge logic in
# two shells invites drift. Centralising in Python keeps behaviour identical.
# -----------------------------------------------------------------------------

import json
import os
import sys


def is_nestwork_hook(cmd: str, host: str, agent_id: str) -> bool:
    """Return True if a stored hook command was installed by nestwork.

    Matches legacy flat layout, v1 subdir layout, and current v2 layout so
    re-running the installer cleanly supersedes any prior install.
    """
    legacy_hook = "hive" + "queen.sh"
    legacy_flat_hook = "hook-" + legacy_hook
    if "hook-nestwork.sh" in cmd or "hooks/nestwork.sh" in cmd:
        return True
    if legacy_flat_hook in cmd or f"hooks/{legacy_hook}" in cmd:
        return True
    if "export-claude-mem.sh" in cmd:
        return True
    if "sync-local-history.sh" in cmd:
        return True
    if "session-start.sh" in cmd:
        return True
    if f"memory: update {agent_id}" in cmd or f"memory: update {host}/{agent_id}" in cmd:
        return True
    if agent_id in cmd and "git push" in cmd:
        return True
    return False


def upsert(hooks: dict, event: str, matcher: str, cmd: str,
           host: str, agent_id: str) -> None:
    entries = hooks.get(event, [])
    filtered = []
    for e in entries:
        inner = (e.get("hooks") or [{}])[0].get("command", "")
        if not is_nestwork_hook(inner, host, agent_id):
            filtered.append(e)
    filtered.append({
        "matcher": matcher,
        "hooks":   [{"type": "command", "command": cmd}],
    })
    hooks[event] = filtered


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: _install-hooks.py <settings_path> <nestwork_path> <host> <agent_id>",
            file=sys.stderr,
        )
        return 2

    settings_path  = sys.argv[1]
    nestwork_path = sys.argv[2].replace("\\", "/").rstrip("/")
    host           = sys.argv[3]
    agent_id       = sys.argv[4]

    hook_script   = f"{nestwork_path}/scripts/hooks/nestwork.sh"
    export_mem    = f"{nestwork_path}/scripts/hooks/export-claude-mem.sh"
    sync_local    = f"{nestwork_path}/scripts/hooks/sync-local-history.sh"
    session_start = f"{nestwork_path}/scripts/hooks/session-start.sh"

    start_cmd = f"bash {session_start} {host} {agent_id}"
    pre_cmd  = f"bash {hook_script} pre {host} {agent_id}"
    post_cmd = f"bash {hook_script} post {host} {agent_id}"
    stop_cmd = f"bash {hook_script} stop {host} {agent_id}"
    session_end_cmd = (
        f"bash {export_mem} {host} {agent_id}; "
        f"bash {sync_local} {host} {agent_id}"
    )

    os.makedirs(os.path.dirname(settings_path) or ".", exist_ok=True)
    if not os.path.exists(settings_path):
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)

    hooks = settings.setdefault("hooks", {})
    upsert(hooks, "SessionStart", "",           start_cmd,       host, agent_id)
    upsert(hooks, "PreToolUse",   "Write|Edit", pre_cmd,         host, agent_id)
    upsert(hooks, "PostToolUse",  "Write|Edit", post_cmd,        host, agent_id)
    upsert(hooks, "Stop",         "",           stop_cmd,        host, agent_id)
    upsert(hooks, "SessionEnd",   "",           session_end_cmd, host, agent_id)

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

    print(f"nestwork hooks registered in {settings_path} for {host}/{agent_id}")
    print(f"  SessionStart             -> {start_cmd}")
    print(f"  PreToolUse  (Write|Edit) -> {pre_cmd}")
    print(f"  PostToolUse (Write|Edit) -> {post_cmd}")
    print(f"  Stop                     -> {stop_cmd}")
    print(f"  SessionEnd               -> {session_end_cmd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

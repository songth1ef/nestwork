#!/usr/bin/env python3
"""Register the Nestwork Codex hooks in current Codex configuration.

Hooks written to ~/.codex/hooks.json:
  PreToolUse  (apply_patch) -> nestwork.sh pre   pull --rebase before a memory write
  PostToolUse (apply_patch) -> nestwork.sh post  commit + push the write
  Stop                      -> nestwork.sh stop  safety net at the end of a turn
  SessionEnd                -> launch-local-history-sync.py (local-history snapshot)

Re-running is idempotent: every prior nestwork entry is dropped before the
current set is appended, and entries that are not nestwork's are kept.
"""

import json
import os
import re
import shlex
import sys


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def install_hooks_path(config: str, hooks_path: str) -> str:
    line = f"hooksPath = {toml_string(hooks_path)}"
    core = re.search(r"(?ms)^\[core\]\s*\n(?P<body>.*?)(?=^\[|\Z)", config)
    if core:
        body = core.group("body")
        if re.search(r"(?m)^\s*hooksPath\s*=", body):
            body = re.sub(r"(?m)^\s*hooksPath\s*=.*$", line, body, count=1)
        else:
            body = line + "\n" + body
        return config[: core.start("body")] + body + config[core.end("body") :]
    suffix = "" if not config or config.endswith("\n") else "\n"
    prefix = "" if not config else "\n"
    return config + suffix + prefix + "[core]\n" + line + "\n"


# Codex hands apply_patch edits to hooks with tool_name "apply_patch" and
# also accepts the Edit / Write aliases in matchers; anchor so unrelated tools
# (e.g. mcp__*__write_file) never spawn the hook.
WRITE_MATCHER = "^(apply_patch|Edit|Write)$"
NESTWORK_EVENTS = ("PreToolUse", "PostToolUse", "Stop", "SessionEnd")


def is_nestwork_hook(command: str) -> bool:
    # Match on nestwork's own script paths, like the Claude installer does. Do
    # not require "nestwork" in the command: a nest cloned to ~/memory or
    # ~/my-nest has no such substring, and re-installing would stack duplicate
    # hooks instead of replacing them.
    command = command.replace("\\", "/")
    return (
        "scripts/hooks/nestwork.sh" in command
        or "scripts/hooks/launch-local-history-sync.py" in command
        or "scripts/hooks/sync-local-history.sh" in command
    )


def remove_existing_nestwork_hooks(hooks: dict) -> None:
    events = hooks.setdefault("hooks", {})
    for event in NESTWORK_EVENTS:
        retained = []
        for entry in events.get(event, []):
            commands = [
                hook.get("command", "")
                for hook in entry.get("hooks", [])
                if isinstance(hook, dict)
            ]
            if not any(is_nestwork_hook(item) for item in commands):
                retained.append(entry)
        if retained:
            events[event] = retained
        else:
            events.pop(event, None)


def upsert_nestwork_hooks(
    hooks: dict, nestwork_path: str, host: str, agent_id: str, platform: str
) -> None:
    remove_existing_nestwork_hooks(hooks)
    events = hooks["hooks"]

    def add(event: str, command: str, timeout: int, matcher: str = "") -> None:
        entry: dict = {}
        if matcher:
            entry["matcher"] = matcher
        entry["hooks"] = [{"type": "command", "command": command, "timeout": timeout}]
        events.setdefault(event, []).append(entry)

    add("PreToolUse", sync_command("pre", nestwork_path, host, agent_id, platform),
        30, WRITE_MATCHER)
    add("PostToolUse", sync_command("post", nestwork_path, host, agent_id, platform),
        60, WRITE_MATCHER)
    add("Stop", sync_command("stop", nestwork_path, host, agent_id, platform), 60)
    # Codex caps SessionEnd at 3s, hence the detached launcher.
    add("SessionEnd", hook_command(nestwork_path, host, agent_id, platform), 3)


def join_command(args: list, platform: str) -> str:
    if platform == "windows":
        import subprocess

        return subprocess.list2cmdline(args)
    return shlex.join(args)


def sync_command(
    phase: str, nestwork_path: str, host: str, agent_id: str, platform: str
) -> str:
    # Same per-write sync script as Claude Code / Kimi Code; on Windows it
    # needs Git Bash's `bash` on PATH, exactly like the Claude installer.
    script = f"{nestwork_path}/scripts/hooks/nestwork.sh"
    return join_command(["bash", script, phase, host, agent_id], platform)


def hook_command(nestwork_path: str, host: str, agent_id: str, platform: str) -> str:
    script = f"{nestwork_path}/scripts/hooks/launch-local-history-sync.py"
    args = [sys.executable, script, nestwork_path, host, agent_id]
    return join_command(args, platform)


def main() -> int:
    if len(sys.argv) != 6:
        print(
            "usage: _codex_hooks.py <config.toml> <hooks.json> "
            "<nestwork_path> <host> <agent_id>",
            file=sys.stderr,
        )
        return 2

    config_path, hooks_path, nestwork_path, host, agent_id = sys.argv[1:]
    platform = os.environ.get("NESTWORK_CODEX_PLATFORM", "posix")
    if platform not in {"posix", "windows"}:
        print("NESTWORK_CODEX_PLATFORM must be posix or windows", file=sys.stderr)
        return 2

    nestwork_path = nestwork_path.replace("\\", "/").rstrip("/")
    hooks_path = hooks_path.replace("\\", "/")
    os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(hooks_path) or ".", exist_ok=True)

    config = ""
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as file:
            config = file.read()
    updated_config = install_hooks_path(config, hooks_path)
    with open(config_path, "w", encoding="utf-8") as file:
        file.write(updated_config)

    hooks = {}
    if os.path.exists(hooks_path):
        with open(hooks_path, encoding="utf-8") as file:
            hooks = json.load(file)
    upsert_nestwork_hooks(hooks, nestwork_path, host, agent_id, platform)
    with open(hooks_path, "w", encoding="utf-8") as file:
        json.dump(hooks, file, indent=2)
        file.write("\n")

    print(f"nestwork Codex hooks registered in {hooks_path} for {host}/{agent_id}")
    print(f"  PreToolUse  ({WRITE_MATCHER}) -> nestwork.sh pre")
    print(f"  PostToolUse ({WRITE_MATCHER}) -> nestwork.sh post")
    print("  Stop                                 -> nestwork.sh stop")
    print("  SessionEnd                           -> launch-local-history-sync.py")
    print("  Codex asks you to review and trust new or changed hooks: run /hooks once.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

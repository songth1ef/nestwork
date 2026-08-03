#!/usr/bin/env python3
"""Register the Nestwork Codex SessionEnd hook in current Codex configuration."""

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


def is_nestwork_hook(command: str) -> bool:
    return (
        "nestwork" in command
        and (
            "sync-local-history.sh" in command
            or "launch-local-history-sync.py" in command
        )
    )


def remove_existing_nestwork_hooks(hooks: dict) -> None:
    events = hooks.setdefault("hooks", {})
    for event in ("Stop", "SessionEnd"):
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


def upsert_session_end_hook(hooks: dict, command: str) -> None:
    remove_existing_nestwork_hooks(hooks)
    hooks["hooks"].setdefault("SessionEnd", []).append(
        {
            "hooks": [
                {"type": "command", "command": command, "timeout": 3}
            ]
        }
    )


def hook_command(nestwork_path: str, host: str, agent_id: str, platform: str) -> str:
    script = f"{nestwork_path}/scripts/hooks/launch-local-history-sync.py"
    args = [sys.executable, script, nestwork_path, host, agent_id]
    if platform == "windows":
        import subprocess

        return subprocess.list2cmdline(args)
    return shlex.join(args)


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
    upsert_session_end_hook(
        hooks, hook_command(nestwork_path, host, agent_id, platform)
    )
    with open(hooks_path, "w", encoding="utf-8") as file:
        json.dump(hooks, file, indent=2)
        file.write("\n")

    print(
        f"nestwork Codex SessionEnd hook registered in {hooks_path} "
        f"for {host}/{agent_id}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

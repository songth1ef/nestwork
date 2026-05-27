#!/usr/bin/env python3
"""Register the Nestwork Codex Stop hook in current Codex CLI configuration."""

import json
import os
import re
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
    return "sync-local-history.sh" in command and "nestwork" in command


def upsert_stop_hook(hooks: dict, command: str) -> None:
    stop_hooks = hooks.setdefault("hooks", {}).get("Stop", [])
    retained = []
    for entry in stop_hooks:
        commands = [
            hook.get("command", "")
            for hook in entry.get("hooks", [])
            if isinstance(hook, dict)
        ]
        if not any(is_nestwork_hook(item) for item in commands):
            retained.append(entry)
    retained.append(
        {
            "hooks": [
                {"type": "command", "command": command, "timeout": 60}
            ]
        }
    )
    hooks["hooks"]["Stop"] = retained


def hook_command(nestwork_path: str, host: str, agent_id: str, platform: str) -> str:
    script = f"{nestwork_path}/scripts/hooks/sync-local-history.sh"
    if platform == "windows":
        return (
            "bash -lc 'bash "
            f'"{script}" "{host}" "{agent_id}" '
            '>> "${TEMP:-/tmp}/nestwork-codex-stop-hook.log" 2>&1; '
            'printf "{}\\n"\''
        )
    return (
        "bash -lc 'bash "
        f'"{script}" "{host}" "{agent_id}" '
        '>> "${TMPDIR:-/tmp}/nestwork-codex-stop-hook.log" 2>&1; '
        'printf "{}\\n"\''
    )


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
    upsert_stop_hook(hooks, hook_command(nestwork_path, host, agent_id, platform))
    with open(hooks_path, "w", encoding="utf-8") as file:
        json.dump(hooks, file, indent=2)
        file.write("\n")

    print(f"nestwork Codex Stop hook registered in {hooks_path} for {host}/{agent_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

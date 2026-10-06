#!/usr/bin/env python3
"""Register the Nestwork Antigravity hooks in hooks.json.

Hooks written to ~/.gemini/config/hooks.json (under "nestwork" key):
  PreInvocation -> antigravity-session-start.py
  Stop          -> antigravity-sync.py

Re-running is idempotent: existing "nestwork" hook entry is updated,
while user-defined hooks in hooks.json are preserved.
"""

import json
import os
import sys


def upsert_nestwork_hooks(
    data: dict, nestwork_path: str, host: str, agent_id: str, platform: str
) -> None:
    py_bin = "python" if platform == "windows" else "python3"
    start_script = f"{nestwork_path}/scripts/hooks/antigravity-session-start.py"
    sync_script = f"{nestwork_path}/scripts/hooks/antigravity-sync.py"

    start_cmd = f'{py_bin} "{start_script}" "{nestwork_path}" "{host}" "{agent_id}"'
    sync_cmd = f'{py_bin} "{sync_script}" "{nestwork_path}" "{host}" "{agent_id}"'

    data["nestwork"] = {
        "PreInvocation": [
            {
                "type": "command",
                "command": start_cmd,
                "timeout": 30,
            }
        ],
        "Stop": [
            {
                "type": "command",
                "command": sync_cmd,
                "timeout": 45,
            }
        ],
    }


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: _antigravity_hooks.py <hooks_json> <nestwork_path> <host> <agent_id>",
            file=sys.stderr,
        )
        return 2

    hooks_path, nestwork_path, host, agent_id = sys.argv[1:5]
    platform = os.environ.get("NESTWORK_ANTIGRAVITY_PLATFORM", "windows" if os.name == "nt" else "posix")

    nestwork_path = nestwork_path.replace("\\", "/").rstrip("/")
    hooks_path = os.path.abspath(hooks_path)
    os.makedirs(os.path.dirname(hooks_path) or ".", exist_ok=True)

    data = {}
    if os.path.exists(hooks_path):
        try:
            with open(hooks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    upsert_nestwork_hooks(data, nestwork_path, host, agent_id, platform)

    with open(hooks_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"nestwork Antigravity hooks registered in {hooks_path} for {host}/{agent_id}")
    print("  PreInvocation -> antigravity-session-start.py")
    print("  Stop          -> antigravity-sync.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

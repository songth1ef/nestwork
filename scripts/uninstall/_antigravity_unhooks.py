#!/usr/bin/env python3
"""Remove the Nestwork Antigravity hooks from hooks.json.

Removes the "nestwork" key while preserving any user-defined hooks.
Usage:
  _antigravity_unhooks.py <hooks_json>
"""

import json
import os
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: _antigravity_unhooks.py <hooks_json>", file=sys.stderr)
        return 2

    hooks_path = sys.argv[1]
    if not os.path.exists(hooks_path):
        print(f"nestwork Antigravity hooks: {hooks_path} does not exist (nothing to remove)")
        return 0

    try:
        with open(hooks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        print(f"nestwork Antigravity hooks: failed to read {hooks_path}")
        return 1

    if "nestwork" not in data:
        print(f"nestwork Antigravity hooks: no nestwork entry in {hooks_path} (nothing to remove)")
        return 0

    del data["nestwork"]

    with open(hooks_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"removed nestwork Antigravity hooks from {hooks_path} (user hooks preserved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

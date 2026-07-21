#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# nestwork hook remover for Kimi Code (inverse of scripts/install/_kimi_hooks.py)
#
# Deletes the nestwork hook block from ~/.kimi-code/config.toml using the same
# comment markers the installer uses. User hooks and other config outside the
# markers are preserved.
#
# Usage:
#   _kimi_unhooks.py <config.toml>
# -----------------------------------------------------------------------------

import os
import sys

BEGIN_MARK = "# === nestwork hooks begin ==="
END_MARK   = "# === nestwork hooks end ==="


def strip_block(content: str) -> tuple[str, bool]:
    lines = content.splitlines(keepends=True)
    result = []
    in_block = False
    removed = False
    for line in lines:
        if BEGIN_MARK in line:
            in_block = True
            removed = True
            continue
        if END_MARK in line:
            in_block = False
            continue
        if not in_block:
            result.append(line)
    # Collapse multiple blank lines left by the removed block
    text = "".join(result)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text, removed


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: _kimi_unhooks.py <config.toml>", file=sys.stderr)
        return 2

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"nestwork Kimi hooks: {config_path} does not exist (nothing to remove)")
        return 0

    with open(config_path, encoding="utf-8") as f:
        content = f.read()

    content, removed = strip_block(content)
    if not removed:
        print(f"nestwork Kimi hooks: no marker block in {config_path} (nothing to remove)")
        return 0

    if not content.strip():
        os.remove(config_path)
        print(f"nestwork Kimi hooks removed; deleted now-empty {config_path}")
    else:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"nestwork Kimi hooks removed from {config_path} (user config preserved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

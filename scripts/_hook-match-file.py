#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# hivequeen hook helper: file-path matcher
#
# Reads Claude Code hook JSON from stdin (with tool_input.file_path), and
# compares it to <hivequeen>/agents/<agent-id>/. Exit 0 on match, 1 otherwise.
#
# Invoked by hook-hivequeen.sh — kept in a separate file so bash can forward
# stdin to python without heredoc collisions.
# ─────────────────────────────────────────────────────────────────────────────

import json
import os
import sys


def norm(p: str) -> str:
    p = p.replace('\\', '/')
    # Windows drive letter: C:/... -> /c/...
    if len(p) >= 2 and p[1] == ':':
        p = '/' + p[0].lower() + p[2:]
    return os.path.normpath(p).replace('\\', '/').rstrip('/')


def main() -> int:
    if len(sys.argv) < 3:
        return 1
    hivequeen_path, agent_id = sys.argv[1], sys.argv[2]

    try:
        data = json.load(sys.stdin)
    except Exception:
        return 1

    file_path = (data.get('tool_input') or {}).get('file_path', '')
    if not file_path:
        return 1

    target = norm(file_path)
    agent_dir = norm(os.path.join(hivequeen_path, 'agents', agent_id))

    if target == agent_dir or target.startswith(agent_dir + '/'):
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())

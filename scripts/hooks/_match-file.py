#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# nestwork hook helper: file-path matcher
#
# Reads hook JSON from stdin and compares the written path(s) to
# <nestwork>/agents/<host>/<agent-id>/. Exit 0 on match, 1 otherwise.
#
# Accepted payload shapes:
#   - Claude Code / Kimi Code: tool_input.file_path (absolute path)
#   - Codex CLI apply_patch:   tool_input.command holds the raw patch text;
#     target paths come from its "*** Add File: / Update File: / Delete File: /
#     Move to:" headers and are resolved against the payload's top-level cwd
#     when relative. Any one target inside the agent dir counts as a match.
#
# Invoked by hook-nestwork.sh -- kept in a separate file so bash can forward
# stdin to python without heredoc collisions.
# -----------------------------------------------------------------------------

import json
import os
import re
import sys

# Patch headers per Codex's apply_patch grammar (codex-rs/core/assets/tools/
# apply_patch.lark). Anchored at column 0 on purpose: hunk body lines start
# with '+', '-' or ' ', so a header quoted inside file content never matches.
PATCH_HEADER = re.compile(
    r'^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+?)\s*$'
)


def norm(p: str) -> str:
    p = p.replace('\\', '/')
    # Windows drive letter: C:/... -> /c/...
    if len(p) >= 2 and p[1] == ':':
        p = '/' + p[0].lower() + p[2:]
    return os.path.normpath(p).replace('\\', '/').rstrip('/')


def patch_paths(patch: str, cwd: str) -> list:
    paths = []
    for line in patch.splitlines():
        m = PATCH_HEADER.match(line)
        if not m:
            continue
        path = m.group(1)
        if not os.path.isabs(path) and not re.match(r'^[A-Za-z]:[\\/]', path):
            path = os.path.join(cwd or os.getcwd(), path)
        paths.append(path)
    return paths


def candidate_paths(data: dict) -> list:
    tool_input = data.get('tool_input') or {}
    if not isinstance(tool_input, dict):
        return []
    file_path = tool_input.get('file_path')
    if isinstance(file_path, str) and file_path:
        return [file_path]
    command = tool_input.get('command')
    if isinstance(command, str) and '*** Begin Patch' in command:
        cwd = data.get('cwd') if isinstance(data.get('cwd'), str) else ''
        return patch_paths(command, cwd)
    return []


def main() -> int:
    if len(sys.argv) < 4:
        return 1
    nestwork_path = sys.argv[1]
    host           = sys.argv[2]
    agent_id       = sys.argv[3]

    try:
        data = json.load(sys.stdin)
    except Exception:
        return 1

    if not isinstance(data, dict):
        return 1

    agent_dir = norm(os.path.join(nestwork_path, 'agents', host, agent_id))
    for path in candidate_paths(data):
        target = norm(path)
        if target == agent_dir or target.startswith(agent_dir + '/'):
            return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())

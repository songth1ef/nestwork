#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# hivequeen identity resolver (protocol v2.0)
#
# Returns (host, agent-id) for this machine, creating them on first run and
# caching on disk so reinstalls keep the same identity. One file:
#
#   ~/.hivequeen_id              two lines:
#                                1. lowercased short hostname
#                                2. per-tool agent id (e.g. "claude-a7k2")
#
# Usage:
#   _identity.py <tool> [--with-suffix]
#
#   <tool>            prefix used for the agent-id (claude / codex / ...)
#   --with-suffix     append a 4-char random suffix, persisted across reinstalls
#
# Env overrides (highest priority, not persisted):
#   HIVEQUEEN_HOST       override host segment
#   HIVEQUEEN_AGENT_ID   override full agent-id
#
# Output: prints two lines to stdout
#   <host>
#   <agent-id>
#
# Legacy migration:
# - if ~/.hivequeen_host exists and ~/.hivequeen_id is one line, merge both into
#   the v2 single-file format.
# - if ~/.hivequeen_id contains an old v1 three-segment id
#   (<tool>-<host>-<suffix>), extract <host> to ~/.hivequeen_host and rewrite
#   ~/.hivequeen_id as two lines: <host>, <tool>-<suffix>.
# -----------------------------------------------------------------------------

import os
import random
import re
import socket
import string
import sys

HOST_FILE = os.path.join(os.path.expanduser("~"), ".hivequeen_host")
ID_FILE   = os.path.join(os.path.expanduser("~"), ".hivequeen_id")


def compute_host() -> str:
    h = socket.gethostname() or "unknown"
    return h.split(".")[0].lower()


def random_suffix(n: int = 4) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def read_one_line(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def write_one_line(path: str, value: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(value + "\n")


def read_lines(path: str) -> list[str]:
    try:
        with open(path, encoding="utf-8") as f:
            return [line.strip() for line in f.read().splitlines() if line.strip()]
    except FileNotFoundError:
        return []


def write_identity(host: str, agent_id: str) -> None:
    with open(ID_FILE, "w", encoding="utf-8") as f:
        f.write(host + "\n")
        f.write(agent_id + "\n")


# v1 legacy ids look like: <tool>-<host>-<4-char-suffix>
# Heuristic: exactly three segments split by '-', final segment is [a-z0-9]{4}.
LEGACY_ID_RE = re.compile(r"^([a-z]+)-([a-z0-9][a-z0-9-]*?)-([a-z0-9]{4})$")


def migrate_legacy_if_needed(tool: str) -> None:
    """Normalize legacy identity files into the single v2 two-line file."""
    host = read_one_line(HOST_FILE)
    identity = read_lines(ID_FILE)

    if host and len(identity) == 1:
        write_identity(host, identity[0])
        return

    if len(identity) != 1:
        return

    legacy = identity[0]
    m = LEGACY_ID_RE.match(legacy)
    if not m:
        return

    legacy_tool, legacy_host, legacy_suffix = m.group(1), m.group(2), m.group(3)
    agent_id = f"{tool}-{legacy_suffix}" if legacy_tool == tool else legacy
    write_identity(legacy_host, agent_id)


def resolve_host() -> str:
    env = os.environ.get("HIVEQUEEN_HOST", "").strip()
    if env:
        return env.lower()
    identity = read_lines(ID_FILE)
    if len(identity) >= 2:
        return identity[0]
    host = compute_host()
    return host


def resolve_agent_id(tool: str, with_suffix: bool) -> str:
    env = os.environ.get("HIVEQUEEN_AGENT_ID", "").strip()
    if env:
        return env
    identity = read_lines(ID_FILE)
    cached = identity[1] if len(identity) >= 2 else ""
    if not with_suffix:
        return tool
    if cached and cached.startswith(tool + "-") and LEGACY_ID_RE.match(cached) is None:
        # v2 format: <tool>-<suffix>
        return cached
    if cached and cached == tool:
        return cached
    new_id = f"{tool}-{random_suffix()}"
    write_one_line(ID_FILE, new_id)
    return new_id


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: _identity.py <tool> [--with-suffix]", file=sys.stderr)
        return 2
    tool = sys.argv[1].strip().lower()
    with_suffix = "--with-suffix" in sys.argv[2:]

    migrate_legacy_if_needed(tool)

    host     = resolve_host()
    agent_id = resolve_agent_id(tool, with_suffix)

    if not os.environ.get("HIVEQUEEN_HOST", "").strip() and not os.environ.get("HIVEQUEEN_AGENT_ID", "").strip():
        write_identity(host, agent_id)

    print(host)
    print(agent_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())

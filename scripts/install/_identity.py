#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# nestwork identity resolver
#
# Returns (host, agent-id) for this machine, caching a shared host plus one
# agent id per tool so installing Codex cannot overwrite a Claude identity.
#
# Current files:
#   ~/.nestwork_host                 lowercased short hostname
#   ~/.nestwork_id_<tool>            agent id for that tool
#                                     (e.g. claude-a7k2, codex)
#
# Legacy ~/.nestwork_id and hivequeen identity files are read for migration,
# but never overwritten by this version.
# -----------------------------------------------------------------------------

import os
import random
import re
import socket
import string
import sys

HOME = os.path.expanduser("~")
HOST_FILE = os.path.join(HOME, ".nestwork_host")
LEGACY_ID_FILE = os.path.join(HOME, ".nestwork_id")
LEGACY_HIVE_HOST_FILE = os.path.join(HOME, "." + "hive" + "queen_host")
LEGACY_HIVE_ID_FILE = os.path.join(HOME, "." + "hive" + "queen_id")

# v1 ids look like: <tool>-<host>-<4-char-suffix>.
LEGACY_ID_RE = re.compile(r"^([a-z]+)-([a-z0-9][a-z0-9-]*?)-([a-z0-9]{4})$")


def tool_id_file(tool: str) -> str:
    return os.path.join(HOME, f".nestwork_id_{tool}")


def compute_host() -> str:
    host = socket.gethostname() or "unknown"
    return host.split(".")[0].lower()


def random_suffix(n: int = 4) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def read_one_line(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""


def read_lines(path: str) -> list[str]:
    try:
        with open(path, encoding="utf-8") as file:
            return [line.strip() for line in file.read().splitlines() if line.strip()]
    except FileNotFoundError:
        return []


def write_one_line(path: str, value: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        file.write(value + "\n")


def import_agent_id(agent_id: str) -> None:
    match = LEGACY_ID_RE.match(agent_id)
    if match:
        tool, host, suffix = match.groups()
        if not read_one_line(HOST_FILE):
            write_one_line(HOST_FILE, host)
        agent_id = f"{tool}-{suffix}"
    else:
        tool = agent_id.split("-", 1)[0]
    path = tool_id_file(tool)
    if agent_id and not read_one_line(path):
        write_one_line(path, agent_id)


def migrate_legacy_if_needed() -> None:
    """Import pre-per-tool identity formats without destroying their source."""
    legacy = read_lines(LEGACY_ID_FILE)
    legacy_host = read_one_line(HOST_FILE)
    if len(legacy) >= 2:
        if not legacy_host:
            write_one_line(HOST_FILE, legacy[0].lower())
        import_agent_id(legacy[1])
    elif len(legacy) == 1:
        import_agent_id(legacy[0])

    hive = read_lines(LEGACY_HIVE_ID_FILE)
    hive_host = read_one_line(LEGACY_HIVE_HOST_FILE)
    if len(hive) >= 2:
        if not read_one_line(HOST_FILE):
            write_one_line(HOST_FILE, hive[0].lower())
        import_agent_id(hive[1])
    elif hive_host and len(hive) == 1:
        if not read_one_line(HOST_FILE):
            write_one_line(HOST_FILE, hive_host.lower())
        import_agent_id(hive[0])


def resolve_host() -> str:
    override = os.environ.get("NESTWORK_HOST", "").strip()
    if not override:
        override = os.environ.get("HIVE" + "QUEEN_HOST", "").strip()
    if override:
        return override.lower()
    return read_one_line(HOST_FILE) or compute_host()


def resolve_agent_id(tool: str, with_suffix: bool) -> str:
    override = os.environ.get("NESTWORK_AGENT_ID", "").strip()
    if not override:
        override = os.environ.get("HIVE" + "QUEEN_AGENT_ID", "").strip()
    if override:
        return override
    cached = read_one_line(tool_id_file(tool))
    if not with_suffix:
        return tool
    if cached.startswith(tool + "-") and LEGACY_ID_RE.match(cached) is None:
        return cached
    if cached == tool:
        return cached
    return f"{tool}-{random_suffix()}"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: _identity.py <tool> [--with-suffix]", file=sys.stderr)
        return 2
    tool = sys.argv[1].strip().lower()
    with_suffix = "--with-suffix" in sys.argv[2:]
    migrate_legacy_if_needed()

    host = resolve_host()
    agent_id = resolve_agent_id(tool, with_suffix)
    has_override = (
        os.environ.get("NESTWORK_HOST", "").strip()
        or os.environ.get("NESTWORK_AGENT_ID", "").strip()
        or os.environ.get("HIVE" + "QUEEN_HOST", "").strip()
        or os.environ.get("HIVE" + "QUEEN_AGENT_ID", "").strip()
    )
    if not has_override:
        write_one_line(HOST_FILE, host)
        write_one_line(tool_id_file(tool), agent_id)

    print(host)
    print(agent_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())

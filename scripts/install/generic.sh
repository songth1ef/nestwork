#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# nestwork x generic markdown-config installer
#
# Works for any AI CLI that loads a single markdown file at startup as its
# system prompt / instructions / rules. Writes the nestwork bootstrap block
# into that file using the same marker-block convention as install-claude.
#
# Usage:
#   bash install-generic.sh <tool-prefix> <config-path>
#
# Examples:
#   # Qwen Code (based on Gemini CLI; confirm path with `qwen --help`)
#   bash install-generic.sh qwen ~/.qwen/QWEN.md
#
#   # OpenCode (check tool docs for the exact rules file)
#   bash install-generic.sh opencode ~/.config/opencode/prompt.md
#
#   # Any other tool -- pass its rules/instructions path
#   bash install-generic.sh <prefix> <path>
#
# The script:
#   - Generates a deterministic agent-id "<prefix>", rooted under agents/<host>/
#   - Creates agents/<host>/<agent-id>/memory.md if missing
#   - Injects (or updates) the nestwork bootstrap block in the target file
#     via scripts/install/_bootstrap.py (preserves any non-nestwork content)
#
# Does NOT register hooks -- only Claude Code has a PreToolUse-style hook
# system that nestwork can plug into. All other tools rely on the session
# instructions (written into the config file) to commit+push memory manually
# at session end.
# -----------------------------------------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PREFIX="${1:-}"
CONFIG_PATH="${2:-}"

if [ -z "$PREFIX" ] || [ -z "$CONFIG_PATH" ]; then
  cat >&2 <<USAGE
usage: bash install-generic.sh <tool-prefix> <config-path>

example:
  bash install-generic.sh qwen ~/.qwen/QWEN.md
  bash install-generic.sh opencode ~/.config/opencode/prompt.md

<tool-prefix>: short identifier used in agent-id (e.g. qwen, opencode, trae)
<config-path>: absolute or ~-relative path to the tool's prompt/rules file
USAGE
  exit 2
fi

# Expand ~ in config path
eval CONFIG_PATH="$CONFIG_PATH"

# Resolve (host, agent-id) via shared identity helper. Generic installer uses
# the deterministic one-per-host layout: agents/<host>/<prefix>/
IDENTITY="$(python3 "$NESTWORK_PATH/scripts/install/_identity.py" "$PREFIX")"
HOST="$(printf '%s\n' "$IDENTITY" | sed -n 1p)"
AGENT_ID="$(printf '%s\n' "$IDENTITY" | sed -n 2p)"
if [ -z "$HOST" ] || [ -z "$AGENT_ID" ]; then
  echo "ERROR: identity resolver returned host='$HOST' agent='$AGENT_ID' (expected two non-empty lines); check python3 and scripts/install/_identity.py" >&2
  exit 1
fi
AGENT_DIR="$NESTWORK_PATH/agents/$HOST/$AGENT_ID"

echo "-> nestwork path : $NESTWORK_PATH"
echo "-> host           : $HOST"
echo "-> agent id       : $AGENT_ID"
echo "-> config target  : $CONFIG_PATH"

# 1. Create agent memory directory
mkdir -p "$AGENT_DIR"
if [ ! -f "$AGENT_DIR/memory.md" ]; then
  cat > "$AGENT_DIR/memory.md" <<EOF
# MEMORY -- $HOST/$AGENT_ID

> Private memory for this agent instance.
> Only $HOST/$AGENT_ID writes here.

---

_No memory yet._
EOF
  echo "[ok] created $AGENT_DIR/memory.md"
fi

# 2. Inject bootstrap into the tool's config file
CONFIG_DIR="$(dirname "$CONFIG_PATH")"
mkdir -p "$CONFIG_DIR"
python3 "$NESTWORK_PATH/scripts/install/_bootstrap.py" \
  "$CONFIG_PATH" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"

echo ""
echo "OK nestwork installed for $PREFIX"
echo "   agent  : $HOST/$AGENT_ID"
echo "   memory : $AGENT_DIR/memory.md"
echo "   config : $CONFIG_PATH"

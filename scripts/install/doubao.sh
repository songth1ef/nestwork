#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------
# nestwork x Doubao Work installer
#
# Doubao Work (豆包办公) is a conversational AI office client. It has no
# CLI-level config file of its own and no session hooks, so this installer
# writes the nestwork startup protocol to a markdown file the agent reads at
# session start. The agent (Doubao) then follows the protocol inside the
# conversation: git pull at start, commit+push on memory writes.
#
# Override the target file with DOUBAO_NESTWORK_MD if you keep your rules
# elsewhere.
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOUBAO_DIR="${DOUBAO_HOME:-$HOME/.doubao}"
TARGET_MD="${DOUBAO_NESTWORK_MD:-$DOUBAO_DIR/nestwork.md}"
IDENTITY="$(python3 "$NESTWORK_PATH/scripts/install/_identity.py" doubao)"
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
echo "-> doubao home    : $DOUBAO_DIR"
echo "-> rules file     : $TARGET_MD"

# 1. Create this agent's memory directory
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

# 2. Inject nestwork bootstrap into the Doubao rules file (preserves user content).
mkdir -p "$DOUBAO_DIR"
python3 "$NESTWORK_PATH/scripts/install/_bootstrap.py" \
  "$TARGET_MD" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"

echo ""
echo "OK nestwork installed for Doubao Work"
echo "   agent  : $HOST/$AGENT_ID"
echo "   memory : $AGENT_DIR/memory.md"
echo "   rules  : $TARGET_MD"
echo ""
echo "[i] Doubao Work has no session hooks; at each session start the agent"
echo "  should pull the nest and read the resident files listed in the rules"
echo "  file, and commit+push memory writes before the session ends."

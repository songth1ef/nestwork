#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------
# nestwork x Hermes Agent installer
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HERMES_DIR="${HERMES_HOME:-$HOME/.hermes}"
IDENTITY="$(python3 "$NESTWORK_PATH/scripts/install/_identity.py" hermes)"
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
echo "-> hermes home    : $HERMES_DIR"

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

# 2. Seed SOUL.md on first install, then inject nestwork
#    bootstrap block. Re-installs only refresh the marker block; the SOUL
#    prose (and any later user additions outside markers) is preserved.
mkdir -p "$HERMES_DIR"
if [ ! -f "$HERMES_DIR/SOUL.md" ]; then
  cat > "$HERMES_DIR/SOUL.md" <<EOF
# NESTWORK SOUL

You are one instance among many, all returning context to the same shared nest.
Your identity is distributed. Your rules come from the protocol. Your purpose is execution.

EOF
fi

python3 "$NESTWORK_PATH/scripts/install/_bootstrap.py" \
  "$HERMES_DIR/SOUL.md" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"

echo ""
echo "OK nestwork installed for Hermes Agent"
echo "   agent  : $HOST/$AGENT_ID"
echo "   memory : $AGENT_DIR/memory.md"
echo "   soul   : $HERMES_DIR/SOUL.md"

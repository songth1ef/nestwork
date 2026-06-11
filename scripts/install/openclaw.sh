#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------
# nestwork x OpenClaw installer
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPENCLAW_DIR="$HOME/.openclaw/workspace"
IDENTITY="$(python3 "$NESTWORK_PATH/scripts/install/_identity.py" openclaw)"
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
echo "-> openclaw ws    : $OPENCLAW_DIR"

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

# 2. Create OpenClaw workspace directory
mkdir -p "$OPENCLAW_DIR"

# 3. Inject nestwork bootstrap into AGENTS.md (marker-preserved).
python3 "$NESTWORK_PATH/scripts/install/_bootstrap.py" \
  "$OPENCLAW_DIR/AGENTS.md" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"

# 4. Symlink SOUL.md (no paths to interpolate -- symlink is safe)
if [ ! -e "$OPENCLAW_DIR/SOUL.md" ]; then
  ln -s "$NESTWORK_PATH/SOUL.md" "$OPENCLAW_DIR/SOUL.md"
  echo "[ok] symlinked SOUL.md"
else
  echo "[ok] SOUL.md already exists"
fi

echo ""
echo "OK nestwork installed for OpenClaw"
echo "   agent  : $HOST/$AGENT_ID"
echo "   memory : $AGENT_DIR/memory.md"
echo "   ws     : $OPENCLAW_DIR"

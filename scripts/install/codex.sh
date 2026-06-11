#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------
# nestwork x Codex installer
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CODEX_DIR="$HOME/.codex"
CODEX_AGENTS="$CODEX_DIR/AGENTS.md"
CODEX_INSTRUCTIONS="$CODEX_DIR/instructions.md"
CODEX_CONFIG="$CODEX_DIR/config.toml"
CODEX_HOOKS="$CODEX_DIR/hooks.json"

IDENTITY="$(python3 "$NESTWORK_PATH/scripts/install/_identity.py" codex)"
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

# 2. Inject nestwork bootstrap into Codex startup files (marker-preserved).
mkdir -p "$CODEX_DIR"
python3 "$NESTWORK_PATH/scripts/install/_bootstrap.py" \
  "$CODEX_AGENTS" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"
python3 "$NESTWORK_PATH/scripts/install/_bootstrap.py" \
  "$CODEX_INSTRUCTIONS" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"

# 3. Register the Codex Stop hook used for optional local-history snapshots.
#    Current Codex reads config.toml + hooks.json; the old config.json
#    session.end_hook entry is ignored by recent releases.
python3 "$NESTWORK_PATH/scripts/install/_codex_hooks.py" \
  "$CODEX_CONFIG" "$CODEX_HOOKS" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"

echo ""
echo "OK nestwork installed for Codex"
echo "   agent: $HOST/$AGENT_ID"
echo "   memory: $AGENT_DIR/memory.md"

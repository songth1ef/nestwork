#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------
# nestwork x Antigravity installer
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GEMINI_DIR="${GEMINI_HOME:-$HOME/.gemini}"
[ -n "${ANTIGRAVITY_HOME:-}" ] && GEMINI_DIR="$ANTIGRAVITY_HOME"
GEMINI_MD="$GEMINI_DIR/GEMINI.md"
HOOKS_JSON="$GEMINI_DIR/config/hooks.json"

IDENTITY="$(python3 "$NESTWORK_PATH/scripts/install/_identity.py" antigravity)"
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
echo "-> antigravity dir: $GEMINI_DIR"

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

# 2. Inject nestwork bootstrap into ~/.gemini/GEMINI.md (preserves user content).
mkdir -p "$GEMINI_DIR"
python3 "$NESTWORK_PATH/scripts/install/_bootstrap.py" \
  "$GEMINI_MD" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"

# 3. Register Antigravity hooks (PreInvocation + Stop) in ~/.gemini/config/hooks.json
mkdir -p "$GEMINI_DIR/config"
python3 "$NESTWORK_PATH/scripts/install/_antigravity_hooks.py" \
  "$HOOKS_JSON" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"

echo ""
echo "OK nestwork installed for Antigravity"
echo "   agent  : $HOST/$AGENT_ID"
echo "   memory : $AGENT_DIR/memory.md"
echo "   config : $GEMINI_MD"
echo "   hooks  : $HOOKS_JSON"

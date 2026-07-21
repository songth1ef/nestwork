#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------
# nestwork x Kimi Code installer
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
KIMI_CODE_HOME="${KIMI_CODE_HOME:-$HOME/.kimi-code}"
KIMI_CONFIG="$KIMI_CODE_HOME/config.toml"

# Resolve (host, agent-id) via shared identity helper. Kimi Code uses a random
# suffix so multiple installs on one machine stay distinct.
IDENTITY="$(python3 "$NESTWORK_PATH/scripts/install/_identity.py" kimi --with-suffix)"
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
echo "-> Kimi Code home : $KIMI_CODE_HOME"

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

# 2. Inject nestwork bootstrap into Kimi Code's startup reference file.
#    Kimi Code does not (yet) support SessionStart additionalContext, so the
#    bootstrap instructs the agent to Read the priority-chain files itself.
mkdir -p "$KIMI_CODE_HOME"
python3 "$NESTWORK_PATH/scripts/install/_bootstrap.py" \
  "$KIMI_CODE_HOME/NESTWORK.md" "$NESTWORK_PATH" "$HOST" "$AGENT_ID" --tool=kimi

# 3. Register hooks in ~/.kimi-code/config.toml.
#    - SessionStart: git pull --rebase (keeps context fresh)
#    - PreToolUse/PostToolUse (Write|Edit): atomic per-write sync
#    - Stop: safety-net commit+push
python3 "$NESTWORK_PATH/scripts/install/_kimi_hooks.py" \
  "$KIMI_CONFIG" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"

echo ""
echo "OK nestwork installed for Kimi Code"
echo "   agent : $HOST/$AGENT_ID"
echo "   memory: $AGENT_DIR/memory.md"
echo "   config: $KIMI_CONFIG"
echo ""
echo "Run '/reload' in Kimi Code (or start a new session) for hooks to take effect."

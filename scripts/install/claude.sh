#!/usr/bin/env bash
set -e

# ---------------------------------------------
# nestwork x Claude Code installer
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CLAUDE_DIR="$HOME/.claude"
SETTINGS="$CLAUDE_DIR/settings.json"

# Resolve (host, agent-id) via shared identity helper. Claude uses a random
# suffix so multiple installs on one machine stay distinct.
IDENTITY="$(python3 "$NESTWORK_PATH/scripts/install/_identity.py" claude --with-suffix)"
HOST="$(printf '%s\n' "$IDENTITY" | sed -n 1p)"
AGENT_ID="$(printf '%s\n' "$IDENTITY" | sed -n 2p)"
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

# 2. Inject nestwork bootstrap into global CLAUDE.md.
#    Preserves any existing user content via HTML-comment marker block.
mkdir -p "$CLAUDE_DIR"
python3 "$NESTWORK_PATH/scripts/install/_bootstrap.py" \
  "$CLAUDE_DIR/CLAUDE.md" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"

# 3. Register hooks: SessionStart / PreToolUse / PostToolUse / Stop / SessionEnd
#    Atomic per-write sync: pull before every memory Write/Edit,
#    commit+push right after. Stop hook is a per-turn safety net;
#    SessionEnd runs claude-mem export + local-history sync once when the
#    session truly ends (not on every /clear or compact).
mkdir -p "$CLAUDE_DIR"

if [ ! -f "$SETTINGS" ]; then
  echo '{}' > "$SETTINGS"
fi

python3 "$NESTWORK_PATH/scripts/install/_hooks.py" \
  "$SETTINGS" "$NESTWORK_PATH" "$HOST" "$AGENT_ID"

echo ""
echo "OK nestwork installed for Claude Code"
echo "   agent : $HOST/$AGENT_ID"
echo "   memory: $AGENT_DIR/memory.md"

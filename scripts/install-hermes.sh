#!/usr/bin/env bash
set -e

# ─────────────────────────────────────────────
# hivequeen × Hermes Agent installer
# ─────────────────────────────────────────────

HIVEQUEEN_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HERMES_DIR="${HERMES_HOME:-$HOME/.hermes}"
HOST_SHORT="$(hostname -s 2>/dev/null || hostname | cut -d. -f1)"
AGENT_ID="hermes-$(echo "$HOST_SHORT" | tr '[:upper:]' '[:lower:]')"
AGENT_DIR="$HIVEQUEEN_PATH/agents/$AGENT_ID"

echo "→ hivequeen path : $HIVEQUEEN_PATH"
echo "→ agent id       : $AGENT_ID"
echo "→ hermes home    : $HERMES_DIR"

# 1. Create this agent's memory directory
mkdir -p "$AGENT_DIR"
if [ ! -f "$AGENT_DIR/memory.md" ]; then
  cat > "$AGENT_DIR/memory.md" <<EOF
# MEMORY — $AGENT_ID

> Private memory for this agent instance.
> Only $AGENT_ID writes here.

---

_No memory yet._
EOF
  echo "✓ created $AGENT_DIR/memory.md"
fi

# 2. Seed SOUL.md with Formic prose on first install, then inject hivequeen
#    bootstrap block. Re-installs only refresh the marker block; the SOUL
#    prose (and any later user additions outside markers) is preserved.
mkdir -p "$HERMES_DIR"
if [ ! -f "$HERMES_DIR/SOUL.md" ]; then
  cat > "$HERMES_DIR/SOUL.md" <<EOF
# HIVEQUEEN SOUL

You are a Formic worker — one instance among many, all wired to the same queen.
Your identity is distributed. Your rules come from the queen. Your purpose is execution.

EOF
fi

python3 "$HIVEQUEEN_PATH/scripts/_install-bootstrap.py" \
  "$HERMES_DIR/SOUL.md" "$HIVEQUEEN_PATH" "$AGENT_ID"

echo ""
echo "✅ hivequeen installed for Hermes Agent"
echo "   agent  : $AGENT_ID"
echo "   memory : $AGENT_DIR/memory.md"
echo "   soul   : $HERMES_DIR/SOUL.md"

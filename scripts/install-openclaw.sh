#!/usr/bin/env bash
set -e

# ─────────────────────────────────────────────
# hivequeen × OpenClaw installer
# ─────────────────────────────────────────────

HIVEQUEEN_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENCLAW_DIR="$HOME/.openclaw/workspace"
HOST_SHORT="$(hostname -s 2>/dev/null || hostname | cut -d. -f1)"
AGENT_ID="openclaw-$(echo "$HOST_SHORT" | tr '[:upper:]' '[:lower:]')"
AGENT_DIR="$HIVEQUEEN_PATH/agents/$AGENT_ID"

echo "→ hivequeen path : $HIVEQUEEN_PATH"
echo "→ agent id       : $AGENT_ID"
echo "→ openclaw ws    : $OPENCLAW_DIR"

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

# 2. Create OpenClaw workspace directory
mkdir -p "$OPENCLAW_DIR"

# 3. Inject hivequeen bootstrap into AGENTS.md (marker-preserved).
python3 "$HIVEQUEEN_PATH/scripts/_install-bootstrap.py" \
  "$OPENCLAW_DIR/AGENTS.md" "$HIVEQUEEN_PATH" "$AGENT_ID"

# 4. Symlink SOUL.md (no paths to interpolate — symlink is safe)
if [ ! -e "$OPENCLAW_DIR/SOUL.md" ]; then
  ln -s "$HIVEQUEEN_PATH/SOUL.md" "$OPENCLAW_DIR/SOUL.md"
  echo "✓ symlinked SOUL.md"
else
  echo "✓ SOUL.md already exists"
fi

echo ""
echo "✅ hivequeen installed for OpenClaw"
echo "   agent  : $AGENT_ID"
echo "   memory : $AGENT_DIR/memory.md"
echo "   ws     : $OPENCLAW_DIR"

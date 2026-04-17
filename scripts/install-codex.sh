#!/usr/bin/env bash
set -e

# ─────────────────────────────────────────────
# hivequeen × Codex installer
# ─────────────────────────────────────────────

HIVEQUEEN_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_DIR="$HOME/.codex"
SETTINGS="$CODEX_DIR/config.json"
HOST_SHORT="$(hostname -s 2>/dev/null || hostname | cut -d. -f1)"
AGENT_ID="codex-$(echo "$HOST_SHORT" | tr '[:upper:]' '[:lower:]')"
AGENT_DIR="$HIVEQUEEN_PATH/agents/$AGENT_ID"

echo "→ hivequeen path : $HIVEQUEEN_PATH"
echo "→ agent id       : $AGENT_ID"

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

# 2. Inject hivequeen bootstrap into Codex instructions (marker-preserved).
mkdir -p "$CODEX_DIR"
python3 "$HIVEQUEEN_PATH/scripts/_install-bootstrap.py" \
  "$CODEX_DIR/instructions.md" "$HIVEQUEEN_PATH" "$AGENT_ID"

# 4. Register session end hook (Codex uses config.json)
if [ ! -f "$SETTINGS" ]; then
  echo '{}' > "$SETTINGS"
fi

python3 - <<PYEOF
import json

settings_path = "$SETTINGS"
hivequeen_path = "$HIVEQUEEN_PATH"
agent_id = "$AGENT_ID"

with open(settings_path) as f:
    settings = json.load(f)

hook_cmd = f"cd {hivequeen_path} && git pull --rebase --autostash -q && git add agents/{agent_id}/ && git diff --cached --quiet || git commit -m 'memory: update {agent_id}' && git push -q"

settings.setdefault("session", {})["end_hook"] = hook_cmd

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print(f"✓ registered session end hook in {settings_path}")
PYEOF

echo ""
echo "✅ hivequeen installed for Codex"
echo "   agent: $AGENT_ID"
echo "   memory: $AGENT_DIR/memory.md"

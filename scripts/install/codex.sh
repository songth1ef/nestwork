#!/usr/bin/env bash
set -e

# ---------------------------------------------
# hivequeen x Codex installer
# ---------------------------------------------

HIVEQUEEN_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CODEX_DIR="$HOME/.codex"
CODEX_AGENTS="$CODEX_DIR/AGENTS.md"
CODEX_INSTRUCTIONS="$CODEX_DIR/instructions.md"
SETTINGS="$CODEX_DIR/config.json"

IDENTITY="$(python3 "$HIVEQUEEN_PATH/scripts/install/_identity.py" codex)"
HOST="$(printf '%s\n' "$IDENTITY" | sed -n 1p)"
AGENT_ID="$(printf '%s\n' "$IDENTITY" | sed -n 2p)"
AGENT_DIR="$HIVEQUEEN_PATH/agents/$HOST/$AGENT_ID"

echo "-> hivequeen path : $HIVEQUEEN_PATH"
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

# 2. Inject hivequeen bootstrap into Codex startup files (marker-preserved).
mkdir -p "$CODEX_DIR"
python3 "$HIVEQUEEN_PATH/scripts/install/_bootstrap.py" \
  "$CODEX_AGENTS" "$HIVEQUEEN_PATH" "$HOST" "$AGENT_ID"
python3 "$HIVEQUEEN_PATH/scripts/install/_bootstrap.py" \
  "$CODEX_INSTRUCTIONS" "$HIVEQUEEN_PATH" "$HOST" "$AGENT_ID"

# 4. Register session end hook (Codex uses config.json)
if [ ! -f "$SETTINGS" ]; then
  echo '{}' > "$SETTINGS"
fi

python3 - <<PYEOF
import json

settings_path = "$SETTINGS"
hivequeen_path = "$HIVEQUEEN_PATH"
host = "$HOST"
agent_id = "$AGENT_ID"

with open(settings_path) as f:
    settings = json.load(f)

hook_cmd = (
    f"cd {hivequeen_path} && "
    f"git pull --rebase --autostash -q && "
    f"python3 {hivequeen_path}/scripts/hooks/sync-local-history.py {hivequeen_path} {host} {agent_id} && "
    f"git add agents/{host}/{agent_id}/ && "
    f"(git diff --cached --quiet -- agents/{host}/{agent_id}/ || "
    f"git commit -m 'memory: update {host}/{agent_id}' -- agents/{host}/{agent_id}/) && "
    f"git push -q"
)

settings.setdefault("session", {})["end_hook"] = hook_cmd

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print(f"[ok] registered session end hook in {settings_path}")
PYEOF

echo ""
echo "OK hivequeen installed for Codex"
echo "   agent: $HOST/$AGENT_ID"
echo "   memory: $AGENT_DIR/memory.md"

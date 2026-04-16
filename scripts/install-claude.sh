#!/usr/bin/env bash
set -e

# ─────────────────────────────────────────────
# hivequeen × Claude Code installer
# ─────────────────────────────────────────────

HIVEQUEEN_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_DIR="$HOME/.claude"
SETTINGS="$CLAUDE_DIR/settings.json"
AGENT_ID="claude-$(hostname -s)"
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

# 2. Write global CLAUDE.md to bootstrap hivequeen
mkdir -p "$CLAUDE_DIR"
cat > "$CLAUDE_DIR/CLAUDE.md" <<EOF
# Global Startup Protocol

Before starting analysis, planning, or implementation, run:

\`\`\`bash
git -C $HIVEQUEEN_PATH pull --rebase
\`\`\`

Then load context from hivequeen in this order:

1. \`$HIVEQUEEN_PATH/queen/agent-rules.md\`
2. \`$HIVEQUEEN_PATH/queen/strategy.md\`
3. \`$HIVEQUEEN_PATH/shared/memory.md\`
4. \`$HIVEQUEEN_PATH/agents/$AGENT_ID/memory.md\`
5. Relevant \`$HIVEQUEEN_PATH/projects/*.md\` for current task

Write protocol: only write to \`$HIVEQUEEN_PATH/agents/$AGENT_ID/\`

See full protocol: \`$HIVEQUEEN_PATH/AGENTS.md\`
EOF
echo "✓ wrote $CLAUDE_DIR/CLAUDE.md"

# 3. Register Stop hook for auto-commit
mkdir -p "$CLAUDE_DIR"

# Read or init settings.json
if [ ! -f "$SETTINGS" ]; then
  echo '{}' > "$SETTINGS"
fi

# Inject Stop hook via Python (available on most systems)
python3 - <<PYEOF
import json, os

settings_path = "$SETTINGS"
hivequeen_path = "$HIVEQUEEN_PATH"
agent_id = "$AGENT_ID"

with open(settings_path) as f:
    settings = json.load(f)

hook_cmd = f"""bash {hivequeen_path}/scripts/export-claude-mem.sh; cd {hivequeen_path} && git pull --rebase --autostash -q && git add agents/{agent_id}/ && git diff --cached --quiet || git commit -m 'memory: update {agent_id}' && git push -q"""

hook = {"matcher": "", "hooks": [{"type": "command", "command": hook_cmd}]}

hooks = settings.setdefault("hooks", {})
stop_hooks = hooks.setdefault("Stop", [])

# Avoid duplicate
existing_cmds = [h.get("hooks", [{}])[0].get("command", "") for h in stop_hooks]
if hook_cmd not in existing_cmds:
    stop_hooks.append(hook)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
    print(f"✓ registered Stop hook in {settings_path}")
else:
    print("✓ Stop hook already registered")
PYEOF

echo ""
echo "✅ hivequeen installed for Claude Code"
echo "   agent: $AGENT_ID"
echo "   memory: $AGENT_DIR/memory.md"

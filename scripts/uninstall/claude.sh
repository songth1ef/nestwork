#!/usr/bin/env bash
set -e

# ---------------------------------------------
# nestwork x Claude Code uninstaller
#
# Unbinds only: removes the bootstrap block from ~/.claude/CLAUDE.md and the
# nestwork hooks from settings.json, so Claude no longer loads nestwork at
# session start. Never deletes memory (agents/<host>/<id>/ stays in the repo)
# or identity files (~/.nestwork_host, ~/.nestwork_id_claude) -- re-running
# the installer restores the exact same agent identity.
#
# Usage:
#   bash uninstall/claude.sh [--purge-identity]
#
# --purge-identity additionally deletes ~/.nestwork_id_claude, so the next
# install starts as a brand-new agent id. The shared ~/.nestwork_host file is
# kept either way (other tools on this machine may still use it).
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CLAUDE_DIR="$HOME/.claude"
SETTINGS="$CLAUDE_DIR/settings.json"

HOST="$(cat "$HOME/.nestwork_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.nestwork_id_claude" 2>/dev/null || true)"

echo "-> nestwork path : $NESTWORK_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

# 1. Remove the bootstrap block from global CLAUDE.md (user content preserved)
python3 "$NESTWORK_PATH/scripts/uninstall/_unbootstrap.py" "$CLAUDE_DIR/CLAUDE.md"

# 2. Remove nestwork hooks from settings.json (user hooks preserved)
python3 "$NESTWORK_PATH/scripts/uninstall/_unhooks.py" \
  "$SETTINGS" "$HOST" "$AGENT_ID"

# 3. Optionally purge this tool's identity file
if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.nestwork_id_claude"
  echo "[ok] removed $HOME/.nestwork_id_claude (next install gets a new agent id)"
fi

echo ""
echo "OK nestwork unbound from Claude Code"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $NESTWORK_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $NESTWORK_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $NESTWORK_PATH/scripts/install/claude.sh"

#!/usr/bin/env bash
set -e

# ---------------------------------------------
# nestwork x Codex uninstaller
#
# Unbinds only: removes the bootstrap block from ~/.codex/AGENTS.md and
# instructions.md, and the nestwork Stop hook from hooks.json. `hooksPath`
# in config.toml is left alone (generic pointer; hooks.json may still hold
# user hooks). Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/codex.sh [--purge-identity]
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CODEX_DIR="$HOME/.codex"

HOST="$(cat "$HOME/.nestwork_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.nestwork_id_codex" 2>/dev/null || true)"

echo "-> nestwork path : $NESTWORK_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

# 1. Remove the bootstrap block from Codex startup files (user content preserved)
python3 "$NESTWORK_PATH/scripts/uninstall/_unbootstrap.py" "$CODEX_DIR/AGENTS.md"
python3 "$NESTWORK_PATH/scripts/uninstall/_unbootstrap.py" "$CODEX_DIR/instructions.md"

# 2. Remove the nestwork Stop hook from hooks.json (user hooks preserved)
python3 "$NESTWORK_PATH/scripts/uninstall/_codex_unhooks.py" "$CODEX_DIR/hooks.json"

# 3. Optionally purge this tool's identity file
if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.nestwork_id_codex"
  echo "[ok] removed $HOME/.nestwork_id_codex (next install gets a new agent id)"
fi

echo ""
echo "OK nestwork unbound from Codex"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $NESTWORK_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $NESTWORK_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $NESTWORK_PATH/scripts/install/codex.sh"

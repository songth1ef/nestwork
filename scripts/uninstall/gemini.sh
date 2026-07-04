#!/usr/bin/env bash
set -e

# ---------------------------------------------
# nestwork x Gemini CLI uninstaller
#
# Unbinds only: removes the bootstrap block from ~/.gemini/GEMINI.md.
# Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/gemini.sh [--purge-identity]
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GEMINI_DIR="${GEMINI_HOME:-$HOME/.gemini}"

HOST="$(cat "$HOME/.nestwork_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.nestwork_id_gemini" 2>/dev/null || true)"

echo "-> nestwork path : $NESTWORK_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

python3 "$NESTWORK_PATH/scripts/uninstall/_unbootstrap.py" "$GEMINI_DIR/GEMINI.md"

if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.nestwork_id_gemini"
  echo "[ok] removed $HOME/.nestwork_id_gemini (next install gets a new agent id)"
fi

echo ""
echo "OK nestwork unbound from Gemini CLI"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $NESTWORK_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $NESTWORK_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $NESTWORK_PATH/scripts/install/gemini.sh"

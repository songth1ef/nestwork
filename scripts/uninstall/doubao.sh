#!/usr/bin/env bash
set -e

# ---------------------------------------------
# nestwork x Doubao Work uninstaller
#
# Unbinds only: removes the bootstrap block from the Doubao rules file.
# Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/doubao.sh [--purge-identity]
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOUBAO_DIR="${DOUBAO_HOME:-$HOME/.doubao}"
TARGET_MD="${DOUBAO_NESTWORK_MD:-$DOUBAO_DIR/nestwork.md}"

HOST="$(cat "$HOME/.nestwork_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.nestwork_id_doubao" 2>/dev/null || true)"

echo "-> nestwork path : $NESTWORK_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

python3 "$NESTWORK_PATH/scripts/uninstall/_unbootstrap.py" "$TARGET_MD"

if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.nestwork_id_doubao"
  echo "[ok] removed $HOME/.nestwork_id_doubao (next install gets a new agent id)"
fi

echo ""
echo "OK nestwork unbound from Doubao Work"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $NESTWORK_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $NESTWORK_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $NESTWORK_PATH/scripts/install/doubao.sh"

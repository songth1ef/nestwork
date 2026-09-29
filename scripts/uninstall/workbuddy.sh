#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------
# nestwork x WorkBuddy AI uninstaller
#
# Unbinds only: removes the bootstrap block from the WorkBuddy rules file.
# Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/workbuddy.sh [--purge-identity]
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORKBUDDY_DIR="${WORKBUDDY_HOME:-$HOME/.workbuddy-ai}"
TARGET_MD="${WORKBUDDY_NESTWORK_MD:-$WORKBUDDY_DIR/nestwork.md}"

HOST="$(cat "$HOME/.nestwork_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.nestwork_id_workbuddy" 2>/dev/null || true)"

echo "-> nestwork path  : $NESTWORK_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

python3 "$NESTWORK_PATH/scripts/uninstall/_unbootstrap.py" "$TARGET_MD"

if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.nestwork_id_workbuddy"
  echo "[ok] removed $HOME/.nestwork_id_workbuddy (next install gets a new agent id)"
fi

echo ""
echo "OK nestwork unbound from WorkBuddy AI"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $NESTWORK_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $NESTWORK_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $NESTWORK_PATH/scripts/install/workbuddy.sh"

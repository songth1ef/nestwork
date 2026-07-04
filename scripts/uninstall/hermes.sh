#!/usr/bin/env bash
set -e

# ---------------------------------------------
# nestwork x Hermes Agent uninstaller
#
# Unbinds only: removes the bootstrap block from ~/.hermes/SOUL.md. The SOUL
# prose seeded at install (and anything the user added outside the markers)
# is preserved. Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/hermes.sh [--purge-identity]
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HERMES_DIR="${HERMES_HOME:-$HOME/.hermes}"

HOST="$(cat "$HOME/.nestwork_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.nestwork_id_hermes" 2>/dev/null || true)"

echo "-> nestwork path : $NESTWORK_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

python3 "$NESTWORK_PATH/scripts/uninstall/_unbootstrap.py" "$HERMES_DIR/SOUL.md"

if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.nestwork_id_hermes"
  echo "[ok] removed $HOME/.nestwork_id_hermes (next install gets a new agent id)"
fi

echo ""
echo "OK nestwork unbound from Hermes Agent"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $NESTWORK_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $NESTWORK_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $NESTWORK_PATH/scripts/install/hermes.sh"

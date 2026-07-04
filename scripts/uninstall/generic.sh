#!/usr/bin/env bash
set -e

# -----------------------------------------------------------------------------
# nestwork x generic markdown-config uninstaller
#
# Inverse of install/generic.sh: removes the nestwork bootstrap block from the
# given config file. Memory and identity files are never deleted.
#
# Usage:
#   bash uninstall/generic.sh <tool-prefix> <config-path> [--purge-identity]
#
# Examples:
#   bash uninstall/generic.sh qwen ~/.qwen/QWEN.md
#   bash uninstall/generic.sh opencode ~/.config/opencode/prompt.md
# -----------------------------------------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PREFIX="${1:-}"
CONFIG_PATH="${2:-}"

if [ -z "$PREFIX" ] || [ -z "$CONFIG_PATH" ]; then
  cat >&2 <<USAGE
usage: bash uninstall/generic.sh <tool-prefix> <config-path> [--purge-identity]

example:
  bash uninstall/generic.sh qwen ~/.qwen/QWEN.md
USAGE
  exit 2
fi

HOST="$(cat "$HOME/.nestwork_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.nestwork_id_$PREFIX" 2>/dev/null || true)"

echo "-> nestwork path : $NESTWORK_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

python3 "$NESTWORK_PATH/scripts/uninstall/_unbootstrap.py" "$CONFIG_PATH"

if [ "${3:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.nestwork_id_$PREFIX"
  echo "[ok] removed $HOME/.nestwork_id_$PREFIX (next install gets a new agent id)"
fi

echo ""
echo "OK nestwork unbound from $PREFIX"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $NESTWORK_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $NESTWORK_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $NESTWORK_PATH/scripts/install/generic.sh $PREFIX $CONFIG_PATH"

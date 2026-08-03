#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------
# nestwork x Kimi Code uninstaller
#
# Unbinds only: removes the bootstrap block from ~/.kimi-code/AGENTS.md (and
# from the pre-2026-08-02 ~/.kimi-code/NESTWORK.md, if that install left one)
# plus the nestwork hook block from ~/.kimi-code/config.toml. Memory and
# identity files are never deleted.
#
# Usage:
#   bash uninstall/kimi.sh [--purge-identity]
#
# --purge-identity additionally deletes ~/.nestwork_id_kimi, so the next
# install starts as a brand-new agent id. The shared ~/.nestwork_host file is
# kept either way (other tools on this machine may still use it).
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
KIMI_CODE_HOME="${KIMI_CODE_HOME:-$HOME/.kimi-code}"

HOST="$(cat "$HOME/.nestwork_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.nestwork_id_kimi" 2>/dev/null || true)"

echo "-> nestwork path : $NESTWORK_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

# 1. Remove the bootstrap block from AGENTS.md (user content preserved), plus
#    the legacy NESTWORK.md left by installs made before 2026-08-02.
python3 "$NESTWORK_PATH/scripts/uninstall/_unbootstrap.py" "$KIMI_CODE_HOME/AGENTS.md"
if [ -f "$KIMI_CODE_HOME/NESTWORK.md" ]; then
  python3 "$NESTWORK_PATH/scripts/uninstall/_unbootstrap.py" "$KIMI_CODE_HOME/NESTWORK.md"
fi

# 2. Remove the nestwork hook block from config.toml (user hooks preserved)
python3 "$NESTWORK_PATH/scripts/uninstall/_kimi_unhooks.py" "$KIMI_CODE_HOME/config.toml"

# 3. Optionally purge this tool's identity file
if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.nestwork_id_kimi"
  echo "[ok] removed $HOME/.nestwork_id_kimi (next install gets a new agent id)"
fi

echo ""
echo "OK nestwork unbound from Kimi Code"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $NESTWORK_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $NESTWORK_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $NESTWORK_PATH/scripts/install/kimi.sh"

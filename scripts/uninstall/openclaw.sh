#!/usr/bin/env bash
set -e

# ---------------------------------------------
# nestwork x OpenClaw uninstaller
#
# Unbinds only: removes the bootstrap block from the workspace AGENTS.md and
# the SOUL.md symlink (only if it still points into this nestwork checkout;
# a regular file the user replaced it with is left alone). Memory and
# identity files are never deleted.
#
# Usage:
#   bash uninstall/openclaw.sh [--purge-identity]
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPENCLAW_DIR="$HOME/.openclaw/workspace"

HOST="$(cat "$HOME/.nestwork_host" 2>/dev/null || true)"
AGENT_ID="$(cat "$HOME/.nestwork_id_openclaw" 2>/dev/null || true)"

echo "-> nestwork path : $NESTWORK_PATH"
echo "-> host           : ${HOST:-<unknown>}"
echo "-> agent id       : ${AGENT_ID:-<unknown>}"

# 1. Remove the bootstrap block from workspace AGENTS.md
python3 "$NESTWORK_PATH/scripts/uninstall/_unbootstrap.py" "$OPENCLAW_DIR/AGENTS.md"

# 2. Remove the SOUL.md symlink if it was ours
if [ -L "$OPENCLAW_DIR/SOUL.md" ] && \
   [ "$(readlink "$OPENCLAW_DIR/SOUL.md")" = "$NESTWORK_PATH/SOUL.md" ]; then
  rm "$OPENCLAW_DIR/SOUL.md"
  echo "[ok] removed SOUL.md symlink"
fi

# 3. Optionally purge this tool's identity file
if [ "${1:-}" = "--purge-identity" ]; then
  rm -f "$HOME/.nestwork_id_openclaw"
  echo "[ok] removed $HOME/.nestwork_id_openclaw (next install gets a new agent id)"
fi

echo ""
echo "OK nestwork unbound from OpenClaw"
if [ -n "$HOST" ] && [ -n "$AGENT_ID" ]; then
  echo "   memory kept : $NESTWORK_PATH/agents/$HOST/$AGENT_ID/"
else
  echo "   memory kept : $NESTWORK_PATH/agents/<host>/<agent-id>/"
fi
echo "   to rebind   : bash $NESTWORK_PATH/scripts/install/openclaw.sh"

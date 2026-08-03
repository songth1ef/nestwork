#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# nestwork local-history sync (thin wrapper)
#
# Gated by ~/.nestwork/settings.json -> {"sync_local_history": true};
# the gate is enforced inside sync-local-history.py so this wrapper stays thin.
#
# Called at SessionEnd (directly by Claude, detached by Codex).
# -----------------------------------------------------------------------------

set -u

HOST_ID="${1:-${NESTWORK_HOST:-}}"
AGENT_ID="${2:-${NESTWORK_AGENT_ID:-}}"
NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

[ -z "$HOST_ID" ] && exit 0
[ -z "$AGENT_ID" ] && exit 0

python3 "$NESTWORK_PATH/scripts/hooks/sync-local-history.py" \
  "$NESTWORK_PATH" "$HOST_ID" "$AGENT_ID" || exit 0

# After sync, push a snapshot of agents/<host>/<id>/local/ to the per-agent
# orphan branch. Keeps cross-machine backup without bloating main history.
# See AGENTS.md §12.
bash "$NESTWORK_PATH/scripts/hooks/snapshot-local-orphan.sh" \
  "$HOST_ID" "$AGENT_ID" || true

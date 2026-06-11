#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# nestwork: snapshot agents/<host>/<agent-id>/local/ to an orphan branch
#
# Why: local/ artefacts (history.jsonl, plans/) change frequently and don't
# delta-compress well. Committing them on main bloats history. Instead, we
# keep a single-commit "rolling snapshot" on a per-agent orphan branch:
#
#     agent-history-<host>-<agent-id>
#
# Each invocation rebuilds the branch with one commit containing the current
# working-tree local/ files, then force-pushes it. No history accumulation.
#
# To restore on a fresh clone (or another machine):
#     git fetch origin agent-history-<host>-<agent-id>
#     git restore --source=origin/agent-history-<host>-<agent-id> -- agents/<host>/<agent-id>/local
#
# Usage:
#   snapshot-local-orphan.sh <host> <agent-id>
#
# Always exit 0 on logical "nothing to do"; exit non-zero only on real errors.
# -----------------------------------------------------------------------------

set -u
HOST_ID="${1:-${NESTWORK_HOST:-}}"
AGENT_ID="${2:-${NESTWORK_AGENT_ID:-}}"
NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

[ -z "$HOST_ID" ] && exit 0
[ -z "$AGENT_ID" ] && exit 0

cd "$NESTWORK_PATH" || exit 0

LOCAL_REL="agents/$HOST_ID/$AGENT_ID/local"
[ -d "$LOCAL_REL" ] || exit 0

# Anything to snapshot?
if ! find "$LOCAL_REL" -type f 2>/dev/null | grep -q .; then
  exit 0
fi

BRANCH="agent-history-$HOST_ID-$AGENT_ID"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo unknown)"

# Build a tree containing only local/ files using a temporary index, so the
# main working index stays untouched. We add files relative to NESTWORK_PATH
# so the resulting tree mirrors the original path layout.
TMP_INDEX="$(mktemp -t nw-snapshot.XXXXXX 2>/dev/null || echo "${TMPDIR:-/tmp}/nw-snapshot.$$.$RANDOM")"
cleanup() { [ -f "$TMP_INDEX" ] && rm -f "$TMP_INDEX"; }
trap cleanup EXIT

# Populate the temp index with the local/ tree only.
GIT_INDEX_FILE="$TMP_INDEX" git read-tree --empty 2>/dev/null
if ! GIT_INDEX_FILE="$TMP_INDEX" git add --force -- "$LOCAL_REL" 2>/dev/null; then
  echo "[!] nestwork[$HOST_ID/$AGENT_ID]: orphan snapshot — failed to stage $LOCAL_REL" >&2
  exit 1
fi

TREE="$(GIT_INDEX_FILE="$TMP_INDEX" git write-tree 2>/dev/null)"
[ -z "$TREE" ] && exit 1

# Skip if tree matches the current branch tip (no real change).
EXISTING_TREE="$(git rev-parse --verify "refs/heads/$BRANCH^{tree}" 2>/dev/null || true)"
if [ -n "$EXISTING_TREE" ] && [ "$EXISTING_TREE" = "$TREE" ]; then
  exit 0
fi

# Parentless commit (orphan: each push replaces the previous one).
COMMIT="$(printf 'snapshot %s for %s/%s\n' "$TS" "$HOST_ID" "$AGENT_ID" \
  | GIT_AUTHOR_NAME="nestwork-snapshot" GIT_AUTHOR_EMAIL="snapshot@nestwork" \
    GIT_COMMITTER_NAME="nestwork-snapshot" GIT_COMMITTER_EMAIL="snapshot@nestwork" \
    git commit-tree "$TREE" 2>/dev/null)"
[ -z "$COMMIT" ] && exit 1

git update-ref "refs/heads/$BRANCH" "$COMMIT" 2>/dev/null || exit 1

# Force-push the orphan branch. Failures are logged but never block the agent.
if ! git push -q -f origin "$BRANCH:$BRANCH" 2>/dev/null; then
  echo "[warn] nestwork[$HOST_ID/$AGENT_ID]: orphan snapshot pushed locally but remote push failed" >&2
fi

exit 0

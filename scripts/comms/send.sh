#!/usr/bin/env bash
# Nestwork agent mailbox — send a message (Tier 0/1, git-native, async).
# Single-writer design: writes ONLY into the caller's own outbox, so there are
# never write conflicts and the nestwork pre/post-write hooks commit+push it
# automatically. The recipient reads it on their next pull / session start.
#
# Usage: send.sh <to-host/agent | all> <task|message|broadcast> <subject> [thread] [reply_to]
#        body is read from stdin.
#
# "Who am I" is resolved from NESTWORK_SELF, else ~/.nestwork_host +
# ~/.nestwork_id_claude. Other tool-chains: export NESTWORK_SELF=<host>/<agent-id>.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
SELF="${NESTWORK_SELF:-$(cat ~/.nestwork_host)/$(cat ~/.nestwork_id_claude 2>/dev/null || true)}"
case "$SELF" in */) echo "ERROR: cannot resolve agent id; set NESTWORK_SELF=host/agent" >&2; exit 1;; esac

TO="${1:?usage: send.sh <to-host/agent|all> <task|message|broadcast> <subject> [thread] [reply_to]}"
TYPE="${2:?type required: task|message|broadcast}"
SUBJECT="${3:?subject required}"
THREAD="${4:-}"
REPLY_TO="${5:-}"

TS="$(date +%Y%m%dT%H%M%S%z)"
RAND="$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' \n')"
ID="${TS}-${SELF##*/}-${RAND}"
[ -z "$THREAD" ] && THREAD="$ID"

OUTDIR="$ROOT/agents/$SELF/outbox"
mkdir -p "$OUTDIR"
BODY="$(cat || true)"

cat > "$OUTDIR/$ID.md" <<EOF
---
id: $ID
from: $SELF
to: $TO
type: $TYPE
thread: $THREAD
reply_to: $REPLY_TO
status: open
created: $TS
subject: $SUBJECT
---

$BODY
EOF

echo "sent: agents/$SELF/outbox/$ID.md  ->  $TO  [$TYPE]"

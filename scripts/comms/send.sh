#!/usr/bin/env bash
# Nestwork agent mailbox — send a message (Tier 0/1, git-native, async).
# Single-writer design: writes ONLY into the caller's own outbox, so there are
# never write conflicts. The script commits and pushes the message itself
# (tool-neutral: works the same from Claude Code, Codex, or a plain shell);
# the recipient reads it on their next pull / session start. On Claude Code
# the Stop-hook safety net additionally covers any message whose push failed.
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

# Deliver: commit + push the message ourselves. The per-write hooks only match
# Write/Edit tool calls, so a Bash-invoked send must not rely on them. Push
# failures are non-fatal — the message is durable in the local commit and will
# reach the remote on the next successful push (or the Stop-hook safety net).
MSG_REL="agents/$SELF/outbox/$ID.md"
deliver() {
  cd "$ROOT" || return 1
  git add -- "$MSG_REL" || return 1
  git commit -q -m "comms: $TYPE to $TO ($ID)" -- "$MSG_REL" || return 1
  local attempt
  for attempt in 1 2 3; do
    if git push -q 2>/dev/null; then
      return 0
    fi
    git pull --rebase --autostash -q 2>/dev/null || { git rebase --abort 2>/dev/null || true; }
  done
  return 1
}
if ! deliver; then
  echo "[warn] comms: message saved at $MSG_REL but commit/push incomplete; it will sync on the next push" >&2
fi

echo "sent: agents/$SELF/outbox/$ID.md  ->  $TO  [$TYPE]"

#!/usr/bin/env bash
# Nestwork agent mailbox — archive old messages from MY OWN outbox.
#
# Moves messages older than <days> (default 30) from agents/<self>/outbox/
# into agents/<self>/outbox/archive/, then commits and pushes the move.
# read.sh only scans outbox/*.md, so archived messages stop being scanned —
# this keeps read cost bounded as the mailbox ages. Archived files stay in
# git history; this trims the scan path, it does not rewrite history.
#
# Single-writer rule: you only archive your OWN outbox. Recipients' seen
# state is local to them, so a sender cannot know whether a message was
# read — archival is therefore time-based. Pick a window comfortably larger
# than your slowest agent's check-in cadence.
#
# Usage: archive.sh [days]
#
# "Who am I" is resolved from NESTWORK_SELF, else ~/.nestwork_host +
# ~/.nestwork_id_claude. Other tool-chains: export NESTWORK_SELF=<host>/<agent-id>.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
SELF="${NESTWORK_SELF:-$(cat ~/.nestwork_host)/$(cat ~/.nestwork_id_claude 2>/dev/null || true)}"
case "$SELF" in */) echo "ERROR: cannot resolve agent id; set NESTWORK_SELF=host/agent" >&2; exit 1;; esac

DAYS="${1:-30}"
case "$DAYS" in ''|*[!0-9]*) echo "usage: archive.sh [days]" >&2; exit 2 ;; esac

OUTDIR="$ROOT/agents/$SELF/outbox"
ARCHIVE="$OUTDIR/archive"
[ -d "$OUTDIR" ] || { echo "(no outbox for $SELF)"; exit 0; }

# GNU date first, BSD/macOS date as fallback.
CUTOFF="$(date -d "${DAYS} days ago" +%Y%m%d 2>/dev/null || date -v "-${DAYS}d" +%Y%m%d 2>/dev/null)" \
  || { echo "ERROR: cannot compute cutoff date" >&2; exit 1; }

moved=0
shopt -s nullglob
for f in "$OUTDIR"/*.md; do
  base="$(basename "$f")"
  ts="${base%%T*}"   # message ids start with YYYYMMDDT...
  case "$ts" in
    [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;;
    *) continue ;;
  esac
  if [ "$ts" -lt "$CUTOFF" ]; then
    mkdir -p "$ARCHIVE"
    mv "$f" "$ARCHIVE/$base"
    moved=$((moved+1))
  fi
done

if [ "$moved" -gt 0 ]; then
  (
    cd "$ROOT"
    git add -A -- "agents/$SELF/outbox" || exit 1
    git commit -q -m "comms: archive $moved message(s) older than ${DAYS}d" -- "agents/$SELF/outbox" || exit 1
    git push -q 2>/dev/null || echo "[warn] comms: archive committed locally but push failed; it will sync on the next push" >&2
  ) || echo "[warn] comms: archive moved files but commit failed; commit agents/$SELF/outbox manually" >&2
fi

echo "archived $moved message(s) older than ${DAYS}d for $SELF"

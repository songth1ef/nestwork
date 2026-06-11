#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# nestwork unified hook entry
#
# Usage (invoked by Claude Code settings.json hooks):
#   hook-nestwork.sh pre  <host> <agent-id>   -- PreToolUse
#   hook-nestwork.sh post <host> <agent-id>   -- PostToolUse
#   hook-nestwork.sh stop <host> <agent-id>   -- Stop safety-net
#
# Design: atomic per-write sync.
# - pre:  pull --rebase before memory write; abort write on conflict
# - post: commit + push with retry; surface rebase conflict to Claude
# - stop: same as post (safety net for writes that skipped post)
# -----------------------------------------------------------------------------

set -u
PHASE="${1:-}"
HOST_ID="${2:-}"
AGENT_ID="${3:-}"
NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MATCHER_SCRIPT="$NESTWORK_PATH/scripts/hooks/_match-file.py"

[ -z "$PHASE" ] && exit 0
[ -z "$HOST_ID" ] && exit 0
[ -z "$AGENT_ID" ] && exit 0

AGENT_REL_PATH="agents/$HOST_ID/$AGENT_ID"

# -- Check whether the Write/Edit target is under agents/<host>/<id>/ ----------
match_agent_file() {
  python3 "$MATCHER_SCRIPT" "$NESTWORK_PATH" "$HOST_ID" "$AGENT_ID"
}

# -- git pull --rebase, abort on conflict --------------------------------------
#
# --autostash stashes any uncommitted working-tree change before rebasing. If
# re-applying that stash conflicts, git leaves the changes parked in the stash,
# resets the working tree clean, and STILL EXITS 0 — a later Write would then
# silently overwrite the parked edit. Detect the leftover stash entry (locale-
# independent, unlike grepping git's message) and treat it as a conflict.
pull_rebase() {
  cd "$NESTWORK_PATH" || return 1
  local stash_before stash_after
  stash_before=$(git stash list 2>/dev/null | wc -l)
  if git pull --rebase --autostash -q 2>/dev/null; then
    stash_after=$(git stash list 2>/dev/null | wc -l)
    if [ "$stash_after" -gt "$stash_before" ]; then
      echo "[!] nestwork[$HOST_ID/$AGENT_ID]: autostash conflict -- uncommitted changes were parked in 'git stash'; run 'git stash pop' and resolve before writing memory" >&2
      return 1
    fi
    return 0
  fi
  git rebase --abort 2>/dev/null || true
  return 1
}

# -- Read integer setting from agents/<host>/settings.json with default -------
read_setting_int() {
  local key="$1" default="$2"
  local settings="$NESTWORK_PATH/agents/$HOST_ID/settings.json"
  [ -f "$settings" ] || { echo "$default"; return; }
  python3 - "$settings" "$key" "$default" <<'PY' 2>/dev/null || echo "$default"
import json, sys
path, key, default = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(path, 'r', encoding='utf-8') as f:
        v = json.load(f).get(key, default)
    print(int(v))
except Exception:
    print(default)
PY
}

# -- commit + push with retry; warn on persistent conflict ---------------------
#
# IMPORTANT: scope all commits to agents/<host>/<agent-id>/ via explicit
# pathspec to avoid vacuuming unrelated staged files.
#
# Throttle: when the only staged changes are under agents/<host>/<id>/local/
# (high-frequency runtime artefacts like history.jsonl / plans/), gate the
# commit by `local_commit_min_interval_sec` (default 3600s) since the last
# commit touching local/. Distilled memory changes always commit immediately
# and pull local/ along.
commit_push_retry() {
  cd "$NESTWORK_PATH" || return 1
  git add "$AGENT_REL_PATH/" >/dev/null 2>&1 || return 1
  git diff --cached --quiet -- "$AGENT_REL_PATH/" && return 0

  local local_path="$AGENT_REL_PATH/local"
  local non_local
  non_local=$(git diff --cached --name-only -- "$AGENT_REL_PATH/" ":(exclude)$local_path/*" | head -1)
  if [ -z "$non_local" ]; then
    local interval last_ts now_ts elapsed
    interval=$(read_setting_int "local_commit_min_interval_sec" 3600)
    last_ts=$(git log -1 --format=%ct -- "$local_path/" 2>/dev/null)
    now_ts=$(date +%s)
    if [ -n "$last_ts" ]; then
      elapsed=$((now_ts - last_ts))
      if [ "$elapsed" -lt "$interval" ]; then
        git reset -q HEAD -- "$local_path/" 2>/dev/null
        echo "[skip] nestwork[$HOST_ID/$AGENT_ID]: local/ throttled, last commit ${elapsed}s ago (< ${interval}s)" >&2
        return 0
      fi
    fi
  fi

  git commit -m "memory: update $HOST_ID/$AGENT_ID" -q -- "$AGENT_REL_PATH/" || return 1
  local attempt
  for attempt in 1 2 3; do
    if git push -q 2>/dev/null; then
      return 0
    fi
    # push rejected -- backoff with jitter (~0.5s, ~1s, ~2s) to reduce
    # thundering-herd when multiple agents commit concurrently, then
    # undo local commit, rebase, re-commit, retry.
    sleep "$(awk -v a="$attempt" 'BEGIN{srand(); printf "%.2f", (2^(a-1))*0.5 + rand()*0.3}')"
    git reset --soft HEAD~1 >/dev/null 2>&1
    if ! pull_rebase; then
      echo "[!] nestwork[$HOST_ID/$AGENT_ID]: rebase conflict, memory not pushed, manual merge needed" >&2
      return 1
    fi
    git commit -m "memory: update $HOST_ID/$AGENT_ID" -q -- "$AGENT_REL_PATH/" || return 1
  done
  echo "[!] nestwork[$HOST_ID/$AGENT_ID]: push retried 3 times, all failed; local commit kept, will retry on next hook" >&2
  return 1
}

case "$PHASE" in
  pre)
    match_agent_file || exit 0
    pull_rebase || {
      echo "[!] nestwork[$HOST_ID/$AGENT_ID]: upstream has conflicting changes, resolve manually before writing memory" >&2
      exit 2   # exit 2 blocks the Write/Edit tool in Claude Code
    }
    ;;
  post)
    match_agent_file || exit 0
    commit_push_retry || exit 0   # don't block; warning already emitted
    ;;
  stop)
    commit_push_retry || exit 0
    ;;
  *)
    exit 0
    ;;
esac
exit 0

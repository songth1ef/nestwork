#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# hivequeen unified hook entry
#
# Usage (invoked by Claude Code settings.json hooks):
#   hook-hivequeen.sh pre  <agent-id>   — PreToolUse  (Write/Edit on memory)
#   hook-hivequeen.sh post <agent-id>   — PostToolUse (Write/Edit on memory)
#   hook-hivequeen.sh stop <agent-id>   — Stop safety-net
#
# Design: atomic per-write sync.
# - pre:  pull --rebase before memory write; abort write on conflict
# - post: commit + push with retry; surface rebase conflict to Claude
# - stop: same as post (safety net for writes that skipped post)
# ─────────────────────────────────────────────────────────────────────────────

set -u
PHASE="${1:-}"
AGENT_ID="${2:-}"
HIVEQUEEN_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MATCHER_SCRIPT="$HIVEQUEEN_PATH/scripts/_hook-match-file.py"

[ -z "$PHASE" ] && exit 0
[ -z "$AGENT_ID" ] && exit 0

# ── Check whether the Write/Edit target is under agents/<id>/ ─────────────────
# Reads hook JSON from THIS script's stdin and forwards to the matcher python.
# Matcher exits 0 on match, 1 otherwise.
match_agent_file() {
  python3 "$MATCHER_SCRIPT" "$HIVEQUEEN_PATH" "$AGENT_ID"
}

# ── git pull --rebase, abort on conflict ──────────────────────────────────────
pull_rebase() {
  cd "$HIVEQUEEN_PATH" || return 1
  if git pull --rebase --autostash -q 2>/dev/null; then
    return 0
  fi
  git rebase --abort 2>/dev/null || true
  return 1
}

# ── commit + push with retry; warn on persistent conflict ─────────────────────
commit_push_retry() {
  cd "$HIVEQUEEN_PATH" || return 1
  git add "agents/$AGENT_ID/" >/dev/null 2>&1 || return 1
  git diff --cached --quiet && return 0
  git commit -m "memory: update $AGENT_ID" -q || return 1
  for i in 1 2 3; do
    if git push -q 2>/dev/null; then
      return 0
    fi
    # push rejected — undo local commit, rebase, retry
    git reset --soft HEAD~1 >/dev/null 2>&1
    if ! pull_rebase; then
      echo "⚠ hivequeen: rebase 冲突，memory 未 push，需手动合并" >&2
      return 1
    fi
    git commit -m "memory: update $AGENT_ID" -q || return 1
  done
  echo "⚠ hivequeen: push 重试 3 次失败" >&2
  return 1
}

case "$PHASE" in
  pre)
    match_agent_file || exit 0
    pull_rebase || {
      echo "⚠ hivequeen: upstream 有冲突变更，请手动合并后再写入 memory" >&2
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

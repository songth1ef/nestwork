#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# nestwork SessionStart hook (v2.5: tiered loading)
#
# Usage (registered by installer in Claude Code settings.json):
#   session-start.sh <host> <agent-id>
#
# Behavior:
#   - Pull latest nestwork (rebase, autostash) so context is fresh.
#   - Emit a *small* context skeleton (<~1.8KB) that Claude Code's SessionStart
#     hook will reliably inject without truncation:
#       1. bundle header
#       2. agent-rules full text (highest priority, smallest file)
#       3. READ-ON-START manifest pointing to strategy / shared / agent memory
#       4. READ-ON-DEMAND manifest pointing to workflow/*.md
#   - The agent is required (by CLAUDE.md / AGENTS.md) to Read the manifest
#     paths before its first response. Large files are pulled in via the agent's
#     Read tool, not via stdout, because Claude Code truncates hook stdout
#     around 2KB regardless of plain-text or JSON-mode output.
#   - Always exit 0. SessionStart must never block session startup.
# -----------------------------------------------------------------------------

set -u
HOST_ID="${1:-}"
AGENT_ID="${2:-}"
NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

[ -z "$HOST_ID" ] && exit 0
[ -z "$AGENT_ID" ] && exit 0

cd "$NESTWORK_PATH" || exit 0

# Native-format path for the manifest. On Git Bash / MSYS the pwd above yields
# `/f/code/...`, which the agent's Read tool on Windows cannot resolve. cygpath
# -m converts to mixed format (`F:/code/...`); on POSIX hosts cygpath is absent
# and we keep the original POSIX path.
if command -v cygpath >/dev/null 2>&1; then
  NESTWORK_PATH_NATIVE="$(cygpath -m "$NESTWORK_PATH" 2>/dev/null || printf '%s' "$NESTWORK_PATH")"
else
  NESTWORK_PATH_NATIVE="$NESTWORK_PATH"
fi

# Refresh, but never block on failure (offline, conflict, etc.)
git pull --rebase --autostash -q 2>/dev/null || git rebase --abort 2>/dev/null || true

# Agent mailbox (Tier 1): refresh this agent's unread-message snapshot into its
# git-ignored local/ dir, so it can be surfaced via the manifest below without
# spending the hook's ~2KB stdout budget (the agent Reads the file, like memory).
# Deletes the snapshot when there is nothing unread. Never blocks startup.
if [ -f scripts/comms/read.sh ]; then
  NESTWORK_SELF="$HOST_ID/$AGENT_ID" \
    bash scripts/comms/read.sh --write "agents/$HOST_ID/$AGENT_ID/local/inbox.md" 2>/dev/null || true
fi

emit_file() {
  local label="$1" path="$2"
  if [ -f "$path" ]; then
    printf '\n=== %s (%s) ===\n' "$label" "$path"
    cat "$path"
  fi
}

# Compact manifest entry: one path per line, absolute, no purpose annotation
# (the section header carries that semantic). Skip missing files silently.
manifest_line() {
  local rel="$1"
  if [ -f "$NESTWORK_PATH/$rel" ]; then
    printf -- '- %s/%s\n' "$NESTWORK_PATH_NATIVE" "$rel"
  fi
}

printf 'nestwork context bundle for %s/%s\n' "$HOST_ID" "$AGENT_ID"
emit_file "agent-rules" "queen/agent-rules.md"

printf '\n=== READ-ON-START (MANDATORY before first reply; see CLAUDE.md) ===\n'
manifest_line "queen/strategy.md"
manifest_line "shared/memory.md"
manifest_line "agents/$HOST_ID/$AGENT_ID/memory.md"
manifest_line "agents/$HOST_ID/$AGENT_ID/local/inbox.md"

printf '\n=== READ-ON-DEMAND (when task-relevant) ===\n'
if [ -d workflow ]; then
  for f in workflow/*.md; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    [ "$base" = "_template.md" ] && continue
    manifest_line "$f"
  done
fi

# Upstream protocol-version check (AGENTS.md §11, v2.3+).
# Compressed to one line so a triggered advisory does not blow the ~2KB budget.
# 24h cache to avoid hitting the network every session start. Never blocks.
check_upstream_version() {
  local cache_dir="${HOME:-/tmp}/.cache/nestwork"
  local cache_file="${cache_dir}/upstream-check"
  local upstream_url="https://raw.githubusercontent.com/songth1ef/nestwork/main/AGENTS.md"
  local now upstream_ver=""
  local local_ver=""
  now="$(date +%s 2>/dev/null || echo 0)"

  local_ver="$(grep -oE 'protocol-version: [0-9]+\.[0-9]+' AGENTS.md 2>/dev/null | awk '{print $2}')"
  [ -z "$local_ver" ] && return 0

  if [ -f "$cache_file" ]; then
    local cached_ts="" cached_ver=""
    read -r cached_ts cached_ver < "$cache_file" 2>/dev/null || true
    if [ -n "$cached_ts" ] && [ -n "$cached_ver" ] && \
       [ "$((now - cached_ts))" -lt 86400 ] 2>/dev/null; then
      upstream_ver="$cached_ver"
    fi
  fi

  if [ -z "$upstream_ver" ]; then
    upstream_ver="$(curl -sf -m 3 "$upstream_url" 2>/dev/null \
      | grep -oE 'protocol-version: [0-9]+\.[0-9]+' \
      | awk '{print $2}')"
    if [ -n "$upstream_ver" ]; then
      mkdir -p "$cache_dir" 2>/dev/null || true
      printf '%s %s\n' "$now" "$upstream_ver" > "$cache_file" 2>/dev/null || true
    fi
  fi

  [ -z "$upstream_ver" ] && return 0
  [ "$upstream_ver" = "$local_ver" ] && return 0

  local newer
  newer="$(printf '%s\n%s\n' "$local_ver" "$upstream_ver" | sort -V | tail -n1)"
  if [ "$newer" = "$upstream_ver" ]; then
    printf '\n[!] nestwork upstream protocol-version %s available (local %s) -- run `bash scripts/maintenance/update.sh` to review.\n' \
      "$upstream_ver" "$local_ver"
  fi
}
check_upstream_version || true

exit 0

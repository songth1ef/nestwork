#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------
# nestwork compile
# Aggregates all agents/*/*/memory.md into shared/memory.md
# ---------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SHARED="$NESTWORK_PATH/shared/memory.md"
AGENTS_DIR="$NESTWORK_PATH/agents"

echo "-> scanning $AGENTS_DIR"

# Collect all agent memory files
MEMORY_FILES=()
while IFS= read -r -d '' f; do
  MEMORY_FILES+=("$f")
done < <(find "$AGENTS_DIR" -name "memory.md" -print0 | sort -z)

if [ ${#MEMORY_FILES[@]} -eq 0 ]; then
  echo "[!] no agent memory files found, nothing to compile"
  exit 0
fi

echo "-> found ${#MEMORY_FILES[@]} agent(s): ${MEMORY_FILES[*]}"

# Strip the installer-generated header (leading H1, blockquote lines, blank
# lines, and the first horizontal rule) plus the empty-memory placeholder,
# passing all real content through verbatim. Content must never be run
# through printf %b or similar: agent memory may legally contain backslash
# sequences that %b would mangle.
strip_header() {
  awk '
    NR == 1 && /^# /                   { next }
    !body && /^[[:space:]]*$/          { next }
    !body && /^>/                      { next }
    !body && /^---[[:space:]]*$/       { next }
    /^_No memory yet\._[[:space:]]*$/  { next }
    { body = 1; print }
  ' "$1"
}

# Build compiled output in a temp file, then move into place atomically.
NOW=$(date -u +"%Y-%m-%d %H:%M UTC")
TMP="$SHARED.tmp"
trap '[ -f "$TMP" ] && rm -f "$TMP"' EXIT

cat > "$TMP" <<EOF
# SHARED MEMORY

> This file is compiled from all agents' private memory.
> Read-only for agents. Do not edit manually.
> Last compiled: $NOW

---

EOF

for f in "${MEMORY_FILES[@]}"; do
  # Build label as <host>/<agent-id> from the two directory levels above memory.md
  AGENT_DIR=$(dirname "$f")
  AGENT_ID=$(basename "$AGENT_DIR")
  HOST_ID=$(basename "$(dirname "$AGENT_DIR")")
  LABEL="$HOST_ID/$AGENT_ID"
  printf '## %s\n\n' "$LABEL" >> "$TMP"
  CONTENT=$(strip_header "$f")
  if [ -z "$(printf '%s' "$CONTENT" | tr -d '[:space:]')" ]; then
    printf '> _No memory recorded yet._\n\n' >> "$TMP"
  else
    printf '%s\n\n' "$CONTENT" >> "$TMP"
  fi
done

mv "$TMP" "$SHARED"
echo "[ok] compiled -> $SHARED"

# Commit and push
cd "$NESTWORK_PATH"
git add shared/memory.md
git diff --cached --quiet -- shared/memory.md || \
  git commit -m "memory: compile shared $(date -u +%Y-%m-%d)" -- shared/memory.md
git push -q

echo "OK shared memory compiled and pushed"

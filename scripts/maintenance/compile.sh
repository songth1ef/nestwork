#!/usr/bin/env bash
set -e

# ---------------------------------------------
# hivequeen compile
# Aggregates all agents/*/*/memory.md into shared/memory.md
# ---------------------------------------------

HIVEQUEEN_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SHARED="$HIVEQUEEN_PATH/shared/memory.md"
AGENTS_DIR="$HIVEQUEEN_PATH/agents"

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

# Build compiled output
NOW=$(date -u +"%Y-%m-%d %H:%M UTC")
OUTPUT="# SHARED MEMORY\n\n"
OUTPUT+="> This file is compiled from all agents' private memory.\n"
OUTPUT+="> Read-only for agents. Do not edit manually.\n"
OUTPUT+="> Last compiled: $NOW\n\n---\n\n"

for f in "${MEMORY_FILES[@]}"; do
  # Build label as <host>/<agent-id> from the two directory levels above memory.md
  AGENT_DIR=$(dirname "$f")
  AGENT_ID=$(basename "$AGENT_DIR")
  HOST_ID=$(basename "$(dirname "$AGENT_DIR")")
  LABEL="$HOST_ID/$AGENT_ID"
  OUTPUT+="## $LABEL\n\n"
  # Strip frontmatter-style header (first H1 + metadata lines)
  CONTENT=$(tail -n +4 "$f" | sed '/^---$/d' | sed '/^_No memory yet\._/d')
  if [ -z "$(echo "$CONTENT" | tr -d '[:space:]')" ]; then
    OUTPUT+="> _No memory recorded yet._\n\n"
  else
    OUTPUT+="$CONTENT\n\n"
  fi
done

printf "%b" "$OUTPUT" > "$SHARED"
echo "[ok] compiled -> $SHARED"

# Commit and push
cd "$HIVEQUEEN_PATH"
git add shared/memory.md
git diff --cached --quiet -- shared/memory.md || \
  git commit -m "memory: compile shared $(date -u +%Y-%m-%d)" -- shared/memory.md
git push -q

echo "OK shared memory compiled and pushed"

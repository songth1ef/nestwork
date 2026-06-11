#!/usr/bin/env bash
set -e

# -----------------------------------------------------------------------------
# nestwork updater
#
# Pulls protocol-layer changes from upstream (songth1ef/nestwork) into your
# private nest. Never touches agents/, queen/, shared/, or projects/ -- those
# belong to you.
#
# Usage:
#   bash ~/my-nest/scripts/maintenance/update.sh
# -----------------------------------------------------------------------------

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UPSTREAM_URL="https://github.com/songth1ef/nestwork.git"
UPSTREAM_BRANCH="main"

# Protocol-layer files that are safe to overwrite from upstream.
# queen/, agents/, shared/, projects/ are intentionally excluded.
#
# .github/workflows/ is included so CI workflow fixes (e.g. the YAML
# indentation bug fixed in nestwork 43ae297) reach every private nest.
# If you need per-nest workflow customization, do it via repo-level
# Variables or Secrets rather than editing the YAML in place.
# Keep this list in sync with PROTOCOL_PATHS in
# .github/workflows/sync-upstream.yml (which carries everything here except
# .github/workflows/ — GITHUB_TOKEN cannot push workflow files).
PROTOCOL_FILES=(
  scripts/
  .github/workflows/
  AGENTS.md
  CLAUDE.md
  SOUL.md
  README.md
  README.zh.md
  CHANGELOG.md
  CHANGELOG.zh.md
  VERSION
  llms.txt
  docs/
  schemas/
  workflow/README.md
  workflow/_template.md
  projects/_template.md
  decisions/_template.md
  decisions/README.md
)

cd "$NESTWORK_PATH"

# -- 1. Ensure upstream remote exists -----------------------------------------
if ! git remote get-url upstream > /dev/null 2>&1; then
  git remote add upstream "$UPSTREAM_URL"
  echo "[ok] added upstream: $UPSTREAM_URL"
else
  echo "[ok] upstream: $(git remote get-url upstream)"
fi

# -- 2. Fetch upstream --------------------------------------------------------
echo "-> fetching upstream/$UPSTREAM_BRANCH ..."
git fetch upstream "$UPSTREAM_BRANCH" -q
echo "[ok] fetched"

# -- 3. Check if protocol layer has changes -----------------------------------
CHANGES=$(git diff HEAD upstream/"$UPSTREAM_BRANCH" -- "${PROTOCOL_FILES[@]}" 2>/dev/null)

if [ -z "$CHANGES" ]; then
  echo ""
  echo "OK already up to date -- no protocol changes"
  exit 0
fi

# -- 4. Show what will change -------------------------------------------------
echo ""
echo "--- incoming protocol changes -------------------------------------------"
git diff HEAD upstream/"$UPSTREAM_BRANCH" --stat -- "${PROTOCOL_FILES[@]}"
echo "-------------------------------------------------------------------------"
echo ""
echo "Files that will NOT be touched: agents/  queen/  shared/  projects/"
echo ""

# -- 5. Confirm ---------------------------------------------------------------
read -r -p "Apply update? [y/N] " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
  echo "aborted"
  exit 0
fi

# -- 6. Apply protocol-layer files from upstream ------------------------------
git checkout upstream/"$UPSTREAM_BRANCH" -- "${PROTOCOL_FILES[@]}"
echo "[ok] protocol layer updated"

# -- 7. Commit ----------------------------------------------------------------
if git diff --cached --quiet; then
  echo "nothing to commit (files already identical)"
else
  git commit -m "chore: update nestwork protocol from upstream"
  echo "[ok] committed"
fi

echo ""
echo "OK done. run 'git push' when ready."

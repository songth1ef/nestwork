#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# hivequeen × claude-mem exporter
#
# Fetches today's observations from claude-mem's HTTP API and writes a digest
# to agents/<id>/claude-mem-digest.md so hivequeen can sync it across machines.
#
# Called automatically during Session End (registered by install-claude.sh).
# Exits cleanly if claude-mem is not running — never blocks the main hook.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

HIVEQUEEN_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_ID="${HIVEQUEEN_AGENT_ID:-claude-$(hostname -s)}"
OUTPUT_FILE="$HIVEQUEEN_PATH/agents/$AGENT_ID/claude-mem-digest.md"
WORKER_URL="${CLAUDE_MEM_URL:-http://localhost:37777}"

# ── 1. Guard: skip silently if claude-mem worker is not running ───────────────
if ! curl -sf "$WORKER_URL/api/health" > /dev/null 2>&1; then
  echo "⚠  claude-mem not running at $WORKER_URL — skipping export"
  exit 0
fi

# ── 2. Fetch today's observations ─────────────────────────────────────────────
TODAY=$(date +%Y-%m-%d)

DIGEST=$(python3 - <<PYEOF
import urllib.request, json, sys

base_url = "$WORKER_URL"
today    = "$TODAY"

def fetch_json(path):
    try:
        with urllib.request.urlopen(base_url + path, timeout=5) as r:
            return json.loads(r.read())
    except Exception:
        return None

data = fetch_json(f"/api/search?date={today}&limit=100")
if not data:
    sys.exit(0)

lines = []

# MCP envelope: {"content": [{"type": "text", "text": "..."}]}
if isinstance(data, dict) and "content" in data:
    for item in data.get("content", []):
        if isinstance(item, dict) and item.get("type") == "text":
            lines.append(item["text"])

# Raw list of observation objects
elif isinstance(data, list):
    for obs in data:
        if not isinstance(obs, dict):
            continue
        ts      = obs.get("timestamp", obs.get("created_at", ""))[:16]
        content = obs.get("content",   obs.get("text", ""))
        if content:
            lines.append(f"- [{ts}] {content}")

# Direct text / result field
elif isinstance(data, dict):
    text = data.get("text", data.get("result", ""))
    if text:
        lines.append(text)

print("\n".join(lines))
PYEOF
)

if [ -z "$DIGEST" ]; then
  echo "⚠  claude-mem returned empty digest for $TODAY — skipping"
  exit 0
fi

# ── 3. Write digest file ──────────────────────────────────────────────────────
mkdir -p "$(dirname "$OUTPUT_FILE")"
NOW=$(date -u +"%Y-%m-%d %H:%M UTC")

cat > "$OUTPUT_FILE" <<MDEOF
# claude-mem digest — $AGENT_ID

> Exported: $NOW
> Source: claude-mem @ $WORKER_URL
> Coverage: $TODAY

---

$DIGEST
MDEOF

echo "✓ claude-mem digest → $OUTPUT_FILE"

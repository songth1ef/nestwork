#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# nestwork x claude-mem exporter
#
# Fetches today's observations from claude-mem's HTTP API and writes a digest
# to agents/<host>/<id>/claude-mem-digest.md so nestwork can sync it across machines.
#
# Called automatically during Session End (registered by install-claude.sh).
# Exits cleanly if claude-mem is not running -- never blocks the main hook.
# -----------------------------------------------------------------------------

set -euo pipefail

NESTWORK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Args: $1 = host, $2 = agent-id (both required, forwarded from Stop hook)
HOST_ID="${1:-${NESTWORK_HOST:-}}"
AGENT_ID="${2:-${NESTWORK_AGENT_ID:-}}"

if [ -z "$HOST_ID" ] || [ -z "$AGENT_ID" ]; then
  # Fallback: resolve from identity helper (e.g. when run manually)
  eval "$(python3 "$NESTWORK_PATH/scripts/install/_identity.py" claude --with-suffix 2>/dev/null | \
    awk 'NR==1{print "HOST_ID="$0} NR==2{print "AGENT_ID="$0}')"
fi

[ -z "$HOST_ID" ] && { echo "[!]  claude-mem export: host unresolved, skipping" >&2; exit 0; }
[ -z "$AGENT_ID" ] && { echo "[!]  claude-mem export: agent-id unresolved, skipping" >&2; exit 0; }

OUTPUT_FILE="$NESTWORK_PATH/agents/$HOST_ID/$AGENT_ID/claude-mem-digest.md"
WORKER_URL="${CLAUDE_MEM_URL:-http://localhost:37777}"

# -- 1. Guard: skip silently if claude-mem worker is not running ---------------
if ! curl -sf "$WORKER_URL/api/health" > /dev/null 2>&1; then
  echo "[!]  claude-mem not running at $WORKER_URL -- skipping export"
  exit 0
fi

# -- 2. Fetch today's observations ---------------------------------------------
TODAY=$(date +%Y-%m-%d)

# Pass URL/date via argv (quoted heredoc) so a user-controlled CLAUDE_MEM_URL
# can never inject into the Python source.
DIGEST=$(python3 - "$WORKER_URL" "$TODAY" <<'PYEOF'
import urllib.request, json, sys

base_url = sys.argv[1]
today    = sys.argv[2]

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
  echo "[!]  claude-mem returned empty digest for $TODAY -- skipping"
  exit 0
fi

# -- 3. Write digest file ------------------------------------------------------
mkdir -p "$(dirname "$OUTPUT_FILE")"
NOW=$(date -u +"%Y-%m-%d %H:%M UTC")

cat > "$OUTPUT_FILE" <<MDEOF
# claude-mem digest -- $HOST_ID/$AGENT_ID

> Exported: $NOW
> Source: claude-mem @ $WORKER_URL
> Coverage: $TODAY

---

$DIGEST
MDEOF

echo "[ok] claude-mem digest -> $OUTPUT_FILE"

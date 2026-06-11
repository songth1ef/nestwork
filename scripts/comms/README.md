# Nestwork Agent Mailbox — git-native inter-agent messaging

Let multiple agents (across machines / tool-chains) message each other with **zero
external dependencies** — pure git + bash, reusing nestwork's existing
pull/commit/push pipeline. No server, no IM, no bot.

This is the answer to "how do my agents talk to each other?" when IM platforms
won't do it: e.g. **Telegram bots cannot see each other's messages** by design, so
agent↔agent traffic needs a different channel. This is that channel. (IM/group
chat stays useful for *human↔agent* — the two layers are complementary.)

## Core design: single-writer outbox

Nestwork's rule is **each agent may only write its own `agents/<host>/<agent-id>/`
directory.** So there is no shared mailbox. Instead:

- **Send** = write into *your own* `outbox/` (tagged `to:`). One file = one commit.
- **Receive** = scan *everyone's* `agents/*/*/outbox/`, pick the ones `to == me`.
- **Read state** = the recipient records seen ids in its own git-ignored
  `local/comms/seen.txt` (never committed; legacy `comms/seen.txt` is imported
  automatically on first read).

Zero write conflicts (one writer per file), fully protocol-compliant, decentralized.

## Envelope format (markdown + frontmatter)

```
---
id: 20260606T103000+0800-a0t3-a1b2c3d4   # globally unique
from: meizu21/claude-a0t3
to:   vm-0-6-ubuntu/claude-va1k          # a host/agent, or "all" for broadcast
type: task | message | broadcast
thread: <thread id; first message = its own id>
reply_to: <id being replied to, or empty>
status: open
created: 20260606T103000+0800
subject: one-line subject
---

free-form markdown body
```

| type | meaning | reply expected |
|---|---|---|
| `task` | A delegates to B; B replies with `reply_to` carrying the result | yes |
| `message` | two-way conversation, multi-turn sharing one `thread` | usually |
| `broadcast` | one-way notice / status (`to: all`) | no |

## Usage

"Who am I" is resolved from `NESTWORK_SELF`, else `~/.nestwork_host` +
`~/.nestwork_id_claude`. Other tool-chains: `export NESTWORK_SELF=<host>/<agent-id>`.

```bash
cd <nestwork repo root>

# send a task
echo "please confirm receipt with a reply" | \
  bash scripts/comms/send.sh vm-0-6-ubuntu/claude-va1k task "handshake test"

# read unread messages addressed to me (view only)
bash scripts/comms/read.sh

# read and mark them seen
bash scripts/comms/read.sh --mark

# move my own outbox messages older than 30 days into outbox/archive/
bash scripts/comms/archive.sh 30
```

`send.sh` commits and pushes the message itself (the per-write hooks only match
Write/Edit tool calls, so a Bash-invoked send cannot rely on them); the recipient
sees it on their next `pull` (or session start).

## Tiers

- **Tier 0 — async (this, manual):** send/read by hand. Messages are delivered on
  the recipient's next pull. Persistent, auditable, zero infra.
- **Tier 1 — async with auto-injection (this, wired into the hook):** the
  `session-start` hook runs `read.sh --write agents/<self>/local/inbox.md` on
  startup and adds that path to the READ-ON-START manifest, so **the agent reads
  unread messages automatically on every session start** — without blowing the
  hook's ~2KB stdout budget (the agent Reads the file, same pattern as
  strategy/memory). `local/` is git-ignored, so the snapshot never bloats the repo
  and never triggers a commit.
- **Tier 2 — real-time (not built):** for genuine sub-second agent coordination,
  add a self-hosted bus/IM (e.g. Matrix/MQTT over Tailscale). Only worth it if
  async (Tier 1) proves insufficient.

## Why not just use git for everything (won't it bloat?)

Mailbox messages are **many small files, each written once** — git handles that
well (a commit ≈ the message itself, a few KB). This is unlike high-churn single
files like `history.jsonl` (see CHANGELOG v0.6.0), which bloated a downstream repo
to 177 MB. Guardrails: the Tier-1 inbox snapshot and the seen list live in
git-ignored `local/`; `archive.sh [days]` moves old messages out of the scanned
`outbox/` path so read cost stays bounded; for high-frequency machine-to-machine
streams, do **not** route them through git history — use a real-time bus (Tier 2)
instead. Match the traffic to the channel.

## Volume guidance

- Low-frequency, structured (tasks/notices, tens/day): git mailbox is the right fit.
- High-frequency, machine heartbeat/state (hundreds–thousands/day): do not put it
  in git main history — that is what re-creates the 177 MB problem. Use Tier 2.

# Agent mailbox (git-native inter-agent messaging)

> Built-in capability. Let multiple agents — across machines and tool-chains — message
> each other with **zero external dependencies**: pure git + bash, reusing nestwork's
> existing pull/commit/push pipeline. No server, no IM, no bot.

---

## 0. One-line definition

Each agent sends by writing into *its own* `outbox/` (one message = one file = one commit)
and receives by scanning *everyone's* outbox for messages addressed to it. Git is the
transport; `send.sh` commits and pushes the message itself on send.

## 1. Why this exists

This is the answer to "how do my agents talk to each other?" when IM platforms can't do
it. For example, **Telegram bots cannot see each other's messages** by design, so
agent↔agent traffic needs a different channel. The mailbox is that channel. (IM / group
chat stays useful for *human↔agent* — the two layers are complementary, not competing.)

Because messages are plain Markdown committed to git, the channel is **persistent,
auditable, and decentralized** for free: every message is a versioned file, every
delivery is a push, and there is no broker to run or trust.

## 2. Single-writer design (why there are no write conflicts)

Nestwork's core rule is **each agent may only write its own `agents/<host>/<agent-id>/`
directory.** A shared mailbox would violate that. So instead of one shared inbox, the
mailbox is built from per-agent outboxes:

- **Send** = write into *your own* `outbox/`, tagged with `to:`. One file, one commit.
- **Receive** = scan *everyone's* `agents/*/*/outbox/`, select the ones where `to == me`
  (or `to == all`).
- **Read state** = the recipient records seen ids in *its own* git-ignored
  `local/comms/seen.txt`. It never enters a commit, so marking messages read creates no
  churn on `main`. (A legacy committed `comms/seen.txt` from older versions is imported
  automatically on first read; you may `git rm` it afterwards.)

One writer per file means **zero write conflicts**, fully protocol-compliant, with no
central component.

## 3. Envelope format (Markdown + frontmatter)

```
---
id: 20260606T103000+0800-a0t3-a1b2c3d4   # globally unique (timestamp-agent-random)
from: meizu21/claude-a0t3
to:   vm-0-6-ubuntu/claude-va1k          # a host/agent, or "all" for broadcast
type: task | message | broadcast
thread: <thread id; the first message is its own thread>
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

## 4. Usage

"Who am I" is resolved from `NESTWORK_SELF`, else `~/.nestwork_host` +
`~/.nestwork_id_claude`. Other tool-chains: `export NESTWORK_SELF=<host>/<agent-id>`.

```bash
cd <nestwork repo root>

# send a task
echo "please confirm receipt with a reply" | \
  bash scripts/comms/send.sh vm-0-6-ubuntu/claude-va1k task "handshake test"

# read unread messages addressed to me (view only)
bash scripts/comms/read.sh

# read and mark them seen (do this after you have acted on them)
bash scripts/comms/read.sh --mark

# move my own outbox messages older than 30 days into outbox/archive/
bash scripts/comms/archive.sh 30
```

`send.sh` commits and pushes the message itself, so delivery works the same from any
tool-chain or a plain shell. (The per-write hooks only match Write/Edit tool calls, so a
Bash-invoked send cannot rely on them; on Claude Code the Stop-hook safety net
additionally covers any message whose push failed.) The recipient sees the message on its
next `pull` (or session start).

## 5. Tiers

- **Tier 0 — async, manual.** Send / read by hand. Messages arrive on the recipient's
  next pull. Persistent, auditable, zero infrastructure.
- **Tier 1 — async with auto-injection (wired into the hook).** The `session-start` hook
  runs `read.sh --write agents/<self>/local/inbox.md` on startup and adds that path to the
  READ-ON-START manifest, so **the agent reads unread messages automatically on every
  session start** — without blowing the hook's ~2KB stdout budget (the agent Reads the
  file, the same pattern used for strategy / memory). `local/` is git-ignored, so the
  snapshot never bloats the repo and never triggers a commit. When there is nothing
  unread the snapshot file is deleted.
- **Tier 2 — real-time (not built).** For genuine sub-second coordination, add a
  self-hosted bus / IM (e.g. Matrix or MQTT over Tailscale). Only worth it if async
  (Tier 1) proves insufficient.

## 6. Volume guidance (will git bloat?)

Mailbox messages are **many small files, each written once** — git handles that well (a
commit ≈ the message itself, a few KB). This is unlike high-churn *single* files such as
`history.jsonl` (see CHANGELOG v0.6.0), which once bloated a downstream repo to 177 MB.

- **Low-frequency, structured** (tasks / notices, tens per day): the git mailbox is the
  right fit.
- **High-frequency machine heartbeat / state** (hundreds–thousands per day): do **not**
  route it through git main history — that re-creates the 177 MB problem. Use Tier 2.

Guardrails: the Tier-1 inbox snapshot and the seen list both live in git-ignored
`local/`; `archive.sh` moves old messages out of the scanned `outbox/` path
(`bash scripts/comms/archive.sh [days]`, default 30) so read cost stays bounded as the
mailbox ages. Match the traffic to the channel.

## 7. Integration with other parts of Nestwork

- **Write protocol** (see `AGENTS.md`): sending is a write into your own directory, so it
  is fully protocol-compliant. Delivery is handled by `send.sh` itself (commit + push with
  rebase-retry); on Claude Code the Stop-hook safety net also commits anything that
  slipped through.
- **Session lifecycle**: Tier 1 plugs into the same `session-start` injection used for
  `strategy.md` and memory — the inbox snapshot is one more READ-ON-START path.
- **Human↔agent channels** (Telegram / group chat): orthogonal and complementary. Use IM
  for a human to direct agents; use the mailbox for agents to coordinate with each other.

## 8. Maintenance

- This is a built-in capability of the Nestwork protocol. Scripts live in
  `scripts/comms/` (`send.sh`, `read.sh`, `archive.sh`, `README.md`); the Tier-1 hook is
  in `scripts/hooks/session-start.sh`.
- Last reviewed: 2026-06-11.
- Known stale conditions: changes to the `agents/<host>/<agent-id>/` layout, the identity
  resolution (`NESTWORK_SELF` / `~/.nestwork_*`), or the READ-ON-START manifest budget.

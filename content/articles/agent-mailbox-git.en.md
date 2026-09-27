---
title: Agent-to-Agent Communication with a Git Mailbox
description: AI agents can message each other through git: each writes to its own outbox, reads mail addressed to it on demand. No server, queue or bot needed.
keywords: agent to agent communication, AI agents message each other, multi-agent messaging, git mailbox, nestwork, AI coding agents
date: 2026-09-27
---

**Can two AI coding agents on different machines leave each other messages without a server?** Yes. If they already share a git repository, a message can simply be a small Markdown file that one agent commits and the other reads after its next pull. nestwork ships this as a built-in "agent mailbox": each agent writes only into its own `outbox/`, and receiving means scanning everyone's outbox for messages addressed to you. There is no message queue, no broker and no bot.

This article answers the practical questions: why not use a chat platform, how the single-writer design avoids conflicts, the exact commands, and the identity setting (`NESTWORK_SELF`) that trips people up.

## Why agents need their own channel

Human-to-agent chat is well covered: you type in a terminal, or you wire a bot into Telegram or a group chat. Agent-to-agent traffic is a different problem. nestwork's [mailbox reference](https://github.com/songth1ef/nestwork/blob/main/docs/agent-mailbox.md) points out that Telegram bots cannot see each other's messages by design, so a group chat full of bots is not a coordination channel.

The things agents actually need to pass each other are low-frequency and structured: "I finished the migration, you take the tests", "this deploy script has a trap", "please confirm you received this". That traffic wants to be persistent (it survives a closed session), auditable (you can see who asked what) and cheap to run. A git repo that the agents already pull at session start gives you all three.

## How the mailbox works: single-writer outboxes

nestwork's core rule is that each agent may only write its own directory, `agents/<host>/<agent-id>/`. A shared inbox would break that rule, so the mailbox is built the other way around:

| Action | What happens |
|---|---|
| Send | Write one file into *your own* `outbox/`, tagged with `to:`. One message = one file = one commit. |
| Receive | Scan every `agents/*/*/outbox/*.md` and pick messages where `to` is you or `all`. |
| Mark read | Append the message id to your git-ignored `local/comms/seen.txt`. No commit is created. |

Because only one agent ever writes a given file, two agents sending at the same time cannot produce a write conflict. Read state never enters git, so checking mail does not churn the history.

Each message is Markdown with front matter:

```markdown
---
id: 20260606T103000+0800-a0t3-a1b2c3d4
from: meizu21/claude-a0t3
to: vm-0-6-ubuntu/claude-va1k
type: task
thread: 20260606T103000+0800-a0t3-a1b2c3d4
reply_to:
status: open
created: 20260606T103000+0800
subject: handshake test
---

please confirm receipt with a reply
```

There are three types: `task` (a reply is expected), `message` (a multi-turn conversation sharing one `thread`) and `broadcast` (one-way notice, usually `to: all`).

## Sending, reading and archiving

All three scripts live in [`scripts/comms/`](https://github.com/songth1ef/nestwork/blob/main/scripts/comms/README.md) and must be run from inside your nest repository, because they locate the repo with `git rev-parse --show-toplevel`.

```bash
cd ~/nestwork

# send: recipient, type, subject; the body comes from stdin
echo "please confirm receipt with a reply" | \
  bash scripts/comms/send.sh vm-0-6-ubuntu/claude-va1k task "handshake test"

# reply in the same thread: add the thread id and the id you answer
echo "received, running now" | \
  bash scripts/comms/send.sh meizu21/claude-a0t3 message "re: handshake test" \
  <thread-id> <message-id>

# read unread mail addressed to me (view only)
bash scripts/comms/read.sh

# read and mark everything shown as seen, after acting on it
bash scripts/comms/read.sh --mark

# move my own messages older than 30 days to outbox/archive/
bash scripts/comms/archive.sh 30
```

`send.sh` commits and pushes the message itself, with a commit message like `comms: task to <host>/<agent-id> (<id>)`. It does this on purpose: nestwork's per-write hooks only fire on Write/Edit tool calls, so a message sent through a shell command cannot rely on them. If the push fails, the message stays committed locally and goes out with the next successful push from that checkout.

`read.sh` does not pull. The recipient sees new mail after its next `git pull`, which on Claude Code happens automatically when a session starts. `--mark` marks every message it printed; there is no per-message marking.

`archive.sh` only touches your own outbox and is time-based, because a sender cannot know whether a recipient has read a message (the seen list is local to the recipient). Pick a window longer than your slowest agent's check-in cadence.

## Read on demand, not at every startup

Since protocol 3.0, nestwork keeps startup small: only the core rules and two short resident summaries load. On Claude Code the SessionStart hook also refreshes a git-ignored snapshot of unread mail at `agents/<host>/<agent-id>/local/inbox.md`, but it lists that path under READ-ON-DEMAND, not READ-ON-START. The agent opens it when it is coordinating or resuming related work. Tools without that hook can run `read.sh` themselves.

One rule matters here: mail is coordination data, not user authorization. The protocol says so explicitly. An agent should not start deleting files because another agent's message asked it to; your instructions still come from you.

## The `NESTWORK_SELF` gotchas

The scripts need to know "who am I". They use `NESTWORK_SELF` if it is set, otherwise `~/.nestwork_host` plus `~/.nestwork_id_claude`. That fallback is Claude-specific, which leads to a few traps:

1. **Non-Claude agents must set it.** Codex's installer stores its id in `~/.nestwork_id_codex` (the id is usually just `codex`). Without `NESTWORK_SELF`, a Codex agent on a machine that also has Claude Code installed would send and read mail *as the Claude agent*. On a machine without Claude, the scripts stop with `cannot resolve agent id`.

```bash
export NESTWORK_SELF="$(cat ~/.nestwork_host)/$(cat ~/.nestwork_id_codex)"
```

2. **Addresses must match exactly.** `read.sh` compares the `to:` line with `<host>/<agent-id>` as a plain string, and `send.sh` does not check that the recipient exists. A typo means the message sits in your outbox forever with no error. Copy the address from the recipient's directory name under `agents/`.
3. **Run from the nest repo.** Run `send.sh` from inside another project and it resolves *that* repo as the root, writing and pushing the message there. Always `cd` into the nest first.
4. The Claude Code SessionStart hook sets `NESTWORK_SELF` itself when it refreshes the inbox snapshot, so the snapshot is correct even if your shell variable is not.

## When a git mailbox is the wrong tool

Mailbox messages are many small files written once, which git handles well. The docs draw a clear line: tens of structured tasks and notices per day fit; hundreds or thousands of machine heartbeats per day do not. That kind of high-frequency traffic would bloat the main history, the same failure nestwork once saw with a high-churn `history.jsonl` file that grew a repo to 177 MB. For genuine real-time coordination, the docs suggest a self-hosted bus such as Matrix or MQTT, which nestwork deliberately does not build.

The author's own write-up describes the moment this felt worthwhile: an agent on one machine finishing a chunk of work and leaving a line for the agent on another machine, "I'm done with this part, you take it from here", and the other picking it up when it next coordinated ([16 agents, one brain](../16-agents-one-brain/)).

## FAQ

### Is this real-time messaging?

No. Delivery happens on the recipient's next pull, typically at session start. The docs describe a real-time tier as "not built" and only worth adding if asynchronous delivery proves insufficient.

### Can I broadcast to every agent?

Yes. Send with `to` set to `all` and type `broadcast`. Every agent's `read.sh` treats `all` as addressed to it.

### Does marking mail as read create commits?

No. Seen ids live in `agents/<host>/<agent-id>/local/comms/seen.txt`, and `local/` is git-ignored by default. Only sending and archiving create commits.

### Can other agents read messages that are not addressed to them?

Yes, technically. Every outbox is a plain file in a repo all your agents can read, and the filter is only a convention. Keep secrets out of messages, just as you keep them out of memory.

## Related

- [Git-native memory for AI agents](../git-native-agent-memory/)
- [Multi-agent memory without conflicts](../multi-agent-memory-without-conflicts/)
- [Loading topic memory on demand](../topic-memory-on-demand-loading/)
- [Encrypt agent memory with git-crypt](../encrypt-agent-memory-git-crypt/)
- [I gave 16 AI agents one shared brain](../16-agents-one-brain/)

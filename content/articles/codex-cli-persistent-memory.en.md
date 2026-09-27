---
title: Codex CLI Memory, AGENTS.md and Persistent Recall
description: How Codex CLI remembers today (AGENTS.md and opt-in local memories), and how to give Codex persistent memory across sessions and machines with git.
keywords: Codex CLI memory, Codex persistent memory, Codex AGENTS.md, Codex memories, ~/.codex/AGENTS.md, AI agent memory, nestwork
date: 2026-09-27
---

Codex CLI has two ways to carry context between sessions: `AGENTS.md` instruction files, which it reads every time it starts, and an optional memories feature that writes summaries of past chats to `~/.codex/memories/`. Memories are off by default and stored locally; OpenAI's own docs tell you to keep rules that must always apply in `AGENTS.md`. For Codex persistent memory that survives across sessions and machines, put that context in a private git repository and have your global `~/.codex/AGENTS.md` tell Codex to pull it, read it, and commit what it learns.

## What Codex remembers on its own

OpenAI documents two built-in mechanisms.

**AGENTS.md instruction chain.** Per the [AGENTS.md guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md), Codex builds an instruction chain when it starts, once per run (in the TUI, usually once per launched session):

1. Global scope: in your Codex home (`~/.codex` unless you set `CODEX_HOME`), it reads `AGENTS.override.md` if it exists, otherwise `AGENTS.md`.
2. Project scope: starting at the project root (typically the git root), it walks down to your current directory, checking `AGENTS.override.md`, then `AGENTS.md`, then any fallback names you configured.
3. Files are concatenated root-first, so guidance closer to your working directory appears later and wins. Codex stops adding files once the total reaches `project_doc_max_bytes`, 32 KiB by default.

**Memories.** The [memories page](https://learn.chatgpt.com/docs/customization/memories?surface=cli) says local Codex memories are off by default. You turn them on with `[features] memories = true` in `config.toml` (or a toggle in the desktop app). Codex then turns useful context from earlier chats into memory files under `~/.codex/memories/` in the background. It skips active or short-lived sessions, redacts secrets from generated fields, and may skip a pass when your rate-limit headroom is low. `/memories` controls, per chat, whether that chat uses existing memories and whether it can feed future ones.

OpenAI is explicit about the division of labor: keep required guidance in `AGENTS.md` or checked-in docs, and treat memories as a helpful recall layer, not the only source for rules that must always apply.

## Where that leaves you

Both mechanisms live on one machine. Your global `~/.codex/AGENTS.md` is a file in your home directory, and memories are files under your Codex home. The memories documentation describes local storage and says nothing about syncing it between devices. A second laptop, a cloud dev box, or a fresh install starts without them. And because generated memories are summaries Codex writes for itself, they are not a place to curate decisions you want other tools to read.

A project `AGENTS.md` does travel with its repository, which is the right home for project rules. What is missing is a layer for everything else: personal preferences, cross-project decisions, and progress notes that should follow you to any machine and any tool.

## Persistent memory for Codex with a git repo

The simplest durable layer is a private git repository of markdown files, loaded through the one file Codex always reads: the global `AGENTS.md`. The instruction in that file does the work: pull at session start, read a small set of files, search the rest on demand, and commit your own changes before you finish.

nestwork packages this as a protocol and an installer. What [`scripts/install/codex.sh`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/codex.sh) does:

1. Resolves this machine's host name (`~/.nestwork_host`) and the Codex agent id, which is `codex` (`~/.nestwork_id_codex`).
2. Creates `agents/<host>/codex/memory.md` in your nest.
3. Writes a startup block into `~/.codex/AGENTS.md`, and the same block into `~/.codex/instructions.md` for older setups. The block sits between `<!-- nestwork:begin -->` and `<!-- nestwork:end -->`, so your other content stays.
4. Registers one SessionEnd hook in `~/.codex/hooks.json` (and points `config.toml` at it) for optional local-history snapshots.

## Step by step

The commands (on Windows, run `.\nestwork\scripts\install\codex.ps1`; `python3` must be on `PATH`):

```bash
git clone git@github.com:<you>/nestwork.git ~/nestwork
bash ~/nestwork/scripts/install/codex.sh
```

1. Create a private repo from the [nestwork template](https://github.com/songth1ef/nestwork/generate) and clone it with the first command.
2. Run the Codex installer with the second command.
3. Open `~/.codex/AGENTS.md` and check the nestwork block is there.
4. Start Codex and ask it to summarize its current instructions; the block should appear. OpenAI's guide suggests the same check to confirm which files loaded.
5. Put one non-sensitive rule in `queen/agent-rules.md`, push it, and ask Codex on another machine (installed the same way) to repeat it.

## What Codex reads, and when it commits

At session start, Codex pulls the nest and reads only the resident tier: `queen/agent-rules.md`, `shared/resident.md`, and `agents/<host>/codex/resident.md` if present. Strategy, shared history, its own `memory.md`, `projects/` and `workflow/` are searched when a task needs them. This keeps the startup cost small; on the author's own nest the resident startup is about 640 tokens, compared with about 69,600 for a 2.x-style load of everything (measured 2026-09, `o200k_base`). That matters for Codex specifically, since its instruction chain stops at 32 KiB by default: the nestwork block only adds pointers, not the memory itself.

Committing is manual by design. The SessionEnd hook only launches the optional history snapshot, detached, because Codex gives SessionEnd hooks at most 3 seconds ([Codex hooks docs](https://learn.chatgpt.com/docs/hooks)). It does not touch memory. The bootstrap tells Codex to sync its directory when memory changed:

```bash
git -C ~/nestwork add agents/<host>/codex/
git -C ~/nestwork diff --cached --quiet -- agents/<host>/codex/ || \
  git -C ~/nestwork commit -m "memory: update <host>/codex" -- agents/<host>/codex/
git -C ~/nestwork push
```

Codex itself now supports PreToolUse and PostToolUse hooks on file edits, but nestwork does not register per-write sync for Codex today; only Claude Code and Kimi Code get that. If a session ends abruptly, the next session's commit picks up whatever was left in the directory.

## Using Codex memories and nestwork together

They do different jobs and don't collide. Codex memories are automatic, local recall about your past chats. The nest holds curated context you chose to keep, readable by other tools. If Codex memories contain something worth keeping, carry it over deliberately: nestwork's [AGENTS.md §13](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md) lists `~/.codex/memories/` as a source and describes distilling it into `resident.md`, on-demand memory, or a cold `carryover/codex.md`. Details in [rescuing tool-native memory](../rescue-tool-native-memory/).

## FAQ

### Does Codex CLI have long-term memory built in?

It has two things: `AGENTS.md` files that load every session, and an opt-in memories feature that summarizes past chats into `~/.codex/memories/`. Memories are off by default and stored under your Codex home on that machine.

### Where is the global Codex AGENTS.md?

In your Codex home, `~/.codex/AGENTS.md` by default, or `$CODEX_HOME/AGENTS.md` if you set `CODEX_HOME`. An `AGENTS.override.md` in the same place takes precedence.

### Will a long memory file push my project AGENTS.md past the 32 KiB limit?

Not with this setup. The nestwork block in the global file is a short list of paths and rules; Codex reads the memory files themselves with its normal file tools, and only the ones the task needs.

### Can I use Codex and Claude Code on the same nest?

Yes. Each tool gets its own agent id and directory on the same machine. See [sharing memory between Claude Code and Codex](../share-memory-claude-code-codex/).

## Related

- [Share memory between Claude Code and Codex](../share-memory-claude-code-codex/)
- [AGENTS.md vs CLAUDE.md vs memory](../agents-md-vs-claude-md-vs-memory/)
- [Topic memory and on-demand loading](../topic-memory-on-demand-loading/)
- [Rescue tool-native memory](../rescue-tool-native-memory/)
- [AI agent memory](../ai-agent-memory/)

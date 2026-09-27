---
title: Claude Code Memory Across Machines, Synced with Git
description: Claude Code's CLAUDE.md and auto memory stay on one machine. Where they're stored, why they don't sync, and how to share them across machines with git.
keywords: Claude Code memory, Claude Code memory across machines, sync Claude Code memory, Claude Code auto memory, CLAUDE.md, nestwork
date: 2026-09-27
---

Claude Code remembers things in two places: CLAUDE.md files that you write, and auto memory that Claude writes for itself under `~/.claude/projects/<project>/memory/`. Anthropic's documentation says plainly that auto memory is machine-local, so a second laptop or a cloud host starts without it. To make Claude Code memory follow you across machines, keep the memory in a git repository you own and have every machine pull before it reads and push after it writes. That is what nestwork's Claude Code installer sets up.

## Where Claude Code stores memory today

Claude Code has two memory systems, and both are loaded at the start of every conversation, according to the [official memory docs](https://code.claude.com/docs/en/memory).

| | CLAUDE.md files | Auto memory |
|---|---|---|
| Who writes it | You | Claude |
| Where it lives | `~/.claude/CLAUDE.md` (user), `./CLAUDE.md` or `./.claude/CLAUDE.md` (project), `./CLAUDE.local.md` (personal, per project) | `~/.claude/projects/<project>/memory/` |
| What loads at startup | The whole file (Claude Code loads a CLAUDE.md of up to 4 MiB in full) | The first 200 lines or 25KB of `MEMORY.md`; topic files are read on demand |
| Scope | User, project, or organization | Per repository, shared across worktrees |

A project's `CLAUDE.md` travels with the repository if you commit it. Everything else is a file on the machine where it was written. Your user-level `~/.claude/CLAUDE.md` sits in your home directory, `CLAUDE.local.md` is meant to be gitignored, and auto memory lives under `~/.claude`.

## Why auto memory does not follow you

The memory page is direct about it: *"Auto memory is machine-local. All worktrees and subdirectories within the same git repository share one auto memory directory. Files are not shared across machines or cloud environments."*

There is a second, less obvious catch. The `<project>` folder name is derived from a path. The [sessions documentation](https://code.claude.com/docs/en/sessions) says transcripts are stored under `~/.claude/projects/<project>/`, where `<project>` is the working directory path with non-alphanumeric characters replaced by `-`. So even if you copy `~/.claude` to a new machine, a repository checked out at a different path or on a different drive produces a different folder name, and the copied memory does not attach to it.

You can move auto memory with the `autoMemoryDirectory` setting (an absolute path or one starting with `~/`), but that only changes where it sits on disk. It does not add syncing, review, or history.

## The general approach: memory in a git repo you own

Cross-machine memory needs three things: one source of truth, a way for each machine to fetch updates before it reads, and a way to publish changes after it writes without clobbering another machine. Git already does all three for text files. Agent memory is text, so the simplest durable answer is a private git repository with markdown memory, plus hooks that run `pull` and `push` at the right moments.

nestwork is a protocol built on that idea. You create a private repository from the [template](https://github.com/songth1ef/nestwork/generate), clone it on each machine, and run a per-tool installer. Every agent instance gets its own directory, `agents/<host>/<agent-id>/`, and only writes there, so two machines never edit the same memory file.

## Step by step: Claude Code memory across machines with nestwork

The commands for each machine (on Windows, run `.\nestwork\scripts\install\claude.ps1` instead of the `.sh` script; `python3` must be on `PATH`):

```bash
git clone git@github.com:<you>/nestwork.git ~/nestwork
bash ~/nestwork/scripts/install/claude.sh
```

1. Create your private nest from the template (Use this template, visibility Private). Don't fork: forks are public by default and share history with upstream.
2. Clone it on the first machine with the first command above.
3. Run the Claude Code installer with the second command.
4. Repeat steps 2 and 3 on every other machine. Each machine gets its own host name in `~/.nestwork_host` and its own Claude agent id (such as `claude-a7k2`) in `~/.nestwork_id_claude`.
5. Verify: write a harmless, recognizable rule into the nest on machine A, let it push, then open Claude Code on machine B and ask it to summarize your rules.

## What the installer actually registers

The installer does three things, which you can check in [`scripts/install/claude.sh`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/claude.sh) and [`scripts/install/_hooks.py`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/_hooks.py):

- Creates `agents/<host>/<agent-id>/memory.md` for this instance.
- Writes a startup protocol block into `~/.claude/CLAUDE.md` between `<!-- nestwork:begin -->` and `<!-- nestwork:end -->` markers. Your own content in that file is kept.
- Merges five hooks into `~/.claude/settings.json`. Re-running replaces earlier nestwork entries instead of duplicating them.

| Hook | Matcher | What it does |
|---|---|---|
| SessionStart | all | `session-start.sh`: `git pull --rebase`, then prints a READ-ON-START list of resident files |
| PreToolUse | Write, Edit | `nestwork.sh pre`: if the target is inside this agent's directory, pull first; a conflict exits with code 2, which blocks the write |
| PostToolUse | Write, Edit | `nestwork.sh post`: commit and push this agent's directory, retrying the push up to 3 times |
| Stop | all | Safety-net commit and push after each turn; a no-op when nothing changed |
| SessionEnd | all | Optional claude-mem digest export and optional local history sync |

The Claude Code [hooks reference](https://code.claude.com/docs/en/hooks) confirms the two behaviors this relies on: SessionStart stdout is added to Claude's context, and exit code 2 from a PreToolUse hook blocks the tool call. The result is that the window in which two machines can collide shrinks from a whole session to a single write.

## What loads at startup, and what stays on demand

Syncing everything would be pointless if every session had to read everything. Since protocol 3.0 (current: 3.1), startup reads only a small resident tier: `queen/agent-rules.md`, `shared/resident.md` and the agent's own `resident.md`. History, projects, and workflows are searched when a task needs them.

On the author's own nest (10 machines, 30+ agent instances, measured 2026-09 with `o200k_base`), a 2.x-style full startup was about 69,600 tokens; the 3.x resident startup is about 640 tokens, and a git task that also reads an index and one topic file is about 3,600. You can measure your own with `python3 scripts/maintenance/measure-context.py`.

## What about the auto memory already on this machine?

nestwork does not mirror `~/.claude/projects/*/memory/` automatically. Carrying it over is a deliberate, reviewed step described in [AGENTS.md §13](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md): distill what is still true, send the entries that must apply without lookup to `resident.md`, and keep restore-only notes in a cold `carryover/claude-code.md` that is never loaded at startup. If you would rather have a live mirror, pointing `autoMemoryDirectory` into your agent folder is possible as a local choice, but every write then becomes a commit and the review step disappears. The full method is in [rescuing tool-native memory](../rescue-tool-native-memory/).

## FAQ

### Does Claude Code sync memory between computers on its own?

Not auto memory. The official docs say auto memory files are not shared across machines or cloud environments. A project `CLAUDE.md` you commit to a repository is shared through that repository, but user-level and local files stay on the machine.

### Can I just put ~/.claude in Dropbox or a git repo?

You can, but it copies sessions, caches, and settings too, and auto memory folders are named after absolute paths, so they may not match on another machine. A dedicated memory repository with per-agent directories avoids both problems and keeps a readable history.

### Will two machines overwrite each other's memory?

Not for ordinary memory writes. Each instance writes only to `agents/<host>/<agent-id>/`, and the PreToolUse hook pulls before every write. If a pull hits a conflict, the write is blocked and you merge by hand.

### What if the push fails because I'm offline?

The PostToolUse hook keeps the local commit and prints a warning, and the next hook run (Stop, or a later write) tries again. A SessionStart pull that fails never blocks the session; you simply work from the local copy until the network is back.

### Does this replace CLAUDE.md?

No. Project `CLAUDE.md` files keep doing their job. nestwork only adds a marked block to your user-level `~/.claude/CLAUDE.md` that tells Claude where the shared memory is and what to read.

## Related

- [Share memory between Claude Code and Codex](../share-memory-claude-code-codex/)
- [Rescue tool-native memory before you lose it](../rescue-tool-native-memory/)
- [AGENTS.md vs CLAUDE.md vs memory](../agents-md-vs-claude-md-vs-memory/)
- [Git-native agent memory](../git-native-agent-memory/)
- [nestwork getting started FAQ](../nestwork-getting-started-faq/)

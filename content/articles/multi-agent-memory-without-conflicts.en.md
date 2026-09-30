---
title: Multi-Agent Shared Memory Without Write Conflicts
description: Several AI agents can share one memory if each writes only its own directory, every write syncs atomically, and fixed ownership rules settle conflicts.
keywords: multi-agent shared memory, multiple AI agents same memory, shared memory for AI agents, agent memory conflicts, git memory sync, nestwork
date: 2026-09-27
---

How do multiple AI agents share the same memory without overwriting each other? Give every agent its own directory that only it writes to, wrap each memory write in pull, write, commit and push, and decide in advance who wins when a pull conflicts. nestwork does exactly this on top of a git repository, and the result is that agents on different machines and from different vendors read one memory while their writes almost never collide.

The rest of this article walks through the four pieces: write isolation, the per-write hook, the conflict rules and the priority chain.

## Why shared memory is hard for agents

Sharing memory is easy when only one agent writes. It gets hard when several do. The nestwork author ran into this before building anything: an agent on one machine wrote down that a project's deploy script had a nasty gotcha, and the next day an agent on another machine stepped on the same problem ([blog post](https://github.com/songth1ef/nestwork/blob/main/docs/blog/16-agents-one-brain.md)). Once memory is shared to prevent that, three new questions appear:

- **Concurrency.** Two machines write memory at nearly the same time. Which write survives?
- **Authority.** One agent's note contradicts another's. Which one should an agent follow?
- **Scope.** A throwaway debugging note from one agent. Should every other agent see it?

None of these is about where memory is stored. They are coordination rules, which is why nestwork treats memory as a protocol rather than a database.

## 1. Write isolation: one directory per host and agent

Every agent instance owns exactly one directory:

```text
agents/<host>/<agent-id>/
agents/workstation/claude-a7k2/
agents/macbook/codex/
```

The host is the lowercased short hostname; the agent id is `<tool>-<4-char suffix>` for tools that run several instances, or just `<tool>`. The installer saves them in `~/.nestwork_host` and `~/.nestwork_id_<tool>`, so installing Codex never changes Claude Code's identity on the same machine.

The write rules in [AGENTS.md §2](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md) follow from that:

| Path | Who writes | Can agents collide here? |
|---|---|---|
| `agents/<host>/<agent-id>/` | only that agent | no, for ordinary memory writes |
| `agents/<other-host>/...` | never this agent | no |
| `queen/` | you, by hand | no; agents never write it |
| `shared/` | only during an explicit distillation | no, during normal work |
| `projects/`, `workflow/` | agents or you | possible; the pre-write pull makes it rare |

A git conflict needs two writers on the same lines. With this layout, two agents usually aren't even in the same file.

## 2. Atomic per-write sync

Isolation removes most conflicts, but two machines still push to the same branch. If an agent only synced at the end of a long session, the window for a rejected push would be the whole session. On Claude Code and Kimi Code, nestwork closes that window with hooks around every Write or Edit inside the agent's own directory. The logic lives in [`scripts/hooks/nestwork.sh`](https://github.com/songth1ef/nestwork/blob/main/scripts/hooks/nestwork.sh):

```text
PreToolUse   path under agents/<host>/<agent-id>/ ?
             git pull --rebase --autostash
             on conflict (or a leftover autostash) -> exit 2, the write is blocked
(write)      the agent edits its memory file
PostToolUse  git add + commit, scoped to its own directory
             git push; if rejected: back off (~0.5s, ~1s, ~2s plus jitter),
             undo the local commit, pull --rebase, commit again, retry
             after three failed pushes the commit stays local for the next hook
Stop         the same commit + push once per turn as a safety net
```

A few details matter:

- The commit uses an explicit pathspec, `memory: update <host>/<agent-id>`, so it never sweeps up unrelated staged files.
- The autostash check exists because git can park uncommitted changes in the stash and still exit 0; a later write would then silently overwrite them. The hook counts stash entries and treats a leftover as a conflict.
- The post hook never blocks the agent; it prints a warning and leaves the commit for the next attempt.

The effect is that the race window shrinks from a session to a single write. Codex, Gemini CLI, OpenClaw and Hermes have no per-write hooks; they follow the bootstrap and commit their own directory at session end, which widens the window but, because each writes only its own directory, rarely matters.

## 3. Deterministic conflict rules

When a pull does hit a conflict, nobody should have to guess. [AGENTS.md §5](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md) settles it by ownership:

| Conflicting path | Take | Reason |
|---|---|---|
| `queen/`, `shared/` | remote | managed upstream by you or by distillation |
| `agents/<host>/<agent-id>/` (your own) | local | this instance owns its directory |
| `agents/<other-host>/...` | remote | another machine owns it |

The owner decides, and every agent applies the same rule, so two machines resolving the same conflict reach the same result.

## 4. The priority chain for contradictions

Git conflicts are about bytes. Contradicting instructions are about meaning, and they need a separate rule. nestwork uses a fixed authority order:

```text
queen/agent-rules.md > queen/strategy.md > shared/memory.md > agents/*/*/memory.md > projects/*.md > workflow/*.md
```

When two sources disagree, the agent follows the higher one and does not merge them. A blended "compromise" instruction is often worse than either original. This order is authority, not loading order: since protocol 3.0 an agent loads only small resident files at startup and looks up the rest on demand, and a resident summary inherits the priority of the source it summarizes.

## How agents share without writing to each other

If nobody writes anywhere but their own directory, how does knowledge spread?

- **Reading is open.** Every agent can read every directory after a pull. An agent on your desktop can read what the laptop agent recorded this morning.
- **Distillation merges.** Stable facts from all agents are merged into `shared/` only when you trigger it, with a sub-agent review and your confirmation (see [memory distillation](../memory-distillation/)).
- **The mailbox handles messages.** To address another agent, an agent writes a file into its own `outbox/` tagged `to:`; the recipient scans everyone's outboxes. There is no shared inbox, so the single-writer rule still holds (see [agent mailbox over git](../agent-mailbox-git/)).

The author runs this across 10 machines and more than 30 agent instances on Windows, macOS, Linux and Android.

## FAQ

### What if two agents edit the same project file?

`projects/` and `workflow/` are the places where two agents can touch one file. The pre-write `pull --rebase` shrinks the window to one write; if a real conflict happens, the write is blocked and you merge by hand. Keeping project status short and per-project reduces the odds further.

### Do two Claude Code sessions on one machine get separate directories?

No. The identity is per tool per machine: the installer generates an id such as `claude-a7k2` once and reuses it from `~/.nestwork_id_claude`. Two sessions on the same machine write the same directory in the same local clone, so git sees no conflict between them; they only need to avoid rewriting the same memory file at the same moment. Different tools and different machines always get separate directories.

### Why not use a lock or a database transaction?

That needs a running service, which nestwork deliberately avoids. Ownership plus rebase-and-retry gets close enough for memory, where writes are small and infrequent, without any server.

### What does the hook do when I'm offline?

The pre-write pull fails, and the hook treats that like a conflict: on Claude Code the memory write is blocked until the remote is reachable. Reading memory still works from the local clone.

## Related

- [Git-native agent memory: why git is enough](../git-native-agent-memory/)
- [Memory distillation: merging many agents' memory](../memory-distillation/)
- [An agent mailbox over git](../agent-mailbox-git/)
- [Sharing memory between Claude Code and Codex](../share-memory-claude-code-codex/)
- [16 agents, one brain](../16-agents-one-brain/)

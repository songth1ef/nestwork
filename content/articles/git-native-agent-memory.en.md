---
title: Git-Native Memory for AI Agents — Why Git Is Enough
description: You can give AI coding agents persistent memory without a server by storing it as markdown in a private git repo. What git covers, and what it doesn't.
keywords: git-native memory, agent memory without a server, AI agent memory git, persistent memory for AI agents, nestwork, markdown memory
date: 2026-09-27
---

Can an AI coding agent keep long-term memory without a memory server or database? Yes: store the memory as plain markdown files in a private git repository, have each agent `git pull` before it works and commit and push after it writes. Git already provides storage, history, conflict handling, offline copies and ownership. What it does not provide is semantic search, and it assumes you are comfortable with git.

This article explains why that is enough for most coding-agent setups, where it falls short, and how nestwork turns the idea into a protocol.

## The question behind "agent memory"

Most memory products answer "where do I store memories and how do I fetch them back?" with a vector store, a graph or a hosted service. For one agent on one machine that is a reasonable framing.

The problem changes once you use several agents on several machines. Claude Code's own documentation says its auto memory "is machine-local" and that "files are not shared across machines or cloud environments" ([Claude Code docs](https://code.claude.com/docs/en/memory)). Codex and Kimi Code keep their memory in local home directories too (see [AGENTS.md §13](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md)). So what you learned with one tool on your laptop is invisible to a different tool on your desktop.

What you actually need is a store that is shared, versioned, works across tools and belongs to you. That describes a git repository.

## What git already solves

Memory for a coding agent is mostly text: rules, preferences, decisions, project status, lessons. Git was built to share text across people, machines and versions. Mapped onto the memory problem:

| Need | What git gives you |
|---|---|
| Storage | Plain files in a repo you control; any host, or none |
| History | Every change is a commit; `git log` and `git blame` show who changed what and when |
| Undo | `git revert` a bad memory write instead of hoping a service supports rollback |
| Sync across machines | `git pull` / `git push` over a remote you already use |
| Concurrent writers | Rebase and merge, plus clear ownership rules (below) |
| Offline | A full local clone; agents read memory from disk |
| Ownership | The repo is yours; switching hosts means changing a remote |
| Tool neutrality | Any agent that reads markdown can read it |

The author of nestwork describes the moment it clicked in the project blog: memory is "at its core, a pile of text. And the best home for text is git" ([blog post](https://github.com/songth1ef/nestwork/blob/main/docs/blog/16-agents-one-brain.md)).

## How nestwork turns a repo into memory

nestwork is a protocol, not a service. You create a private repository from the [template](https://github.com/songth1ef/nestwork/generate), clone it to each machine and run a per-tool installer. The installer writes a bootstrap into the tool's startup file, so the agent knows what to read and where it may write.

The repository is layered:

| Layer | Path | Holds |
|---|---|---|
| Rules | `queen/agent-rules.md` | Behaviour rules you write; agents only read |
| Strategy | `queen/strategy.md` | Current direction |
| Shared memory | `shared/` | Facts distilled from all agents |
| Private memory | `agents/<host>/<agent-id>/` | One agent instance's own notes |
| Projects | `projects/<name>.md` | Project snapshots |
| Workflow | `workflow/<topic>.md` | Portable methods |

Each session follows the same lifecycle:

```text
session start   git pull --rebase, read the small resident files
during work     look up history or project files only when the task needs them
memory write    pull --rebase -> write -> commit -> push (hooked tools)
session end     commit + push own directory (tools without per-write hooks)
```

On Claude Code and Kimi Code the per-write sync runs from hooks in [`scripts/hooks/nestwork.sh`](https://github.com/songth1ef/nestwork/blob/main/scripts/hooks/nestwork.sh). Codex, Gemini CLI, OpenClaw and Hermes follow the bootstrap and commit their own directory at the end of the session. Claude Code and Codex are the author's daily drivers; the other installers exist but are less battle-tested.

Install for Claude Code is one command per machine:

```bash
git clone git@github.com:<you>/nestwork.git ~/nestwork
bash ~/nestwork/scripts/install/claude.sh
```

## Conflicts: ownership beats clever merging

Git can merge text, but it cannot decide whose memory is right. nestwork answers that with ownership rather than algorithms. Every agent writes only to `agents/<host>/<agent-id>/`, so two agents normally never touch the same file. When a pull does conflict, [AGENTS.md §5](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md) makes the resolution deterministic: take local for your own directory, take remote for `queen/`, `shared/` and other hosts' directories.

For instructions that disagree, a fixed priority chain applies: rules, then strategy, then shared memory, then private memory, then projects, then workflow. The higher source wins and the two are never blended. The details are in [multi-agent memory without conflicts](../multi-agent-memory-without-conflicts/).

## The trade-offs, stated plainly

Git is enough for this job, not for every job.

- **No semantic search.** nestwork finds memory by reading indexes and searching headings or keywords, not by embedding similarity. If you need "find anything vaguely like this across 100,000 notes", a vector store does that better.
- **You need to know git.** When a rebase conflicts, someone has to read `git status` and resolve it. The README is blunt: if you don't know git, nestwork isn't a good fit.
- **Asynchronous, not real time.** Another machine sees a write after its next pull. There is no live notification.
- **Offline has an edge.** Reading works fully offline and hookless tools commit locally and push later. With Claude Code's per-write hooks, though, the pre-write `pull --rebase` must succeed; the hook treats a failed pull like a conflict and blocks the memory write until the remote is reachable again.
- **Plaintext by default.** A private repo relies on your git host's security. For confidential memory there is an optional git-crypt mode; API keys and secrets should never go into the repo at all (see [encrypting agent memory](../encrypt-agent-memory-git-crypt/)).
- **History grows.** Everything you keep is retained, so loading has to be selective. That is what the resident tier and topic memory are for (see [loading memory on demand](../topic-memory-on-demand-loading/)).

## Does it hold up in practice?

The author runs one nest across 10 machines and more than 30 agent instances on Windows, macOS, Linux and Android. That nest holds 180 memory files, roughly 369,000 tokens in total, yet a session starts by reading about 640 tokens of resident context. Git stores all of it; the protocol decides what gets read.

## FAQ

### Do I need GitHub?

No. Any git remote works, including a self-hosted server, and the README shows how to keep a nest purely local by never adding a remote. GitHub is only needed for the "Use this template" button and the optional sync workflow.

### Is nestwork a vector database?

No. It stores readable markdown in git. Agents navigate by indexes, headings and keywords. You can still run a separate retrieval tool alongside it if you need semantic search.

### What happens when two machines write at the same moment?

Each agent writes only its own directory, so they rarely touch the same file. On hooked tools every write is wrapped in `pull --rebase` before and commit plus push with retries after, which shrinks the race window to a single write. A real conflict blocks the write and asks for a manual merge.

### Can I switch from Claude Code to Codex without losing memory?

Yes. The memory lives in your repo, not in either tool. Run the Codex installer on the same clone and the next Codex session reads the same files.

## Related

- [What AI agent memory is and why it breaks across machines](../ai-agent-memory/)
- [Multi-agent memory without conflicts](../multi-agent-memory-without-conflicts/)
- [Loading agent memory on demand](../topic-memory-on-demand-loading/)
- [Agent memory tools compared](../agent-memory-tools-compared/)
- [Getting started with nestwork: FAQ](../nestwork-getting-started-faq/)

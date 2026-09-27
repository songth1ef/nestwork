---
title: Agent Memory Tools Compared — Mem0, Letta, Zep and More
description: Mem0, Letta, Zep, Supermemory, claude-mem, built-in tool memory and nestwork compared on architecture, deployment, data ownership and best fit.
keywords: agent memory tools, mem0 alternative, Letta vs mem0, Zep, Supermemory, claude-mem, nestwork, AI agent memory comparison
date: 2026-09-27
---

Agent memory tools split into three groups: **memory services** you call from your own application (Mem0, Zep, Supermemory), **agent runtimes** that manage memory for agents running inside them (Letta), and **coding-agent add-ons** that give tools like Claude Code or Codex memory across sessions (claude-mem, the tools' built-in memory, nestwork). If you are building a product that must remember thousands of end users, you want the first group; if you want your own coding agents to share rules and project state across machines and tools, look at the third. Letta sits in between and, since 2026, also keeps memory in git.

## The short version

| Tool | Architecture | Deployment | Where memory lives | Best fit |
|---|---|---|---|---|
| [Mem0](https://github.com/mem0ai/mem0) | LLM extracts memories; vector store plus optional graph | Library, self-hosted server, or managed cloud | Your database or Mem0's cloud | Adding per-user memory to an AI application |
| [Letta](https://github.com/letta-ai/letta) | Runtime for stateful agents; memory blocks, now a git-backed memory filesystem | Letta Code locally, self-hosted server, or Letta Cloud | The agent's own git repo, hosted by Letta for cloud agents | Agents that live inside Letta and manage their own memory |
| [Zep](https://www.getzep.com/) | Temporal knowledge graph ([Graphiti](https://github.com/getzep/graphiti) is the open-source engine) | Zep Cloud, bring-your-own-key, or bring-your-own-cloud | Zep's cloud or your VPC; Graphiti on your graph DB | Enterprise context that combines conversations and business data |
| [Supermemory](https://github.com/supermemoryai/supermemory) | Fact extraction with temporal updates, contradictions and forgetting; hybrid search | Hosted API or a self-hosted binary | Supermemory's cloud or your machine | Memory API and plugins for apps and assistants |
| [claude-mem](https://github.com/thedotmack/claude-mem) | Hooks capture tool usage into SQLite plus a Chroma vector index | Local worker process | Local database on each machine | Automatic session capture for a coding agent on one machine |
| Built-in memory (Claude Code, Codex) | The agent writes markdown notes for itself | Built in | `~/.claude/projects/…/memory/`, `~/.codex/memories/` | One tool, one machine, zero setup |
| [nestwork](https://github.com/songth1ef/nestwork) | Protocol: markdown in a private git repo, loaded through each tool's instruction file | Template repo plus per-tool installers | Your own git repo | Several coding agents sharing rules and state across machines and tools |

Each row is a snapshot as of September 2026; check each project's own documentation before relying on details.

## Tool by tool

### Mem0

Mem0 describes itself as "The Memory Layer for AI Agents." It is Apache-2.0 licensed and comes in three forms: a Python/JavaScript library, a self-hosted server with Docker, and a managed platform. You send conversations; an LLM extracts memories; Mem0 stores them in a vector database, with graph memory as an option, and retrieves relevant ones on request. It integrates with frameworks such as LangGraph and CrewAI.

Mem0's [paper](https://arxiv.org/abs/2504.19413) reports that on LoCoMo it used about 1,764 tokens per query against 26,031 for a full-context baseline, with 91% lower p95 latency. It is a strong choice when you need per-user memory inside a product. People searching for a **mem0 alternative** usually want one of two things: a different service with similar APIs (Zep, Supermemory), or no service at all for a smaller, personal use case.

### Letta

Letta, formerly MemGPT, is "a platform for stateful agents," Apache-2.0 licensed. In its classic API, agents carry labelled **memory blocks** (for example `human` and `persona`) that they edit with tools. Active development has moved to [Letta Code](https://github.com/letta-ai/letta-code), and its newer memory system, [MemFS](https://docs.letta.com/concepts/memfs), keeps each agent's memory in a git repository: files under `system/` load into the prompt every turn, the rest are read when needed. For cloud agents the repo is hosted by Letta; Letta Code [clones it locally](https://www.letta.com/blog/context-repositories/), and subagents write concurrently through git worktrees.

**Letta vs Mem0** is mostly a question of where the agent runs. Mem0 is a memory component you bolt onto your own agent loop. Letta is the agent loop, with memory management built into how the agent thinks. If you are happy to work inside Letta, its git-backed memory is a mature option and overlaps with nestwork's ideas; the difference is that nestwork is aimed at other vendors' tools rather than Letta's own agents.

### Zep

Zep now calls itself "the unified context layer for enterprise data." Its core is a temporal knowledge graph in which each fact has "a validity window: when it became true, and when (if ever) it was superseded." The managed service offers Zep Cloud, bring-your-own-key encryption and deployment in your own VPC. The open-source engine, Graphiti (Apache-2.0), runs on Neo4j, FalkorDB or Amazon Neptune if you want to build the surrounding system yourself. Choose it when facts change over time and you need to query their history across business data.

### Supermemory

Supermemory is MIT-licensed and describes itself as a "memory and context engine." It extracts facts from conversations, handles temporal changes and contradictions, and offers automatic forgetting, with hybrid search over documents and memories. You can use the hosted API or run "one binary. Zero config." locally, and it ships an MCP server and plugins for Claude Code, Cursor, Windsurf and VS Code. Its README claims first place on LongMemEval, LoCoMo and ConvoMem; as with every vendor benchmark, those are [self-reported numbers under the vendor's own setup](../agent-memory-benchmarks/).

### claude-mem

claude-mem uses five lifecycle hooks to capture what an agent does, generates summaries, and makes them searchable in later sessions. Storage is SQLite plus a Chroma vector index, served by a local worker. Its README lists Claude Code, OpenClaw, OpenCode and others. Because the database is local, memory stays on the machine running the worker. nestwork can run alongside it: when the claude-mem worker is reachable on `localhost:37777`, nestwork's Claude Code SessionEnd hook exports that day's observations to `agents/<host>/<agent-id>/claude-mem-digest.md`, which then travels through git.

### Built-in tool memory

Claude Code's auto memory and Codex's memories need no setup and are written automatically. Both are machine-local: Claude Code's docs say auto memory files "are not shared across machines or cloud environments," and Codex stores memories under `~/.codex/memories/`. Codex's own guidance is to keep required rules in `AGENTS.md` and "treat memories as a helpful recall layer." For one person on one machine with one tool, this is often enough.

### nestwork

nestwork is a protocol, not a service. You create a private repository from the template, run an installer per tool, and each tool's instruction file gets a bootstrap: pull the repo, read a small resident tier, fetch everything else on demand. Each agent writes only to `agents/<host>/<agent-id>/`; shared memory changes only through a reviewed distillation; a fixed priority chain decides conflicts. On the author's nest (10 machines, 30+ agent instances), resident startup is about 640 tokens.

Claude Code and Codex are the author's daily drivers; Gemini CLI, Kimi Code, Hermes and OpenClaw installers exist but are less battle-tested.

## When nestwork is the wrong choice

Be clear about what nestwork does not do:

- **End-user chat applications.** It has no per-user API, no multi-tenant storage and no SDK. Use Mem0, Zep or Supermemory.
- **Semantic search over large conversation archives.** Retrieval is the agent searching headings and keywords, optionally routed by a topic index. There is no embedding index.
- **Automatic capture of everything.** nestwork stores what agents or you decide is worth keeping. If you want every session recorded, use claude-mem or built-in memory, and distill from them.
- **Teams that need access control.** Permissions are whatever your git host provides; there is no ACL layer.
- **People who don't use git.** Git is the transport. The README is blunt: "If you don't know git, nestwork isn't a good fit."
- **Secrets.** API keys do not belong in it, encrypted or not.

## How to choose

1. Building a product with many end users? Start with a memory service: Mem0, Zep or Supermemory.
2. Want agents whose whole runtime is memory-aware? Look at Letta.
3. One coding tool, one machine? Built-in memory, optionally with claude-mem.
4. Several coding tools or machines, and you want rules and project state as reviewable text you own? A file protocol such as nestwork.

These are not exclusive. A common setup is built-in memory for tool-local notes, periodically distilled into a git-based nest that every tool reads.

## FAQ

### What is the best Mem0 alternative?

It depends on why you are leaving. For another hosted memory API, compare Zep (temporal graph) and Supermemory (fact extraction, self-host option). For personal coding-agent memory without a service, a file-based approach such as nestwork or Letta's git-backed memory is lighter.

### Letta vs Mem0 — which should I use?

Use Mem0 if you already have an agent or application and want to add memory to it. Use Letta if you want the platform to run the agent and manage its memory for you. They solve adjacent problems rather than competing head-on.

### Can I use nestwork together with Mem0 or claude-mem?

Yes. nestwork only concerns the files your coding agents read and write. It has a built-in export for claude-mem digests, and nothing stops an application from using Mem0 while its developers use nestwork for their own agents.

### Where is my data in each tool?

Managed services keep it in the vendor's cloud unless you self-host; claude-mem and built-in memory keep it on each local machine; Letta keeps it in the agent's git repo; nestwork keeps it in a git repository you own.

## Related

- [AI agent memory: four types and their trade-offs](../ai-agent-memory/)
- [Agent memory benchmarks: LoCoMo, LongMemEval and BEAM](../agent-memory-benchmarks/)
- [Rescue your tool's native memory](../rescue-tool-native-memory/)
- [Multi-agent memory without conflicts](../multi-agent-memory-without-conflicts/)
- [nestwork getting-started FAQ](../nestwork-getting-started-faq/)

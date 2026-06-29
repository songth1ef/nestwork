# Agent memory landscape: where nestwork fits

## Short answer

"Cross-device, cross-vendor memory for AI coding agents" is an active space in
2025–2026. Projects cluster into three architecture routes. nestwork sits in the
**git-native plaintext** route, alongside projects like ai-memory, DiffMem, and
Wuphf. The hosted and runtime routes (Mem0, Letta/MemGPT) solve a related but
different problem and are best treated as adjacent categories rather than direct
substitutes.

This doc is a neutral map of the landscape so you can pick the right tool. For a
focused one-to-one comparison, see [nestwork vs claude-mem](claude-mem.md).

## Three architecture routes

| Route | What it is | Storage | Examples |
|---|---|---|---|
| **Git-native plaintext** | Memory is Markdown in a git repo as the source of truth; retrieval is local (grep / FTS5 / BM25) | Markdown + git | nestwork, [ai-memory](https://github.com/akitaonrails/ai-memory), [DiffMem](https://github.com/Growth-Kinetics/DiffMem), Wuphf |
| **Plugin / local service** | A tool-side plugin captures sessions into a local DB + optional vector index | SQLite + vector store | [claude-mem](https://github.com/thedotmack/claude-mem) |
| **Hosted / runtime** | A managed retrieval service or an agent runtime owns memory behind an API/SDK | pgvector / graph DB / managed | Mem0, Letta / MemGPT |

## Git-native plaintext projects (closest to nestwork)

These share nestwork's core idea: keep memory as human-readable text in git,
auditable with standard tooling, no memory server required.

- **[ai-memory](https://github.com/akitaonrails/ai-memory)** — Markdown `wiki/`
  as the git-versioned source of truth plus a local SQLite (FTS5) index. Targets
  cross-vendor handoff inside a working directory (Claude Code, Codex, Cursor,
  Gemini CLI, OpenClaw, and others) via MCP and session hooks that inject a
  "where you left off" block.
- **[DiffMem](https://github.com/Growth-Kinetics/DiffMem)** — Markdown files for
  human-readable storage, git for tracking temporal evolution. Retrieval is done
  by a git-native agent using `grep` / `git log` / `diff` / `blame` rather than a
  vector database. Offers an optional GitHub backend for two-way mirroring across
  machines.
- **Wuphf** (Nex.ai) — a git Markdown wiki with a local BM25 + SQLite index and
  no vector or graph database. Differentiation is framed around local, auditable
  text files and standard git tooling.

What still differs across this group is **cross-machine sync and concurrent
writes**: some projects are single-machine first, and some libraries do not yet
ship automatic git synchronization or multi-writer concurrency. nestwork's design
emphasis is git-remote sync (pull/commit/push hooks), template inheritance ("use
this template" to connect a new instance), per-host/per-agent private
directories, and a per-agent write model that avoids write contention.

## Plugin / local service

- **[claude-mem](https://github.com/thedotmack/claude-mem)** — a plugin that
  stores sessions in a local SQLite (FTS5) database plus a Chroma vector index,
  served by a local worker process. It is explicitly cross-vendor (Claude Code,
  OpenClaw, Codex, Gemini, Hermes, Copilot, OpenCode). It is not git-native — git
  is only a distribution channel. nestwork can integrate it as an optional
  session digest. See [nestwork vs claude-mem](claude-mem.md).

## Hosted / runtime (adjacent categories)

- **Mem0** — a memory layer offered as both open source and a managed service,
  integrated in a few lines of code and reached across frameworks/SDKs (e.g.
  CrewAI, Flowise, Langflow). Cross-vendor reach comes through framework
  integration rather than sharing files across CLI agent tools. It is a hosted
  retrieval service, not a git-native cross-machine protocol.
- **Letta / MemGPT** — a runtime platform where agents run inside Letta, with
  git-backed memory, skills, and subagents across model providers. It offers the
  most integrated experience and, correspondingly, the tightest coupling to the
  runtime.

## A note on retrieval vs write strategy

Recent research on long-term agent memory reports that, on the LoCoMo benchmark,
the **retrieval method is the dominant factor** in answer quality, with a much
larger spread across retrieval methods than across write strategies; raw chunked
storage (no extra LLM calls) can match or outperform expensive fact-extraction or
summarization pipelines. This is one benchmark and an early result, but it is
relevant context for plaintext-first designs: simple storage with good retrieval
is a defensible choice, and retrieval quality is where investment tends to pay
off. (See arXiv:2603.02473.)

## When nestwork is a better fit

Use nestwork if:

- You use more than one agent tool and want them to share the same memory.
- You want memory as Markdown in git history, auditable with standard tooling.
- You want cross-machine sync over a git remote, with no memory server.
- You want private, per-host and per-agent memory directories.
- You want to connect a new instance by inheriting a template.

## When an alternative is a better fit

- **ai-memory / DiffMem / Wuphf** — if you want a git-native plaintext system and
  one of their specific workflows (in-directory handoff, agent-driven git
  retrieval, or a local BM25 wiki) matches how you work.
- **claude-mem** — if you want a plugin that auto-captures sessions into a local
  DB with vector search.
- **Mem0** — if you want a managed memory service reached through framework SDKs.
- **Letta / MemGPT** — if you want agents to run inside a memory-aware runtime.

## Related docs

- [nestwork vs claude-mem](claude-mem.md)
- [AI agent memory](../ai-agent-memory.md)
- [Git-native memory protocol](../git-native-memory-protocol.md)
- [Shared context for AI coding agents](../shared-context-for-ai-coding-agents.md)

> Landscape note: this space moves quickly and project details change. Treat the
> specifics above as a snapshot and verify against each project's own
> documentation before relying on them.

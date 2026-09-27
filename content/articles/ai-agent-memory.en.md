---
title: AI Agent Memory — Four Types and Their Trade-offs
description: AI agent memory is context an agent keeps beyond one session. Compare context windows, built-in memory, vector services and files for coding agents.
keywords: AI agent memory, long-term memory for AI agents, agent memory types, coding agent memory, persistent memory, AGENTS.md
date: 2026-09-27
---

AI agent memory is any context an agent can rely on beyond the current conversation: the rules it must follow, facts about you and your projects, and decisions made earlier. Long-term memory for AI agents comes in four broad shapes — the context window itself, memory built into a tool, a retrieval service backed by vectors or graphs, and plain files loaded by a protocol. For coding agents the deciding questions are less about retrieval cleverness and more about where the memory lives, which tools can read it, and whether a human can review it.

## Why agents need memory at all

A language model has no state between calls. Claude Code's documentation puts it plainly: "Each Claude Code session begins with a fresh context window" ([Claude Code memory docs](https://code.claude.com/docs/en/memory)). Everything the agent "knows" about you at the start of a session was put there by some mechanism — a file it read, a note it wrote last time, or a search against a store.

Without such a mechanism you re-explain the same things every session: your coding conventions, the directory nobody should touch, why an approach was abandoned last week. Memory is whatever removes that repetition. The four types below differ in who writes it, where it is stored, and how it gets back into the context window.

## Type 1: in-session context

The simplest memory is the conversation itself. Everything said in the current session sits in the context window until the session ends or the window is compacted.

- **Strengths**: nothing to install; perfect recall within the window.
- **Weaknesses**: gone when the session ends; long sessions get expensive and attention degrades as the window fills.

It is working memory, not long-term memory. Every other type exists to decide what gets copied into this window next time.

## Type 2: memory built into the tool

Most coding agents now keep notes for themselves. Claude Code's auto memory writes notes about your preferences and corrections into `~/.claude/projects/<project>/memory/`, with a `MEMORY.md` index whose first 200 lines or 25 KB load into every session. Codex stores its memories under `~/.codex/memories/` and generates them from earlier chats in the background ([Codex memories docs](https://learn.chatgpt.com/docs/customization/memories?surface=app)).

- **Strengths**: zero setup, written automatically, tuned for that one tool.
- **Weaknesses**: tied to one tool and one machine. Claude Code's docs state: "Auto memory is machine-local … Files are not shared across machines or cloud environments." Codex's docs advise: "Treat memories as a helpful recall layer, not as the only source for rules that must always apply."

Built-in memory is a good default for a single developer on a single machine with a single tool. It stops being enough the moment any of those three becomes plural.

## Type 3: retrieval services (vector and graph memory)

Services such as [Mem0](https://github.com/mem0ai/mem0), [Zep](https://www.getzep.com/) and [Supermemory](https://github.com/supermemoryai/supermemory) sit behind an API. You send them conversations; an LLM extracts facts; the facts are stored in a vector index, a graph, or both; and at query time the service returns the relevant ones. Zep's open-source engine, [Graphiti](https://github.com/getzep/graphiti), gives each fact "a validity window: when it became true, and when (if ever) it was superseded."

- **Strengths**: semantic search over large volumes of conversation; per-user memory for applications with many end users; handling of updates and contradictions built in.
- **Weaknesses**: a service to run or rent, extra LLM calls on write, and memory stored as database rows you read through the vendor's tools rather than as text you edit.

This is the right shape when you are building a product that has to remember thousands of users. It is a heavier fit for one developer who wants their own rules to follow them between editors.

## Type 4: files and protocols

The fourth type is plain text the agent reads at startup: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and systems built on top of them. [AGENTS.md](https://agents.md/) is an open format used by over 60,000 open-source projects and read by Codex, Cursor, Jules and many other tools; Claude Code reads `CLAUDE.md` and, in current versions, `AGENTS.md` when no `CLAUDE.md` exists.

- **Strengths**: readable, diffable and reviewable; reading needs no network or service; any tool that reads markdown can use it; git gives you history for free.
- **Weaknesses**: no semantic search out of the box; someone has to decide what gets written; files that grow unchecked cost tokens on every session.

| Type | Written by | Lives in | Crosses tools | Crosses machines | Human-reviewable |
|---|---|---|---|---|---|
| In-session context | Conversation | Context window | No | No | Only live |
| Built-in tool memory | The agent | Tool's local directory | No | No | Yes, if you look |
| Retrieval service | LLM extraction | Vector/graph database | Via API/SDK | Via the service | Through vendor tools |
| Files and protocols | You and the agent | Your files / git | Yes | Via git or sync | Yes, as diffs |

## What coding agents need that chatbots don't

Most memory research targets chat assistants that must remember people. Coding agents have a different set of requirements:

1. **Cross-tool.** Many developers switch between Claude Code, Codex, Gemini CLI and others. A rule learned in one tool should hold in the next.
2. **Cross-machine.** Laptop, desktop, cloud dev box. Built-in memory in both Claude Code and Codex stays on the machine that wrote it.
3. **Rule priority.** "Never push to main" must outrank an old note that says "pushed the hotfix to main." Retrieval by similarity does not know which of two conflicting facts is authoritative.
4. **Reviewable.** You should be able to see what the agent believes about you, correct it, and see who changed what. Plain text in version control does this naturally.
5. **Cheap startup.** Whatever loads at session start is paid for on every session, so the resident part has to stay small and the rest must be fetched on demand.

## How nestwork approaches it

[nestwork](https://github.com/songth1ef/nestwork) is a type-4 system: a git-native memory protocol for AI coding agents. Memory is markdown in a private git repository you create from a template; each tool gets a small bootstrap injected into its instruction file (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md` and so on); agents pull before work and push after.

- **Priority is explicit**: `queen/agent-rules.md > queen/strategy.md > shared/memory.md > agents/*/*/memory.md > projects/*.md > workflow/*.md`. On conflict the higher source wins; the two are not merged.
- **Each agent writes only its own directory** (`agents/<host>/<agent-id>/`), so parallel agents on different machines do not overwrite each other. Shared memory changes only through a reviewed distillation step.
- **Startup loads only a resident tier.** On the author's nest (10 machines, 30+ agent instances), a 2.x-style full startup read 37 files, about 69,600 tokens; the protocol 3.x resident startup is about 640 tokens, and a typical git task (resident + index + one topic file) about 3,600. The whole nest is 180 memory files, about 369,000 tokens — too much for most context windows, which is why loading has to be selective. You can measure your own with `scripts/maintenance/measure-context.py`.

Claude Code and Codex are the author's daily drivers; installers for Gemini CLI, Kimi Code, Hermes and OpenClaw exist but are less battle-tested. nestwork is not a vector store or a chat-history archive, and it needs you to be comfortable with git.

## FAQ

### What is the difference between short-term and long-term memory for AI agents?

Short-term memory is the context window of the current session and disappears when it ends. Long-term memory is anything stored outside the session — files, a database, a tool's memory directory — and loaded back later. The engineering work is deciding what to store and what to load.

### Is a bigger context window a substitute for memory?

Not really. A bigger window lets you load more, but everything loaded costs tokens on every session and attention still degrades as the window fills. The Mem0 paper found a full-context baseline more accurate than their memory system on LoCoMo, but at about 26,000 tokens per query against under 2,000 ([arXiv:2504.19413](https://arxiv.org/abs/2504.19413)). Memory is largely about loading less, precisely.

### Should I turn off my tool's built-in memory if I use a file-based system?

No. They cover different layers. Built-in memory is convenient for tool-local notes; a file-based layer carries rules and decisions across tools and machines. nestwork treats built-in memory as a source to distill from periodically, not something to replace.

### Do I need a vector database for a coding agent?

Usually not for personal rules and project state, which are small and benefit from exact, reviewable text. A vector or graph service earns its cost when you must search large volumes of unstructured conversation, typically in an end-user product.

## Related

- [Agent memory benchmarks: LoCoMo, LongMemEval and BEAM](../agent-memory-benchmarks/)
- [Agent memory tools compared](../agent-memory-tools-compared/)
- [AGENTS.md vs CLAUDE.md vs memory](../agents-md-vs-claude-md-vs-memory/)
- [Git-native agent memory](../git-native-agent-memory/)
- [Topic memory and on-demand loading](../topic-memory-on-demand-loading/)

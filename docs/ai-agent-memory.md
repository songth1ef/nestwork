# AI agent memory

## Short answer

AI agent memory is persistent context that an AI coding agent can rely on across sessions: rules it must follow, facts about the user and projects, and past decisions. nestwork stores that memory in git so agents can share it across sessions, machines, and tools.

## What problem does it solve?

AI coding agents often forget useful context between sessions. A developer may repeat the same rules, project goals, coding preferences, and current priorities every time they use Claude Code, Codex CLI, Gemini CLI, Kimi Code, or another agent. nestwork turns that repeated context into files that every agent can load.

## How nestwork stores memory

nestwork uses a private git repository with this structure:

```text
nestwork/
├── queen/                 # human-managed rules and strategy
├── shared/                # distilled cross-agent memory
├── agents/<host>/<id>/    # private memory for one agent instance
├── projects/              # project-specific context
└── workflow/              # portable cross-project methodology
```

Each agent writes only to its own `agents/<host>/<agent-id>/` directory. Shared memory is distilled from agent memory instead of edited by every agent directly.

Memory is loaded in two tiers. At startup an agent reads only the resident tier: `queen/agent-rules.md` plus small, optional `resident.md` summaries. Everything else — strategy, memory history, projects, workflows — is on demand: the agent searches it when the current task needs it. When a memory file grows large, protocol 3.1 lets it become an index of topic files, so the agent reads only the topics that match the task. See [context loading](context-loading.md).

## When to use nestwork

Use nestwork when:

- You use more than one AI coding agent.
- You work across multiple machines.
- You want persistent memory without a hosted database.
- You want project context loaded from files such as `AGENTS.md`.
- You want version history for memory changes.

## When not to use nestwork

Do not use nestwork as a database, vector store, chat history archive, or team knowledge base. It is a lightweight memory protocol for agent context, not a replacement for product documentation or source control.

## Related docs

- [Claude Code memory](claude-code-memory.md)
- [Codex persistent memory](codex-persistent-memory.md)
- [Git-native memory protocol](git-native-memory-protocol.md)
- [Context loading and topic memory](context-loading.md)
- [FAQ](faq.md)

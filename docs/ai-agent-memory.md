# AI agent memory

## Short answer

AI agent memory is persistent context that an AI coding agent loads before it starts work. nestwork stores that memory in git so agents can share rules, project context, and past decisions across sessions, machines, and tools.

## What problem does it solve?

AI coding agents often forget useful context between sessions. A developer may repeat the same rules, project goals, coding preferences, and current priorities every time they use Claude Code, Codex CLI, Gemini CLI, Kimi Code, or another agent. nestwork turns that repeated context into files that every agent can load.

## How nestwork stores memory

nestwork uses a private git repository with this structure:

```text
nestwork/
├── queen/                 # human-managed rules and strategy
├── agents/<host>/<id>/    # private memory for one agent instance
├── shared/                # compiled cross-agent memory
└── projects/              # project-specific context
```

Each agent writes only to its own `agents/<host>/<agent-id>/` directory. Shared memory is compiled from agent memory instead of edited by every agent directly.

## When to use nestwork

Use nestwork when:

- You use more than one AI coding agent.
- You work across multiple machines.
- You want persistent memory without a hosted database.
- You want project context loaded from files such as `AGENTS.md`.
- You want version history for memory changes.

## When not to use nestwork

Do not use nestwork as a database, vector store, chat history archive, or team knowledge base. It is a lightweight memory protocol for agent startup context, not a replacement for product documentation or source control.

## Related docs

- [Claude Code memory](claude-code-memory.md)
- [Codex persistent memory](codex-persistent-memory.md)
- [Git-native memory protocol](git-native-memory-protocol.md)
- [FAQ](faq.md)

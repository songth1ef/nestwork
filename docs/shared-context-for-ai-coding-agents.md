# Shared context for AI coding agents

## Short answer

Shared context for AI coding agents is the set of rules, goals, memory, and project facts that multiple agents load before they work. nestwork stores shared context in git so Claude Code, Codex CLI, Gemini CLI, and other agents can start from the same source of truth.

## Why shared context matters

Without shared context, each AI agent session depends on whatever the user remembers to paste. This causes drift:

- different agents follow different rules
- project priorities are repeated manually
- decisions are forgotten across sessions
- multiple machines accumulate different context

nestwork solves this by making context load order explicit and versioned.

## nestwork shared context layers

```text
queen/agent-rules.md          behavior rules
queen/strategy.md             current direction
shared/memory.md              distilled memory
agents/<host>/<agent-id>/     private agent memory
projects/<name>.md            project context
workflow/<topic>.md           portable cross-project methodology
```

The important detail is ownership. Humans own `queen/`. Each agent owns only its own memory directory. Shared memory is compiled or distilled deliberately.

## When to use this pattern

Use shared context when you:

- switch between Claude Code and Codex CLI
- work from more than one machine
- need project rules to survive new sessions
- want AI agent memory in a private repository
- want git history for memory changes

## Related docs

- [AI agent memory](ai-agent-memory.md)
- [Claude Code memory](claude-code-memory.md)
- [Codex persistent memory](codex-persistent-memory.md)
- [AGENTS.md best practices](agents-md-best-practices.md)

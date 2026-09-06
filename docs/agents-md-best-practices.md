# AGENTS.md best practices

## Short answer

`AGENTS.md` should tell an AI coding agent what to load, what rules to follow, and where it may write. nestwork uses `AGENTS.md` as a startup protocol for persistent AI agent memory.

## What belongs in AGENTS.md?

Good `AGENTS.md` files include:

- session startup steps
- context load order
- rule priority
- write boundaries
- project-specific context rules
- session end sync rules

Bad `AGENTS.md` files mix temporary notes, long chat history, vague preferences, and project implementation details that should live in separate docs.

## nestwork pattern

nestwork keeps `AGENTS.md` focused on protocol:

```text
1. Pull the latest context with git.
2. Read queen/agent-rules.md.
3. Read shared/resident.md and agents/<host>/<agent-id>/resident.md, if present.
4. Follow the current task; search history and project context only as needed.
5. Read strategy and recent git activity when prioritizing, resuming or coordinating.
```

Protocol 3.0 separates loading from authority. Missing resident summaries do
not make historical memory mandatory, and links are retrieval pointers rather
than instructions to load everything. Keep history in `memory.md`; only small,
reviewed facts needed across tasks belong in `resident.md`.
See [context loading and migration](context-loading.md).

## Why this helps AI agents

AI coding agents perform better when startup context is explicit, ordered, and repeatable. A clear `AGENTS.md` reduces repeated prompting and makes every session start from the same rules.

## Related docs

- [AI agent memory](ai-agent-memory.md)
- [Git-native memory protocol](git-native-memory-protocol.md)
- [Shared context for AI coding agents](shared-context-for-ai-coding-agents.md)

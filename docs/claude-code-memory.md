# Claude Code memory

## Short answer

nestwork gives Claude Code persistent memory by injecting a startup protocol into `~/.claude/CLAUDE.md` and registering hooks that sync its Nestwork agent directory with git. Tool-native memory carryover is a separate, reviewed workflow (AGENTS.md §13).

## How it works with Claude Code

The Claude Code installer:

1. Creates `agents/<host>/<agent-id>/memory.md`.
2. Injects the nestwork startup protocol into `~/.claude/CLAUDE.md`.
3. Registers Claude Code hooks for memory writes.
4. Pulls latest memory before writes and commits memory after writes.

Install on macOS or Linux:

```bash
bash ~/nestwork/scripts/install/claude.sh
```

Install on Windows:

```powershell
.\nestwork\scripts\install\claude.ps1
```

## Why Claude Code users need this

Claude Code can read instruction files, but project rules and long-term context can drift across machines and projects. nestwork gives Claude Code a shared context layer backed by git history.

## What gets loaded at session start?

Protocol 3.0 startup reads only:

- `queen/agent-rules.md`
- `shared/resident.md`, if present
- `agents/<host>/<agent-id>/resident.md`, if present

The SessionStart hook emits these paths in READ-ON-START; the agent reads the
files. Strategy, historical `memory.md`, projects, workflows and the inbox are
on demand. Missing optional summaries never cause a full-history fallback.
Existing installations must refresh their bootstrap and open a new session;
see [context loading and migration](context-loading.md).

## Related docs

- [AI agent memory](ai-agent-memory.md)
- [Git-native memory protocol](git-native-memory-protocol.md)
- [nestwork vs claude-mem](comparisons/claude-mem.md)

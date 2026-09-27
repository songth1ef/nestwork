# Claude Code memory

## Short answer

nestwork gives Claude Code persistent memory by injecting a startup protocol into `~/.claude/CLAUDE.md` and registering hooks that sync its Nestwork agent directory with git. Claude Code's own auto memory (`~/.claude/projects/<project>/memory/`) stays machine-local; nestwork does not mirror it automatically. Carrying it into the nest is a separate, reviewed distillation step (AGENTS.md §13).

## How it works with Claude Code

The Claude Code installer:

1. Creates `agents/<host>/<agent-id>/memory.md` (the agent id looks like `claude-a7k2`).
2. Injects the nestwork startup protocol into `~/.claude/CLAUDE.md`, inside marker comments that preserve your own content.
3. Registers hooks in `~/.claude/settings.json`:
   - **SessionStart** pulls the repository and emits the resident file list.
   - **PreToolUse** / **PostToolUse** on Write and Edit under the agent directory: pull before each memory write, commit and push right after it.
   - **Stop** runs a safety-net commit and push once per turn (a no-op when clean).
   - **SessionEnd** exports an optional claude-mem digest and runs optional local history sync.

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

Since protocol 3.0 (current: 3.1), startup reads only:

- `queen/agent-rules.md`
- `shared/resident.md`, if present
- `agents/<host>/<agent-id>/resident.md`, if present

The SessionStart hook emits these paths in READ-ON-START; the agent reads the
files. Strategy, historical `memory.md`, projects, workflows and the inbox are
on demand. Missing optional summaries never cause a full-history fallback.
If a memory scope uses topic memory (protocol 3.1), its `memory.md` is an index
of topic files, and the agent opens only the topics whose description matches
the task. Existing installations must refresh their bootstrap and open a new session;
see [context loading and migration](context-loading.md).

## Related docs

- [AI agent memory](ai-agent-memory.md)
- [Git-native memory protocol](git-native-memory-protocol.md)
- [nestwork vs claude-mem](comparisons/claude-mem.md)

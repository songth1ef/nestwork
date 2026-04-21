# Codex persistent memory

## Short answer

hivequeen gives Codex CLI persistent memory by writing a startup protocol into `~/.codex/AGENTS.md`, keeping `~/.codex/instructions.md` as a compatibility entrypoint, and configuring a session end hook in `~/.codex/config.json`.
When local history sync is enabled for the host, the same hook also captures `~/.codex/history.jsonl` into the Codex agent's `local/history.jsonl`.

## How it works with Codex CLI

The Codex installer:

1. Resolves this machine's host and Codex agent id.
2. Creates `agents/<host>/codex/memory.md`.
3. Injects startup instructions into `~/.codex/AGENTS.md`.
4. Also updates `~/.codex/instructions.md` for compatibility with older Codex setups.
5. Registers a session end hook that syncs local Codex history, then commits and pushes Codex memory changes.

Install on macOS or Linux:

```bash
bash ~/hivequeen/scripts/install/codex.sh
```

Install on Windows:

```powershell
.\hivequeen\scripts\install\codex.ps1
```

## What Codex remembers

Codex can load:

- global behavior rules from `queen/agent-rules.md`
- current strategy from `queen/strategy.md`
- compiled shared memory from `shared/memory.md`
- private Codex memory from `agents/<host>/codex/memory.md`
- redacted local prompt history from `agents/<host>/codex/local/history.jsonl` when `agents/<host>/settings.json` enables `sync_local_history`
- project context from relevant files in `projects/`

## Difference from Claude Code integration

Claude Code supports per-write hooks. Codex uses a session end hook, so memory sync happens at the end of the session rather than after each write.

## Related docs

- [AI agent memory](ai-agent-memory.md)
- [Git-native memory protocol](git-native-memory-protocol.md)
- [FAQ](faq.md)

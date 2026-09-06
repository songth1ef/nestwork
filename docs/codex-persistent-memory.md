# Codex persistent memory

## Short answer

nestwork gives Codex CLI persistent memory by writing a startup protocol into `~/.codex/AGENTS.md` and keeping `~/.codex/instructions.md` as a compatibility entrypoint.
For current Codex releases, the installer also sets `hooksPath` in `~/.codex/config.toml` and registers a SessionEnd hook in `~/.codex/hooks.json`. When local history sync is enabled for the host, that hook captures `~/.codex/history.jsonl` into the Codex agent's `local/history.jsonl`.

## How it works with Codex CLI

The Codex installer:

1. Resolves this machine's host and Codex agent id.
2. Creates `agents/<host>/codex/memory.md`.
3. Injects startup instructions into `~/.codex/AGENTS.md`.
4. Also updates `~/.codex/instructions.md` for compatibility with older Codex setups.
5. Registers a SessionEnd hook in `~/.codex/hooks.json` that launches optional local Codex history snapshots in a detached process, allowing the hook to return within Codex's three-second SessionEnd limit.

Install on macOS or Linux:

```bash
bash ~/nestwork/scripts/install/codex.sh
```

Install on Windows:

```powershell
.\nestwork\scripts\install\codex.ps1
```

## What Codex remembers

Startup reads only core rules and optional `shared/resident.md` and
`agents/<host>/codex/resident.md`. Other sources below are retrieved on demand.
See [loading and migration](context-loading.md).

Codex can retrieve:

- global behavior rules from `queen/agent-rules.md`
- current strategy from `queen/strategy.md`
- compiled shared memory from `shared/memory.md`
- private Codex memory from `agents/<host>/codex/memory.md`
- redacted local prompt history from `agents/<host>/codex/local/history.jsonl` when `agents/<host>/settings.json` enables `sync_local_history`
- project context from relevant files in `projects/`

## Difference from Claude Code integration

Claude Code supports Nestwork's full per-write memory synchronization flow. Codex uses a SessionEnd hook only for optional local-history snapshots; memory changes under `agents/<host>/codex/` still follow the manual commit/push instruction in the injected bootstrap.

## Related docs

- [AI agent memory](ai-agent-memory.md)
- [Git-native memory protocol](git-native-memory-protocol.md)
- [FAQ](faq.md)

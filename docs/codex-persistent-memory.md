# Codex persistent memory

## Short answer

nestwork gives Codex CLI persistent memory by writing a startup protocol into `~/.codex/AGENTS.md` and keeping `~/.codex/instructions.md` as a compatibility entrypoint.
For current Codex releases, the installer also sets `hooksPath` in `~/.codex/config.toml` and registers hooks in `~/.codex/hooks.json`: PreToolUse / PostToolUse on file edits and Stop for per-write memory sync (the same `nestwork.sh` flow as Claude Code), and SessionEnd for optional local-history snapshots. When local history sync is enabled for the host, the SessionEnd hook captures `~/.codex/history.jsonl` into the Codex agent's `local/history.jsonl`.

## How it works with Codex CLI

The Codex installer:

1. Resolves this machine's host and Codex agent id.
2. Creates `agents/<host>/codex/memory.md`.
3. Injects startup instructions into `~/.codex/AGENTS.md`.
4. Also updates `~/.codex/instructions.md` for compatibility with older Codex setups.
5. Registers PreToolUse / PostToolUse hooks matching `^(apply_patch|Edit|Write)$` and a Stop hook in `~/.codex/hooks.json`. They run `scripts/hooks/nestwork.sh`, which reads the target paths from the `apply_patch` patch headers and only acts on files under `agents/<host>/codex/`: pull before the write (a conflict blocks it with exit 2), commit and push after it.
6. Registers a SessionEnd hook that launches optional local Codex history snapshots in a detached process, allowing the hook to return within Codex's three-second SessionEnd limit.

Codex asks you to review and trust new or changed hooks before they run: open Codex and run `/hooks` once after installing. See [Codex hooks](https://learn.chatgpt.com/docs/hooks).

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
- distilled shared memory from `shared/memory.md` (with topic memory, an index into `shared/<topic>.md` files)
- private Codex memory from `agents/<host>/codex/memory.md`
- redacted local prompt history from `agents/<host>/codex/local/history.jsonl` when `agents/<host>/settings.json` enables `sync_local_history`
- project context from relevant files in `projects/`

## Difference from Claude Code integration

Both use the same per-write memory synchronization flow. Differences: Codex edits files with `apply_patch`, so the hook parses the patch headers instead of a `file_path` field; Codex has no claude-mem export; and Codex's SessionStart hook is not used, so the injected bootstrap in `~/.codex/AGENTS.md` performs the startup pull.

## Related docs

- [AI agent memory](ai-agent-memory.md)
- [Git-native memory protocol](git-native-memory-protocol.md)
- [FAQ](faq.md)

# nestwork vs claude-mem

## Short answer

nestwork is a git-native memory protocol: memory is Markdown in a private git repository, shared by several AI coding agents across machines without a memory server. [claude-mem](https://github.com/thedotmack/claude-mem) is a plugin that captures agent sessions into a local database with search, served by a local worker process. They solve different layers of the problem and can be used together.

## Comparison

| Question | nestwork | claude-mem |
|---|---|---|
| Primary model | Git repository protocol | Session-capture plugin with a local worker |
| Storage | Markdown files in git | Local SQLite (FTS5) database plus a Chroma vector index |
| What gets stored | Curated rules, facts and decisions that agents write deliberately | Observations captured automatically from sessions |
| Multi-agent support | One protocol for Claude Code, Codex CLI, Gemini CLI, Kimi Code, OpenClaw, Hermes Agent and other markdown-config tools | Integrates with several agent tools; check its documentation for the current list |
| Cross-machine sync | Git pull, commit and push | Not built on git; its database is local to the machine running the worker |
| Server required | No | A local worker process |
| Human-readable memory | Yes, plain Markdown with git history | Stored in a database; read through its own tools |

## Using them together

nestwork has an optional claude-mem integration. When the claude-mem worker is running on `localhost:37777`, the Claude Code SessionEnd hook exports that day's observations to `agents/<host>/<agent-id>/claude-mem-digest.md`, which is committed and pushed with the rest of the agent's memory. That gives claude-mem's observations cross-machine reach through git. If the worker is not running, the step is skipped silently.

## When nestwork is a better fit

Use nestwork if:

- You want one memory protocol for multiple AI coding agents.
- You want memory changes in git history.
- You want private memory directories per machine and agent.
- You prefer Markdown files over a service dependency.
- You want startup context through `AGENTS.md`, `CLAUDE.md`, or similar instruction files.

## When claude-mem may be a better fit

Use claude-mem if:

- You want sessions captured automatically, without deciding what to write down.
- You want vector search over past sessions on one machine.
- You are comfortable running a local worker process.

> This comparison is a snapshot. claude-mem changes quickly; verify its current storage and tool support against its own documentation. For the wider field, see the [agent memory landscape](agent-memory-landscape.md).

## Related docs

- [Agent memory landscape](agent-memory-landscape.md)
- [AI agent memory](../ai-agent-memory.md)
- [Claude Code memory](../claude-code-memory.md)
- [Git-native memory protocol](../git-native-memory-protocol.md)

# Git-native memory protocol

## Short answer

A git-native memory protocol stores AI agent memory as versioned files in a git repository. nestwork uses git pull, commit, and push to sync memory across agents without a server.

## Protocol layers

nestwork separates context into layers:

| Layer | Path | Purpose |
|---|---|---|
| Rules | `queen/agent-rules.md` | Non-negotiable behavior rules |
| Strategy | `queen/strategy.md` | Current decision direction |
| Shared memory | `shared/memory.md` | Distilled cross-agent facts |
| Private memory | `agents/<host>/<agent-id>/memory.md` | One agent's own memory |
| Project context | `projects/<name>.md` | Context for a specific project |
| Workflow | `workflow/<topic>.md` | Portable cross-project methodology |

Priority order:

```text
queen/agent-rules.md > queen/strategy.md > shared/memory.md > agents/*/*/memory.md > projects/*.md > workflow/*.md
```

## Why git?

Git gives nestwork:

- offline local files
- version history
- branch and merge tooling
- cross-machine sync
- private repository support
- no runtime server

## Conflict model

Each agent writes only to `agents/<host>/<agent-id>/`. Normal memory writes stay isolated because no two agents should write to the same file. Shared memory is updated by compile or distillation workflows, not by every agent at once.

## Related docs

- [AI agent memory](ai-agent-memory.md)
- [Claude Code memory](claude-code-memory.md)
- [Codex persistent memory](codex-persistent-memory.md)

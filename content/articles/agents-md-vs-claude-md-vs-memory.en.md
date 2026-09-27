---
title: AGENTS.md vs CLAUDE.md vs Memory — What Goes Where
description: AGENTS.md is a tool-neutral instruction file, CLAUDE.md is Claude Code's, and memory is what agents write. Which tool reads which, and how to combine them.
keywords: AGENTS.md vs CLAUDE.md, AGENTS.md memory, CLAUDE.md, GEMINI.md, Claude Code memory, Codex AGENTS.md, agent instructions
date: 2026-09-27
---

`AGENTS.md` and `CLAUDE.md` are both instruction files that you write and the agent reads at the start of a session; the difference is who reads them. `AGENTS.md` is an open format read by Codex, Cursor, Jules and many other tools, while `CLAUDE.md` is Claude Code's own file — and current Claude Code reads `AGENTS.md` too when no `CLAUDE.md` is present. Memory is a third thing: notes the agent writes for itself, which in Claude Code and Codex stay on the local machine. Put rules in instruction files, let memory hold what the agent learns, and keep one source of truth so the files don't drift.

## Three kinds of files, three owners

It helps to sort agent context by who writes it and how far it should travel:

| Kind | Example | Written by | Scope | Travels via |
|---|---|---|---|---|
| Repository instructions | `AGENTS.md`, `CLAUDE.md` in the repo | You and your team | One project | Source control |
| User-level instructions | `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md` | You | All your projects on this machine | Nothing, by default |
| Tool memory | `~/.claude/projects/<project>/memory/`, `~/.codex/memories/` | The agent | One tool on one machine | Nothing, by default |

Repository instructions are the only layer that already travels well: they are committed with the code. User-level instructions and tool memory both sit in your home directory and stay on the machine that has them.

## Which tool reads which file

| Tool | Repository file | User-level file | Built-in memory |
|---|---|---|---|
| Claude Code | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`; `AGENTS.md` when no `CLAUDE.md` exists | `~/.claude/CLAUDE.md` | Auto memory in `~/.claude/projects/<project>/memory/` |
| Codex CLI | `AGENTS.override.md` or `AGENTS.md`, from the git root down to the working directory | `~/.codex/AGENTS.md` (or `AGENTS.override.md`) | `~/.codex/memories/` |
| Gemini CLI | `GEMINI.md` by default; `context.fileName` can add `AGENTS.md` | `~/.gemini/GEMINI.md` | — |
| Cursor, Jules, Copilot coding agent and others | `AGENTS.md` | Varies by tool | Varies by tool |

Sources: [Claude Code memory docs](https://code.claude.com/docs/en/memory), [Codex AGENTS.md guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Gemini CLI GEMINI.md docs](https://geminicli.com/docs/cli/gemini-md/), [agents.md](https://agents.md/).

A few details matter in practice:

- **Codex caps the combined size.** It concatenates files from the root down, one per directory, and stops at `project_doc_max_bytes`, 32 KiB by default. Files closer to your working directory appear later and so take precedence.
- **Claude Code concatenates rather than overrides.** All `CLAUDE.md` files from the filesystem root down to the working directory are loaded, ordered root first. Anthropic suggests keeping each file under 200 lines.
- **AGENTS.md is stewarded by the Agentic AI Foundation** under the Linux Foundation and, per its site, used by over 60,000 open-source projects. Nested files follow one rule: the closest `AGENTS.md` to the edited file wins.

## How Claude Code decides between AGENTS.md and CLAUDE.md

Since v2.1.277, Claude Code can read `AGENTS.md` directly. The default (`claude-md-or-agents-md`) is:

| Your repository has | Claude reads |
|---|---|
| `AGENTS.md`, and no `CLAUDE.md` or `CLAUDE.local.md` in the working directory or above | `AGENTS.md` |
| `AGENTS.md` and a `CLAUDE.md` or `CLAUDE.local.md` | Only the `CLAUDE.md` files |
| A `CLAUDE.md` that imports `@AGENTS.md` | `CLAUDE.md`, with `AGENTS.md` included through the import |

Two traps follow. Adding a personal `CLAUDE.local.md` to a project that relies on `AGENTS.md` silently stops Claude from reading `AGENTS.md` for you. And your user-level `~/.claude/CLAUDE.md` does not count for this check — it always loads alongside. You can change the behavior with the **Project instructions** setting, for example `claude-md-and-agents-md` to read both.

## Combining them: one source, thin wrappers

The pattern that avoids drift is to write the shared rules once in `AGENTS.md` and make every other file a thin wrapper.

For Claude Code, Anthropic's docs recommend an import when you also need Claude-specific content:

```markdown
@AGENTS.md

## Claude Code

Use plan mode for changes under `src/billing/`.
```

A symlink (`ln -s AGENTS.md CLAUDE.md`) also works, but the docs warn against it if anyone clones on Windows: Git checks a committed symlink out as a plain text file unless `core.symlinks` is enabled, leaving a one-line `CLAUDE.md` in place of your instructions. For Gemini CLI, add `AGENTS.md` to `context.fileName` in `settings.json`.

Then decide what does not belong in these files at all:

- **Temporary task notes and chat history.** They bloat every session.
- **Facts the agent learned about you.** That is memory, and it changes more often than rules.
- **Anything secret.** Instruction files are committed and shared.

Codex's documentation draws the same line from the other side: "Keep required team guidance in `AGENTS.md` or checked-in documentation. Treat memories as a helpful recall layer, not as the only source for rules that must always apply."

## The gap: user-level context that travels

Repository instructions cover one project. What they don't cover is everything that belongs to *you* rather than to a repo — your preferences, cross-project lessons, the state of work you left on another machine. That lands in user-level files and tool memory, and both stay on one machine. Claude Code's docs say it outright: "Auto memory is machine-local … Files are not shared across machines or cloud environments."

So you end up with four copies of your preferences in four home directories, each a little different, and a rule you taught Claude Code on the laptop is unknown to Codex on the desktop.

## How nestwork uses AGENTS.md as a startup protocol

[nestwork](https://github.com/songth1ef/nestwork) closes that gap by moving user-level context into a private git repository and using instruction files only as a pointer to it.

1. **One canonical protocol.** The nest's own [`AGENTS.md`](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md) is the single bootstrap source; `CLAUDE.md` in the nest is a generated mirror kept in sync by `scripts/maintenance/sync-claude-md.sh`. It is a real file rather than a symlink because Windows clones without symlink support were receiving a broken 9-byte text file.
2. **A marked block in each tool's user-level file.** The installers write a short startup block between `<!-- nestwork:begin -->` and `<!-- nestwork:end -->` markers into `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md` and similar files, preserving whatever else you keep there. Re-running an installer replaces only the block.
3. **What the block says.** Pull the nest; read only the resident tier — `queen/agent-rules.md`, `shared/resident.md` and this agent's `resident.md`; search history, projects and workflows on demand; write memory only to this agent's own directory.

```text
queen/agent-rules.md > queen/strategy.md > shared/memory.md
  > agents/*/*/memory.md > projects/*.md > workflow/*.md
```

That priority chain decides conflicts, and it is separate from load order: only the resident files load at startup, about 640 tokens on the author's nest, against about 69,600 for the older load-everything startup.

nestwork does not replace a project's own `AGENTS.md`. Its rule of thumb: if knowledge changes when you switch employers, it belongs in that repository's docs; if it survives the switch, it belongs in the nest's `workflow/`; project state that helps an agent resume work goes in the nest's `projects/<name>.md`. Claude Code and Codex are the author's daily drivers; the Gemini CLI, Kimi Code, Hermes and OpenClaw installers exist but are less battle-tested.

## FAQ

### Should I use AGENTS.md or CLAUDE.md?

If more than one tool touches the repository, write `AGENTS.md` as the source and add a `CLAUDE.md` containing `@AGENTS.md` only if you need Claude-specific instructions or some sessions can't read `AGENTS.md` directly. If only Claude Code is used, `CLAUDE.md` alone is fine.

### Is AGENTS.md memory?

Not in the usual sense. It is instructions you write and review; memory is what the agent records on its own. An `AGENTS.md` can, however, tell the agent where its memory lives and how to load it, which is exactly how nestwork uses it.

### Does Claude Code read both AGENTS.md and CLAUDE.md?

By default it reads `CLAUDE.md` when one exists and falls back to `AGENTS.md` otherwise. Import `@AGENTS.md` from `CLAUDE.md`, or set Project instructions to `claude-md-and-agents-md`, to get both.

### Where should personal preferences go?

Not in a committed repository file. Use a user-level file such as `~/.claude/CLAUDE.md` for one machine, or keep them in a synced store like a nestwork repository if they should follow you across machines and tools.

## Related

- [AI agent memory: four types and their trade-offs](../ai-agent-memory/)
- [Share memory between Claude Code and Codex](../share-memory-claude-code-codex/)
- [Claude Code memory across machines](../claude-code-memory-across-machines/)
- [Codex CLI persistent memory](../codex-cli-persistent-memory/)
- [Topic memory and on-demand loading](../topic-memory-on-demand-loading/)

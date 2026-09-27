---
title: Share Memory Between Claude Code and Codex
description: Claude Code reads ~/.claude/CLAUDE.md, Codex reads ~/.codex/AGENTS.md. Point both at one git repo to share memory, each writing only its own directory.
keywords: share memory between Claude Code and Codex, Claude Code and Codex together, Codex AGENTS.md, Claude Code memory, shared agent memory, nestwork
date: 2026-09-27
---

Claude Code and Codex each have their own startup file and their own native memory, and neither reads the other's. To share memory between Claude Code and Codex, give both tools the same instruction: pull one private git repository at session start, read the same rules and shared memory, and write new memory only into a directory that belongs to that tool. With nestwork you do this by running two installers against one clone; Claude Code then syncs every memory write through hooks, and Codex commits its own directory at the end of the session.

## What each tool reads at startup

The two tools look in different places, which is why they don't see each other's context by default.

| | Claude Code | Codex CLI |
|---|---|---|
| Global instruction file | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` (or `AGENTS.override.md` if present) |
| Project instruction files | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`; can also read `AGENTS.md` | `AGENTS.md` from the project root down to the current directory |
| Native memory | Auto memory in `~/.claude/projects/<project>/memory/` | Memories in `~/.codex/memories/`, off by default |
| Where hooks live | `~/.claude/settings.json` | `~/.codex/hooks.json` or `config.toml` |

Sources: Anthropic's [memory docs](https://code.claude.com/docs/en/memory), OpenAI's [AGENTS.md guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md) and [memories page](https://learn.chatgpt.com/docs/customization/memories?surface=cli).

A repository-level `AGENTS.md` can already give both tools the same *project* rules. Recent Claude Code versions read `AGENTS.md` when a project has no `CLAUDE.md`, and a `CLAUDE.md` can import it with `@AGENTS.md`. What a project file cannot carry is everything that is not about that one project: your personal preferences, decisions that span repositories, and what the other tool learned yesterday on another machine. Native memory does not help here either: Claude Code's auto memory and Codex's memories are separate stores on the local disk.

## One repo, two entry files

The approach is to put the cross-project context in a separate private git repository and make both global entry files point at it. nestwork's installers write the same startup block into each tool's global file:

- `scripts/install/claude.sh` writes it into `~/.claude/CLAUDE.md`.
- `scripts/install/codex.sh` writes it into `~/.codex/AGENTS.md`, and also into `~/.codex/instructions.md` for older Codex setups.

The block sits between `<!-- nestwork:begin -->` and `<!-- nestwork:end -->` markers, so your own content in those files survives re-installs. It tells the agent to pull the repository, read the resident files (core rules, the shared resident summary, and its own resident summary), and search history only when a task needs it.

## Separate identities, separate directories

Installing both tools on one machine gives you two agents, not one. The identity resolver ([`scripts/install/_identity.py`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/_identity.py)) stores one host name in `~/.nestwork_host` and one agent id per tool:

- `~/.nestwork_id_claude`, for example `claude-a7k2` (Claude gets a random suffix so several installs stay distinct)
- `~/.nestwork_id_codex`, which is simply `codex`

So on a machine called `desktop` the nest gets two write areas:

```text
agents/desktop/claude-a7k2/memory.md
agents/desktop/codex/memory.md
```

Each agent writes only to its own directory. Both read `queen/agent-rules.md`, `shared/`, `projects/` and `workflow/`, and either can search the other's `memory.md` when a task calls for it. That single-writer rule is what makes sharing safe: two tools never append to the same file, so there is nothing to merge in ordinary use.

## Set it up on one machine

The commands (on Windows, use the matching `.ps1` scripts):

```bash
git clone git@github.com:<you>/nestwork.git ~/nestwork
bash ~/nestwork/scripts/install/claude.sh
bash ~/nestwork/scripts/install/codex.sh
```

1. Create a private repository from the [nestwork template](https://github.com/songth1ef/nestwork/generate) and clone it with the first command.
2. Run both installers against that one clone.
3. Start a Claude Code session, ask it to record a small, non-sensitive decision, and let the hooks push it.
4. Start Codex in any directory and ask what was decided. It pulls the repository per its bootstrap and finds the note in Claude's directory or in shared memory.

Repeat on other machines; each one adds its own `agents/<host>/` folder.

## The one real difference: when memory gets committed

The tools are not wired the same way, and it matters for how quickly the other side sees a change.

**Claude Code** gets five hooks ([`_hooks.py`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/_hooks.py)): SessionStart pulls; PreToolUse on Write/Edit pulls before a memory write and blocks it on conflict; PostToolUse commits and pushes right after; Stop is a per-turn safety net; SessionEnd handles optional exports. A Claude memory write is on the remote seconds later.

**Codex** gets one hook ([`_codex_hooks.py`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/_codex_hooks.py)). The installer adds a SessionEnd entry to `~/.codex/hooks.json` and points `config.toml` at that file. The hook only launches the optional local-history snapshot, detached, because Codex allows SessionEnd hooks at most 3 seconds ([Codex hooks docs](https://learn.chatgpt.com/docs/hooks)). It does not commit memory. Codex memory edits follow the manual step in the injected bootstrap, which the agent runs when it finishes:

```bash
git -C ~/nestwork add agents/<host>/codex/
git -C ~/nestwork diff --cached --quiet -- agents/<host>/codex/ || \
  git -C ~/nestwork commit -m "memory: update <host>/codex" -- agents/<host>/codex/
git -C ~/nestwork push
```

Codex itself now supports PreToolUse and PostToolUse hooks on file edits, but nestwork's Codex installer does not register per-write sync today. In practice: a note Codex writes reaches Claude after Codex's session-end commit, and a note Claude writes reaches Codex at Codex's next session start. If you want it sooner, ask Codex to run the commit step right away.

## Keep the shared layer small and deliberate

Two tools writing freely would still create two diverging stories. nestwork keeps a hard priority order, `queen/agent-rules.md > queen/strategy.md > shared/memory.md > agents/*/*/memory.md > projects/*.md > workflow/*.md`, and on conflict the agent follows the higher source instead of blending them. `shared/` changes only through an explicit distillation (`scripts/maintenance/distill.py`), which merges what individual agents learned, with a review step, and writes files for you to check; it commits only when you pass `--commit`.

Claude Code and Codex are the author's two daily drivers, so this pairing is the most exercised path in the project. Installers for Gemini CLI, Kimi Code, OpenClaw and Hermes follow the same pattern but are less battle-tested.

## FAQ

### Can Claude Code and Codex share one project AGENTS.md instead?

For project rules, yes: Codex reads `AGENTS.md`, and Claude Code can read it directly or import it from `CLAUDE.md`. A project file does not cover personal preferences, cross-project decisions, or notes from other machines, which is what the shared memory repo is for.

### Do the two agents ever write the same file?

Not in ordinary memory writes. Claude writes `agents/<host>/claude-xxxx/`, Codex writes `agents/<host>/codex/`. `shared/` is changed only during distillation, and `queen/` only by you.

### Why does Codex commit manually while Claude Code is automatic?

Because the nestwork Codex installer registers only a SessionEnd hook for optional history snapshots, and SessionEnd hooks in Codex are limited to 3 seconds. Memory commits for Codex come from the bootstrap instruction the agent follows at the end of its work.

### Does Codex's built-in memory conflict with this?

No. Codex memories are off by default and live in `~/.codex/memories/`. OpenAI's own docs recommend keeping required guidance in `AGENTS.md` and treating memories as a recall layer, which fits the same split.

## Related

- [Claude Code memory across machines](../claude-code-memory-across-machines/)
- [Codex CLI persistent memory](../codex-cli-persistent-memory/)
- [AGENTS.md vs CLAUDE.md vs memory](../agents-md-vs-claude-md-vs-memory/)
- [Multi-agent memory without conflicts](../multi-agent-memory-without-conflicts/)
- [Memory distillation](../memory-distillation/)

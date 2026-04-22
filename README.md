# nestwork

[中文](README.zh.md) | English

Version: v0.2.0 | Protocol: 2.0

Template it, clone it anywhere — your agents share one brain. A git-native memory protocol for AI agents, like Formic workers wired to their queen. No plugins, no servers. Just git.

## What is nestwork?

nestwork is an AI agent memory system for coding agents. It gives Claude Code, Codex CLI, Gemini CLI, and other markdown-config agents persistent memory, shared context, project context, and startup rules through a git-native memory protocol.

Use nestwork when you want AI coding agents to remember context across sessions, machines, and tools without running a server or installing a hosted memory service.

## Answer-ready docs

- [AI agent memory](docs/ai-agent-memory.md)
- [Claude Code memory](docs/claude-code-memory.md)
- [Codex persistent memory](docs/codex-persistent-memory.md)
- [Git-native memory protocol](docs/git-native-memory-protocol.md)
- [AGENTS.md best practices](docs/agents-md-best-practices.md)
- [Shared context for AI coding agents](docs/shared-context-for-ai-coding-agents.md)
- [FAQ](docs/faq.md)
- [nestwork vs claude-mem](docs/comparisons/claude-mem.md)

---

## How it works

```
nestwork repo (your private queen)
├── queen/          ← read-only rules & strategy (you write this)
├── agents/         ← each agent writes ONLY to its own directory
├── shared/         ← compiled memory across all agents (read-only)
└── projects/       ← per-project context files
```

Every machine that clones your queen gets the same brain.
Every agent instance writes only to its own `agents/<host>/<agent-id>/` directory, so normal memory writes stay isolated.

```
Session start  →  git pull  →  load context
Session end    →  git commit agents/<host>/<agent-id>/  →  git push
```

---

## Quickstart

### 1. Create your private queen

Click **Use this template → Create a new repository** on GitHub.
Set it to **Private** — your memory stays yours.

> **Why not Fork?** Forks are public by default and tied to the upstream repo.
> A private repo created from this template is fully yours.
> 
> When nestwork ships updates, `git merge upstream/main` would conflict with your
> private `queen/strategy.md`, `agents/`, and `shared/` — files you intentionally
> diverged. The `update.sh` script syncs only the protocol layer, leaving your
> private data untouched.

### 2. Clone to each machine

```bash
git clone git@github.com:<you>/nestwork.git ~/nestwork
```

### 3. Install for your agent tool

**Claude Code (macOS / Linux)**
```bash
bash ~/nestwork/scripts/install/claude.sh
```

**Claude Code (Windows)**
```powershell
.\nestwork\scripts\install\claude.ps1
```

**Codex (macOS / Linux)**
```bash
bash ~/nestwork/scripts/install/codex.sh
```

**Codex (Windows)**
```powershell
.\nestwork\scripts\install\codex.ps1
```

**OpenClaw (macOS / Linux)**
```bash
bash ~/nestwork/scripts/install/openclaw.sh
```

**OpenClaw (Windows)**
```powershell
.\nestwork\scripts\install\openclaw.ps1
```

**Hermes Agent (macOS / Linux)**
```bash
bash ~/nestwork/scripts/install/hermes.sh
```

**Hermes Agent (Windows)**
```powershell
.\nestwork\scripts\install\hermes.ps1
```

**Gemini CLI (macOS / Linux)**
```bash
bash ~/nestwork/scripts/install/gemini.sh
```

**Gemini CLI (Windows)**
```powershell
.\nestwork\scripts\install\gemini.ps1
```

**Aider (macOS / Linux)**
```bash
bash ~/nestwork/scripts/install/aider.sh
```

**Aider (Windows)**
```powershell
.\nestwork\scripts\install\aider.ps1
```

**Any other markdown-config CLI** (Qwen Code, OpenCode, Trae, Kimi Code, …) — see
[Supported tools](#supported-tools) and `install/generic.sh`.

Repeat on every machine. Same queen, different agent IDs, one shared brain.

### Prompt examples

Skip the manual steps — paste one of these into any Claude Code session:

- **From scratch**
  > Read the README at https://github.com/songth1ef/nestwork and follow
  > Quickstart: create a private queen repo from the template, clone it
  > on this machine, and install Claude Code.

- **Discover configurable features**
  > Read the README at https://github.com/songth1ef/nestwork and list
  > every configurable feature nestwork exposes (hooks, optional syncs,
  > filters, …). Then recommend which ones to enable for my current
  > machine.

---

## Customize

### Your rules
Edit `queen/agent-rules.md` — behavior boundaries that apply to all agents.

### Your strategy
Edit `queen/strategy.md` — your current goals and decision direction.

### Your projects
Add `projects/<project-name>.md` — context loaded when working on that project.

---

## Compile shared memory

After agents have accumulated memory, merge it into `shared/memory.md`
using one of two strategies:

```bash
# Mechanical: concatenate every agents/*/*/memory.md, commit, push.
bash ~/nestwork/scripts/maintenance/compile.sh

# LLM-oriented: print a distillation prompt. Feed the output to any
# agent session, then commit the agent's merged shared/memory.md.
python3 ~/nestwork/scripts/maintenance/distill.py
```

Both variants leave the input agent memories untouched. All agents pick
the new `shared/memory.md` up on their next `git pull`.

---

## Directory structure

```
nestwork/
├── AGENTS.md                   bootstrap source of truth (Codex, OpenClaw, Gemini, ...)
├── CLAUDE.md                   verbatim mirror of AGENTS.md (Claude Code loads this name)
├── SOUL.md                     short persona file (Hermes entry point)
├── queen/
│   ├── agent-rules.md          behavior rules — read-only for agents
│   └── strategy.md             decision direction — read-only for agents
├── agents/
│   └── <host>/<agent-id>/
│       └── memory.md           this agent's private memory
├── shared/
│   └── memory.md               compiled cross-agent memory
├── projects/
│   └── <project>.md            per-project context
└── scripts/
    ├── install/                   per-tool installers
    │   ├── claude.{sh,ps1}
    │   ├── codex.{sh,ps1}
    │   ├── gemini.{sh,ps1}
    │   ├── hermes.{sh,ps1}
    │   ├── openclaw.{sh,ps1}
    │   ├── aider.{sh,ps1}         (yaml wiring, not marker block)
    │   ├── generic.{sh,ps1}       any markdown-config CLI
    │   ├── _bootstrap.py          shared bootstrap injector
    │   └── _hooks.py              shared hook registrar (Claude Code)
    ├── hooks/                     runtime hooks
    │   ├── nestwork.sh           pre/post/stop entry
    │   ├── _match-file.py         stdin-based file matcher
    │   ├── export-claude-mem.sh   optional claude-mem bridge
    │   ├── sync-local-history.sh  optional local-history capture (wrapper)
    │   └── sync-local-history.py  optional local-history capture (worker)
    └── maintenance/               ops
        ├── compile.sh             aggregate agents/*/* into shared/ (mechanical)
        ├── distill.py             LLM-oriented variant: print a merge prompt
        ├── sync-claude-md.sh      regenerate CLAUDE.md from AGENTS.md
        └── update.sh              pull upstream protocol layer
```

---

## File size limits

Each file has a line limit. When exceeded, split into topic files and use an index with links.

| File | Max lines |
|---|---|
| `queen/agent-rules.md` | 80 |
| `queen/strategy.md` | 80 |
| `agents/<host>/<agent-id>/memory.md` | 200 |
| `shared/memory.md` | 500 |
| `projects/<name>.md` | 150 |

**Example — split `agents/macbook/claude/memory.md` when it hits 150 lines:**

```
agents/macbook/claude/
├── memory.md          ← becomes an index
├── user_profile.md
├── feedback_collab.md
└── project_nestwork.md
```

`memory.md` after split:
```markdown
# MEMORY — claude-macbook

- [User Profile](user_profile.md) — role, stack, preferences
- [Collaboration](feedback_collab.md) — working style, corrections
- [Project: nestwork](project_nestwork.md) — goals, decisions
```

Agents read the index first, follow links only when the topic is relevant.

---

## Why memory writes stay isolated

Each agent owns exactly one directory under `agents/`. No two agents should write to the same file during normal memory updates, so normal agent-memory commits avoid content conflicts by construction.

| Path | Who writes | Conflict possible? |
|---|---|---|
| `queen/` | You (human) | No |
| `agents/<host>/<agent-id>/` | That agent only | No for normal memory writes |
| `shared/` | `compile.sh` only | No |

---

## Supported tools

### Native installers (known config path)

| Tool | Vendor | Entry file | Install | Adaptation status |
|---|---|---|---|---|
| Claude Code | Anthropic | `~/.claude/CLAUDE.md` + hooks | `bash scripts/install/claude.sh` | Adapted and personally used |
| Codex CLI | OpenAI | `~/.codex/AGENTS.md` + `~/.codex/instructions.md` compatibility | `bash scripts/install/codex.sh` | Adapted and personally used |
| Gemini CLI | Google | `~/.gemini/GEMINI.md` | `bash scripts/install/gemini.sh` | Installer exists; not personally used or verified yet |
| OpenClaw | open source | `~/.openclaw/workspace/AGENTS.md` | `bash scripts/install/openclaw.sh` | Installer exists; not personally used or verified yet |
| Hermes Agent | open source | `~/.hermes/SOUL.md` | `bash scripts/install/hermes.sh` | Installer exists; not personally used or verified yet |
| Aider | open source | `~/.aider-nestwork.md` (wired via `.aider.conf.yml` `read:`) | `bash scripts/install/aider.sh` | Installer exists; not personally used or verified yet |

Only Claude Code and Codex CLI are actively adapted in this queen right now.
Other installers are reference entry points for later adaptation; users can
adapt them themselves, and LLMs can usually help map the protocol to each
tool's current config format.

Only Claude Code registers session hooks for atomic per-write memory sync.
Other tools follow the session-end commit protocol written into their
bootstrap config.

### Optional: capture local tool history

Claude Code keeps prompt history and plan artefacts under `~/.claude/`.
Codex CLI keeps prompt history under `~/.codex/`.
You can have them mirrored into `agents/<host>/<id>/local/` so they
travel with your queen across machines.

Opt-in per host — no env var, no re-install needed after the first
install. Create `agents/<host>/settings.json` inside your queen (the
host dir that matches this machine):

```json
{ "sync_local_history": true }
```

Default is `false` (or file absent). The setting is versioned in git
with the rest of your queen, so each machine's host dir tracks its
own toggle.

When enabled, Claude Code and Codex session hooks sync:

| Source | Target | Notes |
|---|---|---|
| `~/.claude/history.jsonl` | `local/history.jsonl` | redacted: `pastedContents` dropped, `$HOME` paths and common token patterns (`sk-*`, `ghp_*`, `Bearer …`) scrubbed |
| `~/.claude/plans/` | `local/plans/` | plan-mode artefacts, mirrored |
| `~/.codex/history.jsonl` | `local/history.jsonl` | Codex agents only; same redaction pass |

`todos/` and `tasks/` are intentionally excluded — >99% of them are
empty UUID-per-session bookkeeping.

### Via `install/generic.sh` (you confirm the config path)

Any CLI that loads a single markdown file at startup as its system prompt
can be bootstrapped in one line. Confirm the tool's instruction-file path
(usually `--help` or its docs), then:

```bash
bash scripts/install/generic.sh <prefix> <config-path>
```

Examples — paths are illustrative, verify before running:

| Tool | Vendor | Suggested prefix |
|---|---|---|
| Qwen Code | Alibaba 通义 | `qwen` |
| OpenCode | open source | `opencode` |
| CodeBuddy Code | Tencent | `codebuddy` |
| iFlow CLI | Alibaba 心流 | `iflow` |
| Trae CLI / Solo | ByteDance | `trae` |
| Qoder | Alibaba | `qoder` |
| Kimi Code CLI | Moonshot | `kimi` |
| 通义灵码 CLI | Alibaba Cloud | `lingma` |

> **Tip**: Qwen Code is a Gemini CLI fork and may also honour
> `~/.gemini/GEMINI.md` out of the box — try `install/gemini.sh` first.

### Workspace-level (IDE plugins, symlink)

| Tool | Target | Install |
|---|---|---|
| Cursor | `.cursor/rules/nestwork.md` | `ln -s AGENTS.md .cursor/rules/nestwork.md` |
| Windsurf | `.windsurf/rules/nestwork.md` | `ln -s AGENTS.md .windsurf/rules/nestwork.md` |
| Cline (VS Code) | `.clinerules/nestwork.md` | `ln -s AGENTS.md .clinerules/nestwork.md` |
| GitHub Copilot (repo) | `.github/copilot-instructions.md` | `ln -s AGENTS.md .github/copilot-instructions.md` |

### Not supported (and why)

| Tool | Reason |
|---|---|
| GitHub Copilot CLI (`gh copilot`) | Q&A style, no persistent instruction-file mechanism |
| Antigravity | IDE-first; CLI entrypoint is project-scoped and undocumented for external bootstrap |
| CloudBase AI CLI | Gateway that invokes downstream CLIs — install nestwork on the downstream tools instead |
| ChatDev | Simulated "software company" workflow, not a persistent single-agent loop |

---

## Adding a new tool via `install/generic.sh`

For any CLI whose startup loads a single markdown file as its system prompt:

1. Find the config path (check `--help` or the tool's docs)
2. Pick a short prefix for the `agent-id`
3. Run:

```bash
bash scripts/install/generic.sh <prefix> <config-path>
```

This:
- Creates `agents/<host>/<prefix>/memory.md` for that tool on this machine
- Writes the nestwork bootstrap block into `<config-path>` inside
  `<!-- nestwork:begin -->` / `<!-- nestwork:end -->` markers, preserving
  any existing user content
- Does NOT register hooks — the bootstrap block instructs the agent to
  `git add / commit / push` its memory dir at session end

---

## Staying up to date

Two paths — both keep your private data (`agents/`, `queen/`,
`shared/`, `projects/`) untouched.

### Automatic (recommended)

The `.github/workflows/sync-upstream.yml` in your queen runs daily at
03:00 UTC (and on manual **Run workflow**), compares the protocol
layer against the upstream template, and opens a PR to your `main`
when upstream drifts. You review the diff and merge.

PR create/update/reopen now uses the GitHub REST API instead of
`gh pr ...` because some repositories reject GraphQL PR mutations from
Actions. If your repo still blocks the default token, add an Actions
secret named `NESTWORK_SYNC_TOKEN`; the workflow will prefer it
automatically.

GitHub blocks `GITHUB_TOKEN` from pushing workflow-file changes, so
`.github/workflows/` is **not** touched by the CI path — use the
manual path below for workflow updates.

### Manual

```bash
bash ~/my-queen/scripts/maintenance/update.sh
```

Covers `scripts/`, `.github/workflows/`, `AGENTS.md`, `CLAUDE.md`,
`SOUL.md`, and the READMEs.

---

## Inspired by

*Ender's Game* — the Formic hive mind. Every worker wired to the same queen.
No individual memory. No conflicting selves. One distributed intelligence.

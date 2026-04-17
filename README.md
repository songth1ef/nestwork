# hivequeen

[中文](README.zh.md) | English

Fork it, clone it anywhere — your agents share one brain. A git-native memory protocol for AI agents, like Formic workers wired to their queen. No plugins, no servers. Just git. // fork 即继承，clone 即连接，所有 agent 共用同一个大脑。git 原生记忆协议，无需插件，无需服务器。

---

## How it works

```
hivequeen repo (your fork)
├── queen/          ← read-only rules & strategy (you write this)
├── agents/         ← each agent writes ONLY to its own directory
├── shared/         ← compiled memory across all agents (read-only)
└── projects/       ← per-project context files
```

Every machine that clones your fork gets the same brain.
Every agent instance writes only to its own `agents/<agent-id>/` directory — no conflicts, ever.

```
Session start  →  git pull  →  load context
Session end    →  git commit agents/<id>/  →  git push
```

---

## Quickstart

### 1. Create your private queen

Click **Use this template → Create a new repository** on GitHub.
Set it to **Private** — your memory stays yours.

> **Why not Fork?** Forks are public by default and tied to the upstream repo.
> A private repo created from this template is fully yours.
> 
> When hivequeen ships updates, `git merge upstream/main` would conflict with your
> private `queen/strategy.md`, `agents/`, and `shared/` — files you intentionally
> diverged. The `update.sh` script syncs only the protocol layer, leaving your
> private data untouched.

### 2. Clone to each machine

```bash
git clone git@github.com:<you>/hivequeen.git ~/hivequeen
```

### 3. Install for your agent tool

**Claude Code (macOS / Linux)**
```bash
bash ~/hivequeen/scripts/install/claude.sh
```

**Claude Code (Windows)**
```powershell
.\hivequeen\scripts\install\claude.ps1
```

**Codex (macOS / Linux)**
```bash
bash ~/hivequeen/scripts/install/codex.sh
```

**Codex (Windows)**
```powershell
.\hivequeen\scripts\install\codex.ps1
```

**OpenClaw (macOS / Linux)**
```bash
bash ~/hivequeen/scripts/install/openclaw.sh
```

**OpenClaw (Windows)**
```powershell
.\hivequeen\scripts\install\openclaw.ps1
```

**Hermes Agent (macOS / Linux)**
```bash
bash ~/hivequeen/scripts/install/hermes.sh
```

**Hermes Agent (Windows)**
```powershell
.\hivequeen\scripts\install\hermes.ps1
```

**Gemini CLI (macOS / Linux)**
```bash
bash ~/hivequeen/scripts/install/gemini.sh
```

**Gemini CLI (Windows)**
```powershell
.\hivequeen\scripts\install\gemini.ps1
```

**Aider (macOS / Linux)**
```bash
bash ~/hivequeen/scripts/install/aider.sh
```

**Aider (Windows)**
```powershell
.\hivequeen\scripts\install\aider.ps1
```

**Any other markdown-config CLI** (Qwen Code, OpenCode, Trae, Kimi Code, …) — see
[Supported tools](#supported-tools) and `install/generic.sh`.

Repeat on every machine. Same fork, different agent IDs, one shared brain.

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

After agents have accumulated memory, compile it into `shared/memory.md`:

```bash
bash ~/hivequeen/scripts/maintenance/compile.sh
```

This aggregates all `agents/*/memory.md` files and pushes the result.
All agents will pick it up on their next `git pull`.

---

## Directory structure

```
hivequeen/
├── AGENTS.md                   universal bootstrap (Codex, OpenClaw, others)
├── CLAUDE.md                   bootstrap for Claude Code
├── SOUL.md                     personality file (OpenClaw, Hermes)
├── queen/
│   ├── agent-rules.md          behavior rules — read-only for agents
│   └── strategy.md             decision direction — read-only for agents
├── agents/
│   └── <tool>-<hostname>/
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
    │   ├── hivequeen.sh           pre/post/stop entry
    │   ├── _match-file.py         stdin-based file matcher
    │   └── export-claude-mem.sh   optional claude-mem bridge
    └── maintenance/               ops
        ├── compile.sh             aggregate agents/* into shared/ (mechanical)
        ├── distill.py             LLM-oriented variant: print a merge prompt
        └── update.sh              pull upstream protocol layer
```

---

## File size limits

Each file has a line limit. When exceeded, split into topic files and use an index with links.

| File | Max lines |
|---|---|
| `queen/agent-rules.md` | 80 |
| `queen/strategy.md` | 80 |
| `agents/<id>/memory.md` | 200 |
| `shared/memory.md` | 500 |
| `projects/<name>.md` | 150 |

**Example — split `agents/claude-macbook/memory.md` when it hits 150 lines:**

```
agents/claude-macbook/
├── memory.md          ← becomes an index
├── user_profile.md
├── feedback_collab.md
└── project_hivequeen.md
```

`memory.md` after split:
```markdown
# MEMORY — claude-macbook

- [User Profile](user_profile.md) — role, stack, preferences
- [Collaboration](feedback_collab.md) — working style, corrections
- [Project: hivequeen](project_hivequeen.md) — goals, decisions
```

Agents read the index first, follow links only when the topic is relevant.

---

## Why no conflicts?

Each agent owns exactly one directory under `agents/`. No two agents ever write to the same file. Git conflicts are structurally impossible during normal operation.

| Path | Who writes | Conflict possible? |
|---|---|---|
| `queen/` | You (human) | No |
| `agents/<id>/` | That agent only | No |
| `shared/` | `compile.sh` only | No |

---

## Supported tools

### Native installers (known config path, tested)

| Tool | Vendor | Entry file | Install |
|---|---|---|---|
| Claude Code | Anthropic | `~/.claude/CLAUDE.md` + hooks | `bash scripts/install/claude.sh` |
| Codex CLI | OpenAI | `~/.codex/instructions.md` | `bash scripts/install/codex.sh` |
| Gemini CLI | Google | `~/.gemini/GEMINI.md` | `bash scripts/install/gemini.sh` |
| OpenClaw | open source | `~/.openclaw/workspace/AGENTS.md` | `bash scripts/install/openclaw.sh` |
| Hermes Agent | open source | `~/.hermes/SOUL.md` | `bash scripts/install/hermes.sh` |
| Aider | open source | `~/.aider-hivequeen.md` (wired via `.aider.conf.yml` `read:`) | `bash scripts/install/aider.sh` |

Only Claude Code registers session hooks for atomic per-write memory sync.
Other tools follow the session-end commit protocol written into their
bootstrap config.

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
| Cursor | `.cursor/rules/hivequeen.md` | `ln -s AGENTS.md .cursor/rules/hivequeen.md` |
| Windsurf | `.windsurf/rules/hivequeen.md` | `ln -s AGENTS.md .windsurf/rules/hivequeen.md` |
| Cline (VS Code) | `.clinerules/hivequeen.md` | `ln -s AGENTS.md .clinerules/hivequeen.md` |
| GitHub Copilot (repo) | `.github/copilot-instructions.md` | `ln -s AGENTS.md .github/copilot-instructions.md` |

### Not supported (and why)

| Tool | Reason |
|---|---|
| GitHub Copilot CLI (`gh copilot`) | Q&A style, no persistent instruction-file mechanism |
| Antigravity | IDE-first; CLI entrypoint is project-scoped and undocumented for external bootstrap |
| CloudBase AI CLI | Gateway that invokes downstream CLIs — install hivequeen on the downstream tools instead |
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
- Creates `agents/<prefix>-<hostname>/memory.md` for that tool on this machine
- Writes the hivequeen bootstrap block into `<config-path>` inside
  `<!-- hivequeen:begin -->` / `<!-- hivequeen:end -->` markers, preserving
  any existing user content
- Does NOT register hooks — the bootstrap block instructs the agent to
  `git add / commit / push` its memory dir at session end

---

## Staying up to date

When hivequeen ships improvements, pull only the protocol layer into your private queen:

```bash
bash ~/my-queen/scripts/maintenance/update.sh
```

This updates `scripts/`, `AGENTS.md`, `CLAUDE.md`, `SOUL.md`, and docs.
It **never touches** `agents/`, `queen/`, `shared/`, or `projects/` — those are yours.

---

## Inspired by

*Ender's Game* — the Formic hive mind. Every worker wired to the same queen.
No individual memory. No conflicting selves. One distributed intelligence.

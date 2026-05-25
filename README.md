# nestwork

[中文](README.zh.md) | English

Version: v0.3.0 | Protocol: 2.4

[![Protocol](https://img.shields.io/badge/protocol-2.4-blue)](AGENTS.md) [![Tools](https://img.shields.io/badge/tools-Claude%20%7C%20Codex%20%7C%20Gemini%20%7C%20Aider-green)](#supported-tools) [![Storage](https://img.shields.io/badge/storage-git-orange)](#how-it-works)

> About `agent-history-*` branches: orphan branches introduced in v2.4 hold rolling-overwrite snapshots of high-churn artefacts (e.g. `history.jsonl`). They each contain a single force-pushed commit and are not meant to be merged into `main`. Ignore GitHub's "Compare & pull request" prompt for these branches. See [AGENTS.md §12](AGENTS.md) for details.

---

## Purpose

Use a git repo as the shared external brain for your AI coding agents. Configure your working context on an office computer, then continue from your personal laptop or a cloud server without every new agent starting from "who are you?" and "where was this project left?" All your agents (Claude / Codex / Gemini / any markdown-config CLI) can read the same versioned context across sessions, machines, tools, and vendors. No plugins, no servers, no third-party dependencies. Just a private git repo.

### Problems it solves
- The agent configured on your work computer knows your rules, but your personal computer starts blank
- A cloud development host cannot see current project progress already recorded on another machine
- Switching sessions or tools makes you repeatedly explain who you are and what was decided
- Vendor-private memory (OpenAI Memory, etc.) locks you into one ecosystem

### What you get

> [!TIP]
> One private, versioned context source across sessions, personal/work devices, cloud servers, tools, and vendors.

- Memory is 100% in your own git repo. Zero vendor lock-in, works offline.
- Protocol-level multi-agent collaboration (not a feature of any specific tool)
- Stable rules, preferences, and project progress can follow you to a newly opened agent session.

### What becomes continuous

- On your work computer, an agent records approved project progress and working rules.
- At home, a new session pulls the same context instead of rebuilding your identity and project background from scratch.
- On a cloud server, another agent can continue from versioned project state and decisions.
- Over time, your decisions and reusable methods remain searchable assets you control, rather than memory trapped in one vendor.

### Why it's worth writing more

Context windows keep growing. 200K was the ceiling in 2024, 1M reached production in 2025, 1M becomes default from 2026 with 10M in labs. Three years from now an agent can read everything you've ever written in one shot, and cross-project pattern recognition starts to work.

Until then, an agent only pulls in 3–5 memory files per session. You store 100, 95% of reads look wasted. They aren't. Git storage cost is near zero, writes happen once, read value grows linearly with the window size. The 95 files no one reads today are the base layer of cross-employer, cross-project retrieval three years from now.

A few uses are independent of any agent:

- A versioned decision archive that can answer "why did I choose NestJS over Express in 2023?"
- Training material for your future personal fine-tuned model
- A cognitive layer that doesn't disappear when you switch device, employer, or tool

In practice: when you hit a non-sensitive decision, a lesson, or a cross-project methodology, write it down. Even one line. Split per v2.2 when files get long. Don't ration writes against "the agent can't read it all today." Nestwork is for portable context, not secrets or unreviewed employer-confidential material.

### Who it's for

> [!NOTE]
> Developers who work long-term with multiple AI agents, develop across machines/tools, and want to crystallize career knowledge into portable assets.

### At-a-glance summary

| Section | One-line answer |
|---|---|
| [Quickstart](#quickstart) | 3 steps: create private repo from template → clone to each machine → run installer |
| [How it works](#how-it-works) | Priority chain + session lifecycle + atomic per-write hook architecture |
| [Core design principles](#core-design-principles) | 6 non-negotiables: git-only, read/write isolation, layered memory, template + private instance, tool-neutral, evolvable protocol |
| [Comparison with other approaches](#comparison-with-other-approaches) | Why not MCP server / claude-mem / vendor memory / self-hosted DB |
| [Customize your nest](#customize-your-nest) | Edit `queen/` `projects/` `workflow/` layers |
| [v2.2 new](#v22-new-workflow-and-nestworkconfigjson) | `workflow/` cross-project knowledge layer + `nestwork.config.json` ingestion contract for external dirs |
| [Real workflow examples](#real-workflow-examples) | Multi-machine collaboration / tool migration / employer-project knowledge ingestion |
| [Compile shared memory](#compile-shared-memory-distillation) | `compile.sh` concat vs `distill.py` LLM distillation, non-destructive merge into `shared/` |
| [Directory structure](#directory-structure) / [Line limits](#file-size-limits-and-split-protocol) | Repo layout + file split protocol |
| [Supported tools](#supported-tools) | Claude Code / Codex / Gemini / Hermes / Aider / generic any markdown-config CLI + IDE plugin symlinks |
| [Staying up to date](#staying-up-to-date) | GitHub Action auto-PR or `update.sh` manual sync, never touches your private data |
| [FAQ](#faq) / [Troubleshooting](#troubleshooting) | Common questions and debugging recipes |
| [Non-goals](#non-goals) | What nestwork explicitly will not do |

---

## Quickstart

### 1. Create your private queen

On GitHub, click Use this template → Create a new repository. Set visibility to Private. Your memory belongs only to you.

> Why not Fork?
> Forks are public by default and tightly coupled to upstream. A repo created from a template is fully yours.
> When nestwork ships updates, `git merge upstream/main` would conflict with the `queen/strategy.md`, `agents/`, `shared/` you've intentionally customized. The `update.sh` script syncs only the protocol layer; your private data is never touched.

### 2. Clone to each machine

```bash
git clone git@github.com:<your-username>/nestwork.git ~/nestwork
```

### 3. Install for your agent tool

Claude Code (macOS / Linux):

```bash
bash ~/nestwork/scripts/install/claude.sh
```

Claude Code (Windows):

```powershell
.\nestwork\scripts\install\claude.ps1
```

Codex (macOS / Linux):

```bash
bash ~/nestwork/scripts/install/codex.sh
```

Codex (Windows):

```powershell
.\nestwork\scripts\install\codex.ps1
```

Gemini CLI / OpenClaw / Hermes / Aider follow the same pattern, swap `claude` for the tool name. See [Supported tools](#supported-tools) for the full list.

Run once per machine. Same queen, different agent IDs, one shared brain.

### 4. Verify cross-device continuity

Add a non-sensitive, recognizable rule or project-status note to your private queen, commit and push it, then open an installed agent on a second computer or cloud host. Ask it to summarize your current rule or project status. It should pull the repository and answer from the shared context without you repeating the setup.

Do not use API keys, secrets, or employer-confidential details as test content.

### Prompt examples

Don't want to follow the steps manually? Paste either of these into a Claude Code session:

- From scratch:
  > Read the README at https://github.com/songth1ef/nestwork. Following the Quickstart, help me create a private queen repo from the template, clone it locally, and finish Claude Code setup.

- Discover configurable features:
  > Read the README at https://github.com/songth1ef/nestwork. List all configurable nestwork features (hooks, optional sync, filters, etc.) and recommend whether to enable each based on my current machine context.

---

## How it works

### Priority chain

```
queen/agent-rules.md > queen/strategy.md > shared/memory.md > agents/*/*/memory.md > projects/*.md > workflow/*.md
```

On conflict, take the higher-priority source. Do not merge. Repository layout: see [Directory structure](#directory-structure).

### Session lifecycle

```
Session starts
  ↓
git pull --rebase                          (SessionStart hook, automatic)
  ↓
Load context by priority chain             (injected as agent system prompt)
  ↓
Agent self-orients (reads git log + strategy.md, gives state summary + next-action proposal)
  ↓
─── During work ────────────────────────
  ↓
Write/Edit triggers PreToolUse hook
  ↓
git pull --rebase (prevent overwriting remote updates)
  ↓
Perform write
  ↓
PostToolUse hook: git add/commit/push
  ↓
(push retries 3 times on failure, re-pulling each time)
─────────────────────────────────────
  ↓
Session ends
  ↓
Stop hook safety-net commit+push (no-op when clean)
  ↓
SessionEnd hook: claude-mem export + local history sync (if enabled)
```

The race window shrinks from "the whole session" to "a single write." Multiple agents on one machine almost never collide.

### Hook architecture (atomic per-write, introduced 2026-04-17)

| Hook event | Action | Purpose |
|---|---|---|
| SessionStart | pull + inject agent-rules / strategy / shared / agent memory / `workflow/*` into additionalContext | Replaces manual session-start protocol |
| PreToolUse (Write\|Edit, scoped to `agents/<id>/`) | `git pull --rebase`; conflicts → `exit 2` blocks the write | Prevent overwriting remote updates |
| PostToolUse (same scope) | `git add/commit/push`; on push failure, retry 3× (re-pulling each time) | Instant sync |
| Stop | Safety-net commit+push (no-op when clean) | Backstop |
| SessionEnd | claude-mem export + local history sync | Cross-machine reach |

Only Claude Code registers session hooks. Other tools follow the "commit on session end" protocol (see [Supported tools](#supported-tools)).

---

## Core design principles

1. Git is the only infrastructure. No servers, databases, or third-party services. Git already solves distributed storage, version control, and conflict resolution; reinventing this is a mistake.

2. Read/write isolation. Each agent owns one directory (`agents/<host>/<agent-id>/`); regular memory writes never collide with another agent. Combined with the atomic per-write hook from principle 1, even the race window inside a single Write/Edit is eliminated.

3. Layered memory and strict priority chain. Different content types live in different layers. On conflict, pick by priority; don't merge. This avoids the "all info smushed together, agent doesn't know whom to listen to" problem.

4. Template plus private instance. The public `nestwork` template evolves the protocol; each user creates a private instance via Use this template. Private data never leaks; protocol updates pulled selectively. Builds on principle 3: your private data sits in low-priority layers, so template evolution only touches the protocol layer and can't overwrite it.

5. Tool-neutral. AGENTS.md is the single bootstrap source; CLAUDE.md / SOUL.md / GEMINI.md are mirrors or links. Switch tools without losing memory.

6. The protocol itself is evolvable. `protocol-version` header uses `MAJOR.MINOR`. Private instances can pin trusted versions. Only MAJOR bumps require downstream action; MINOR is additive-compatible.

---

## Comparison with other approaches

### Limits of mainstream approaches

| Approach | Limitation |
|---|---|
| Stuff a long system prompt into agent config | No cross-device sync, no cross-tool reuse, painful to maintain |
| MCP memory server | Needs a running service, single point of failure, must be deployed per machine |
| Vendor-private memory (e.g. OpenAI Memory) | Vendor lock-in, not open, no cross-vendor migration |
| Hosted memory like claude-mem | Depends on third-party worker, may cost money, privacy-sensitive |
| Self-hosted DB + API | Heavyweight, decoupled from the agent, high maintenance |
| README/AGENT.md per project | No cross-project sharing, nowhere for user-level preferences |

nestwork's answer: use a git repo as the agent's brain. Each agent writes memory into specific directories of the repo; the next session's `git pull` makes it accessible across sessions, machines, and tools. It's not a tool, it's a protocol. Any agent that can read markdown as a system prompt can join.

### Dimension-by-dimension

| Dimension | nestwork | MCP memory server | claude-mem | Vendor memory | Self-hosted DB |
|---|---|---|---|---|---|
| Infrastructure | Git repo | Local server | Remote worker | Vendor cloud | Self-hosted service |
| Cross-device | ✅ git pull | ❌ Needs deployment | ✅ but worker-dependent | ✅ via vendor account | Depends |
| Cross-tool | ✅ Any markdown-config agent | Partial (needs MCP client) | Claude only | ❌ Vendor lock | Depends |
| Cross-account migration | ✅ Just change remote | ✅ | Partial | ❌ | ✅ |
| Multi-agent collaboration | ✅ Protocol-level | Needs coordination | Single agent | Single vendor | Depends |
| Offline | ✅ | Depends | ❌ | ❌ | Depends |
| Data ownership | 100% your git repo | 100% local | Third-party worker | Vendor | Yours |
| Maintenance | Low (you already know git) | Medium (needs MCP literacy) | Medium (worker-dependent) | Zero (but locked) | High |
| Privacy | Private repo is enough | Depends on deployment | Third-party risk | Depends on terms | Depends |

See [docs/comparisons/claude-mem.md](docs/comparisons/claude-mem.md) for details.

---

## Customize your nest

Your rules: edit `queen/agent-rules.md`. Behavior boundaries that apply to every agent (e.g. "always answer in Chinese", "lead with conclusion before details"). Highest priority; cannot be overridden by any later context.

Your strategy: edit `queen/strategy.md`. Current-stage goals and decision direction. For example, "prioritize small, verifiable, monetizable tools" or "don't build complex systems before validating demand."

Your projects: add `projects/<project-name>.md`. Auto-loaded context when working on that project. Naming, module boundaries, tech-stack rationale, lessons learned, etc.

Your workflow (new in v2.2+): add `workflow/<topic>.md`. Cross-project portable workflow knowledge: coding disciplines, tool preferences, methodologies, migration guides. See next section.

---

## v2.2 new: workflow/ and nestwork.config.json

### Why we need `workflow/`

Before v2.2, nestwork had 4 context layers: `queen/` `shared/` `agents/` `projects/`. One place was missing: cross-project portable user-level knowledge.

Examples:

- Estimate effort by AI speed, not by person-months
- Use skeleton screens for loading UI; v-loading when re-fetching with existing data
- When initializing a new repo, scaffold 5 docs (AGENT.md + conventions.md + domain.md + architecture.md + lessons.md)
- A 30-minute checklist for restoring your workflow on a new machine

These aren't facts about the user (→ `shared/`), aren't project-specific (→ `projects/`), and aren't behavior rules (→ `queen/`). They deserve to be preserved across employers, projects, and machines. `workflow/` is for that layer.

### What `workflow/` is for

| Belongs | Doesn't belong |
|---|---|
| Cross-project coding disciplines, estimation rules | Project-specific business rules → `projects/` |
| Tool-stack preferences and setup conventions | Stable user facts across agents → `shared/` |
| Skill assets, prompt templates | Single-agent transient observations → `agents/` |
| Migration / cross-machine deployment guides | One-off task notes |
| Methodology useful in multiple repos | Employer-confidential info (must not exist in this repo in any form) |

The test: "Will this still apply after I change employers?" Yes → `workflow/`; No → somewhere else.

### `nestwork.config.json`: ingestion contract for external directories

Some working directory of yours (e.g. `~/work/some-employer-project/`) contains content worth ingesting into nestwork's `projects/` or `workflow/`, but it also has employer secrets, client names, internal codenames. You can't just copy it.

`nestwork.config.json` is a metadata file placed in the source working directory (not inside nestwork) declaring:

- Which category this directory's content can be ingested into
- The required level of desensitization
- Which terms to redact (employer names, client names, internal codenames)

Minimal example (place at the root of your working directory):

```json
{
  "$schema": "https://github.com/songth1ef/nestwork/schemas/nestwork.config.schema.json",
  "version": "1.0",
  "ingest": {
    "target": "projects",
    "name": "some-project"
  },
  "desensitize": {
    "level": "strong",
    "custom_rules": [
      "<your-employer-name>",
      "<internal-codename>",
      "<client-name>"
    ]
  }
}
```

Field semantics:

| Field | Meaning |
|---|---|
| `ingest.target` | Which category receives content: `projects` / `workflow` / `null` (not ingestable) |
| `ingest.name` | Destination filename |
| `desensitize.level` | `none` (no transformation) / `weak` (pattern replace via custom_rules) / `strong` (AI semantic desensitization + custom_rules) |
| `desensitize.custom_rules` | User-defined sensitive terms, layered on top of the general methodology |

Key constraints:

- The config file lives only in the source directory, never inside nestwork
- Default `desensitize.level: "strong"`
- If an agent detects ingestable content but no config exists, it must stop and prompt the user to create one; never ingest silently
- Ingestion is one-way: source dir → private nest (never reverse-flows from private nest to upstream)

Full rules: [docs/workflow-protocol.md](docs/workflow-protocol.md) and `AGENTS.md` §8, §9.

### Desensitization methodology

Upstream nestwork provides only the methodology and prompt template ([docs/desensitization-prompt.md](docs/desensitization-prompt.md)). No specific employer/client/codename names. Specifics live in each user's `nestwork.config.json` `custom_rules`.

`strong`-level desensitization invokes an AI (Claude Haiku is sufficient and cheap) following the prompt template:

1. Replace every `custom_rules` hit with a placeholder (`<EMPLOYER>`, `<CLIENT-A>`, etc.)
2. Identify content that leaks confidential information without naming it directly (e.g. internal API structure, unreleased product features) and rewrite
3. Preserve portable methodology
4. Output structured JSON (desensitized content + redaction record + flags for human review)
5. Write into nestwork only after human review

---

## Real workflow examples

### Scenario: multi-machine collaborative development

You use Claude Code on an office computer, a personal laptop, and optionally a cloud development host. Each machine has your private queen cloned.

Monday morning (office computer):

- Launch Claude Code, SessionStart hook auto-`git pull` and injects context
- You say "continue last night's NestJS module work"
- Claude reads `agents/macbook/claude-xxx/memory.md`, sees yesterday's progress
- Also loads `shared/memory.md`, knows your stack preferences (Vue 3 + NestJS)
- Picks up directly without re-explaining

Same evening (personal laptop or cloud host):

- Launch Claude Code, auto-pull
- Agent sees the morning updates from `agents/macbook/claude-xxx/` (a different machine's agent, but synced via git)
- You switch to a different task; the agent writes to its own `agents/desktop/claude-yyy/`

Two agents never write each other's directories, yet they share full context via git.

### Scenario: tool migration

One day you want to try Codex CLI.

```bash
bash ~/nestwork/scripts/install/codex.sh
```

Codex starts up, reads `~/.codex/AGENTS.md` (the installer injected the nestwork bootstrap there). It will:

- pull your queen
- read `queen/`, `shared/`, and its own `agents/<host>/codex/memory.md`
- know your preferences, past decisions, current project state

Memory isn't in any vendor; it's in your git repo. The cost of switching tools is near zero.

### Scenario: ingest employer-project knowledge into the nest (v2.2+)

You spot a worth-recording architectural pattern in an employer project (e.g. NestJS module organization conventions).

1. Create `nestwork.config.json` at the project root (see example above), put the employer name and internal codenames in `custom_rules`
2. Tell Claude Code to ingest the methodology:
   > Ingest the XX pattern from this project into mynestwork's `projects/<project>.md`, desensitizing per nestwork.config.json
3. The agent reads the config, runs the desensitization prompt, produces a draft
4. You review before it's written

The employer name never appears in the nest repo; the methodology is preserved. When you change employers, this methodology is still with you.

---

## Compile shared memory (distillation)

When agents have accumulated enough memory, merge it into `shared/memory.md` via one of:

```bash
# Pure concat: concatenate agents/*/memory.md, commit, push
bash ~/nestwork/scripts/maintenance/compile.sh

# LLM version, vendor-agnostic: prints a distillation prompt for you to feed any agent session
python3 ~/nestwork/scripts/maintenance/distill.py

# Codex one-shot manual distill: aggregate all agent memory, write back to shared/memory.md,
# then commit, push. Replace <your-profile> with the Codex profile available on this
# machine; if the default config is correct, you can omit --profile.
python3 ~/nestwork/scripts/maintenance/distill.py --run-codex --profile <your-profile>

# Preview only, don't write
python3 ~/nestwork/scripts/maintenance/distill.py --run-codex --profile <your-profile> --dry-run
```

None of these modify the original agent memory. `--run-codex` updates only `shared/memory.md`, with commit message `memory: distill shared`. All agents see the new `shared/memory.md` on their next `git pull`.

### Distillation design tradeoffs

- Shared is a union, not an intersection. Never drop any agent's unique observation.
- Non-destructive. Each agent's private memory is unchanged; distillation is read-only.
- Sub-agent review required. Checks for sensitive data, factual errors, contradictions, outdated entries.
- Human confirmation required. Sub-agent reports only; the human merges.
- Never delete. Only merge and add; preserve history.

---

## Directory structure

```
nestwork/
├── AGENTS.md                   Single bootstrap source (Codex, OpenClaw, Gemini, …)
├── CLAUDE.md                   Line-by-line mirror of AGENTS.md (Claude Code reads this name)
├── SOUL.md                     Hermes' short persona file
├── queen/
│   ├── agent-rules.md          Behavior rules, agent read-only
│   └── strategy.md             Decision direction, agent read-only
├── agents/
│   └── <host>/<agent-id>/
│       └── memory.md           That agent's private memory
├── shared/
│   └── memory.md               Cross-agent compiled memory
├── projects/
│   └── <project>.md            Project context
├── workflow/                   v2.2+: cross-project portable workflow knowledge
│   ├── README.md
│   └── <topic>.md
├── docs/                       Protocol methodology and external docs
│   ├── workflow-protocol.md       v2.2 workflow deep dive
│   ├── desensitization-prompt.md  AI desensitization prompt template
│   ├── ai-agent-memory.md
│   ├── claude-code-memory.md
│   ├── codex-persistent-memory.md
│   ├── git-native-memory-protocol.md
│   ├── agents-md-best-practices.md
│   └── faq.md
├── schemas/
│   └── nestwork.config.schema.json   v2.2 config JSON Schema
└── scripts/
    ├── install/                   Per-tool installers
    │   ├── claude.{sh,ps1}
    │   ├── codex.{sh,ps1}
    │   ├── gemini.{sh,ps1}
    │   ├── hermes.{sh,ps1}
    │   ├── openclaw.{sh,ps1}
    │   ├── aider.{sh,ps1}
    │   ├── generic.{sh,ps1}       Any markdown-config CLI
    │   ├── _bootstrap.py          Shared bootstrap injector
    │   └── _hooks.py              Shared hook registrar (Claude Code)
    ├── hooks/                     Runtime hooks
    │   ├── nestwork.sh            Unified pre/post/stop entrypoint
    │   ├── _match-file.py         stdin file matcher
    │   ├── export-claude-mem.sh   Optional claude-mem bridge
    │   ├── sync-local-history.sh  Local history sync (wrapper, optional)
    │   └── sync-local-history.py  Local history sync (worker, optional)
    └── maintenance/               Operations
        ├── compile.sh             Aggregate agents/* into shared/ (pure concat)
        ├── distill.py             Print prompt or trigger Codex distillation
        ├── sync-claude-md.sh      Regenerate CLAUDE.md from AGENTS.md
        └── update.sh              Pull upstream protocol layer
```

---

## File size limits and split protocol

### Universal rule (v2.2+)

Any markdown file in the repo, when it exceeds the limit, is split using the same pattern: the original filename becomes a folder, the original file becomes an index (or `<folder>/index.md`), and content is split by topic.

Example: `plan-all.md` (1200 lines) → `plan-all.md` (index) + `plan/plan-a.md` / `plan/plan-b.md` / `plan/plan-c.md`.

Files not in the table below use the defaults: soft limit 500 lines (start considering a split), hard limit 1000 lines (must split before next write).

### Specific limits

| File | Max lines |
|---|---|
| `queen/agent-rules.md` | 80 |
| `queen/strategy.md` | 80 |
| `agents/<host>/<agent-id>/memory.md` | 200 |
| `shared/memory.md` | 500 |
| `projects/<name>.md` | 150 |
| `workflow/<topic>.md` | 200 |

Example. Splitting `agents/macbook/claude/memory.md` after it hits the limit:

```
agents/macbook/claude/
├── memory.md          ← becomes the index
├── user_profile.md
├── feedback_collab.md
└── project_nestwork.md
```

The split `memory.md`:

```markdown
# MEMORY — claude-macbook

- [User profile](user_profile.md): role, stack, preferences
- [Collaboration habits](feedback_collab.md): workflow, corrections
- [Project: nestwork](project_nestwork.md): goals, decisions
```

The agent reads the index first, then follows links to relevant topic files.

### Why line limits?

LLM context windows are large, but attention degrades with token count. Stuffing a 5000-line `memory.md` in wholesale is poorly utilized. Splitting into topic files plus an index lets an agent follow only the relevant context.

The next optimization direction is generated indexes and selective loading by active project or topic, so a growing nest does not become a growing startup prompt.

---

## Supported tools

### Native installers (config path is well-defined)

| Tool | Vendor | Entry file | Install | Adoption |
|---|---|---|---|---|
| Claude Code | Anthropic | `~/.claude/CLAUDE.md` + hooks | `bash scripts/install/claude.sh` | Adopted, daily-driven |
| Codex CLI | OpenAI | `~/.codex/AGENTS.md` + compatibility entry | `bash scripts/install/codex.sh` | Adopted, daily-driven |
| Gemini CLI | Google | `~/.gemini/GEMINI.md` | `bash scripts/install/gemini.sh` | Entry exists, untested by author |
| OpenClaw | Open source | `~/.openclaw/workspace/AGENTS.md` | `bash scripts/install/openclaw.sh` | Entry exists, untested by author |
| Hermes Agent | Open source | `~/.hermes/SOUL.md` | `bash scripts/install/hermes.sh` | Entry exists, untested by author |
| Aider | Open source | `~/.aider-nestwork.md` (via `.aider.conf.yml` `read:`) | `bash scripts/install/aider.sh` | Entry exists, untested by author |

Only Claude Code registers session hooks for atomic per-write. Other tools follow the "commit on session end" protocol baked into the bootstrap config.

### Optional: capture local tool history

Claude Code keeps prompt history and plan artifacts under `~/.claude/`; Codex keeps prompt history under `~/.codex/`. These can be mirrored into `agents/<host>/<id>/local/` for cross-machine portability.

Enabled per-host, no env vars or reinstall needed. Create `agents/<host>/settings.json` for the current machine's host directory in your queen:

```json
{ "sync_local_history": true }
```

Default `false`. The switch is git-versioned with the queen; each machine's setting is independent.

When enabled, sync sources:

| Source | Destination | Notes |
|---|---|---|
| `~/.claude/history.jsonl` | `local/history.jsonl` | Desensitized: drop `pastedContents`, normalize `$HOME` paths, replace `sk-*`/`ghp_*`/`Bearer …` with `<REDACTED>` |
| `~/.claude/plans/` | `local/plans/` | Plan-mode artifacts, mirrored as-is |
| `~/.codex/history.jsonl` | `local/history.jsonl` | Codex agents only, same desensitization rules |

`todos/` and `tasks/` excluded: 99% are empty placeholders pre-allocated by session UUID.

### Via `install/generic.sh` (you confirm the config path)

Any "reads a markdown file as system prompt at startup" CLI can be wired up in one command:

```bash
bash scripts/install/generic.sh <prefix> <config-path>
```

| Tool | Vendor | Suggested prefix |
|---|---|---|
| Qwen Code | Alibaba Tongyi | `qwen` |
| OpenCode | Open source | `opencode` |
| CodeBuddy Code | Tencent | `codebuddy` |
| iFlow CLI | Alibaba iFlow | `iflow` |
| Trae CLI / Solo | ByteDance | `trae` |
| Qoder | Alibaba | `qoder` |
| Kimi Code CLI | Moonshot | `kimi` |
| Tongyi Lingma CLI | Alibaba Cloud | `lingma` |

> Tip: Qwen Code is a fork of Gemini CLI and may already accept `~/.gemini/GEMINI.md`. Try `install/gemini.sh` first.

### Workspace-level (IDE plugins, symlinks)

| Tool | Target path | Install |
|---|---|---|
| Cursor | `.cursor/rules/nestwork.md` | `ln -s AGENTS.md .cursor/rules/nestwork.md` |
| Windsurf | `.windsurf/rules/nestwork.md` | `ln -s AGENTS.md .windsurf/rules/nestwork.md` |
| Cline (VS Code) | `.clinerules/nestwork.md` | `ln -s AGENTS.md .clinerules/nestwork.md` |
| GitHub Copilot (repo-level) | `.github/copilot-instructions.md` | `ln -s AGENTS.md .github/copilot-instructions.md` |

### Unsupported (why)

| Tool | Reason |
|---|---|
| GitHub Copilot CLI (`gh copilot`) | Q&A pattern, no persistent-instruction file mechanism |
| Antigravity | IDE-first, CLI entry is project-level, no public bootstrap mechanism |
| CloudBase AI CLI | Gateway-style, calls downstream CLIs. Install nestwork on the downstream tool instead. |
| ChatDev | Simulates a "virtual software company" workflow, not a persistent single-agent loop |

---

## Staying up to date

Two paths, neither touches your private data (`agents/`, `queen/`, `shared/`, `projects/`, `workflow/<topic>.md`).

### Manual (recommended default)

When you want the latest protocol-layer updates, open Actions → Sync Nestwork upstream → Run workflow.

Most repos don't need to follow upstream daily; manual review keeps protocol changes explicit and controllable.

### Automatic (optional)

The `.github/workflows/sync-upstream.yml` in your private repo can run every Monday at 03:00 UTC, opening a PR to your `main` whenever there's a diff. You review the diff and merge.

Auto-sync is off by default. To enable:

1. Settings → Secrets and variables → Actions → Variables
2. Create a repository variable `NESTWORK_AUTO_SYNC`
3. Set value `true`

PR create/update/reopen uses the GitHub REST API, no longer the `gh pr ...` GraphQL path. If the default token is blocked, add an Actions secret `NESTWORK_SYNC_TOKEN` and the workflow will prefer it.

GitHub forbids `GITHUB_TOKEN` from pushing commits that modify workflow files, so the CI path does not overwrite `.github/workflows/`; workflow changes go through the manual path below.

### Manual protocol-layer refresh

```bash
bash ~/my-nest/scripts/maintenance/update.sh
```

Covers `scripts/`, `.github/workflows/`, `AGENTS.md`, `CLAUDE.md`, `SOUL.md`, the bilingual READMEs, `docs/`, `schemas/`, plus `workflow/README.md` + `workflow/_template.md`. Does not touch your private content under `workflow/`.

---

## FAQ

### Why a template instead of a fork?

Forks are public by default and tightly coupled to upstream. Each upstream update would conflict with your private `queen/`, `agents/`, `shared/`. A template-created private repo has no shared git history; you sync the protocol layer selectively via `git checkout upstream/main -- <files>`, leaving private data untouched.

### Will my employer's code be ingested into the nest?

No. Only if you explicitly create a `nestwork.config.json` at the project root and tell the agent to ingest. Even then, `desensitize.level: "strong"` invokes AI desensitization. Employer/client/codename names are replaced with placeholders, and content is written only after human review.

### Can tools other than Claude Code use nestwork?

Yes. Any "reads a markdown file as system prompt at startup" CLI can use `install/generic.sh`. Only Claude Code has the hook system for atomic per-write; other tools rely on "commit on session end", with a slightly larger race window but rarely an issue in practice.

### Do multiple agents writing concurrently cause conflicts?

Each agent owns a directory under `agents/<host>/<agent-id>/`; regular memory writes don't collide. Possible conflict paths:

| Path | Who writes | Conflict possible? |
|---|---|---|
| `queen/` | You (human) | Won't (you have only two hands) |
| `agents/<host>/<agent-id>/` | Only that agent | Won't for regular memory writes |
| `shared/` | Only explicit `compile.sh` / `distill.py --run-codex` | Won't during regular agent memory writes |
| `projects/` | Agent or human | Multiple agents writing theoretically can; PreToolUse hook's `git pull --rebase` greatly reduces this |
| `workflow/` | Agent or human | Same as above |

PreToolUse hook does `git pull --rebase` before each write, shrinking the race window to a single write. Two machines writing the same file in the same second is the only collision; uncommon in practice. If it happens, the hook `exit 2`s the write and prompts manual merge.

### Where does `shared/memory.md` come from?

Not automatically. You explicitly trigger distillation:

- `compile.sh`: pure concat of all agent memory
- `distill.py`: LLM distillation (recommended)

The distillation calls a sub-agent for review (sensitive data, factual contradictions, outdated entries) and you confirm the merge. Goal: non-destructive. Each agent's private memory is unchanged.

### Can I store API keys in nestwork?

No. Even in a private repo. GitHub vulnerabilities, account compromise, mistaken collaborator permissions all leak. Use environment variables or a dedicated secret store.

### Will the protocol break compatibility often?

No. `protocol-version` uses `MAJOR.MINOR`. MAJOR changes need downstream action and should be avoided; MINOR is additive-compatible. v1 → v2.0 → v2.1 → v2.2 are all additive.

### How to handle multilingual / mixed-language content?

- `queen/agent-rules.md` can declare "default to Chinese" as a behavior rule
- agent memory / shared memory can mix languages; agents handle it naturally
- The protocol's field names, directory structure, and filenames are English; not changeable
- Naming convention: keep technical terms in English, behavior rules and domain knowledge in your native language

### Can I swap git for another storage?

No. Git is the core of nestwork, not optional. If you don't know git, nestwork isn't a good fit.

---

## Troubleshooting

### `bash scripts/install/claude.sh` fails

- macOS / Linux: check that `~/.claude/` exists and is writable.
- Windows Git Bash: `hostname -s` is unsupported; the installer falls back to `hostname | cut -d. -f1`. If that still fails, set `NESTWORK_HOST=desktop-xxx` manually.

### Hooks installed, but commits aren't pushed

Check in this order:

1. `git -C $NESTWORK_PATH remote -v`, is the remote correct?
2. `cat ~/.claude/settings.json`, are hooks registered?
3. `cat scripts/hooks/nestwork.sh`, does the tail invoke push?
4. `git push` manually, does it require interactive credentials? (Hooks run non-interactively.)

### Push retries 3× and still fails

Usually expired GitHub credentials.

```bash
git -C $NESTWORK_PATH push  # see specific error
# Credential issue: gh auth login or reset SSH key
```

### `agents/<host>/<agent-id>/memory.md` has a conflict

The PreToolUse hook should have prevented this. If it happens, the hook didn't fire or you edited manually. Resolve manually:

```bash
git -C $NESTWORK_PATH status         # see conflicting files
# Edit files to resolve
git -C $NESTWORK_PATH add agents/<host>/<agent-id>/
git -C $NESTWORK_PATH rebase --continue
```

Per protocol §5, conflicts in `agents/<host>/<agent-id>/` should take local (this agent owns the directory).

### Claude Code starts but doesn't auto-pull / inject context

Check whether the SessionStart hook is registered:

```bash
cat ~/.claude/settings.json | grep -A 5 SessionStart
```

If missing, re-run the installer: `bash scripts/install/claude.sh`.

### Agent ID is inconsistent across machines

Check `~/.nestwork_id`:

```bash
cat ~/.nestwork_id
```

Each machine's `~/.nestwork_id` should differ (`<tool>-<4-char-random>`). If they're the same, you copied dotfiles. Delete the file on the new machine and let the installer regenerate.

### I want to try it without committing my private data to GitHub

Fully local:

```bash
git clone git@github.com:songth1ef/nestwork.git ~/local-nest
# Don't push to any remote
```

Or change the remote to a self-hosted git:

```bash
git remote set-url origin <your-private-git>
```

---

## Non-goals

To keep nestwork lightweight, protocol-neutral, and git-only, the following are explicitly out of scope:

- Team-level ACL / permission management: repo visibility relies on GitHub/GitLab's own permissions; nestwork adds no extra access-control layer
- Server-side API / sync service: there will never be a server; all sync is via git push/pull
- End-to-end encryption: private repos rely on GitHub's security model by default; high-sensitivity content shouldn't be in nestwork (use a secret store)
- Real-time collaboration / live notifications: git is asynchronous; if two agents truly write the same file in the same second, the PreToolUse hook blocks rather than locks in real time
- Cross-vendor LLM call abstraction: distillation uses Codex but doesn't try to unify all LLM APIs; agents read markdown when switching tools
- GUI / web app: pure file protocol; all interaction is via the agent or git CLI
- Automated onboarding / interactive tutorial: README is the entry; no interactive wizard

If you need any of the above, nestwork may not be the right fit. Pick a dedicated tool for that need.

---

## Protocol evolution

- v2.0 (2026-04-17): `agents/` reorganized by host (`agents/<host>/<agent-id>/`); atomic per-write hook architecture
- v2.1 (2026-04-21): SessionStart hook auto-injects context
- v2.2 (2026-05-07): Added `workflow/` context layer + `nestwork.config.json` external-directory ingestion contract + universal markdown split rule
- v2.3 (2026-05-08): Added §10 nestwork-vs-repo-5-doc boundary (`projects/<name>.md` 5-field convention + `decisions/` for protocol-level ADRs + `workflow/lessons.md` for cross-repo lessons); SessionStart hook now auto-checks upstream protocol version (24h cache, advisory only, never auto-applies)
- v2.4 (2026-05-08): Added §12 orphan-branch strategy for high-churn artefacts. `agents/*/*/local/` is now in default `.gitignore`; `agent-history-<host>-<agent-id>` orphan branches hold a single rolling-overwrite snapshot (force-push). Fixes unbounded main-history bloat when `sync_local_history` is enabled (observed mynestwork: 177 MB → 1.6 MB).

Full protocol: [AGENTS.md](AGENTS.md).

---

## Related docs

- [AGENTS.md](AGENTS.md): Protocol spec (authoritative; agents read this on startup)
- [docs/workflow-protocol.md](docs/workflow-protocol.md): v2.2 workflow deep dive
- [docs/desensitization-prompt.md](docs/desensitization-prompt.md): AI desensitization methodology
- [schemas/nestwork.config.schema.json](schemas/nestwork.config.schema.json): `nestwork.config.json` JSON Schema
- [docs/ai-agent-memory.md](docs/ai-agent-memory.md)
- [docs/claude-code-memory.md](docs/claude-code-memory.md)
- [docs/codex-persistent-memory.md](docs/codex-persistent-memory.md)
- [docs/git-native-memory-protocol.md](docs/git-native-memory-protocol.md)
- [docs/agents-md-best-practices.md](docs/agents-md-best-practices.md)
- [docs/shared-context-for-ai-coding-agents.md](docs/shared-context-for-ai-coding-agents.md)
- [docs/faq.md](docs/faq.md)
- [docs/comparisons/claude-mem.md](docs/comparisons/claude-mem.md)

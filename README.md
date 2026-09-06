# nestwork

> Protocol 3.0: only core rules and small shared/agent resident summaries load at startup. History and project context are on demand. Existing users must refresh their tool bootstrap; [migration guide](docs/context-loading.md).

```text
          ♕           //  _   __ ______ _____ ______ _       __ ____  ____  __ __
       \  |  /       //  / | / // ____// ___//_  __/| |     / // __ \/ __ \/ //_/
        .-♡-.       //  /  |/ // __/   \__ \  / /   | | /| / // / / / /_/ / ,<
      ʚ(˶ᵔᴗᵔ˶)ɞ    //  / /|  // /___ ___/ / / /    | |/ |/ // /_/ / _, _/ /| |
       /づ Q づ\   //  /_/ |_//_____//____/ /_/     |__/|__/ \____/_/ |_/_/ |_|
      ╰─╯ ♡ ╰─╯       ╱ ╱ ╱       Y O U R   A G E N T S   R E M E M B E R       ╱ ╱ ╱
        ʚ   ɞ        [ HOME ] ⇄ [ WORK ] ⇄ [ CLOUD ]
```

[中文](README.zh.md) | English

Version: v0.6.0 | Protocol: 3.0

[![Protocol](https://img.shields.io/badge/protocol-3.0-blue)](AGENTS.md) [![Tools](https://img.shields.io/badge/tools-Claude%20%7C%20Codex%20%7C%20Gemini%20%7C%20Kimi%20%7C%20Hermes%20%7C%20OpenClaw-green)](#supported-tools) [![Storage](https://img.shields.io/badge/storage-git-orange)](#how-it-works)

**nestwork is a git-native memory protocol for AI coding agents: persistent memory and shared context that live in your own git repo.** Your AI agent memory follows you across sessions, machines, and tools.

---

## What problem it solves

Every time you open an AI coding agent on a new machine, in a new session, or after switching tools, it starts from zero — "who are you?", "where was this project left?" The agent on your work computer knows your rules; the one on your laptop doesn't. A cloud host can't see progress recorded elsewhere. And vendor-private memory locks you into one ecosystem.

nestwork fixes this with one idea: **use a private git repo as the shared brain for all your agents.** Configure your context once, then every agent — Claude, Codex, Gemini, or any markdown-config CLI — reads the same versioned context across sessions, machines, tools, and vendors. No plugins, no servers, no third-party dependencies. Just a private git repo.

- The agent on your work computer knows your rules, but your personal computer starts blank
- A cloud development host cannot see project progress already recorded on another machine
- Switching sessions or tools makes you repeatedly re-explain who you are and what was decided
- Vendor-private memory (OpenAI Memory, etc.) locks you into one ecosystem

---

## Install

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

Gemini CLI / Kimi Code / OpenClaw / Hermes follow the same pattern, swap `claude` for the tool name. See [Supported tools](#supported-tools) for the full list.

Run once per machine. Same queen, different agent IDs, one shared brain.

### 4. Verify cross-device continuity

Add a non-sensitive, recognizable rule or project-status note to your private queen, commit and push it, then open an installed agent on a second computer or cloud host. Ask it to summarize your current rule or project status. It should pull the repository and answer from the shared context without you repeating the setup.

Do not use API keys, secrets, or employer-confidential details as test content.

### Prompt examples

Don't want to follow the steps manually? Paste either of these into a Claude Code session:

- From scratch:
  > Read the README at https://github.com/songth1ef/nestwork. Following the install steps, help me create a private queen repo from the template, clone it locally, and finish Claude Code setup.

- Discover configurable features:
  > Read the README at https://github.com/songth1ef/nestwork. List all configurable nestwork features (hooks, optional sync, filters, etc.) and recommend whether to enable each based on my current machine context.

### Uninstall

Every installer has a mirror uninstaller under `scripts/uninstall/`. It **unbinds only**: the bootstrap block is removed from the tool's startup file and the nestwork hooks are deregistered, so the tool stops loading nestwork at session start. Nothing else is touched — your memory (`agents/<host>/<agent-id>/`), identity files (`~/.nestwork_host`, `~/.nestwork_id_<tool>`), and any content of your own in the same config files all stay in place. Re-running the installer restores the exact same agent identity.

```bash
bash ~/nestwork/scripts/uninstall/claude.sh     # macOS / Linux
```

```powershell
.\nestwork\scripts\uninstall\claude.ps1         # Windows
```

Same pattern for `codex` / `gemini` / `hermes` / `openclaw` / `generic`. Pass `--purge-identity` (PowerShell: `-PurgeIdentity`) if you also want to drop that tool's agent id, so a future install starts as a brand-new agent.

---

## How to use

After install, there's nothing new to learn — you use your agent the way you already do.

- **It remembers, automatically.** Open a session on any machine and the agent pulls your nest, loading your rules, preferences, and where each project was left. No "who are you?" re-introduction.
- **You decide what's kept.** When you reach a decision, a lesson, or a change in project status, tell the agent to record it (or accept its suggestion to). It writes to its own `agents/<host>/<agent-id>/` directory and pushes — versioned, and yours.
- **It follows you across machines and tools.** Move to your laptop, a cloud host, or from Claude to Codex; the next session reads the same context. Memory lives in your git repo, not a vendor.

In a typical week:

- Office computer: an agent records approved project progress and working rules.
- At home: a new session continues from the same context instead of rebuilding it.
- Cloud server: another agent picks up from versioned project state and decisions.

The git sync, the priority chain, and the hooks all run automatically. See [How it works](#how-it-works) for the mechanics.

---

## What you get

> [!TIP]
> One private, versioned context source across sessions, personal/work devices, cloud servers, tools, and vendors.

- Memory is 100% in your own git repo. Zero vendor lock-in, works offline.
- Protocol-level multi-agent collaboration (not a feature of any specific tool)
- Stable rules, preferences, and project progress can follow you to a newly opened agent session.

---

## Why it's worth keeping history

Retention and loading are separate. Protocol 3.0 starts with core rules and small
shared/agent resident summaries. Historical memory, strategy, projects and
workflows are searched for the current task, not loaded in full at startup.

Keep decisions, lessons and methods with lasting value in the on-demand tier,
organized for retrieval. Promote only reviewed, stable facts and essential
boundaries needed across tasks into resident summaries.

Missing summaries do not trigger full-history reads, and links do not require
recursive loading. Follow file-splitting rules and resident byte budgets during
maintenance; see [loading and migration](docs/context-loading.md). Nestwork is for
portable context, not secrets or unreviewed employer-confidential material.

---

## Who it's for

> [!NOTE]
> Developers who work long-term with multiple AI agents, develop across machines/tools, and want to crystallize career knowledge into portable assets.

---

## At-a-glance summary

| Section | One-line answer |
|---|---|
| [Install](#install) | 3 steps: create private repo from template → clone to each machine → run installer |
| [How it works](#how-it-works) | Priority chain + session lifecycle + atomic per-write hook architecture |
| [Core design principles](#core-design-principles) | 6 non-negotiables: git-only, read/write isolation, layered memory, template + private instance, tool-neutral, evolvable protocol |
| [Comparison with other approaches](#comparison-with-other-approaches) | Why not MCP server / claude-mem / vendor memory / self-hosted DB |
| [Customize your nest](#customize-your-nest) | Edit `queen/` `projects/` `workflow/` layers |
| [Context layers](#context-layers-workflow-and-external-ingestion) | `workflow/` cross-project knowledge layer + `nestwork.config.json` ingestion contract for external dirs |
| [Real workflow examples](#real-workflow-examples) | Multi-machine collaboration / tool migration / employer-project knowledge ingestion |
| [Compile shared memory](#compile-shared-memory-distillation) | `compile.sh` concat vs `distill.py` LLM distillation, non-destructive merge into `shared/` |
| [Agent mailbox](#agent-mailbox-inter-agent-messaging) | git-native inter-agent messaging: single-writer outbox, available on demand, zero external deps |
| [Directory structure](#directory-structure) / [Line limits](#file-size-limits-and-split-protocol) | Repo layout + file split protocol |
| [Supported tools](#supported-tools) | Claude Code / Codex / Gemini / Kimi Code / Hermes / OpenClaw / generic any markdown-config CLI + IDE plugin symlinks |
| [Staying up to date](#staying-up-to-date) | GitHub Action auto-PR or `update.sh` manual sync, never touches your private data |
| [FAQ](#faq) / [Troubleshooting](#troubleshooting) | Common questions and debugging recipes |
| [Non-goals](#non-goals) | What nestwork explicitly will not do |

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
Load core rules + optional shared/agent resident.md (paths from hook)
  ↓
Follow current task; retrieve history / strategy / git log only when relevant
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
| SessionStart | pull + emit resident file paths; history / workflow / inbox on demand | Replaces manual session-start protocol |
| PreToolUse (Write\|Edit, scoped to `agents/<id>/`) | `git pull --rebase`; conflicts → `exit 2` blocks the write | Prevent overwriting remote updates |
| PostToolUse (same scope) | `git add/commit/push`; on push failure, retry 3× (re-pulling each time) | Instant sync |
| Stop | Safety-net commit+push (no-op when clean) | Backstop |
| SessionEnd | claude-mem export + local history sync | Cross-machine reach |

Claude Code and Kimi Code register per-write memory synchronization hooks. Codex registers a SessionEnd hook only for optional local-history snapshots; Codex memory edits still follow the manual commit/push bootstrap protocol. Other tools follow their bootstrap protocol (see [Supported tools](#supported-tools)).

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

## Context layers: `workflow/` and external ingestion

Beyond the four core layers (`queen/` `shared/` `agents/` `projects/`), nestwork has a fifth for **cross-project portable knowledge**: coding disciplines, estimation rules, tool-stack preferences, migration guides — the things that survive a change of employer.

The test: *"Will this still apply after I change employers?"* Yes → `workflow/`; no → `projects/` (project-specific), `shared/` (stable facts about you), or `queen/` (behaviour rules).

When content from an outside working directory is worth absorbing, that directory declares a `nestwork.config.json` stating which category may receive it and how aggressively it must be desensitised. The config lives **only in the source directory, never inside nestwork**, it defaults to `strong` desensitisation, and an agent that finds ingestable content without a config must stop and ask rather than ingest silently.

Ingestion is one-way: source directory → your private nest. Nothing ever auto-flows from a private nest back upstream.

- Layer rules and the full ingestion contract: [AGENTS.md](AGENTS.md) §8, §9
- Deep dive with examples: [docs/workflow-protocol.md](docs/workflow-protocol.md)
- Config schema: [schemas/nestwork.config.schema.json](schemas/nestwork.config.schema.json)
- Desensitisation prompt template: [docs/desensitization-prompt.md](docs/desensitization-prompt.md) — upstream ships the methodology only; employer and client names live in your own `custom_rules`, never here

---

## Real workflow examples

### Scenario: multi-machine collaborative development

You use Claude Code on an office computer, a personal laptop, and optionally a cloud development host. Each machine has your private queen cloned.

Monday morning (office computer):

- Launch Claude Code; the SessionStart hook pulls and lists core rules plus optional resident summaries
- You say "continue last night's NestJS module work"
- Claude retrieves the relevant sections of `agents/macbook/claude-xxx/memory.md` to resume yesterday's work
- Retrieves relevant preferences from `shared/memory.md` only if this task needs them
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
- read core rules and optional shared/agent `resident.md`; retrieve history for the current task
- know your preferences, past decisions, current project state
- use a `~/.codex/config.toml` + `~/.codex/hooks.json` SessionEnd hook for optional local-history snapshots when enabled

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

When agents have accumulated enough memory, merge it into `shared/memory.md`:

```bash
# Pure concat: concatenate agents/*/memory.md, commit, push
bash ~/nestwork/scripts/maintenance/compile.sh

# Vendor-agnostic: prints a distillation prompt for you to feed any agent session
python3 ~/nestwork/scripts/maintenance/distill.py

# Codex one-shot: aggregate, write back to shared/memory.md, commit, push
# (add --dry-run to preview without writing)
python3 ~/nestwork/scripts/maintenance/distill.py --run-codex --profile <your-profile>
```

None of these modify the original agent memory — distillation reads private memory and writes only `shared/memory.md`, with commit message `memory: distill shared`. Every agent picks up the result on its next `git pull`.

The rules that make this safe — shared is a union and not an intersection, never delete, sub-agent review followed by human confirmation — are in [AGENTS.md](AGENTS.md) §7.

---

## Agent mailbox (inter-agent messaging)

When agents need to talk **to each other** across machines and tool-chains, nestwork ships a git-native mailbox: pure git + bash, zero external dependencies, no server and no bot. It answers "how do my agents coordinate?" in the case IM platforms cannot — Telegram bots, for instance, cannot see each other's messages by design.

It respects the single-writer rule, so there is no shared inbox and no write conflicts: you **send** by writing into *your own* `outbox/` tagged `to:` (one message = one file = one commit), and **receive** by scanning everyone's `agents/*/*/outbox/` for messages addressed to you.

```bash
echo "please confirm receipt with a reply" | \
  bash scripts/comms/send.sh <host>/<agent-id> task "handshake test"

bash scripts/comms/read.sh            # view unread addressed to me
bash scripts/comms/read.sh --mark     # mark seen after acting on them
```

Read state lives in a git-ignored local file, so marking mail read creates no commits. Unread mail is snapshotted into a git-ignored local inbox; its path is listed on demand for coordination. Full reference: [docs/agent-mailbox.md](docs/agent-mailbox.md).

---

## Directory structure

```
nestwork/
├── AGENTS.md                   Single bootstrap source (Codex, Kimi, OpenClaw, Gemini, …)
├── CLAUDE.md                   Byte-exact mirror of AGENTS.md (Claude Code reads this name)
├── SOUL.md                     Hermes' short persona file
├── queen/                      Behaviour rules + strategy, agent read-only, never synced
│   ├── agent-rules.md
│   └── strategy.md
├── agents/
│   └── <host>/<agent-id>/
│       ├── resident.md         Small startup facts and retrieval pointers
│       ├── memory.md           Private history (on demand)
│       └── carryover/          Distilled tool-native memory (cold — never injected, v2.5+)
├── shared/resident.md          Small shared startup index
├── shared/memory.md            Cross-agent compiled memory
├── projects/<project>.md       Project context
├── workflow/<topic>.md         Cross-project portable knowledge
├── decisions/                  Protocol-level ADRs
├── docs/                       Methodology, answer-ready docs, comparisons, blog
├── schemas/                    JSON Schema for nestwork.config.json
├── tests/                      Consistency and end-to-end tests
└── scripts/
    ├── install/                Per-tool installers (.sh + .ps1)
    ├── uninstall/              Per-tool uninstallers (unbind only; memory & identity kept)
    ├── hooks/                  Runtime hooks (pre/post/stop, session-start, optional sync)
    ├── comms/                  Agent mailbox (send / read / archive)
    └── maintenance/            compile.sh · distill.py · sync-claude-md.sh · update.sh
```

---

## File size limits and split protocol

Any markdown file in the repo is split once it outgrows its limit, always the same way: **the original filename becomes a folder, and the original file becomes a pure index of links.** Content is divided by topic.

| File | Max lines |
|---|---|
| `queen/agent-rules.md` | 80 |
| `queen/strategy.md` | 80 |
| `agents/<host>/<agent-id>/memory.md` | 200 |
| `shared/memory.md` | 500 |
| `projects/<name>.md` | 150 |
| `workflow/<topic>.md` | 200 |
| anything else | soft 500 / hard 1000 |

**Why limits at all?** Context windows are large, but attention degrades with token count — loading a 5000-line `memory.md` wholesale is poorly utilised. An index plus topic files lets an agent follow only what is relevant.

Tune against **retrieval quality, not raw context-window size**: a bigger window does not justify proportionally bigger files.

A private instance can override the table without touching the protocol layer — copy [docs/limits-override-example.md](docs/limits-override-example.md) to `queen/limits.md` and edit it. `update.sh` never touches `queen/`, so the override survives protocol updates.

Split mechanics and worked examples: [AGENTS.md](AGENTS.md) §6.

---

## Supported tools

### Native installers (config path is well-defined)

| Tool | Vendor | Entry file | Install | Adoption |
|---|---|---|---|---|
| Claude Code | Anthropic | `~/.claude/CLAUDE.md` + hooks | `bash scripts/install/claude.sh` | Adopted, daily-driven |
| Codex CLI | OpenAI | `~/.codex/AGENTS.md` + compatibility entry | `bash scripts/install/codex.sh` | Adopted, daily-driven |
| Gemini CLI | Google | `~/.gemini/GEMINI.md` | `bash scripts/install/gemini.sh` | Entry exists, untested by author |
| Kimi Code | Moonshot AI | `~/.kimi-code/AGENTS.md` + hooks | `bash scripts/install/kimi.sh` | Entry exists, untested by author |
| OpenClaw | Open source | `~/.openclaw/workspace/AGENTS.md` | `bash scripts/install/openclaw.sh` | Entry exists, untested by author |
| Hermes Agent | Open source | `~/.hermes/SOUL.md` | `bash scripts/install/hermes.sh` | Entry exists, untested by author |

Claude Code and Kimi Code register the full atomic per-write synchronization hooks. Codex registers a SessionEnd hook for optional local-history snapshots through `~/.codex/config.toml` + `~/.codex/hooks.json`; Codex memory edits still follow the manual commit/push bootstrap protocol. Other tools follow their bootstrap protocol.

### Optional: capture local tool history

> [!CAUTION]
> Recommended off for now. v2.4's orphan-branch strategy keeps `main` lean, but enabling this still grows your repo's overall footprint (and fetch cost) over time. Until a cleaner approach lands, leave it disabled — which is the default. If you have a better solution, a PR is welcome.

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

**Migrating to 3.0 also requires refreshing tool bootstraps.** `update.sh` and sync PRs update repository files; they do not rewrite tool configuration on each machine. After syncing, rerun the installer for each tool in use (or `_bootstrap.py`), then open a new session. Missing `resident.md` does not require loading full history. See the [migration guide](docs/context-loading.md).

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

Yes. Any "reads a markdown file as system prompt at startup" CLI can use `install/generic.sh`. Claude Code and Kimi Code have per-write sync hooks; tools without them rely on "commit on session end", with a slightly larger race window but rarely an issue in practice.

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

### Can I keep private or sensitive memory confidential?

Two different needs. **Secrets / API keys**: no — never store them here, encrypted or not (see above). **Personal or private memory** that must be both synced across machines and kept unreadable to the git host: turn on the optional git-crypt mode (off by default). It encrypts only the files you mark while the rest of the repo stays plaintext, transparently — the agent reads and writes plaintext, commits store ciphertext. See [docs/encrypted-memory.md](docs/encrypted-memory.md). Mind the trust boundary: the agent decrypts to plaintext to read it, so encryption protects against the git host and anyone who obtains a clone — not against whoever runs the agent.

### Will the protocol break compatibility often?

The current protocol is **3.0**. `protocol-version` uses `MAJOR.MINOR`: MINOR is additive-compatible; MAJOR may require migration. Moving from 2.x to 3.0 changes startup loading: update the protocol, refresh each installed tool bootstrap, then open a new session. Historical memory stays intact; see the [migration guide](docs/context-loading.md). The software release in `VERSION` (currently v0.6.0) is numbered independently from the protocol.

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

Check the shared host and this tool's identity file:

```bash
cat ~/.nestwork_host
cat ~/.nestwork_id_codex       # or ~/.nestwork_id_claude
```

Each tool has its own identity file on a machine. If a suffixed identity such as `claude-xxxx` was copied to another machine, delete that tool-specific file on the new machine and let the installer regenerate it. Legacy `~/.nestwork_id` files are imported automatically.

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
- Built-in or mandatory end-to-end encryption: the protocol does not bake encryption in; private repos rely on GitHub's security model by default. An optional, off-by-default git-crypt mode is available when you have a genuine confidentiality need — see [docs/encrypted-memory.md](docs/encrypted-memory.md). API keys and other secrets still don't belong here; use a secret store.
- Real-time collaboration / live notifications: git is asynchronous; if two agents truly write the same file in the same second, the PreToolUse hook blocks rather than locks in real time
- Cross-vendor LLM call abstraction: distillation uses Codex but doesn't try to unify all LLM APIs; agents read markdown when switching tools
- GUI / web app: pure file protocol; all interaction is via the agent or git CLI
- Automated onboarding / interactive tutorial: README is the entry; no interactive wizard

If you need any of the above, nestwork may not be the right fit. Pick a dedicated tool for that need.

---

## Protocol evolution

> Note on `agent-history-*` branches: orphan branches introduced in v2.4 hold rolling-overwrite snapshots of high-churn artefacts (e.g. `history.jsonl`). They each contain a single force-pushed commit and are not meant to be merged into `main`. Ignore GitHub's "Compare & pull request" prompt for these branches. See [AGENTS.md §12](AGENTS.md) for details.

- v2.0 (2026-04-17): `agents/` reorganized by host (`agents/<host>/<agent-id>/`); atomic per-write hook architecture
- v2.1 (2026-04-21): SessionStart hook auto-injects context
- v2.2 (2026-05-07): Added `workflow/` context layer + `nestwork.config.json` external-directory ingestion contract + universal markdown split rule
- v2.3 (2026-05-08): Added §10 nestwork-vs-repo-5-doc boundary (`projects/<name>.md` 5-field convention + `decisions/` for protocol-level ADRs + `workflow/lessons.md` for cross-repo lessons); SessionStart hook now auto-checks upstream protocol version (24h cache, advisory only, never auto-applies)
- v2.4 (2026-05-08): Added §12 orphan-branch strategy for high-churn artefacts. `agents/*/*/local/` is now in default `.gitignore`; `agent-history-<host>-<agent-id>` orphan branches hold a single rolling-overwrite snapshot (force-push). Fixes unbounded main-history bloat when `sync_local_history` is enabled (observed mynestwork: 177 MB → 1.6 MB).
- v2.5 (2026-07-28): Added §13 tool-native memory carryover. Every coding agent's own memory is machine-local (Claude Code, Codex, Kimi Code alike), so it dies with the disk — and account-bound memory dies with the account. New reserved cold path `agents/<host>/<agent-id>/carryover/<tool>.md` receives that memory **distilled** through the §7 pipeline, never raw-mirrored, and is never injected at session start.
- v3.0 (current protocol): core rules + optional resident summaries at startup; history, strategy, projects, workflows and inbox on demand. Existing instances must refresh tool bootstraps and open a new session; historical data stays intact.

Full protocol: [AGENTS.md](AGENTS.md).

---

## Related docs

- [AGENTS.md](AGENTS.md): Protocol spec (authoritative reference for Nestwork maintenance)
- [docs/workflow-protocol.md](docs/workflow-protocol.md): v2.2 workflow deep dive
- [docs/desensitization-prompt.md](docs/desensitization-prompt.md): AI desensitization methodology
- [docs/encrypted-memory.md](docs/encrypted-memory.md): Optional git-crypt encryption for private memory
- [schemas/nestwork.config.schema.json](schemas/nestwork.config.schema.json): `nestwork.config.json` JSON Schema
- [docs/ai-agent-memory.md](docs/ai-agent-memory.md)
- [docs/claude-code-memory.md](docs/claude-code-memory.md)
- [docs/codex-persistent-memory.md](docs/codex-persistent-memory.md)
- [docs/git-native-memory-protocol.md](docs/git-native-memory-protocol.md)
- [docs/agents-md-best-practices.md](docs/agents-md-best-practices.md)
- [docs/shared-context-for-ai-coding-agents.md](docs/shared-context-for-ai-coding-agents.md)
- [docs/faq.md](docs/faq.md)
- [docs/comparisons/claude-mem.md](docs/comparisons/claude-mem.md)

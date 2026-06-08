# NESTWORK BOOTSTRAP

<!-- protocol-version: 2.4 -->

Every agent that loads this file returns context to the same shared nest.
Follow this protocol exactly on every session.

The `protocol-version` marker above lets tooling detect breaking protocol
changes. Semantics: `MAJOR.MINOR`. MAJOR bumps may require downstream
action (directory layout, hook contract, agent-id format). MINOR bumps are
additive-compatible. Private Nestwork repos may pin a version they trust and gate
auto-sync on it.

---

## 1. Session Start

Run before doing anything else:

```bash
git -C $NESTWORK_PATH pull --rebase
```

If pull fails, note the reason and continue.

Then load context in this order:

1. `queen/agent-rules.md` — behavior rules (highest priority, cannot be overridden)
2. `queen/strategy.md` — current decision direction
3. `shared/memory.md` — shared memory across all agents
4. `agents/<host>/<agent-id>/memory.md` — this instance's private memory (if exists)
5. `projects/<relevant>.md` — current task context (if relevant)
6. `workflow/<relevant>.md` — portable user-level workflow knowledge (if relevant; see Section 8)

**Directory layout** (protocol v2.0): agents are grouped by host.
`agents/<host>/<agent-id>/` — one folder per machine, one subfolder per tool on
that machine. Example: `agents/desktop-rkv5ls4/claude-a7k2/`.

**agent-id format**: `<tool>-<4-char-random-suffix>` for tools that want
distinct instances (e.g. `claude-a7k2`), or just `<tool>` for tools that
treat one-per-host as the norm (e.g. `codex`, `gemini`). The host segment
is **in the path**, not in the id.

**host format**: lowercased short hostname. Installer persists host in
`~/.nestwork_host` and each tool's agent-id in `~/.nestwork_id_<tool>`
(for example `~/.nestwork_id_claude` and `~/.nestwork_id_codex`) so
installing one tool never replaces another tool's identity. Older
`~/.nestwork_id` files are imported automatically. Override via
`NESTWORK_HOST` and/or `NESTWORK_AGENT_ID` env vars.

### After loading — orient first, then propose or ask

Before your first reply, orient yourself:

1. `git -C $NESTWORK_PATH log --oneline -10 -- agents/` — recent activity
   across every instance
2. `git -C $NESTWORK_PATH log --oneline -5` — recent protocol / shared
   changes
3. Cross-reference against `queen/strategy.md` **Current Priorities** and
   the latest entries in `shared/memory.md` and your own
   `agents/<host>/<agent-id>/memory.md`

Then decide:

- **If the context gives clear signal** (in-flight work, an obvious next
  step from memory, a stated priority) → open with a **state summary**
  (2-3 bullets on what's in flight and what priorities say) plus **one
  concrete proposal** for the next action. Do NOT open by asking "what
  would you like me to do?" — the protocol exists so you already know
  enough to propose.
- **If the context is genuinely ambiguous** (conflicting signals, missing
  information, a user message whose intent does not match any active
  thread) → ask a narrow, specific question. `queen/agent-rules.md`
  Decision Rules require asking over guessing when unclear. State briefly
  what you checked and where the ambiguity is.

The goal is to eliminate passive openers when the protocol already gave
you enough to act — not to forbid asking when asking is actually correct.

---

## 2. Write Protocol

- **ONLY** write to `agents/<host>/<agent-id>/`
- **NEVER** write to `queen/` — read-only, human-managed only
- **NEVER** write to another host's folder (`agents/<other-host>/...`)
- `shared/memory.md` is read-only for agents **except during distillation** (see Section 7)
- When saving memory, prefer creating new files over editing existing ones

---

## 3. Session End

**If hooks are installed** (via `scripts/install/<tool>.sh`), per-write sync
happens automatically: every Write/Edit under `agents/<host>/<agent-id>/`
triggers `pull --rebase` before and `commit + push` after. The Stop hook
runs the same safety-net commit+push once per turn (cheap no-op when
clean), and the SessionEnd hook performs the claude-mem export + local
history sync once when the session truly ends. **Do nothing extra.**

**If hooks are NOT available** for your tool, run manually at session end:

```bash
git -C $NESTWORK_PATH add agents/<host>/<agent-id>/
git -C $NESTWORK_PATH diff --cached --quiet -- agents/<host>/<agent-id>/ || \
  git -C $NESTWORK_PATH commit -m "memory: update <host>/<agent-id>" -- agents/<host>/<agent-id>/
git -C $NESTWORK_PATH push
```

Only commit when there are meaningful context changes worth preserving.
Temporary task details, one-off debugging notes — do not commit.

---

## 4. claude-mem Integration (optional)

If [claude-mem](https://github.com/thedotmack/claude-mem) is installed and its worker is running on `localhost:37777`, nestwork will automatically export a session digest at the end of each session:

```
agents/<host>/<agent-id>/claude-mem-digest.md   ← today's observations from claude-mem
```

This file is committed and pushed with the rest of your agent memory, giving claude-mem's observations cross-machine reach via git.

**No configuration needed.** The export step runs as part of the SessionEnd hook (once when the session ends, not every turn) and silently skips if claude-mem is not running.

To override the worker URL:
```bash
export CLAUDE_MEM_URL=http://localhost:37777
```

---

## 5. Conflict Resolution

If `git pull` finds conflicts:
- `queen/` and `shared/` → take remote (they are managed upstream)
- `agents/<host>/<agent-id>/` → take local (this instance owns its directory)
- `agents/<other-host>/...` → take remote (owned by another machine)

---

## 6. File Size Limits & Split Protocol

### Universal rule

**Any markdown file in any Nestwork repository** — including but not limited to memory, plans, projects, workflow, drafts, ad-hoc notes — must be split when it grows too large. The pattern is always the same:

```
oversized.md  →  oversized/index.md (or just leave oversized.md as the index)
                 oversized/<topic-a>.md
                 oversized/<topic-b>.md
                 ...
```

The original filename becomes a folder. Inside the folder, content is split by topic. The top-level file (or `index.md` inside the folder) becomes a pure index — links only, no content.

Example:

```
plan-all.md  (1200 lines)
  ↓ split
plan-all.md  (now an index pointing into plan/)
plan/plan-a.md
plan/plan-b.md
plan/plan-c.md
```

### Default thresholds

When a specific file does not appear in the table below, use these defaults:

- **Soft limit**: 500 lines — start considering a split
- **Hard limit**: 1000 lines — must split before next write

### Specific limits

| File | Max lines | Split target |
|---|---|---|
| `queen/agent-rules.md` | 80 | `queen/rules/<topic>.md` |
| `queen/strategy.md` | 80 | `queen/strategy/<topic>.md` |
| `agents/<host>/<agent-id>/memory.md` | 200 | `agents/<host>/<agent-id>/<topic>.md` |
| `shared/memory.md` | 500 | `shared/<topic>.md` |
| `projects/<name>.md` | 150 | `projects/<name>/<topic>.md` |
| `workflow/<topic>.md` | 200 | `workflow/<topic>/<subtopic>.md` |

### Per-instance override (`queen/limits.md`)

The limits above are protocol defaults. A private instance may override them
without editing this protocol file: create `queen/limits.md` declaring its own
limits table. When present, `queen/limits.md` is authoritative over the defaults
here. It lives in the high-priority `queen/` layer, so agents load it at session
start and apply its numbers; `update.sh` never touches `queen/`, so the override
survives protocol updates. Point to it from `queen/agent-rules.md` (or rely on
this section) so agents know to read it.

Tune limits against retrieval quality / attention, not raw context-window size —
a larger model window does not justify proportionally larger files, because
attention still degrades with token count and selective loading stays sharper
with focused, topic-split files.

**How to split** — replace the oversized file with an index:

```markdown
# MEMORY — claude-macbook

## Index

- [User Profile](user_profile.md) — role, stack, preferences
- [Collaboration](feedback_collab.md) — working style, corrections
- [Project: nestwork](project_nestwork.md) — goals, decisions
```

Each linked file is a standalone topic file. The index is the only file agents
need to read first — they follow links only when the topic is relevant.

**Agent rule**: before writing to or extending any markdown file, check its
current line count against the limit (specific or default). If approaching the
hard limit, split first, then write to the appropriate topic file. This applies
to all markdown files, not only those listed in the table.

---

## 7. Memory Distillation Protocol

Distillation merges all agents' private memory into `shared/memory.md`.
Only agents explicitly triggered for distillation may write to `shared/`.

### When to trigger

- Manually: when the human asks an agent to distill
- Automatically: at session end, if the agent detects new memory worth sharing

### What goes into shared

| Include | Exclude |
|---|---|
| Cross-agent stable facts (user identity, stack, preferences) | Temporary task details |
| Validated collaboration patterns | One-off debugging notes |
| Decisions with lasting impact | Agent-specific context |

### How to distill

1. Read all `agents/*/*/memory.md`
2. Read current `shared/memory.md`
3. **Spawn a sub-agent to review**: check for sensitive data, factual errors, contradictions, and outdated entries — sub-agent reports only, does not write
4. Present review report to human for confirmation
5. Merge: remove duplicates, unify consistent facts, keep divergent observations as-is
6. Write result to `shared/memory.md` — **never delete**, only merge and add
7. Commit with message: `memory: distill shared`

### Rules

- `shared` is the union of agent knowledge, not an intersection — don't drop unique observations
- Each agent's private memory is preserved unchanged — distillation is non-destructive
- After distillation, agents only need to read `shared/memory.md` + their own `agents/<host>/<agent-id>/memory.md`

---

## 8. Workflow Protocol

`workflow/` is the lowest-priority context layer. It captures **portable user-level knowledge** that survives across employers, projects, and machines: coding disciplines, tooling preferences, methodologies, migration guides, skill assets.

### What belongs in `workflow/`

| Belongs | Does not belong |
|---|---|
| Coding disciplines, estimation rules | Project-specific business rules → `projects/` |
| Cross-project tooling stack & preferences | Cross-agent stable facts about user identity → `shared/` |
| Skill assets, prompt templates, perspectives | Single-agent observations → `agents/` |
| Migration / cross-machine setup guides | Temporary task notes |
| Methodologies that outlive any single repo | Anything employer-confidential |

### Two ingestion paths

1. **Distillation from agent memory**: when an agent observes a stable user-level pattern across multiple sessions, it may distill into `workflow/<topic>.md`. Same rules as Section 7 distillation, target is `workflow/` instead of `shared/`.

2. **Ingestion from external source dirs**: when content from a working directory outside Nestwork (e.g. an employer project repo) is worth absorbing, the source dir must declare a `nestwork.config.json` (see Section 9). The agent reads that config, applies its desensitization rules, and writes the cleaned result into `workflow/<topic>.md` or `projects/<name>.md`.

### Direction is one-way

- External source dir → mynestwork (private instance) ✓
- mynestwork → upstream nestwork ✗ (upstream is human-maintained only; never auto-flow)

Whether any artifact is later promoted to public sharing (blog, upstream template, etc.) is always a **separate human decision**, not protocol-driven.

### File size

200-line limit per topic file (see Section 6). Split by subtopic when exceeded.

---

## 9. `nestwork.config.json` Contract

`nestwork.config.json` is a **directory-level metadata file** declaring whether and how content from a working directory may be ingested into a Nestwork repository.

### Where it lives

In the **source working directory**, NOT inside Nestwork. Example:

```
F:/code/project/<some-project>/nestwork.config.json
```

When an agent operating in that directory detects content worth ingesting into Nestwork's `projects/` or `workflow/` category, it reads this config to determine ingestion behavior.

### When config is missing

- Agent **must** remind the user to create one before ingesting anything from that directory.
- Default template **must** set `desensitize.level: "strong"`.
- Agent **never** silently proceeds without a config.

### Schema

See `schemas/nestwork.config.schema.json`. Minimum example:

```json
{
  "$schema": "https://github.com/songth1ef/nestwork/schemas/nestwork.config.schema.json",
  "version": "1.0",
  "ingest": {
    "target": "projects",
    "name": "sign-mgt-web"
  },
  "desensitize": {
    "level": "strong",
    "custom_rules": []
  }
}
```

### Field semantics

| Field | Values | Meaning |
|---|---|---|
| `ingest.target` | `projects` / `workflow` / `null` | Which Nestwork category receives content. `null` = not ingestable. |
| `ingest.name` | string | Destination filename or subfolder under the target. |
| `desensitize.level` | `none` / `weak` / `strong` | How aggressively content must be desensitized before ingestion. |
| `desensitize.custom_rules` | string[] | User-defined rules specific to this directory (employer names, internal codenames, etc.). Layered on top of the global methodology. |

### Desensitization levels

- `none` — no transformation (only valid when content is verifiably non-confidential)
- `weak` — pattern-based redaction following `custom_rules`
- `strong` — AI-driven semantic desensitization following the methodology in `docs/desensitization-prompt.md`, plus all `custom_rules`

### Constraints

- Ingestion is **always agent-driven and manually triggered**; never automatic.
- The config governs the **source side** only. It does not promise anything about what mynestwork does with the artifact afterwards.
- Upstream `nestwork` provides only the methodology and prompt template for desensitization. Specific blacklists (employer names, project codenames) live in each user's `custom_rules` — never in upstream.

---

## 10. Layer Boundary: Nestwork vs Per-Repo Docs

Each working repository should maintain its own 5-doc skeleton (added in v2.3 to clarify scope):

| File (in repo root or `docs/`) | Purpose |
|---|---|
| `AGENT.md` | Per-repo agent behavior directives (entry file pointing to the others) |
| `docs/conventions.md` | Coding standards: naming, directory layout, component patterns, git rules |
| `docs/domain.md` | Business description: core concepts, glossary, business rules |
| `docs/architecture.md` | System architecture: module boundaries, data flow, tech-stack rationale |
| `docs/lessons.md` | Lessons learned: bugs hit, validated decisions, mistakes not to repeat |

Nestwork is the **cross-repo coordination layer** sitting *above* the per-repo docs. The boundary:

| Layer | Lives in | Scope |
|---|---|---|
| **Per-repo 5-doc** | `<repo>/AGENT.md` + `<repo>/docs/*.md` | Project-internal deep knowledge, travels with the repo |
| **Nestwork `projects/<name>.md`** | this repo | Project **snapshot + collaboration state** (see §10.1), shared across machines |
| **Nestwork `decisions/`** | this repo | **Protocol-level** ADRs (see §10.2). Project-level ADRs stay in the repo. |
| **Nestwork `workflow/<topic>.md`** | this repo | Cross-project portable methodology (see §8) |
| **Nestwork `queen/`** | this repo | Global behavior rules and strategy |
| **Nestwork `agents/<host>/<id>/`** | this repo | Single-agent private memory |

Rule of thumb: **if it changes when you switch employers, it belongs in the repo's 5-doc; if it survives the switch, it belongs in nestwork's `workflow/`**. State that helps an agent resume work goes in nestwork's `projects/<name>.md`.

### 10.1. `projects/<name>.md` recommended fields

When writing a project status file, the following five fields are recommended (not strictly required — agents may keep additional notes if useful, but should preserve these as the minimum readable snapshot):

```markdown
## Current Goal
The single most important goal for this project right now.

## Current State
What's been done so far; where work is paused.

## Next Action
The recommended next step (single concrete action, not a plan).

## Do Not
Things explicitly out of scope, or known traps. Includes blockers if applicable.

## Last Verified
Date + what was last verified working. So later sessions know how stale the file is.
```

A reference template ships at `projects/_template.md`.

Deeper project knowledge (architecture, domain, conventions, full ADRs) belongs in the repo's own 5-doc files, not duplicated here.

### 10.2. `decisions/` — protocol-level ADRs only

`decisions/<YYYY-MM-DD>-<slug>.md` is for decisions about **nestwork itself** or its protocol — e.g. "why we don't ship a `runs/` directory", "why projects/<name>.md uses 5 fields not 8". Project-internal decisions belong in that project's `docs/architecture.md` or its own `decisions/` subfolder.

A reference template ships at `decisions/_template.md`.

Reasoning: capturing **why** is the highest-leverage form of memory. ADR format (Context / Decision / Consequence) is industry-standard; nestwork uses it for protocol evolution so future maintainers don't relitigate settled choices.

### 10.3. `workflow/lessons.md` — cross-repo lessons

The repo-level `docs/lessons.md` (5-doc #5) captures lessons specific to that codebase. When a lesson is transferable across repos (e.g. "Git Bash on Windows has no `hostname -s`"), distill it into `workflow/lessons.md` (single file at first; split into `workflow/lessons/<topic>.md` if it exceeds the 200-line limit per §6).

This file is **not shipped by upstream** — each user creates their own as lessons accumulate. `update.sh` does not touch it.

---

## 11. Upstream Protocol Check (session-start, v2.3+)

The SessionStart hook performs a 3-second non-blocking check against upstream `nestwork`'s `AGENTS.md` `protocol-version` marker. If a newer version is detected, an advisory message is appended to the injected context bundle. The agent surfaces this in its session-start orientation and asks the user whether to run `update.sh`.

Implementation contract:
- Hardcoded upstream URL: `https://raw.githubusercontent.com/songth1ef/nestwork/main/AGENTS.md`
- Local cache: `.nestwork-upstream-check` (24h TTL) so most session starts skip the network call
- Network failure / offline / version match → silent skip (never blocks session start)
- Only **MAJOR.MINOR mismatch where upstream > local** triggers the advisory

User remains in control: the hook only emits an advisory; nothing is auto-applied.

---

## 12. High-churn artefacts: per-agent orphan branches (v2.4+)

> [!CAUTION]
> `sync_local_history` is recommended **off** for now (it is off by default).
> The orphan-branch strategy below keeps `main` lean, but enabling the feature
> still grows your repo's overall footprint and fetch cost over time. Leave it
> disabled until a cleaner approach lands — a PR is welcome.

Some artefacts mirrored into `agents/<host>/<id>/local/` (e.g.
`history.jsonl` from `sync_local_history`) are **high-frequency, large, and
poorly delta-compressed**. Committing them to `main` causes the main branch
to bloat unboundedly (observed in practice: 411 commits → 177 MB in two
weeks).

These artefacts are kept out of `main` and stored on a per-agent **orphan
branch** instead:

```
agent-history-<host>-<agent-id>
```

### Mechanics

- `agents/*/*/local/` is in the default `.gitignore` shipped by upstream — main never tracks it.
- After each `sync_local_history` invocation, `scripts/hooks/sync-local-history.sh` calls `scripts/hooks/snapshot-local-orphan.sh`, which:
  - Builds a tree from the working-tree `local/` files using a temporary index (without touching the main working index).
  - Creates a parentless commit (orphan).
  - `git update-ref` on `refs/heads/agent-history-<host>-<agent-id>`.
  - Force-pushes that branch to `origin`.
- Each force-push **replaces** the previous snapshot. Branch always has exactly one commit. Remote object count stabilises at ≈ current `local/` size.

### Cross-machine restore

```bash
git fetch origin agent-history-<host>-<agent-id>
git restore --source=agent-history-<host>-<agent-id> -- \
  agents/<host>/<agent-id>/local/
```

### Why this is safe

- **Single writer per branch**: branch name embeds `host` and `agent-id`. No other instance ever writes the same branch — force-push is collision-free by design.
- **Independent of `main`**: orphan branches share no history with `main`. Force-push affects only the orphan branch's ref, never rewinds `main`.
- **Aligned with priority chain**: `local/` was never part of the priority-chain context bundle. Moving it off `main` does not change agent behaviour.

### When to use this pattern (general rule)

For any future high-churn / poorly-compressing artefact: **default to a per-agent orphan branch, not `main`**. Markdown-style memory (low-churn, human-curated) continues to live on `main`.

---

## Priority Rules

```
queen/agent-rules.md  >  queen/strategy.md  >  shared/memory.md  >  agents/*/*/memory.md  >  projects/*.md  >  workflow/*.md
```

When instructions conflict, follow the higher priority source.
Do not merge conflicting instructions — choose one.

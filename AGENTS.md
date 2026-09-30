# NESTWORK BOOTSTRAP

<!-- protocol-version: 3.2 -->

Every agent that loads this file returns context to the same shared nest.
Follow this protocol exactly in every session.

In the commands below, `$NESTWORK_PATH` is the local clone of your private
Nestwork repository.

The `protocol-version` marker above lets tooling detect breaking protocol
changes. Semantics: `MAJOR.MINOR`. MAJOR bumps may require downstream
action (directory layout, hook contract, agent-id format). MINOR bumps are
additive-compatible. Private Nestwork repos may pin a version they trust and gate
auto-sync on it.

---

## 1. Session Start

Run before doing anything else, unless a SessionStart hook already ran it for
this session:

```bash
git -C $NESTWORK_PATH pull --rebase
```

Where a SessionStart hook is installed (Claude Code, Kimi Code), it runs this
pull automatically and prints the READ-ON-START manifest; do not pull again.
If the pull fails, note the reason and continue.

Load only the resident tier:

1. `queen/agent-rules.md` — core behavior rules
2. `shared/resident.md` — small, current cross-agent facts and retrieval pointers, if present
3. `agents/<host>/<agent-id>/resident.md` — small instance-specific facts and pointers, if present
4. `local/recent.md` — generated recent-activity digest, if present (protocol 3.2+)

Resident files orient the agent before any lookup: who the owner is, what they
are currently aiming for, and what moved recently. `shared/resident.md` may
therefore carry a short owner profile and a summary of current goals and
priorities (source and review date noted; `queen/strategy.md` stays
authoritative). `local/recent.md` is one nest-level file shared by all
agents, rebuilt at every session start by `scripts/maintenance/recent-digest.py`
from git history (recently touched `projects/*.md` fields and topic
descriptions); it is git-ignored, capped at 2048 bytes and never edited by
hand. It orients; it does not assign work.

Where installed, the SessionStart hook prints these paths as a READ-ON-START
manifest and the on-demand paths below as READ-ON-DEMAND. If the nest is not
checked out on its default branch, the hook skips the pull and prints a `[!]`
warning instead: the files may not be this instance's context, so tell the user
before relying on them.

Everything else is **on demand**, including `queen/strategy.md`, historical
`shared/memory.md`, agent `memory.md`, topic files, projects, workflows,
carryover and the mailbox snapshot (`agents/<host>/<agent-id>/local/inbox.md`).
Search headings/keywords and read only the relevant sections; do not
recursively follow links. A missing resident summary never triggers a
fallback to loading full history.
Residency controls loading, not authority (see Priority Rules). Verify dated
project state before acting on it.
See [loading and migration](docs/context-loading.md) when maintaining context.

**Directory layout** (protocol v2.0+): agents are grouped by host.
`agents/<host>/<agent-id>/` — one folder per machine, one subfolder per tool on
that machine. Example: `agents/workstation/claude-a7k2/`.

**agent-id format**: `<tool>-<4-char-random-suffix>` for tools that want
distinct instances (e.g. `claude-a7k2`), or just `<tool>` for tools that
treat one-per-host as the norm (e.g. `codex`, `gemini`). The host segment
is **in the path**, not in the id.

**host format**: lowercased short hostname. The installer persists the host
in `~/.nestwork_host` and each tool's agent-id in `~/.nestwork_id_<tool>`
(for example `~/.nestwork_id_claude` and `~/.nestwork_id_codex`), so
installing one tool never replaces another tool's identity. A legacy
`~/.nestwork_id` file is imported automatically. Override either value with
the `NESTWORK_HOST` / `NESTWORK_AGENT_ID` environment variables.

### Follow the current task

When the user gives a task, proceed with that task. Do not inject unrelated
project status or treat historical assignments as current authorization.
When asked to resume, coordinate, or choose work, inspect relevant project
context, strategy and recent git activity, then propose a concrete next action.
Ask a narrow question only if missing context blocks the task.

---

## 2. Write Protocol

- For ordinary memory writes **within this Nestwork repository**, write only to `agents/<host>/<agent-id>/`. This does not restrict work in other repositories or user-requested artifact destinations. Explicit maintenance authorization can cover protocol/shared changes.
- **NEVER** write to `queen/` — read-only, human-managed only
- **NEVER** write to another host's folder (`agents/<other-host>/...`)
- `shared/` (including `shared/memory.md`) is read-only for agents **except during distillation** (see §7)
- When saving memory, extend the file that already covers the topic; create a new file only when none does (see §6, Topic memory)

---

## 3. Session End

**If your tool has per-write sync hooks installed** (Claude Code, Kimi Code or
Codex), memory sync is automatic: every write (Write/Edit, or Codex `apply_patch`) under `agents/<host>/<agent-id>/`
triggers `pull --rebase` before the write (a conflict blocks the write) and
`commit + push` after it. The Stop hook repeats the commit + push once per turn
as a safety net (a no-op when nothing changed). Claude Code also registers a
SessionEnd hook for the claude-mem export (§4) and the optional local history
sync (§12). **Do not duplicate automatic memory sync.**

**If per-write sync hooks are NOT installed** for your tool, sync manually at
session end. A history-only hook (such as a SessionEnd hook that only runs the
local history sync) does not replace this:

```bash
git -C $NESTWORK_PATH add agents/<host>/<agent-id>/
git -C $NESTWORK_PATH diff --cached --quiet -- agents/<host>/<agent-id>/ || \
  git -C $NESTWORK_PATH commit -m "memory: update <host>/<agent-id>" -- agents/<host>/<agent-id>/
git -C $NESTWORK_PATH push
```

Commit only context changes worth preserving. Do not commit temporary task
details or one-off debugging notes.

---

## 4. claude-mem Integration (optional)

For Claude Code: if [claude-mem](https://github.com/thedotmack/claude-mem) is installed and its worker is running on `localhost:37777`, nestwork automatically exports a digest of today's observations at the end of each session:

```
agents/<host>/<agent-id>/claude-mem-digest.md   ← today's observations from claude-mem
```

The export itself does not commit; the next memory sync (a per-write or Stop hook in a later session) commits and pushes the digest with the rest of your agent memory, giving claude-mem's observations cross-machine reach via git.

**No configuration needed.** The export runs in the Claude Code SessionEnd hook (once per session, not every turn) and is skipped without error when the claude-mem worker is not reachable.

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

**Any markdown file in a Nestwork repository** — memory, plans, projects,
workflow, drafts, ad-hoc notes — must be split when it grows too large. The
pattern is always the same: the original filename becomes a folder, content is
split into topic files inside it, and the original file (or `index.md` inside
the folder) becomes a pure index — links only, no content.

```
plan-all.md  (1200 lines)
  ↓ split
plan-all.md  (now an index pointing into plan-all/)
plan-all/plan-a.md
plan-all/plan-b.md
plan-all/plan-c.md
```

An index looks like this:

```markdown
# MEMORY — claude-macbook

## Index

- [User Profile](user_profile.md) — role, stack, preferences
- [Collaboration](feedback_collab.md) — working style, corrections
- [Project: nestwork](project_nestwork.md) — goals, decisions
```

Each linked file is a standalone topic file. Agents read the index first and
follow a link only when its topic is relevant.

**Agent rule**: before writing to or extending a Nestwork context markdown file
(not unrelated project artifacts), check its current line count against its
limit (specific or default, below). If the file is approaching the hard limit,
split it first, then write to the appropriate topic file. Resident files also
have byte budgets; see `docs/context-loading.md`.

### Default thresholds

For files not listed under Specific limits:

- **Soft limit**: 500 lines — start considering a split
- **Hard limit**: 1000 lines — must split before the next write

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
without editing this protocol file by creating `queen/limits.md` with its own
limits table. When present, `queen/limits.md` is authoritative over the
defaults here. Because it lives in the high-priority `queen/` layer, agents
load it before context maintenance and apply its numbers; `update.sh` never
touches `queen/`, so the override survives protocol updates. Point to it from
`queen/agent-rules.md` (or rely on this section) so agents know to read it.

Tune limits for retrieval quality and attention, not raw context-window size.
A larger model window does not justify proportionally larger files: attention
still degrades with token count, and selective loading stays sharper with
focused, topic-split files.

### Topic memory (protocol v3.1+)

A **memory scope** is `shared/` or `agents/<host>/<agent-id>/`. A scope opts in
to topic storage by putting the index markers `<!-- nestwork:topic-index:begin -->`
and `<!-- nestwork:topic-index:end -->` in its `memory.md`; from then on
`memory.md` is a routing table and the facts live in topic files.
Retrieval works like skills: read the index, pick files by their description,
read only those.

```
shared/
  memory.md            ← index only; block between markers is generated
  owner.md             ← topic file
  engineering.md
  tooling/             ← a topic that outgrew one file
    mailbox.md
```

Every topic file starts with front matter. `description` is the only thing an
agent sees before deciding to open the file, so write it as a trigger — *when*
to read, not a title:

```markdown
---
description: Machine-specific quirks, ports and paths; read before touching a host's setup
updated: 2026-09-27
---
```

Rules:

- **Never hand-edit the index; regenerate it** with
  `python3 scripts/maintenance/memory-index.py` after changing topic files.
  Text outside the markers is preserved. `--check` fails on a stale index, a
  topic file without `description`, a topic file over 32 KB (it warns above
  16 KB), or nesting deeper than `<topic>/<subtopic>.md`.
- **Reuse before creating.** Read the index first; write into the topic whose
  description already covers the fact. Create a new file only when none does.
- **Agents shape only their own scope; `shared/` changes only in distillation.**
  An agent may add leaf topics inside `agents/<host>/<agent-id>/`. In `shared/`,
  every change — a new topic, a rename, a merge, a deletion or a new folder —
  happens during distillation with human review (§7), so 30 agents do not grow
  `owner.md`, `user.md` and `identity.md` side by side.
- **Split by when it is needed, not by who wrote it.** A topic is the unit an
  agent loads for one kind of task. Project state stays in `projects/`, portable
  methods in `workflow/`; do not duplicate them as shared topics.
- Never topics: `memory.md` and `resident.md` at the scope root; anything under
  `outbox/`, `local/`, `carryover/`, `comms/`, `inbox/` or `archive/`; any
  path component starting with `_` or `.`.
- Scopes without markers keep single-file memory; nothing migrates automatically.
  `compile.sh` refuses to run on a topic-mode `shared/`, because concatenation
  would undo the split.

---

## 7. Memory Distillation Protocol

Distillation merges all agents' private memory into `shared/` — into
`shared/memory.md`, or into the `shared/` topic files when `shared/` is in topic
mode (§6). Only agents explicitly triggered for distillation may write to
`shared/` (§2).

### When to trigger

- Only when explicitly triggered: the human asks an agent to distill, or runs a
  scheduled job they configured for it.
- An agent that notices memory worth sharing at session end does **not** write
  `shared/`. It records the candidate in its own directory, where the next
  distillation picks it up.

### What goes into shared

| Include | Exclude |
|---|---|
| Cross-agent stable facts (user identity, stack, preferences) | Temporary task details |
| Validated collaboration patterns | One-off debugging notes |
| Decisions with lasting impact | Agent-specific context |

### How to distill

1. Read all `agents/*/*/memory.md` (plus their topic files, for topic-mode scopes)
2. Read current `shared/memory.md` — in topic mode, the index and every `shared/` topic file
3. **Spawn a sub-agent to review**: check for sensitive data, factual errors, contradictions, and outdated entries — sub-agent reports only, does not write
4. Present review report to human for confirmation
5. Merge: remove duplicates, unify consistent facts, keep divergent observations as-is
6. Preserve historical evidence in the on-demand tier. Update current summaries by replacing superseded facts, with provenance and scope; do not turn the resident tier into an append-only log.
7. In topic mode, write changed topic files only, regenerate the index, and run `memory-index.py --check`. Structural changes (rename / merge / delete / new top-level folder) are listed separately in the review report.
8. Commit with message: `memory: distill shared`

`scripts/maintenance/distill.py` prints a ready-made merge prompt (topic-aware)
by default; `--run-claude` / `--run-codex` run the merge through a local CLI
agent and write the result to the working tree **without committing**, so a
human can review `git diff -- shared/` (steps 3–4) before step 8. `--commit`
commits and pushes in the same run (`--no-push` keeps it local); use it only
when the human has already accepted skipping review, e.g. for a scheduled job
they configured. `--dry-run` prints the candidate without writing.

### Rules

- `shared/` is the union of agent knowledge, not an intersection — do not drop unique observations
- Each agent's private memory is preserved unchanged — distillation is non-destructive
- Distillation does not make its output resident. Startup reads only the resident tier; history remains searchable on demand.

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

1. **Distillation from agent memory**: when an agent observes a stable user-level pattern across multiple sessions, it may distill it into `workflow/<topic>.md`. The §7 distillation rules apply, with `workflow/` as the target instead of `shared/`.

2. **Ingestion from external source dirs**: when content from a working directory outside Nestwork (e.g. an employer project repo) is worth absorbing, the source dir must declare a `nestwork.config.json` (see §9). The agent reads that config, applies its desensitization rules, and writes the cleaned result into `workflow/<topic>.md` or `projects/<name>.md`.

### Direction is one-way

- External source dir → your private Nestwork instance ✓
- Private instance → upstream `nestwork` ✗ (upstream is human-maintained only; content never flows there automatically)

Whether any artifact is later promoted to public sharing (blog, upstream template, etc.) is always a **separate human decision**, not protocol-driven.

### File size

200-line limit per topic file (§6). Split by subtopic when exceeded.

---

## 9. `nestwork.config.json` Contract

`nestwork.config.json` is a **directory-level metadata file** declaring whether and how content from a working directory may be ingested into a Nestwork repository.

### Where it lives

In the **source working directory**, NOT inside Nestwork. Example:

```
~/code/<some-project>/nestwork.config.json
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
    "name": "my-app"
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
| `desensitize.placeholder_overrides` | object (term → placeholder), optional | Mapping from sensitive term to preferred placeholder. Overrides the default placeholder vocabulary in `docs/desensitization-prompt.md`. |

### Desensitization levels

- `none` — no transformation (only valid when content is verifiably non-confidential)
- `weak` — pattern-based redaction following `custom_rules`
- `strong` — AI-driven semantic desensitization following the methodology in `docs/desensitization-prompt.md`, plus all `custom_rules`

### Constraints

- Ingestion is **always agent-driven and manually triggered**; never automatic.
- The config governs the **source side** only. It does not constrain what your private instance does with the artifact afterwards.
- Upstream `nestwork` provides only the methodology and prompt template for desensitization. Specific blacklists (employer names, project codenames) live in each user's `custom_rules` — never in upstream.

---

## 10. Layer Boundary: Nestwork vs Per-Repo Docs

Each working repository should maintain its own 5-doc skeleton (protocol v2.3+):

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

A reference template ships at `decisions/_template.md`; `decisions/README.md` indexes upstream's ADRs with their status.

Reasoning: capturing **why** is the highest-leverage form of memory. ADR format (Context / Decision / Consequence) is industry-standard; nestwork uses it for protocol evolution so future maintainers don't relitigate settled choices.

### 10.3. `workflow/lessons.md` — cross-repo lessons

The repo-level `docs/lessons.md` (5-doc #5) captures lessons specific to that codebase. When a lesson is transferable across repos (e.g. "Git Bash on Windows has no `hostname -s`"), distill it into `workflow/lessons.md` (single file at first; split into `workflow/lessons/<topic>.md` if it exceeds the 200-line limit per §6).

This file is **not shipped by upstream** — each user creates their own as lessons accumulate. `update.sh` does not touch it.

---

## 11. Upstream Protocol Check (session start, protocol v2.3+)

The SessionStart hook (`scripts/hooks/session-start.sh`) compares the local `protocol-version` marker with upstream `nestwork`'s `AGENTS.md`, with a 3-second network timeout that never blocks startup. If upstream is newer, the hook appends a one-line advisory to its output. The agent relays the advisory to the user and asks whether to run `bash scripts/maintenance/update.sh`.

Implementation contract:
- Hardcoded upstream URL: `https://raw.githubusercontent.com/songth1ef/nestwork/main/AGENTS.md`
- Local cache: `~/.cache/nestwork/upstream-check` (24h TTL), so most session starts skip the network call
- Network failure, offline, or matching versions → silent skip
- Only a **MAJOR.MINOR mismatch where upstream > local** triggers the advisory

The user remains in control: the hook only emits an advisory; nothing is applied automatically. `update.sh` shows the incoming diff and asks for confirmation before overwriting protocol files; it never touches `agents/`, `queen/`, `shared/`, or your own files in `projects/` and `decisions/`.

---

## 12. High-churn artefacts: per-agent orphan branches (protocol v2.4+)

> [!CAUTION]
> `sync_local_history` is recommended **off** for now (it is off by default;
> it is enabled per host with `{"sync_local_history": true}` in
> `agents/<host>/settings.json`).
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
- Each force-push **replaces** the previous snapshot, so the branch always has exactly one commit and the remote object count stabilises at roughly the current `local/` size. An unchanged tree is not re-pushed.

### Cross-machine restore

```bash
git fetch origin agent-history-<host>-<agent-id>
git restore --source=origin/agent-history-<host>-<agent-id> -- \
  agents/<host>/<agent-id>/local/
```

### Why this is safe

- **Single writer per branch**: branch name embeds `host` and `agent-id`. No other instance ever writes the same branch — force-push is collision-free by design.
- **Independent of `main`**: orphan branches share no history with `main`. Force-push affects only the orphan branch's ref, never rewinds `main`.
- **Aligned with the priority chain**: `local/` was never part of the priority chain or the startup context. Moving it off `main` does not change agent behaviour.

### When to use this pattern (general rule)

For any future high-churn, poorly compressing artefact: **default to a per-agent orphan branch, not `main`**. Markdown memory (low-churn, human-curated) stays on `main`.

---

## 13. Tool-native memory carryover (protocol v2.5+)

Every coding agent keeps its own memory, and as of 2026-07 **all of it is machine-local**:

| Tool | Native memory location | Redirect setting |
|---|---|---|
| Claude Code | `~/.claude/projects/<project>/memory/` | `autoMemoryDirectory` in `settings.json` |
| Codex | `~/.codex/memories/` | none — only `CODEX_HOME` moves everything |
| Kimi Code | `~/.kimi-code/` | none — only `KIMI_CODE_HOME` |

Claude Code's own documentation states it plainly: *"Auto memory is machine-local. Files are not shared across machines or cloud environments."*

That leaves accumulated context exposed three ways: a new machine starts from zero, a discontinued tool takes its memory with it, and account-bound memory disappears with the account. The root cause is **ownership** — the vendor decides where your context lives and how long it survives.

Nestwork already solves this one layer up. This section connects tool-native memory to the same git-owned store.

### Landing place

```
agents/<host>/<agent-id>/
├── resident.md        # resident — current facts and retrieval pointers
├── memory.md          # on-demand history
└── carryover/         # cold — never injected
    ├── claude-code.md
    ├── codex.md
    └── kimi-code.md
```

`carryover/` is a **cold layer**: it is *never* loaded at session start. `memory.md` may point at it with a single line; it must not inline its content. Read it when restoring onto a new machine, or when deliberately looking something up.

### This is distillation, not mirroring

Use the §7 pipeline — read, filter, human review, merge, commit — with a new input. **Do not raw-copy a tool's memory directory into the nest.** A raw mirror carries duplicates and expired notes across, and the same fact then lives in two places that drift apart.

Filter by one question: **when does this stop being true?**

| When it stops being true | Where it goes |
|---|---|
| Already recorded in the nest | skip — do not write it twice |
| Its own stated delete-condition has fired | do not carry; propose removing the source |
| It is a fast-moving progress snapshot | do not carry — it expires the moment it is committed |
| Only when the machine changes, **and it must apply without being looked up** | `agents/<host>/<agent-id>/resident.md` — after scope review and within the byte budget |
| Only when the machine changes, **and it is needed only on restore** | `agents/<host>/<agent-id>/carryover/<tool>.md` |
| Never (portable method, cross-tool pitfall) | `workflow/<topic>.md` — desensitise first |
| When the project changes | that repository's own `docs/` — propose only, never write across repositories |

The resident/on-demand split is the one people get wrong. Ask whether the entry has to take effect *when nobody went looking for it*. A universal boundary may qualify — put it in `resident.md`; an API limitation belongs on demand unless every task needs it. How a local tool was installed must not — put it in `carryover/`. Resident entries compete for the session-start context budget; when in doubt, choose on demand.

### Restoring onto another machine

Some tools derive their project directory name from the repository's **absolute path**, so the same repository produces a different name on a machine with a different drive or checkout location. Every carryover entry therefore records both the original directory name and the repository it referred to:

```markdown
## <one-line title>

- **source**: `~/.claude/projects/<project-dir>/memory/<file>.md`
- **original project dir**: `<project-dir>` (repository: `<repo path>`)
- **carried on**: YYYY-MM-DD
- **criterion**: cold — needed only on restore

<body, keeping the original Why / How-to-apply structure>
```

On restore, recompute the directory name from the new machine's repository path and write the content back there.

### Notes

- Carryover is low-churn markdown, so it lives on `main`; the §12 orphan-branch rule does not apply.
- Routine flow is one-way: tool memory flows into the nest, and nothing syncs back into a tool's native store automatically. Restoring onto a new machine (above) is the only reverse step, and it is a deliberate, manual one.
- **Deleting a source memory after distilling is irreversible** — tool-native memory is not under version control. Extract anything worth keeping first.
- An instance that prefers a live mirror over periodic distillation can point a tool's memory directory into its agent folder where the tool supports it (for example Claude Code's `autoMemoryDirectory`). That is a local choice, not the protocol default: only some tools offer it, every write becomes a commit, and it drops the review step.

Rationale and rejected alternatives: `decisions/2026-07-28-tool-memory-carryover.md`.

---

## Priority Rules

```
queen/agent-rules.md  >  queen/strategy.md  >  shared/memory.md  >  agents/*/*/memory.md  >  projects/*.md  >  workflow/*.md
```

This is authority order, not startup load order: only the resident files in §1
load at startup, and a resident summary inherits the scope and priority of the
source it summarizes.

When instructions conflict, follow the higher-priority source.
Do not merge conflicting instructions — choose one.

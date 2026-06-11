# Workflow Protocol

> Companion to `AGENTS.md` Section 8 and Section 9. This document explains the rationale, mental model, and concrete usage patterns of the `workflow/` directory and the `nestwork.config.json` ingestion contract.

---

## Why `workflow/` exists

Nestwork already has four context categories:

- `queen/` — human-maintained rules and strategy
- `shared/` — cross-agent distilled facts about the user
- `agents/<host>/<id>/` — per-instance private memory
- `projects/<name>.md` — project-specific context

What was missing: a place for **portable user-level knowledge** that:

- Outlives any single project, employer, or machine
- Is not a fact about the user (that's `shared/`) but a methodology, discipline, or asset the user **uses**
- Is too generic for any single project but too specific to be a behavior rule

Examples:

- "Estimate by AI execution speed, not human-month."
- "Loading state UI: prefer skeleton screens for first paint, `v-loading` for refresh."
- "When initializing a new repo, create the 5-document skeleton (AGENT.md, conventions.md, domain.md, architecture.md, lessons.md)."
- "Migration checklist: 30 minutes to restore full workflow on a new machine."

These are workflow content. They go in `workflow/`.

---

## Three-tier mental model

```
┌─────────────────────────────────────────────────────────────────┐
│ Tier 1: Draft (lives in agent memory)                           │
│ - Raw observations, single-session impressions                  │
│ - Path: agents/<host>/<id>/memory.md or topic files             │
│ - Promoted to Tier 2 via distillation                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓ distill (Section 7 process)
┌─────────────────────────────────────────────────────────────────┐
│ Tier 2: Distilled (lives in private mynestwork)                 │
│ - Cross-agent stable workflow knowledge                         │
│ - Path: workflow/<topic>.md                                     │
│ - May contain employer / project names IF the private repo      │
│   acknowledges that risk                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓ human decision (NOT auto)
┌─────────────────────────────────────────────────────────────────┐
│ Tier 3: Exportable (manually copied to public surface)          │
│ - Blog posts, upstream nestwork PRs, public talks               │
│ - Must be desensitized to the level documented in               │
│   docs/desensitization-prompt.md                                │
│ - Upstream nestwork repo holds ONLY templates and methodology,  │
│   never user-specific content                                   │
└─────────────────────────────────────────────────────────────────┘
```

The boundary between Tier 2 and Tier 3 is a **human gate**. Protocol does not automate it. Upstream nestwork is read-only from the perspective of any private instance.

---

## What goes where

| Content | Location | Why |
|---|---|---|
| "I prefer Vue 3 + TypeScript" | `shared/memory.md` | Stable user fact |
| "Vue 3 components ≥ 1000 lines should be split by responsibility" | `workflow/coding-disciplines.md` | Methodology, portable |
| "sign-mgt-web uses ant-design-vue@4.x with custom theme" | `projects/sign-mgt-web.md` | Project-specific |
| "Today the agent observed user prefers `:loading` over spinning icons" | `agents/<id>/memory.md` | Single-session, may distill later |
| "Hook architecture (PreToolUse + PostToolUse atomic write)" | `workflow/tooling-stack.md` | Methodology + setup guide |
| "Strategy: prioritize small verifiable tools over platforms" | `queen/strategy.md` | Human-maintained direction |

If you cannot decide, ask: "Will this still apply when I change employers?"

- Yes → `workflow/`
- No → `projects/` or `agents/`

---

## Ingestion from external working directories

The most common use case for `nestwork.config.json`: a working directory outside Nestwork contains content the agent recognizes as worth absorbing.

### Trigger

The agent is operating in some path (e.g., `F:/code/project/sign-mgt-web/`) and detects:

- Stable patterns the user follows in this codebase that aren't captured anywhere
- Architectural decisions worth preserving across the user's career, not just this repo
- Methodologies discovered while working here that generalize

### Step-by-step flow

1. Agent identifies candidate content.
2. Agent checks for `nestwork.config.json` in the working directory or any parent.
3. **If absent**:
   - Agent stops and asks the user: "I'd like to ingest the following into Nestwork. This directory has no `nestwork.config.json`. Create one?"
   - Agent proposes a default template with `desensitize.level: "strong"`.
   - User reviews, customizes `custom_rules` (employer names, internal codenames, client names, etc.), and saves.
4. **If present**:
   - Agent reads `ingest.target`, `ingest.name`, `desensitize.level`, `desensitize.custom_rules`.
   - Agent applies desensitization per level.
   - Agent writes cleaned result to `<mynestwork>/<target>/<name>.md`.
5. Agent commits and pushes the new artifact under the standard write protocol.

### Default template

When agent prompts the user to create a config, the default content is:

```json
{
  "$schema": "https://github.com/songth1ef/nestwork/schemas/nestwork.config.schema.json",
  "version": "1.0",
  "ingest": {
    "target": "projects",
    "name": "<dir-name>"
  },
  "desensitize": {
    "level": "strong",
    "custom_rules": [
      "<employer-name>",
      "<internal-codename>",
      "<client-name>"
    ]
  }
}
```

`custom_rules` ships with placeholder entries to **force** the user to think about what's confidential before ingesting anything.

---

## Desensitization levels

### `none`

No transformation. Only valid when content is verifiably non-confidential — for example, a personal side project with no employer/client involvement.

### `weak`

Pattern-based redaction. The agent walks `custom_rules` and replaces matched strings with placeholders (`<EMPLOYER>`, `<CLIENT>`, etc.). Fast, deterministic, but misses semantic leaks (e.g., a sentence that describes the employer's business model without naming it).

### `strong`

AI-driven semantic desensitization. The agent uses the prompt template in `docs/desensitization-prompt.md` to:

1. Apply all `weak`-level redactions
2. Identify and rewrite content that leaks confidential information without naming it
3. Produce a candidate output for human review before committing

`strong` is the default for any new `nestwork.config.json` and is required for any content destined for Tier 3 (exportable).

### What upstream nestwork provides vs. what users provide

| Upstream nestwork | User (in `nestwork.config.json`) |
|---|---|
| The methodology (this document) | Specific employer/project/client names |
| The AI prompt template | Industry-specific terms to redact |
| The schema | Severity calibration via level choice |
| Empty `_template.md` files | All actual content |

**Upstream never contains specific names, codenames, or any user-identifying information.** This is enforced at the human-review gate when promoting Tier 2 → Tier 3.

---

## Conflict resolution and lifecycle

### Workflow content becomes stale

User changes employers, tools, or methodologies. Old `workflow/<topic>.md` may become inaccurate.

- Agents should flag staleness when they observe a contradiction during distillation
- Update is non-destructive: prefer adding a "Superseded" section to the bottom rather than deleting history
- Files that become entirely stale may be moved to `workflow/archive/<topic>.md`

### `nestwork.config.json` updates

When the user changes `custom_rules` (e.g., joins a new company), all future ingestions from that directory use the new rules. Past ingested artifacts in mynestwork are **not** retroactively re-desensitized; the user must manually review and update them if needed.

### When to NOT ingest

- The content is project-specific, not portable → keep it in `projects/<name>.md` only
- The user is not certain about confidentiality → don't ingest, ask first
- The directory has no `nestwork.config.json` and the user does not want to create one → respect that, do not ingest

---

## Quick reference

| Question | Answer |
|---|---|
| Where does `nestwork.config.json` live? | In the source working directory, never in Nestwork |
| Can content flow from mynestwork to upstream nestwork? | No. Upstream is human-maintained only |
| What happens if config is missing? | Agent stops and prompts the user to create one |
| What is the default desensitization level? | `strong` |
| Who decides what's confidential? | The user, via `custom_rules` |
| Where do specific employer names live? | Only in user's `custom_rules`, never in upstream |
| Is ingestion automatic? | No. Always agent-proposed, human-confirmed |

---

## Related sections

- `AGENTS.md` Section 7 — Memory Distillation Protocol (parallel mechanism for `shared/`)
- `AGENTS.md` Section 8 — Workflow Protocol (canonical rules)
- `AGENTS.md` Section 9 — `nestwork.config.json` Contract (canonical schema)
- `docs/desensitization-prompt.md` — AI prompt template for `strong` desensitization
- `schemas/nestwork.config.schema.json` — JSON Schema for `nestwork.config.json`

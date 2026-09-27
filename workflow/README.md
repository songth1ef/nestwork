# `workflow/` — Portable User-Level Knowledge

This directory holds **portable workflow knowledge** that survives across employers, projects, and machines: coding disciplines, tooling preferences, methodologies, migration guides, and skill assets.

It is the lowest-priority context layer in the Nestwork hierarchy. Higher layers can override workflow content; workflow can never override `queen/` rules or `shared/` facts.

## What goes here

- Cross-project coding disciplines (e.g. estimation rules, loading-state UI patterns)
- Tooling stack preferences and setup conventions
- Methodologies (e.g. 5-document repo skeleton, distillation workflow)
- Migration / cross-machine onboarding guides
- Prompt templates and skill asset inventories

## What does NOT go here

| Content | Goes to |
|---|---|
| Project-specific business rules | `projects/<name>.md` |
| Cross-agent stable facts about the user | `shared/` |
| Single-agent observations (raw, unprocessed) | `agents/<host>/<id>/memory.md` |
| Behavior rules or strategy | `queen/` (human-maintained) |
| Anything employer-confidential | Nowhere in this repo without desensitization |

The deciding question: *"Will this still apply when I change employers, machines, or projects?"* Yes → `workflow/`. No → somewhere else.

## How content arrives here

Two paths, both documented in `docs/workflow-protocol.md` and `AGENTS.md` §8:

1. **Distillation from agent memory** — when stable patterns emerge across sessions, an agent distills them into `workflow/<topic>.md`.
2. **Ingestion from external working directories** — when a working dir outside Nestwork has content worth absorbing, the source must declare a `nestwork.config.json` with desensitization rules (see `AGENTS.md` §9). The agent applies those rules and writes the cleaned result here.

## Templates

- `_template.md` — empty workflow document scaffold; copy and rename when starting a new topic file.

## File size

200-line limit per topic file. When exceeded, split per the universal rule in `AGENTS.md` §6:

```
workflow/coding-disciplines.md  (250 lines)
  ↓ split
workflow/coding-disciplines.md  (becomes index)
workflow/coding-disciplines/loading-states.md
workflow/coding-disciplines/estimation.md
workflow/coding-disciplines/file-splits.md
```

## Upstream vs. private instance

In the **upstream `nestwork` template**, this directory contains only `README.md` and `_template.md` — no actual workflow content. Specific user content lives only in private instances (e.g. `mynestwork`).

Upstream is human-maintained. Content does not flow from private instances back to upstream automatically. Promotion of any artifact to upstream (or any public surface) is a separate, manual human decision.

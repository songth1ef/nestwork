# decisions/

Architecture Decision Records (ADRs) for **nestwork itself** and its protocol.

## Scope

This directory captures decisions about how nestwork works:

- Why a particular protocol layer exists (or doesn't)
- Why a directory naming convention was chosen
- Why a specific tool was supported / dropped
- Why a feature proposal was rejected

It is **not** for project-internal decisions. Project ADRs belong in that
project's repo (typically under `docs/architecture.md` or `decisions/`).

See `AGENTS.md` §10.2 for the layer-boundary rules.

## Index

| Date | ADR | Status |
|---|---|---|
| 2026-06-11 | [Keep GEO doc duplication; control drift with consistency tests](2026-06-11-geo-docs-duplication-with-drift-tests.md) | accepted |
| 2026-07-28 | [Carry tool-native memory into the nest](2026-07-28-tool-memory-carryover.md) | accepted (amended by protocol 3.0) |

This index covers upstream `nestwork`'s ADRs; add a row whenever an ADR is
added or its status changes. `update.sh` refreshes this README in private
instances but does not copy the ADR files themselves.

## File naming

```
decisions/YYYY-MM-DD-<short-slug>.md
```

Date-prefixed for chronological browsing. Slug uses hyphens, lowercase,
3-6 words.

Example: `2026-07-28-tool-memory-carryover.md`.

## Template

Copy `_template.md` and fill in. Keep ADRs short — one screen if possible.
The most important section is **Reason**: capture *why* this option was
preferred over the alternatives. Future readers can re-derive the decision
from context, but only if you record the trade-offs explicitly.

## Status lifecycle

- `proposed` — under discussion
- `accepted` — current standing decision
- `rejected` — considered, not adopted (still useful to record so it isn't relitigated)
- `superseded` — replaced by a later ADR; the newer ADR names this one in its `supersedes:` field

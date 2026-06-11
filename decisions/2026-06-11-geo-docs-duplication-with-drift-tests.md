# Keep GEO doc duplication; control drift with consistency tests

- date: 2026-06-11
- status: proposed
- supersedes: —

## Context

The repo intentionally repeats core facts — the priority chain, the layer
table, version/protocol numbers — across README (EN/ZH), AGENTS.md, and the
answer-ready `docs/*.md` stubs, so AI search systems can cite any single file
without following links. A 2026-06 audit found the cost of that strategy:
two docs shipped a 5-layer priority chain for several releases after v2.2
added `workflow/`, the README version line sat three releases stale, and a
hardcoded consistency test went red without anyone noticing. Every protocol
change must currently be hand-propagated to roughly five places.

## Decision

Keep the duplication (it is the point of the GEO strategy), and make drift
mechanically detectable instead: every duplicated fact gets a consistency
test that derives the expected value from its single source of truth.

## Options considered

- **Deduplicate into one canonical doc + links** — defeats the GEO purpose;
  answer-engine snippets need self-contained pages.
- **Generate the stubs from templates at release time** — adds a build step
  to a repo whose core promise is "plain markdown + git, no tooling
  required"; overkill for ~8 short files.
- **Keep duplication, add derived consistency tests (chosen)** — zero new
  infrastructure; drift becomes a red test instead of a silent lie.

## Reason

The duplication is load-bearing for discoverability, and the observed
failure mode was never the duplication itself — it was that nothing noticed
when copies diverged. Tests that *derive* expectations (from `VERSION`,
`AGENTS.md`'s protocol-version marker, the canonical chain) cannot
themselves go stale the way hardcoded assertions did.

## Consequence

- Any new rendition of the priority chain, version string, or protocol
  marker must be covered by `tests/test_docs_consistency.py` (the chain and
  version tests already scan all markdown / derive from source files, so
  most new copies are covered automatically).
- CLAUDE.md is enforced as a byte-exact mirror of AGENTS.md; edit AGENTS.md
  and regenerate, never edit CLAUDE.md directly.
- If the stub count grows well beyond the current ~8 files, revisit the
  generate-from-template option.

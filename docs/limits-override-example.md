# File size limits — override example

> **Copy this file to `queen/limits.md` to activate an override**, then edit the
> table. Agents read `queen/limits.md`; this page is documentation and has no
> effect where it sits.
>
> It ships here in `docs/` rather than as a live `queen/limits.md` for two
> reasons. A live file in every instance would freeze that instance's numbers,
> and since `update.sh` never touches `queen/`, later changes to the protocol
> defaults in `AGENTS.md` §6 would stop reaching it. And `docs/` **is** synced by
> `update.sh`, so this example keeps arriving as the defaults evolve — `queen/`
> stays entirely yours.

> Once copied into `queen/`, the file is read-only for agents. Only humans modify it.

updated: YYYY-MM-DD

---

## Why this file exists

The limits in `AGENTS.md` §6 are protocol defaults synced from upstream. This
file lets a private instance tune them **without editing the protocol layer**,
which `update.sh` would overwrite. It lives in `queen/`, so upstream sync never
touches it, and agents load it at session start as part of the high-priority
`queen/` layer.

The right variable to tune against is **retrieval quality / attention**, not raw
context-window size. A larger model window does **not** justify proportionally
larger files — attention still degrades with token count, and selective loading
stays sharper with focused, topic-split files.

Raise a limit only when you observe the current cap forcing awkward
over-splitting — not just because the context window grew.

## Limits

Values below are the `AGENTS.md` §6 defaults. Change only the rows you actually
need to differ; keep the rest so the table stays a complete picture.

| File | Max lines | Split target |
|---|---|---|
| `queen/agent-rules.md` | 80 | `queen/rules/<topic>.md` |
| `queen/strategy.md` | 80 | `queen/strategy/<topic>.md` |
| `agents/<host>/<agent-id>/memory.md` | 200 | `agents/<host>/<agent-id>/<topic>.md` |
| `shared/memory.md` | 500 | `shared/<topic>.md` |
| `projects/<name>.md` | 150 | `projects/<name>/<topic>.md` |
| `workflow/<topic>.md` | 200 | `workflow/<topic>/<subtopic>.md` |
| (default — any other markdown) | soft 500 / hard 1000 | filename → folder + index |

This file changes **which numbers apply**, not the split mechanics. Splitting
always follows the universal rule in `AGENTS.md` §6: filename becomes a folder,
the original file becomes a pure index of links.

## Tuning log

Record every change with the reason. Without it, a future maintainer cannot tell
a deliberate tune from a stray edit.

- YYYY-MM-DD — Seeded from `AGENTS.md` §6 defaults. Values unchanged; this file
  is the place to adjust them.

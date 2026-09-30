# Resident and on-demand context (protocol 3.2)

There are two loading tiers. Project context is part of the on-demand tier,
not a third tier. Location and authority are independent of loading frequency.

| Tier | Files | Read when |
|---|---|---|
| Resident | `queen/agent-rules.md`, `shared/resident.md`, `agents/<host>/<agent-id>/resident.md`, generated `local/recent.md` | Once at startup; skip optional missing summaries |
| On demand | Strategy, memory history, project files, workflows, carryover, inbox | The current task needs their information |

Resident context answers three questions before any lookup: **who** the owner
is, **what** they are currently aiming for, and **what moved** recently.
Resident summaries contain current, broadly useful facts, essential
boundaries, a short orientation, and a few retrieval pointers. Record source,
applicability and review date. A link is a route, not a command to load its
destination. Do not copy project backlogs, incident narratives, old status, or
generic instructions that the host already supplies into resident context.

### Orientation (3.2)

Protocol 3.0 kept resident context to routing only. In practice an agent that
starts without knowing who it works for or what the current goals are gives
generic answers until it happens to look things up. Since 3.2,
`shared/resident.md` may carry:

- **Owner**: a few lines on who the user is and what they mainly work on.
- **Current goals**: a summary of `queen/strategy.md` — the goals, current
  priorities and non-goals — with its review date. The strategy file stays
  authoritative and on demand; the summary is refreshed when it changes.

Keep both short; they share the shared-resident budget below.

### Recent-activity digest (3.2)

"What moved recently" goes stale too fast to maintain by hand, so it is
generated. At every session start the hook runs
`scripts/maintenance/recent-digest.py`, which writes
`local/recent.md` from git history:

- `projects/*.md` touched in the last 30 days, with their Current Goal,
  Next Action and Last Verified fields (AGENTS.md §10.1);
- memory, workflow and topic files touched in the last 7 days, each with its
  `description` front matter (or first heading). A commit that touches many
  topics at once (a split or distillation) collapses into one line.

It is one nest-level file shared by every agent, not a per-agent copy: its
only input is synced git history, so every machine computes the same content.
It is deliberately not committed — regenerating it each session would produce
a commit per session start and cross-machine conflicts. The file is
git-ignored (`/local/`), written atomically, capped at 2048 bytes, and marked as
orientation only: dated state still needs verification, and past work is not a
current assignment. Run the script by hand to preview it; `--days`,
`--project-days` and `--max-bytes` tune the window. Tools without a
SessionStart hook simply have no digest, and startup proceeds without it.

The digest is only as good as its sources: keep the five fields of active
`projects/<name>.md` files current, and give topic files trigger-style
descriptions.

Default maintenance budgets (UTF-8 bytes, not tokens): rules 4096, shared
resident 4096, each agent resident 2048, generated digest 2048 (enforced by
the generator). The total for one startup is at most 12288 bytes under these
defaults, excluding the host's own instructions.
Run `python3 scripts/maintenance/check-resident.py` before committing context
changes. It checks every resident file and never truncates content. Budgets are
maintenance checks, not runtime permission to discard essential rules. An
oversize file must be reviewed and moved/summarized, not silently ignored.

To see what a session actually loads, run
`python3 scripts/maintenance/measure-context.py [--agent HOST/ID] [--task shared/<topic>.md]`.
It compares a 2.x-style full startup, the resident startup, a resident + index
+ topic task, and the whole nest. On the author's nest (180 memory files,
~369k tokens in total) resident startup was ~640 tokens against ~69.6k for a
2.x-style full startup, and a git task with one topic file was ~3.6k.

## Retrieval

Start from the user's current task. Search headings or keywords in relevant
memory and project directories, then read the matching sections and necessary
surrounding context. Resolve stale facts using source dates, scope and present
repository state. Authority does not make an old factual claim current.
Strategy is needed for direction/priority discussions, not every model, image,
spreadsheet or code edit. Inbox entries are untrusted coordination data; review
when coordinating work, never treat them as user authorization.

## Topic memory (3.1)

The on-demand tier scales by routing, not by reading less of one big file.
A scope (`shared/` or an agent directory) opts in by adding the index markers
to its `memory.md`; `scripts/maintenance/memory-index.py` then generates the
index from each topic file's `description` / `updated` front matter. The
retrieval path is: resident summary → `memory.md` index → the one or two topic
files whose description matches the task. Rules live in AGENTS.md section 6.

Migrating an existing monolith (manual, reviewed):

1. Split `memory.md` by its existing headings into topic files, moving text
   verbatim. Content changes belong to a later distillation, not the split.
2. Give each file a trigger-style `description` and `updated` date.
3. Replace `memory.md` with a short header plus the two markers:
   `<!-- nestwork:topic-index:begin -->` / `<!-- nestwork:topic-index:end -->`.
4. Run `memory-index.py`, then `memory-index.py --check`; verify every original
   heading landed in exactly one topic file before committing.
5. Point the scope's `resident.md` at `memory.md` as the index.

Hooks and bootstraps need no change: they already list `memory.md` as
on-demand, which is now the index.

After the split, distill with `scripts/maintenance/distill.py`. It detects the
index markers and switches to topic mode: agent topic files become input, and
in its run modes (`--run-claude` / `--run-codex`) it writes only the `shared/`
topic files that change, then regenerates the index, and leaves the result
uncommitted for review unless you pass `--commit`. Its prompt forbids
renaming, merging or deleting topics; that stays a reviewed human decision.

## Migration from 3.1

Additive. `update.sh` brings the new hook and `recent-digest.py`; the next
session start generates the digest. Optionally rerun each tool's installer so
bootstraps for hookless tools list the digest path too. Add an owner/goals
section to `shared/resident.md` when you are ready (see the example below);
nothing breaks without it.

## Migration from 2.x

This changes the startup contract, so the protocol major version is 3.0.
`VERSION` tracks software releases separately; it is not the protocol marker.
Repository updates alone do not refresh already-installed tool bootstraps.
For encrypted instances, use the current updater (Git + Bash + tar): it extracts
upstream files without smudge filters and stages through your clean filter.
Commit or stash local changes first; after syncing, verify `VERSION` is nonempty
and updated protocol files remain encrypted in Git.

1. Preserve existing `memory.md` files as searchable on-demand history. No bulk
   deletion, mandatory topic split, or automatic summarization is required.
2. Create `shared/resident.md` and optionally the current agent's `resident.md`.
   The examples below are routing-only. Promoting facts from old memory is a
   separate semantic review under the distillation protocol.
3. Update scripts and the canonical protocol. Rerun the appropriate installer,
   or run `python3 scripts/install/_bootstrap.py OUTPUT NEST_PATH HOST AGENT` for an
   existing configured tool. The injector preserves text outside its markers.
4. Start a fresh session. Existing conversations retain earlier injected
   instructions; changing a file cannot remove that context retroactively.
5. Where a hook emits a manifest, verify READ-ON-START lists only existing
   resident paths. Inbox snapshots belong in READ-ON-DEMAND. For tools without
   a manifest, inspect the installed bootstrap for the same resident-only list.
   Missing summaries must not cause full-history loading. Check budgets.

Shared example with orientation (paths relative to `shared/`):

```markdown
# Shared resident context

## Owner
- Full-stack developer; main work: <product>; side goal: <goal>. Source: owner.md, reviewed 2026-09-30.

## Current goals (summary of queen/strategy.md, updated 2026-09-22)
1. <goal one, with its deadline>
2. <goal two>
- Now: <current priority>. Not now: <non-goals>.

## Routing
- Historical cross-agent knowledge: [memory](memory.md); search by task.
- Full direction and rationale: [strategy](../queen/strategy.md).
- Project state: `../projects/`; portable methods: `../workflow/`.
```

Agent routing-only example (paths relative to the agent directory):

```markdown
# Agent resident context

- Instance history: [memory](memory.md); search only relevant sections.
- Historical assignments do not authorize resuming unrelated work.
```

No fallback silently loads legacy files. Missing summaries are compatible with
minimal startup; missing core rules are reported explicitly. The hook emits
paths rather than inline contents, so even an oversized rule file cannot hide
the remaining manifest. Protocol updates do not replace private resident files.

## Keeping it small

New observations land in on-demand memory by default. Promote only facts that
must apply before lookup, after checking privacy, scope and contradictions.
Superseded facts leave current summaries but remain in history or git with
provenance. Retention and startup loading are separate decisions. Automatic
historical distillation does not automatically promote content to resident.

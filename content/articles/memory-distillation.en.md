---
title: Memory Distillation — Consolidating AI Agent Memory
description: Memory distillation merges many agents' private notes into one reviewed shared memory. What belongs in it, the review flow, and how distill.py runs it.
keywords: memory distillation AI agents, consolidate agent memory, shared memory, merge agent memories, distill.py, nestwork
date: 2026-09-27
---

What is memory distillation for AI agents? It is the step that turns many agents' private notes into one shared memory: read every agent's memory, filter out what is temporary, check the rest for sensitive data and contradictions, merge it, and have a human confirm before it becomes shared. In nestwork it is always explicitly triggered, never destructive, and `scripts/maintenance/distill.py` writes its result to the working tree for review instead of committing it.

Below: why distillation is needed, what should and should not go into shared memory, the review flow, and how `distill.py` works in its three modes.

## Why several agents need a distillation step

When each agent writes only to its own directory, writes never collide (see [multi-agent memory without conflicts](../multi-agent-memory-without-conflicts/)). The cost is that knowledge ends up scattered. The Claude Code agent on your laptop learned that you prefer small commits; the Codex agent on your desktop learned the same thing in different words; a third agent recorded a lesson nobody else has seen.

Every agent can read every directory, but reading 30 private memories each session defeats the point of selective loading. Distillation produces one place, `shared/`, where stable cross-agent facts live, deduplicated and reviewed. It ranks above private memory in the priority chain, so once a fact is distilled, agents treat it as the common baseline.

## What belongs in shared memory

[AGENTS.md §7](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md) draws the line:

| Include | Exclude |
|---|---|
| Cross-agent stable facts (user identity, stack, preferences) | Temporary task details |
| Validated collaboration patterns | One-off debugging notes |
| Decisions with lasting impact | Agent-specific context |

Three rules keep the merge safe:

- **Union, not intersection.** An observation only one agent made is kept. Distillation does not drop unique knowledge because others didn't see it.
- **Non-destructive.** Each agent's private memory stays exactly as it was. Distillation reads it and writes only `shared/`.
- **Not automatically resident.** Distilled content lands in the on-demand tier. Promoting anything into a resident summary is a separate decision.

Divergent observations that are both valid, such as different settings on different machines, are kept side by side rather than forced into one.

## When to distill

Only when you ask. The trigger is a human request, or a scheduled job the human configured. An agent that notices something worth sharing at the end of a session does not write `shared/`; it records the candidate in its own directory, where the next distillation picks it up. That keeps 30 agents from editing shared memory whenever they feel like it.

## The flow: sub-agent review plus human confirmation

The protocol's eight steps:

1. Read all agents' memory, including topic files for topic-mode scopes.
2. Read current `shared/`: the single `memory.md`, or in topic mode the index and every shared topic file.
3. Spawn a sub-agent to review for sensitive data, factual errors, contradictions and outdated entries. It reports only; it does not write.
4. Present the review report to the human for confirmation.
5. Merge: remove duplicates, unify consistent facts, keep divergent observations.
6. Keep historical evidence in the on-demand tier; replace superseded facts in current summaries with provenance, rather than appending forever.
7. In topic mode, write only changed topic files, regenerate the index and run `memory-index.py --check`. List structural changes (rename, merge, delete, new top-level folder) separately in the review.
8. Commit with `memory: distill shared`.

Steps 3 and 4 are the reason the tooling does not commit by default: a human has to see the result first.

## `distill.py`: three modes

[`scripts/maintenance/distill.py`](https://github.com/songth1ef/nestwork/blob/main/scripts/maintenance/distill.py) collects every non-empty agent memory and builds the merge prompt. How it runs depends on the flag:

| Mode | Command | What happens |
|---|---|---|
| Prompt (default) | `distill.py` | Prints a ready-made merge prompt; paste it into any agent session |
| Claude runner | `distill.py --run-claude` | Runs the merge through `claude -p` and writes the result |
| Codex runner | `distill.py --run-codex [--profile <p>]` | Runs the merge through `codex exec` and writes the result |

The two runners are mutually exclusive, and `--profile` applies to Codex only. The prompt mode is vendor-agnostic on purpose; the script's own comment notes that a distiller tied to a single vendor stops working the moment that subscription lapses.

Both runners are sandboxed from the nest's own bootstrap. The Claude runner passes an empty tool list and no setting sources, so a `CLAUDE.md` startup protocol cannot turn the run into a session-start summary; the Codex runner uses a read-only sandbox in an empty temporary directory.

Then the flags that control writing:

```bash
python3 scripts/maintenance/distill.py --run-claude --dry-run   # print candidate, write nothing
python3 scripts/maintenance/distill.py --run-claude             # write shared/, do not commit
git diff -- shared/                                             # review
git commit -m "memory: distill shared" -- shared/
```

Not committing is the default. The run ends with a hint to review `git diff -- shared/` and commit. `--commit` pulls, writes, commits with `memory: distill shared` and pushes in one run, and `--no-push` keeps that commit local. Use `--commit` only when you have already accepted skipping review, for example in a scheduled job you set up. `--no-commit` is still accepted for compatibility but changes nothing.

## Topic mode: write only what changed

If `shared/memory.md` carries the topic-index markers (see [loading memory on demand](../topic-memory-on-demand-loading/)), `distill.py` switches to topic mode automatically:

- Agent topic files become part of the input.
- The model is asked to output only topic files that change or are new, each in full between `<<<FILE shared/<topic>.md` and `>>>END`.
- The script rejects invalid paths (only lowercase kebab-case, at most one subfolder, never `memory.md` or `resident.md`) and any file without a `description`.
- It writes those files, regenerates the index, and refuses to continue if the index check finds problems.

The prompt forbids renaming, merging or deleting topics; that stays a reviewed human decision. Rewriting a split nest back into one file on every run would undo the split, which is also why the plain concatenation script `compile.sh` refuses to run on a topic-mode `shared/`.

In single-file mode the script expects a `# SHARED MEMORY` header and warns if the result passes 500 lines, the protocol limit for `shared/memory.md`.

## The same pipeline for tool-native memory

Distillation is also how nestwork carries Claude Code, Codex or Kimi Code's own machine-local memory into the nest ([AGENTS.md §13](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md)). The input changes, the pipeline doesn't: read, filter, review, merge, commit. The filter question there is "when does this stop being true?", and raw-copying a tool's memory folder is explicitly ruled out because duplicates drift apart. More in [rescuing tool-native memory](../rescue-tool-native-memory/).

## FAQ

### Does distillation delete my agents' memory?

No. It only reads private memory and writes `shared/`. Each agent's directory is left unchanged, so you can always go back to the original observations.

### Can I run distillation on a schedule?

Yes, if you configure it. A scheduled job would typically use `--run-claude --commit` or `--run-codex --commit`, which skips the human review; the protocol allows that only when you have accepted the trade-off.

### What is the difference between `compile.sh` and `distill.py`?

`compile.sh` concatenates agent memory into `shared/memory.md` and commits it; no model, no deduplication. `distill.py` uses a model to merge and deduplicate, and leaves the result for review. `compile.sh` refuses to run once `shared/` uses topic memory.

### Who reviews the result if I use the prompt mode?

You and the agent session you pasted it into. Follow steps 3 and 4: have a sub-agent check for sensitive data, errors, contradictions and stale entries, read its report, then write and commit.

## Related

- [Multi-agent memory without conflicts](../multi-agent-memory-without-conflicts/)
- [Loading agent memory on demand](../topic-memory-on-demand-loading/)
- [Rescuing tool-native memory](../rescue-tool-native-memory/)
- [Git-native agent memory: why git is enough](../git-native-agent-memory/)
- [Memory is a protocol problem](../memory-is-a-protocol-problem/)

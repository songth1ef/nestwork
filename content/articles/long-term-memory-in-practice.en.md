---
title: AI Agent Long-Term Memory in Practice: What Changes
description: What persistent context across sessions is like day to day: how memory accumulates, what happens on a new machine or tool, and the upkeep it needs.
keywords: AI agent long-term memory, persistent context across sessions, AI coding agent memory, agent memory maintenance, nestwork, Claude Code memory
date: 2026-09-27
---

**What is it actually like to give an AI coding agent long-term memory?** Mostly, you stop noticing it. You open a session, the agent already knows your rules and where it can look up past decisions, and you skip the "who are you, where were we" preamble. With nestwork, memory is Markdown in a private git repo: writes are committed and pushed as they happen, other machines and tools pick them up on their next pull, and startup stays small because history is read only when a task needs it.

This article answers the questions people ask after the first week: how memory builds up, what happens when you switch machines or tools, what to do when there is a lot of it, and what upkeep it needs.

## Does memory build up by itself?

Partly. It helps to separate *deciding what to keep* from *keeping it*.

Deciding is still yours. nestwork's [README](https://github.com/songth1ef/nestwork/blob/main/README.md) puts it plainly: when you reach a decision, a lesson or a change in project status, you tell the agent to record it, or accept its suggestion to. The protocol also asks agents to save only context worth preserving, not temporary task details or one-off debugging notes.

Keeping is automatic. On Claude Code and Kimi Code, every Write/Edit inside the agent's own directory is wrapped by hooks:

1. Before the write: `git pull --rebase`, so the agent does not overwrite a newer remote version. A conflict blocks the write.
2. After the write: `git add`, a commit named `memory: update <host>/<agent-id>`, and a push, retried up to three times.
3. At the end of each turn: a Stop hook repeats the commit and push as a safety net; it does nothing when the tree is clean.

Codex, Gemini CLI and the other tools without per-write hooks follow the same protocol from their startup file and commit their directory at the end of the session. The result looks the same in git log: a steady trail of small, dated memory commits, each one reversible.

## What loads when a session starts?

Very little, on purpose. Since protocol 3.0 a session loads only the resident tier: `queen/agent-rules.md` (your rules), `shared/resident.md` and the agent's own `resident.md`. Everything else, including your strategy, the history in `memory.md`, `projects/` and `workflow/`, is searched when the task calls for it.

The author measured this on his own nest (10 machines, 30+ agent instances, September 2026, token counts with `o200k_base`):

| What gets loaded | Files | Tokens |
|---|---|---|
| 2.x-style full startup (rules, strategy, all memory, workflows) | 37 | ~69,600 |
| 3.x startup, resident tier only | 2 | ~640 |
| 3.x task: a git operation (resident + index + one topic) | 4 | ~3,600 |
| Every memory file in the nest | 180 | ~369,000 |

The practical effect: memory can keep growing without making every session start heavier. Resident files have byte budgets (4096 for rules, 4096 for the shared summary, 2048 per agent) that `scripts/maintenance/check-resident.py` checks before you commit.

## What happens on a new machine?

You clone the nest and run the installer for your tool. The new machine gets its own agent directory, for Claude Code an id with a random suffix such as `claude-a7k2`, so it starts with an empty private memory file. It is not starting from zero, though: the shared summary, `shared/memory.md`, every other agent's memory, your projects and your workflows are all in the same clone, available on demand.

This is the exact problem nestwork was built for. In [the author's first write-up](../16-agents-one-brain/), an agent on machine A wrote down that a project's deploy script had a nasty gotcha, and the next day the agent on machine B stepped on the same rake. The first time it worked with git, he had an agent record a decision on Windows, pulled on the Mac, and Codex read it. Once per-write sync was in place, he writes that losing memory across machines or having two machines collide "just hasn't happened again."

## What happens when you switch tools?

Install nestwork for the new tool. The installer injects the startup protocol into that tool's config file and gives it its own identity, so Claude Code, Codex and the others each have a directory but read the same rules, projects and shared memory. The README's tool-migration scenario sums it up: memory is in your git repo, not a vendor, so the cost of switching tools is close to zero.

The tools' own built-in memory is a separate matter. Claude Code's documentation says auto memory lives under `~/.claude/projects/<project>/memory/` and is "machine-local... not shared across machines or cloud environments" ([Claude Code memory docs](https://code.claude.com/docs/en/memory)). nestwork's protocol (AGENTS.md §13) treats that as something to *distill* into the nest, not mirror: stable, portable points go into `workflow/` or shared memory, machine-specific restore notes go into a cold `carryover/<tool>.md` that is never loaded at startup, and fast-moving progress snapshots are dropped.

## What do you do when memory gets big?

Three mechanisms, all explicit rather than magic:

- **File limits and splits.** Agent `memory.md` is capped at 200 lines, `shared/memory.md` at 500, `projects/<name>.md` at 150. Past the limit, a file becomes an index plus topic files.
- **Topic memory (protocol 3.1, opt-in).** A scope's `memory.md` becomes a generated index. Each topic file starts with a `description` that says *when* to read it, and the agent opens only the one or two files that match the task. The migration is manual and reviewed: split by existing headings, move text verbatim, then run `memory-index.py`.
- **Distillation.** When several agents have learned overlapping things, `scripts/maintenance/distill.py` merges them into `shared/`. It never runs on its own, and by default it writes the result to your working tree without committing, so you review `git diff -- shared/` first. Shared memory is a union: an observation only one agent made is kept, and each agent's private memory is untouched.

Distilled content is *not* automatically promoted to startup. Only reviewed, stable facts that must apply before anyone looks them up belong in a resident summary.

## What upkeep does it need?

A short list, none of it daily:

| Task | Command or place |
|---|---|
| Check startup budgets before committing context | `python3 scripts/maintenance/check-resident.py` |
| Rebuild and validate topic indexes | `python3 scripts/maintenance/memory-index.py`, then `--check` |
| Merge agents' memory into shared | `python3 scripts/maintenance/distill.py --run-claude` (or `--run-codex`), review, commit |
| See what sessions really load | `python3 scripts/maintenance/measure-context.py` |
| Keep the mailbox scan small | `bash scripts/comms/archive.sh 30` |
| Pull protocol updates | `bash scripts/maintenance/update.sh` |

One habit matters more than any script: treat old facts with suspicion. The protocol says residency controls loading, not truth, and agents should verify dated project state before acting on it. The recommended `projects/<name>.md` format ends with a "Last Verified" field for this reason.

## FAQ

### Will the agent remember everything I said?

No, and it should not. nestwork keeps what you or the agent decide to record, not raw transcripts. An optional feature can copy local prompt history, but the README recommends leaving it off.

### Does a bigger memory make every session slower?

Startup cost stays flat, because only the resident files load. Cost grows only with what a given task chooses to open.

### How do I undo a bad memory entry?

Edit or remove it like any file, or revert the commit. Every write is a separate git commit, so you can see when a fact appeared and which agent wrote it.

### Can I see what my agents know?

Yes. It is plain Markdown in your own repo; open it in any editor or browse it on your git host.

## Related

- [AI agent memory, explained](../ai-agent-memory/)
- [Topic memory and on-demand loading](../topic-memory-on-demand-loading/)
- [Memory distillation](../memory-distillation/)
- [Claude Code memory across machines](../claude-code-memory-across-machines/)
- [Rescue a tool's native memory](../rescue-tool-native-memory/)

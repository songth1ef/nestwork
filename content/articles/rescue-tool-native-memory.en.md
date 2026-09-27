---
title: Back Up and Migrate Your AI Agent's Native Memory
description: Claude Code auto memory and Codex memories live on one disk. How to back up and migrate AI agent memory before a new laptop, tool switch or lost account.
keywords: Claude Code auto memory backup, migrate AI agent memory, Codex memories backup, AI agent memory lost new computer, tool-native memory, nestwork carryover
date: 2026-09-27
---

The memory that Claude Code, Codex and Kimi Code keep for themselves is stored on your local disk, so it is lost when you get a new laptop, wipe a machine, or stop using the tool. To keep it, copy out what is still true before that happens, put it somewhere you own and version (such as a private git repo), and write down which project each note belonged to so you can restore it later. nestwork calls this *carryover*: distill native memory into a cold file in your agent's directory, instead of mirroring the whole folder.

## Where native memory lives

| Tool | Native memory | Move it with | Synced across devices? |
|---|---|---|---|
| Claude Code | `~/.claude/projects/<project>/memory/` | `autoMemoryDirectory` setting | No: "Auto memory is machine-local" ([docs](https://code.claude.com/docs/en/memory)) |
| Codex CLI | `~/.codex/memories/` (opt-in) | Only `CODEX_HOME`, which moves all Codex data | Not described; stored under your Codex home ([docs](https://learn.chatgpt.com/docs/customization/memories?surface=cli)) |
| Kimi Code | Runtime data under `~/.kimi-code/` | Only `KIMI_CODE_HOME`, which moves everything | Not described; stored locally ([docs](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/data-locations.html)) |

Claude Code's documentation puts it most plainly: auto memory files "are not shared across machines or cloud environments." None of the three vendors documents a built-in way to move this memory to another device.

## Three ways it gets lost

nestwork's [design decision on carryover](https://github.com/songth1ef/nestwork/blob/main/decisions/2026-07-28-tool-memory-carryover.md) names three failure modes:

1. **New machine.** Build commands, conventions, and traps the agent learned are simply not there on the new disk.
2. **Tool goes away.** Tools get discontinued, replaced, or you just move on. If the memory only exists inside the tool, the tool's end is the memory's end.
3. **Account goes away.** Where memory is tied to an account rather than a disk, a suspension, a regional restriction, or a lapsed subscription can take it with it.

The common cause is ownership: the vendor decides where your context lives and how long it lasts.

## Why a plain folder copy is not enough

Copying `~/.claude` or `~/.codex` to a USB stick is better than nothing, but it has two problems.

First, it restores to the wrong place. Claude Code names each project folder after the working directory path with non-alphanumeric characters replaced by `-` ([sessions docs](https://code.claude.com/docs/en/sessions)). Check out the same repository at a different path or on a different drive and the folder name changes, so the copied memory is attached to nothing.

Second, a raw mirror carries everything: duplicates, stale progress notes, and facts you already keep elsewhere. The same fact then lives in two places that drift apart.

## The nestwork approach: distill, don't mirror

[AGENTS.md §13](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md) treats native memory as one more input to the existing distillation pipeline: read, filter, have a human review, merge, commit. The filter is one question: **when does this stop being true?**

| When it stops being true | Where it goes |
|---|---|
| Already recorded in the nest | Skip it |
| Its own delete-condition has fired | Don't carry; propose removing the source |
| It's a fast-moving progress snapshot | Don't carry; it's stale on arrival |
| Only when the machine changes, and it must apply without lookup | `agents/<host>/<agent-id>/resident.md`, within its byte budget |
| Only when the machine changes, and it's needed only on restore | `agents/<host>/<agent-id>/carryover/<tool>.md` |
| Never (a portable method or cross-tool pitfall) | `workflow/<topic>.md`, desensitized first |
| When the project changes | That repository's own docs; propose it, don't write across repos |

The resident-versus-on-demand call is the one people get wrong. Ask whether the note must take effect when nobody went looking for it. A universal boundary may qualify. How a local tool was installed does not. Resident files compete for a small startup budget (2,048 bytes per agent resident file by default), so when in doubt, choose on demand.

## The cold layer and the directory-name problem

`carryover/` is a cold layer. It is never loaded at session start; `memory.md` may point to it with one line but must not inline it. You read it when restoring onto a new machine, or when you deliberately look something up.

Because of the path-derived folder names, every carryover entry records both the original directory name and the repository it referred to:

```markdown
## <one-line title>

- **source**: `~/.claude/projects/<project-dir>/memory/<file>.md`
- **original project dir**: `<project-dir>` (repository: `<repo path>`)
- **carried on**: YYYY-MM-DD
- **criterion**: cold — needed only on restore

<body, keeping the original Why / How-to-apply structure>
```

On restore, you recompute the folder name from the repository's path on the new machine and write the content back there. That is the only step that flows back into a tool's native store, and it is manual.

## Doing a carryover, step by step

1. Install nestwork for the tool on this machine (for example `bash ~/nestwork/scripts/install/claude.sh`), so your agent directory exists.
2. List what the tool holds: `~/.claude/projects/*/memory/` for Claude Code, `~/.codex/memories/` for Codex.
3. Ask the agent to distill it per §13: sort each entry with the table above and draft `carryover/<tool>.md` plus any resident candidates.
4. Review the draft yourself. Remove anything sensitive; API keys and secrets never go into the nest.
5. Let it commit. With Claude Code the per-write hooks push immediately; with Codex, the agent runs the commit step from its bootstrap.
6. Only after the nest has it, decide whether to delete the source. Deleting native memory is irreversible because it is not under version control.

If you would rather have a live copy than periodic distillation, Claude Code lets you point `autoMemoryDirectory` into your agent folder. §13 allows that as a local choice, not the default: only some tools support it, every write becomes a commit, and you lose the review step.

## FAQ

### Can I back up Claude Code auto memory by copying the folder?

Yes, and it's worth doing before wiping a disk. Just note the repository path each project folder came from, because the folder name is derived from that path and will differ if the repo lives somewhere else on the new machine.

### Does nestwork sync my native memory automatically?

No. Routine flow is one-way and deliberate: native memory is distilled into the nest when you choose to. Nothing is copied back into a tool's store automatically.

### Why keep carryover out of the startup context?

Because it is mostly needed on restore. Loading it every session would spend the startup budget on notes like tool install details, crowding out rules that must apply every time.

### How do I carry over Codex memories?

You can still read the files under `~/.codex/memories/` and distill what matters into `carryover/codex.md` or your resident file. OpenAI itself recommends keeping must-follow rules in `AGENTS.md` rather than relying on memories.

## Related

- [Claude Code memory across machines](../claude-code-memory-across-machines/)
- [Codex CLI persistent memory](../codex-cli-persistent-memory/)
- [Memory distillation](../memory-distillation/)
- [Encrypt agent memory with git-crypt](../encrypt-agent-memory-git-crypt/)
- [Long-term memory in practice](../long-term-memory-in-practice/)

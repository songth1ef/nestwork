# Carry tool-native memory into the nest

- date: 2026-07-28
- status: accepted

## Context

Every coding agent keeps its own memory, and as of 2026-07 **all of it is
machine-local**:

| Tool | Native memory location | Redirect setting |
|---|---|---|
| Claude Code | `~/.claude/projects/<project>/memory/` | `autoMemoryDirectory` |
| Codex | `~/.codex/memories/` | none (only `CODEX_HOME` moves everything) |
| Kimi Code | `~/.kimi-code/` | none (only `KIMI_CODE_HOME`) |

Claude Code's documentation states it plainly: *"Auto memory is machine-local.
Files are not shared across machines or cloud environments."* Codex's memories
page documents no sync of any kind. Kimi Code's data-locations page mentions no
cloud sync.

This produces three distinct failure modes, none of them hypothetical:

1. **New machine — total amnesia.** Everything the agent learned about your
   build commands, your conventions, your traps is gone. There are several open
   issues on `anthropics/claude-code` asking for cross-device sync, with no
   official answer.
2. **Vendor disappears.** Tools get discontinued; companies get acquired or shut
   down. When memory lives only inside the tool, the tool's end is the memory's
   end.
3. **Account loss.** Where memory is account-bound and server-side rather than
   local, losing the account — suspension, regional restriction, a lapsed
   subscription — takes the memory with it. Some tools already ship memory
   features documented as unavailable in certain regions.

The common root cause is **ownership**: the vendor decides where your
accumulated context lives and how long it survives. Local-only memory dies with
the disk; account-bound memory dies with the account.

Nestwork already solves the same problem one layer up — agent memory as
markdown in a git repository the user owns. Tool-native memory is simply a
source that has not been connected to it yet.

Existing workarounds do not cover this. Tools that sync the whole `~/.claude`
directory through encrypted cloud storage are not git-native, are single-tool,
and reproduce the ownership problem at a different vendor.

## Decision

Reserve `agents/<host>/<agent-id>/carryover/<tool>.md` as the landing place for
tool-native memory that has been **distilled** into the nest, and extend the
existing distillation concept (§7) to cover this new source.

Carryover is a **cold layer**: never auto-injected at session start. It is read
when restoring onto a new machine, or when someone deliberately looks something
up.

## Options considered

- **Raw mirror of the tool's memory directory** — simple, zero judgement.
  Rejected: it copies duplicates and expired notes into the nest, and the same
  fact then exists in two places that drift apart. §2 already forbids writing
  one memory twice.
- **Redirect the tool's memory directory into the nest** (e.g. Claude Code's
  `autoMemoryDirectory`) — live, zero drift, no manual step. Rejected as the
  protocol default: only one of the three tools offers such a setting, every
  write becomes a commit, and it removes the review step that distillation
  exists to provide. Still available to an instance that wants it, as a local
  choice.
- **Distil periodically into a reserved cold path (chosen)** — keeps the
  judgement step, keeps duplicates out, costs nothing at session start, and
  works identically for tools that have no redirect setting.

## Reason

Distillation is already a first-class concept in this protocol (§7). This is the
same pipeline — read, filter by criteria, human review, merge, commit — with a
different input. Making it an additive extension rather than a new subsystem
keeps the protocol's shape and honours the standing constraint of no central
service and no external dependencies.

Cold-by-default matters more than it looks. The context budget at session start
is finite; a layer that grew with every tool and every project would eventually
crowd out the memory that actually needs to be present. Anything that must act
without being looked up belongs in `memory.md`, not here.

## Consequence

- `carryover/` is reserved under the agent directory. It is never injected at
  session start; `memory.md` may reference it with a single pointer line.
- Distillation criteria must distinguish **hot** (must apply without being
  looked up → `memory.md`) from **cold** (needed only on restore →
  `carryover/`). Getting this wrong in the hot direction wastes context budget;
  in the cold direction it silently disables the memory.
- Each entry must record the tool's original project-directory name **and** the
  repository it corresponded to. Claude Code derives that directory name from
  the repository's absolute path, so a different machine with a different drive
  or checkout location produces a different name. Without both fields, restore
  has no way to map the content back.
- Carryover is markdown and low-churn, so it belongs on `main`. It is not
  subject to the orphan-branch rule for high-churn artefacts (§12).
- The direction stays one-way: tool memory flows into the nest. Nothing in this
  decision writes back into a tool's native store.
- Deleting a source memory after distilling is **irreversible** — tool-native
  memory is not under version control. Extract anything worth keeping first.

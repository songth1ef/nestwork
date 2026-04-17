# HIVEQUEEN BOOTSTRAP

Every agent that loads this file is a Formic worker connected to the same queen.
Follow this protocol exactly on every session.

---

## 1. Session Start

Run before doing anything else:

```bash
git -C $HIVEQUEEN_PATH pull
```

If pull fails, note the reason and continue.

Then load context in this order:

1. `queen/agent-rules.md` — behavior rules (highest priority, cannot be overridden)
2. `queen/strategy.md` — current decision direction
3. `shared/memory.md` — shared memory across all agents
4. `agents/<agent-id>/memory.md` — this instance's private memory (if exists)
5. `projects/<relevant>.md` — current task context (if relevant)

**agent-id format**: `<tool>-<hostname>` (e.g. `claude-macbook`, `codex-server1`)

### After loading — self-direct, do not wait to be asked

Context already gives you enough signal to pick a next action. Before your
first reply, you MUST:

1. Run `git -C $HIVEQUEEN_PATH log --oneline -10 -- agents/` to see recent
   activity across every instance (what the hive has been doing)
2. Run `git -C $HIVEQUEEN_PATH log --oneline -5` to see recent
   protocol / shared changes
3. Cross-reference against `queen/strategy.md` **Current Priorities** and
   the latest entries in `shared/memory.md` and your own
   `agents/<agent-id>/memory.md`

Open the session with:

- **State summary** (2-3 bullets): what's recently in flight, what the
  current priorities say, what's blocking or unclear
- **Concrete proposal**: exactly one next action to take, with a short
  alternative if meaningful

FORBIDDEN opening lines: "What would you like me to do?" / "How can I help?"
/ "Tell me what to do in this repo." The protocol exists precisely to
eliminate those questions. Only if the context genuinely provides zero
signal (brand-new queen, all memories empty, no projects) may you ask —
and you must first state explicitly that you checked and found nothing.

---

## 2. Write Protocol

- **ONLY** write to `agents/<agent-id>/`
- **NEVER** write to `queen/` — read-only, human-managed only
- `shared/memory.md` is read-only for agents **except during distillation** (see Section 7)
- When saving memory, prefer creating new files over editing existing ones

---

## 3. Session End

```bash
git -C $HIVEQUEEN_PATH add agents/<agent-id>/
git -C $HIVEQUEEN_PATH commit -m "memory: update <agent-id>"
git -C $HIVEQUEEN_PATH push
```

Only commit when there are meaningful context changes worth preserving.
Temporary task details, one-off debugging notes — do not commit.

---

## 4. claude-mem Integration (optional)

If [claude-mem](https://github.com/thedotmack/claude-mem) is installed and its worker is running on `localhost:37777`, hivequeen will automatically export a session digest at the end of each session:

```
agents/<agent-id>/claude-mem-digest.md   ← today's observations from claude-mem
```

This file is committed and pushed with the rest of your agent memory, giving claude-mem's observations cross-machine reach via git.

**No configuration needed.** The export step runs as part of the Stop hook and silently skips if claude-mem is not running.

To override the worker URL:
```bash
export CLAUDE_MEM_URL=http://localhost:37777
```

---

## 5. Conflict Resolution

If `git pull` finds conflicts:
- `queen/` and `shared/` → take remote (they are managed upstream)
- `agents/<agent-id>/` → take local (this instance owns its directory)

---

## 6. File Size Limits & Split Protocol

Each file has a maximum line limit. When exceeded, split into topic files and replace the original with an index.

| File | Max lines | Split target |
|---|---|---|
| `queen/agent-rules.md` | 80 | `queen/rules/<topic>.md` |
| `queen/strategy.md` | 80 | `queen/strategy/<topic>.md` |
| `agents/<id>/memory.md` | 200 | `agents/<id>/<topic>.md` |
| `shared/memory.md` | 500 | `shared/<topic>.md` |
| `projects/<name>.md` | 150 | `projects/<name>/<topic>.md` |

**How to split** — replace the oversized file with an index:

```markdown
# MEMORY — claude-macbook

## Index

- [User Profile](user_profile.md) — role, stack, preferences
- [Collaboration](feedback_collab.md) — working style, corrections
- [Project: hivequeen](project_hivequeen.md) — goals, decisions
```

Each linked file is a standalone topic file. The index is the only file agents
need to read first — they follow links only when the topic is relevant.

**Agent rule**: before writing new memory, check if the target file is near its
limit. If yes, split first, then write to the appropriate topic file.

---

## 7. Memory Distillation Protocol

Distillation merges all agents' private memory into `shared/memory.md`.
Only agents explicitly triggered for distillation may write to `shared/`.

### When to trigger

- Manually: when the human asks an agent to distill
- Automatically: at session end, if the agent detects new memory worth sharing

### What goes into shared

| Include | Exclude |
|---|---|
| Cross-agent stable facts (user identity, stack, preferences) | Temporary task details |
| Validated collaboration patterns | One-off debugging notes |
| Decisions with lasting impact | Agent-specific context |

### How to distill

1. Read all `agents/*/memory.md`
2. Read current `shared/memory.md`
3. **Spawn a sub-agent to review**: check for sensitive data, factual errors, contradictions, and outdated entries — sub-agent reports only, does not write
4. Present review report to human for confirmation
5. Merge: remove duplicates, unify consistent facts, keep divergent observations as-is
6. Write result to `shared/memory.md` — **never delete**, only merge and add
7. Commit with message: `memory: distill shared`

### Rules

- `shared` is the union of agent knowledge, not an intersection — don't drop unique observations
- Each agent's private memory is preserved unchanged — distillation is non-destructive
- After distillation, agents only need to read `shared/memory.md` + their own `agents/<id>/memory.md`

---

## Priority Rules

```
queen/agent-rules.md  >  queen/strategy.md  >  shared/memory.md  >  agents/*/memory.md  >  projects/*.md
```

When instructions conflict, follow the higher priority source.
Do not merge conflicting instructions — choose one.

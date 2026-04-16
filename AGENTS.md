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

---

## 2. Write Protocol

- **ONLY** write to `agents/<agent-id>/`
- **NEVER** write to `queen/` or `shared/` — those are read-only for agents
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

## 4. Conflict Resolution

If `git pull` finds conflicts:
- `queen/` and `shared/` → take remote (they are managed upstream)
- `agents/<agent-id>/` → take local (this instance owns its directory)

---

## 5. File Size Limits & Split Protocol

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

## Priority Rules

```
queen/agent-rules.md  >  queen/strategy.md  >  shared/memory.md  >  agents/*/memory.md  >  projects/*.md
```

When instructions conflict, follow the higher priority source.
Do not merge conflicting instructions — choose one.

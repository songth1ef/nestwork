# Tool memory carryover: entry format and restore

Rules for what to carry and where it lands are in `AGENTS.md` §13. This page
holds the entry format and the restore procedure.

## Entry format

Some tools derive their project directory name from the repository's
**absolute path**, so the same repository produces a different name on a
machine with a different drive or checkout location. Every carryover entry
therefore records both the original directory name and the repository it
referred to:

```markdown
## <one-line title>

- **source**: `~/.claude/projects/<project-dir>/memory/<file>.md`
- **original project dir**: `<project-dir>` (repository: `<repo path>`)
- **carried on**: YYYY-MM-DD
- **criterion**: cold — needed only on restore

<body, keeping the original Why / How-to-apply structure>
```

## Restoring onto another machine

1. Read `agents/<host>/<agent-id>/carryover/<tool>.md` from the old machine's
   agent directory.
2. For each entry, recompute the tool's project directory name from the new
   machine's repository path.
3. Write the body back into the tool's native memory location there.

This is the only reverse step of an otherwise one-way flow, and it is always
deliberate and manual. Rationale and rejected alternatives:
`decisions/2026-07-28-tool-memory-carryover.md`.

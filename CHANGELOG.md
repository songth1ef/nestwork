# Changelog

[English](CHANGELOG.md) | [中文](CHANGELOG.zh.md)

## Unreleased

### Documentation alignment (protocol 3.0)

- Fix encrypted-instance updates: extract upstream files without smudge filters, then stage through the private clean filter. This preserves short files such as `VERSION`; dirty worktrees and filter failures stop the update. Covered by a real git-crypt regression test.
- Align both README timelines, upgrade instructions and retention/loading guidance; software release v0.6.0 and protocol 3.0 are independently numbered.
- Correct stale startup behavior in Claude/AGENTS.md guides, mailbox docs, carryover routing, limits examples and acquisition articles. Inbox snapshots still refresh but are read only on demand.
- Add consistency checks for current protocol documentation, resident paths, migration steps and inbox loading tier.

### Protocol v3.0 — resident / on demand

- Startup reads core rules and optional shared/agent `resident.md` only. Existing memory, strategy, projects and workflows remain on demand; no automatic legacy fallback.
- Reinstall the marked tool bootstrap after updating scripts. See `docs/context-loading.md` for migration and byte-budget checks. Historical data is preserved.
- Memory write limits explicitly apply inside Nestwork, not user project artifacts. Current tasks no longer require unrelated status reports.


### Protocol v2.5

- **Tool-native memory carryover (AGENTS.md §13).** Every coding agent keeps its own memory and, as of 2026-07, all of it is machine-local — Claude Code (`~/.claude/projects/<project>/memory/`, documented as "not shared across machines or cloud environments"), Codex (`~/.codex/memories/`), Kimi Code (`~/.kimi-code/`). That exposes accumulated context three ways: a new machine starts from zero, a discontinued tool takes its memory with it, and account-bound memory disappears with the account. The root cause is ownership, and nestwork already solves that one layer up. New reserved path `agents/<host>/<agent-id>/carryover/<tool>.md` receives tool-native memory **distilled** through the §7 pipeline (read → filter → human review → merge → commit), not raw-mirrored — a raw mirror would carry duplicates and expired notes across and create the drift §2 forbids. `carryover/` is a **cold layer**: never auto-injected at session start, referenced from `memory.md` by a single pointer line at most. Triage sorts each entry by "when does this stop being true?", and the hot/cold split is explicit — an entry that must apply *without being looked up* belongs in `memory.md`, everything else in `carryover/`. Entries record the original project-directory name **and** its repository, because some tools derive that name from the repository's absolute path and it will not match on another machine. Additive: no existing path, hook, or priority-chain behaviour changes. Rationale and rejected alternatives in `decisions/2026-07-28-tool-memory-carryover.md`.

### Added

- **`distill.py` gained a second runner: `--run-claude` (`claude -p`) alongside `--run-codex`.** Distillation is the only channel through which one agent's memory reaches another machine, and it was bound to a single vendor's CLI — when that subscription hit its usage limit, a private instance's weekly distillation cron failed silently and its `shared/memory.md` stopped moving for 49 days while an entire new host's memory accumulated unseen. The two runners are mutually exclusive, each reads its own `NESTWORK_DISTILL_{CLAUDE,CODEX}_MODEL`, and `--profile` still applies to Codex only (warns instead of silently ignoring). The Codex path is untouched — fixing one vendor's outage is no reason to remove the other. The Claude runner always passes `--tools '' --setting-sources ''`: without them the distiller loads the nest's own CLAUDE.md bootstrap and answers with a session-start summary instead of a `shared/memory.md` candidate, which reads like a bad LLM response rather than a missing flag, so it is asserted in the tests.
- **`docs/limits-override-example.md`** — a copy-me template for the per-instance file-size-limit override below. Agents read `queen/limits.md`; copying is an explicit act. Shipped as an example rather than a live file on purpose: a live `queen/limits.md` in every instance would freeze that instance's numbers, and since `update.sh` never touches `queen/`, later changes to the §6 protocol defaults would stop reaching it. It lives in `docs/` rather than `queen/` for the mirror-image reason — `docs/` **is** synced by `update.sh`, so the example keeps arriving as defaults evolve, while `queen/` stays entirely the user's. Includes the reasoning to tune against retrieval quality rather than context-window size, and a tuning log so a deliberate change can be told from a stray edit.
- **Per-tool uninstallers (`scripts/uninstall/`)** mirroring `scripts/install/` (claude / codex / gemini / hermes / openclaw / generic, `.sh` + `.ps1`). Uninstall **unbinds only**: removes the bootstrap marker block from the tool's startup file and deregisters nestwork hooks (Claude settings.json, Codex hooks.json). Memory (`agents/<host>/<agent-id>/`), identity files (`~/.nestwork_host`, `~/.nestwork_id_<tool>`), and user content outside the markers are never touched; re-installing restores the same agent identity. Optional `--purge-identity` / `-PurgeIdentity` drops the tool's agent id for a fresh start. Shared helpers `_unbootstrap.py` / `_unhooks.py` / `_codex_unhooks.py` reuse the installers' own matchers, so anything an installer would supersede, the uninstaller removes. Covered by `tests/test_uninstall.py` round-trip tests (install → uninstall preserves user content and user hooks).
- **Per-instance file-size-limit override (`queen/limits.md`).** A private instance can override the default limit table in AGENTS.md §6 without editing the protocol layer — create `queen/limits.md` with its own table; when present it is authoritative, agents load it at session start (high-priority `queen/` layer), and `update.sh` never touches `queen/`, so the override survives protocol updates. Additive, no protocol-version bump. Tune against retrieval quality, not raw context-window size. (AGENTS.md §6 + README §"File size limits".)
- **`scripts/comms/archive.sh`** — moves a sender's own outbox messages older than N days (default 30) into `outbox/archive/`, keeping `read.sh` scan cost bounded as the mailbox ages. Commits and pushes the move.
- **End-to-end tests** for the v2.4 orphan-branch snapshot (`tests/test_snapshot_local_orphan.py`), the agent mailbox (`tests/test_comms.py`), and `compile.sh` content fidelity (`tests/test_compile.py`).
- **End-to-end tests for the atomic per-write hook** (`tests/test_nestwork_hook.py`): pre fast-forward, pre blocking on divergent conflict (exit 2), the autostash-leftover guard, post commit+push, the push-retry path after a concurrent remote advance, post ignoring non-agent paths, and the Stop safety net (dirty and clean).
- **Priority-chain uniformity test**: every rendition of the priority chain across all markdown files must show all six layers, so partial copies can no longer go stale unnoticed.
- **ADR: GEO doc duplication strategy** (`decisions/2026-06-11-geo-docs-duplication-with-drift-tests.md`, proposed) — keep the intentional duplication across README/AGENTS/docs stubs, control drift with derived consistency tests instead of deduplicating or adding a build step.

### Changed

- **README slimmed from 933 to 769 lines (EN) and 930 to 768 (ZH).** Five sections were re-explaining the protocol a third time — Directory structure, File size limits, Compile shared memory, Agent mailbox, and the `workflow/` deep dive — while `AGENTS.md` and the matching `docs/` pages already carried the same material in more detail (`docs/agent-mailbox.md` is 144 lines against the README's 32). Each is now a short summary plus a pointer. The GEO duplication strategy is untouched: nothing was deleted, the self-contained page for each topic simply stays in the one place that owns it. The point is maintenance, not length — adding §13 required editing 7 files across 10 sites, against the "roughly five places" the duplication ADR budgeted for; this brings protocol changes back to `AGENTS.md` + its mirror + both CHANGELOGs.
- **Version-scoped README section retired.** The 90-line "v2.2 new: workflow/ and nestwork.config.json" heading had survived three protocol releases, so readers saw v2.2 advertised as the newest thing while v2.3–v2.5 had no equivalent. Its content now lives under a permanent "Context layers" heading; version slices belong in this file. A new test (`test_readmes_have_no_version_scoped_sections`) rejects any future `## vX.Y new` heading.
- **Directory tree in both READMEs corrected.** It had drifted: `agents/*/carryover/`, `decisions/`, `tests/`, and `scripts/comms/` were all missing, and the per-file script listing was stale enough to mislead. Now shows every top-level layer with the hot/cold distinction on the agent directory.

### Fixed (docs)

- **Kimi Code was missing from the entire answer-engine surface.** Shipped as an installer on 2026-07-21, it appeared only in the README body — both README tool badges, `llms.txt`, `docs/README.md`, `docs/ai-agent-memory.md`, `docs/shared-context-for-ai-coding-agents.md`, and `docs/faq.md` all still advertised a list without it. This is precisely the drift the GEO duplication ADR predicted, in the one place where a stale copy does the most damage. New test `test_advertised_tool_list_covers_every_installer` derives the expected list from `scripts/install/*.sh`, so shipping a tool without updating the docs now turns a test red instead of silently misinforming answer engines.

- **Mailbox delivery is self-contained.** `send.sh` now commits and pushes the message itself (with rebase-retry) instead of relying on the per-write hooks — those only match Write/Edit tool calls, so a Bash-invoked send was never auto-committed, and non-Claude tool-chains had no covering hook at all. Docs updated to describe the real mechanism.
- **Mailbox read state moved to git-ignored `local/comms/seen.txt`.** Marking messages read no longer creates commits on `main`. A legacy committed `comms/seen.txt` is imported automatically on first read; it can be `git rm`-ed afterwards.
- **CI sync scope aligned with `update.sh`.** `sync-upstream.yml` `PROTOCOL_PATHS` previously synced only scripts/AGENTS/CLAUDE/SOUL/READMEs, silently never propagating `docs/`, `schemas/`, CHANGELOGs, or the workflow/projects/decisions templates; both lists now match (CI still excludes `.github/workflows/` — GITHUB_TOKEN cannot push workflow files) and both now also carry `VERSION` and `llms.txt`.
- `export-claude-mem.sh` passes the worker URL and date to Python via argv instead of shell interpolation into the heredoc, so a user-controlled `CLAUDE_MEM_URL` can no longer inject into the script.
- **Installers hardened.** All `scripts/install/*.sh` now run under `set -euo pipefail` and abort with a clear error when the identity resolver does not return two non-empty lines (previously a parse failure silently produced an `agents/<host>/` path with an empty agent-id). The `.ps1` installers force array context on the resolver output (a single-line result previously indexed *characters*, not lines) and validate line count and non-emptiness.
- `update.sh` checks for protocol drift with `git diff --quiet` instead of capturing the full diff into a variable, and applies upstream files per-path — a file missing upstream is skipped with a note instead of aborting the whole update mid-way.
- **`sync_local_history` redaction now covers every string field, recursively.** Redaction was scoped to the `project` and `display` fields; history.jsonl schemas differ between tools and versions, so tokens in any other field passed through unredacted. `pastedContents` is still dropped entirely.
- `distill.py --run-codex` failures now surface Codex's own stderr plus the exact flag list used, instead of a bare `CalledProcessError` string — flag mismatches across Codex CLI versions were undiagnosable before.

### Fixed

- **`distill.py` died on non-ASCII memory outside UTF-8 locales.** Both runners captured their subprocess with `text=True` alone, which decodes using the *locale* codec — on a zh-CN Windows machine that is GBK, and since agent memory is routinely non-ASCII the whole run raised `UnicodeDecodeError` before the distilled memory was ever parsed. Both now pin `encoding="utf-8", errors="replace"`. Reproduced locally: a runner fixture emitting Chinese fails before the change and passes after.
- **Kimi Code installs loaded no context at all.** `scripts/install/kimi.{sh,ps1}` wrote the bootstrap block to `~/.kimi-code/NESTWORK.md` — a filename Kimi Code never reads. Its instruction files are `$KIMI_CODE_HOME/AGENTS.md` (user level, default `~/.kimi-code/AGENTS.md`) and `<project>/AGENTS.md`, nothing else. Every visible signal said the install had worked: it printed success, the hooks were registered and fired (SessionStart pull, per-write sync, Stop safety net), and `git pull` ran on schedule — while the agent started each session with zero nestwork context. Kimi Code cannot inject context from a hook either (a hook may only return a permission decision), so that file was the sole channel and it was silently dead. Installers now write `AGENTS.md`, and clear the stale block from a legacy `NESTWORK.md` while preserving any user content outside the markers; uninstallers remove both. New test `test_installer_entry_file_matches_readme_and_uninstaller` derives the entry file from each installer's own `_bootstrap.py` call and requires the README's Supported tools row **and** the matching uninstaller to agree — the README advertised the same wrong path, so the two copies agreed with each other while the feature was inert, which is exactly what a hardcoded assertion would have blessed. Existing installs: re-run `bash scripts/install/kimi.sh` (or `.\scripts\install\kimi.ps1`).
- **`update.sh` no longer stages upstream plaintext into git-crypt nests.** `git checkout <tree-ish> -- <path>` copies upstream blobs into the index verbatim, bypassing clean filters — on a nest with git-crypt full encryption the update commit contained upstream's plaintext. The apply step now runs `git add --renormalize` over the protocol paths, re-running clean filters (no-op for unencrypted nests).
- **`compile.sh` no longer corrupts memory content.** Output was emitted with `printf "%b"`, which interpreted backslash sequences (`\n`, `\t`, `C:\temp`, regexes) *inside agents' memory text*; content now passes through verbatim. Header stripping no longer assumes a fixed 3-line header and no longer leaks the installer template's second blockquote line into `shared/memory.md`.
- **Pre-write hook autostash guard.** `git pull --rebase --autostash` exits 0 even when re-applying the stash conflicts — git parks the uncommitted change in the stash, leaves the tree clean, and the subsequent Write would silently overwrite it. The hook now detects the leftover stash entry (locale-independent) and blocks the write with a recovery hint instead.
- **Release metadata reconciled; test suite green again.** `VERSION` and the README version line were stale at v0.3.0 while the CHANGELOG had shipped v0.6.0, and `test_docs_consistency.py` still asserted `Protocol: 2.1` — the suite was red. The test now derives version/protocol expectations from `VERSION` + `AGENTS.md` (instead of hardcoding values that drift) and enforces CLAUDE.md as a byte-exact mirror of AGENTS.md.
- AGENTS.md §9 now documents `desensitize.placeholder_overrides` (it existed in `schemas/nestwork.config.schema.json` but was missing from the field table); §11 corrects the upstream-check cache path to `~/.cache/nestwork/upstream-check`, which is what the hook actually uses.
- Stale 5-layer priority chains in `docs/git-native-memory-protocol.md` and `docs/shared-context-for-ai-coding-agents.md` now include `workflow/*.md` (stale since v2.2); removed dead "(to be added in a later step)" notes in `docs/workflow-protocol.md`; `session-start.sh` no longer self-labels a nonexistent protocol v2.5.
- EN CHANGELOG v0.3.0 entry restructured to match the ZH layout (explicit `Protocol v2.1` / `Compatibility` headings) per this file's own bilingual-parity convention. Content unchanged.

## v0.6.0 - 2026-05-08

### Protocol v2.4

Provides an isolated storage path for "high-frequency append + poor delta compression" artefacts (typically `history.jsonl` from `sync_local_history`), avoiding unbounded main-history bloat.

- **AGENTS.md §12 added** — high-churn artefacts go to per-agent orphan branch `agent-history-<host>-<agent-id>`. Each write rebuilds a single parentless commit via `git commit-tree` + `git update-ref` and force-pushes it, replacing the previous snapshot. Branch naming embeds host + agent-id, so each branch has exactly one writer; force-push is collision-free by design.
- **`agents/*/*/local/` in default `.gitignore`** — main no longer absorbs high-churn artefacts; backup lives entirely on orphan branches.
- **New `scripts/hooks/snapshot-local-orphan.sh`** — snapshot builder using `GIT_INDEX_FILE` temp index to avoid touching the main working index; only creates a new commit when the tree hash changes; failed force-pushes never block the agent.
- **`scripts/hooks/sync-local-history.sh` invokes the snapshot script after the python sync** — no configuration change required by users; enabling `sync_local_history` automatically gets the new mechanism.
- **Cross-machine restore**: `git fetch origin agent-history-<host>-<agent-id>` → `git restore --source=...` in a single command.

### Measured effect

Downstream instance mynestwork bloated to 177 MB after running `sync_local_history` for two weeks (411 `history.jsonl` commits). After `git filter-repo` cleanup + switching to this mechanism: repo down to 1.6 MB (**-99%**), backup fully preserved on 4 orphan branches.

### Added

- `scripts/hooks/snapshot-local-orphan.sh`

### Changed

- `scripts/hooks/sync-local-history.sh` — invokes the snapshot script after the python sync
- `.gitignore` — adds `agents/*/*/local/`

### Upgrade notes (private instances)

After upgrading to v2.4, newly-written `local/` entries automatically use the orphan-branch path; main stops growing. **Existing main-history bloat must be cleaned manually**, once:

1. `pip install git-filter-repo`
2. `git filter-repo --path-glob 'agents/*/*/local/*' --invert-paths --refs main --force`
3. `git push origin main --force`
4. `git gc --aggressive --prune=now`

Back up `.git` before running destructive operations.

---

## v0.5.0 - 2026-05-08

### Protocol v2.3

Clarifies the boundary between nestwork (cross-repo coordination layer) and the per-repo 5-doc skeleton, and adds a passive upstream-version check so downstream instances can notice protocol updates without polling.

- **AGENTS.md §10 added** — defines the boundary between nestwork and each repo's own 5-doc skeleton (`AGENT.md` / `docs/conventions.md` / `docs/domain.md` / `docs/architecture.md` / `docs/lessons.md`). Test: "Will this still apply after I change employers?" If yes → nestwork `workflow/`; if no → the repo.
- **`projects/<name>.md` 5-field convention** (§10.1) — `Current Goal` / `Current State` / `Next Action` / `Do Not` / `Last Verified`. Recommended, not enforced. Template ships at `projects/_template.md`.
- **`decisions/` for protocol-level ADRs only** (§10.2) — captures decisions about nestwork itself / its protocol. Project-level ADRs stay in the repo. Files named `YYYY-MM-DD-<slug>.md`. Template at `decisions/_template.md`; scope and status lifecycle in `decisions/README.md`.
- **`workflow/lessons.md` for cross-repo lessons** (§10.3) — repo-level `docs/lessons.md` (5-doc #5) covers project-internal lessons. Lessons that travel across repos go here. Upstream does **not** ship this file; each user creates it as lessons accumulate.
- **AGENTS.md §11 added** — SessionStart hook performs a 3-second non-blocking check against upstream's `protocol-version`. 24h cache; silent on network failure; advisory message only when upstream MAJOR.MINOR is strictly greater than local. Never auto-applies.

### Added

- `projects/_template.md` — 5-field project snapshot template
- `decisions/_template.md` — protocol-level ADR template
- `decisions/README.md` — scope, naming, status lifecycle for protocol ADRs

### Changed

- `scripts/hooks/session-start.sh` — added upstream version check (advisory only)
- `scripts/maintenance/update.sh` — PROTOCOL_FILES now includes `projects/_template.md` / `decisions/_template.md` / `decisions/README.md`

---

## v0.4.0 - 2026-05-07

### Protocol v2.2

Adds a portable workflow context layer and a contract for ingesting external working directories into private nest instances.

- **New top-level `workflow/` directory** — portable cross-project knowledge (coding disciplines, tooling, methodologies, migration guides). Lowest priority. See `AGENTS.md` Section 8.
- **New `nestwork.config.json` contract** — external working directories declare ingestion target and desensitization rules via this file, which **lives only in the source directory and never enters any Nestwork repo**. See `AGENTS.md` Section 9.
- **Universal markdown split rule** — any oversized md file follows the same pattern: original filename becomes a folder, original file becomes an index (or `<folder>/index.md`). Files not listed in the size table use defaults (soft 500 / hard 1000 lines). See `AGENTS.md` Section 6.
- **Priority chain extended** — `queen/agent-rules.md > queen/strategy.md > shared/memory.md > agents/*/*/memory.md > projects/*.md > workflow/*.md`.

### Added

- `docs/workflow-protocol.md` — full rules and three-tier model for `workflow/`
- `docs/desensitization-prompt.md` — AI desensitization prompt template (methodology only, no specific names)
- `schemas/nestwork.config.schema.json` — JSON Schema for `nestwork.config.json`
- `workflow/README.md` + `workflow/_template.md` — workflow scaffolding
- `CHANGELOG.zh.md` — Chinese-maintained changelog

### Changed

- `update.sh` sync scope adds `docs/`, `schemas/`, `workflow/README.md`, `workflow/_template.md`. Private workflow content is **never** touched.
- `README.md` / `README.zh.md` add workflow/ section, directory tree update, file-size table workflow row
- `AGENTS.md` and `CLAUDE.md` synchronously upgraded to protocol-version 2.2

### Compatibility

- Additive-compatible. Existing agents need no action.
- v2.1 private nests can selectively pull v2.2 protocol layer with zero impact on private data.

---

## v0.3.0 - 2026-04-22

### Protocol v2.1

Splits the Stop-hook workload and adds a SessionEnd hook.

- Stop now only runs the lightweight `nestwork.sh stop` safety-net commit+push
- `export-claude-mem.sh` + `sync-local-history.sh` moved to the new SessionEnd hook so they run once at true session end instead of every turn (including `/clear`, resume, compact)
- `_hooks.py` registers the new `SessionEnd` event; existing installs are cleanly superseded on re-run (old Stop composite command is recognised and removed by `is_nestwork_hook`)

### Compatibility

- Additive-compatible: existing agents keep working until they re-run the installer.

## v0.2.0 - 2026-04-19

- Introduced protocol v2 host/agent layout: `agents/<host>/<agent-id>/`.
- Added and hardened installers for Claude Code, Codex CLI, Gemini CLI, OpenClaw, Hermes Agent, and generic markdown-config tools.
- Aligned identity persistence with the protocol v2 two-line `~/.nestwork_id` format.
- Hardened Codex Windows session hook generation for Windows PowerShell 5.1.
- Added answer-ready GitHub docs, `llms.txt`, and repository-first GEO content for AI agent memory searches.
- Added tests for installer syntax, identity migration, protocol docs, and GEO content assets.

## v0.1.0 - 2026-04-17

- Created the initial nestwork protocol template.
- Added `queen/`, `agents/`, `shared/`, and `projects/` repository layout.
- Added startup instructions through `AGENTS.md` and `CLAUDE.md`.

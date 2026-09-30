# Changelog

English | [中文](CHANGELOG.zh.md)

All changes to the nestwork protocol and code. **Maintained continuously.**

Conventions:

- Reverse chronological order, newest first
- One heading per release: `## vX.Y.Z - YYYY-MM-DD`
- Entries grouped by kind: Protocol / Added / Changed / Fixed / Deprecated / Removed
- Protocol changes must be labelled `Protocol vX.Y` — `MAJOR.MINOR`; a MAJOR bump requires downstream action, a MINOR bump is additive-compatible
- Private data protection: no change may break private content under `agents/` `queen/` `shared/` `projects/` `workflow/<topic>.md`

---

## Unreleased

### Fixed

- **`update.sh` makes the `upstream` remote fetch-only.** A private nest that can push to the public upstream can publish its entire history with one push of a branch based on its `main`; deleting the branch afterwards leaves the commits reachable by SHA on GitHub. `update.sh` now sets upstream's push URL to a disabled placeholder (fetching is unaffected). Maintainers of the public repo should work from a separate clone.
- **`update.sh` and the sync workflow now carry `tests/`.** Instances kept stale tests, which then failed against updated scripts.
- `test_no_private_names` skips inside private instances, where real host and agent names are expected.

### Changed — protocol text slimmed (no behavior change, protocol stays 3.2)

- `AGENTS.md` 649 → ~530 lines. Section numbers are unchanged, so existing `§N` references still resolve. Moved out, with a one-line pointer left behind: §4 claude-mem export details → `docs/claude-code-memory.md`; §9 `nestwork.config.json` field table and flow → `docs/workflow-protocol.md` (the rules stay in §9); §10 per-repo doc list and the inline project template → `projects/_template.md` reference; §13 carryover entry format and restore steps → new `docs/tool-memory-carryover.md`.
- §6 no longer shows a hand-written memory index. It predated topic memory and contradicted the 3.1 rule that memory indexes are generated; memory scopes now split through topic memory, other files keep the manual folder + index split.
- Dropped per-heading version annotations such as "(protocol v2.4+)"; version history lives in this changelog.

### Removed

- `scripts/maintenance/compile.sh`: plain concatenation into `shared/memory.md`, superseded by the reviewed `distill.py` flow and already refused on topic-mode nests. `update.sh` does not delete files, so existing instances keep an unused copy; delete it by hand if you like.
- `scripts/maintenance/migrate-v2.sh`: the protocol 1.x → 2.0 layout migration from 2026-04.
- `projects/nestwork.md`: a stale example snapshot (from 2026-04) that every new template instance inherited; `projects/_template.md` remains the reference.

### Protocol v3.2 — resident orientation (additive)

- **Resident context now orients, not just routes.** `shared/resident.md` may carry a short owner profile and a summary of current goals, priorities and non-goals from `queen/strategy.md` (with its review date; strategy stays authoritative). 3.0 kept resident context routing-only, which left agents starting every session without knowing who they work for or what the goals are.
- **Generated recent-activity digest.** New `scripts/maintenance/recent-digest.py` builds `local/recent.md` from git history: `projects/*.md` touched in the last 30 days (Current Goal / Next Action / Last Verified) and topic files touched in the last 7 days (their `description`); bulk commits such as splits collapse into one line. Capped at 2048 bytes, git-ignored, rebuilt by the SessionStart hook and listed in READ-ON-START. The bootstrap lists it as an optional resident file; `measure-context.py` counts it.
- **Branch guard.** When the nest is not on its default branch (`origin/HEAD`), the SessionStart hook skips `git pull` and prints a `[!]` warning with the fix command, instead of silently rebasing a feature branch and serving its context as the instance's.
- Migration: none required. `update.sh` brings the hook and script; rerunning installers is optional (it adds the digest path to hookless bootstraps). See `docs/context-loading.md`.

### Added

- **WorkBuddy AI installer/uninstaller** (`scripts/install/workbuddy.sh` / `.ps1`, `scripts/uninstall/workbuddy.sh` / `.ps1`). WorkBuddy AI (Tencent) is a conversational desktop agent with no CLI config or session hooks; the installer writes the nestwork startup protocol to `~/.workbuddy-ai/nestwork.md` (overridable via `WORKBUDDY_HOME` / `WORKBUDDY_NESTWORK_MD`), and the agent follows it inside the conversation (pull / commit / push). README (EN + zh), llms.txt updated.

- **Codex CLI gets per-write memory sync.** The Codex installer now registers PreToolUse / PostToolUse on `^(apply_patch|Edit|Write)$` and Stop, running the same `nestwork.sh` flow as Claude Code and Kimi Code; `_match-file.py` reads target paths from `apply_patch` patch headers (column-0 `*** Add/Update/Delete File:` / `Move to:`, relative paths resolved against the payload `cwd`). The hook keeps stdout empty because Codex parses a Stop hook's stdout as JSON. Uninstall removes all four events and keeps user hooks. **Existing Codex users: rerun `scripts/install/codex.sh`, then run `/hooks` in Codex once to trust the new hooks.**

- New `scripts/maintenance/measure-context.py`: reports bytes and estimated tokens for a 2.x-style full startup, the resident startup, a resident + index + topic task, and the whole nest, from one agent's point of view. Zero dependencies; uses tiktoken when installed, otherwise a character-class estimate calibrated on a bilingual nest (median error ~6%). README and `docs/context-loading.md` now cite measured numbers instead of the byte budget alone.

### Protocol consistency (3.1, clarifications) — action needed for scheduled distillation

- **`distill.py --run-claude/--run-codex` no longer commits by default.** It writes `shared/` and prints a review hint, matching §7 steps 3–4 (review, then human confirmation). Pass `--commit` to commit and push in the same run (`--no-push` keeps it local). `--no-commit` is still accepted as a no-op. **If a cron or scheduled job runs the distiller unattended, add `--commit`**, or it will keep writing an uncommitted working tree and shared memory will silently stop updating.
- Resolved five contradictions in `AGENTS.md`: §1 skips the manual pull when a SessionStart hook already ran it (matching the installed bootstraps); §2 now says extend the file that covers the topic instead of preferring new files (matching §6); §6 limits agent-added leaf topics to the agent's own directory, while every `shared/` change happens in distillation; §7 drops "automatic at session end" — agents record candidates in their own directory instead; §13 calls restore the one deliberate, manual reverse step of an otherwise one-way flow.
- Script comments corrected: `send.sh` (a failed push is not retried by the Stop hook; it goes out with the next push), `sync-local-history.sh` (the switch lives in `agents/<host>/settings.json`), `generic.sh` / `generic.ps1` (old `install-generic` name).

### Protocol v3.1 — topic memory

- A memory scope (`shared/` or `agents/<host>/<agent-id>/`) can opt in to topic storage: `memory.md` becomes an index generated from each topic file's `description` / `updated` front matter, and agents open only the files whose description matches the task — the same routing pattern as skills. The split rule in §6 existed since v2 but never held in practice: a line-count limit is bypassed by long lines (one private instance reached 114 KB in 430 lines), and `distill.py` / `compile.sh` rewrote everything back into one file.
- New `scripts/maintenance/memory-index.py` (generate / `--check`): fails on a stale index, a topic without `description`, a file over 32 KB, or nesting deeper than two levels.
- `distill.py` detects topic mode and exchanges `<<<FILE shared/<topic>.md … >>>END` blocks with the runner, validates paths and front matter, writes changed topics only and regenerates the index. `compile.sh` refuses to flatten a topic-mode `shared/`.
- Taxonomy governance: agents add leaf topics after checking the index; renames, merges and new top-level folders happen only in reviewed distillation.
- Additive: scopes without markers keep single-file memory; hooks and bootstraps are unchanged.

### Documentation alignment (protocol 3.1, README)

- Both READMEs checked against the scripts: the banner now states protocol 3.1 and introduces topic memory; the directory tree adds `queen/limits.md`, topic files, `outbox/`, the `shared/` layout and every maintenance script; the file-size section covers topic memory and `memory-index.py --check`.
- The distillation section adds the `--run-claude` runner, `--no-commit` / `--no-push`, and topic-mode behaviour; the FAQ and Non-goals no longer describe Codex as the only runner.
- Per-tool hook coverage is rewritten from the installers (Claude Code / Kimi Code / Codex / tools without hooks). The Kimi row in the `generic.sh` table, which duplicated the native `kimi.sh`, is gone; uninstall instructions add `kimi` and the arguments `generic` needs.
- "Staying up to date" is consolidated into two paths, GitHub Action and `update.sh`; the sync scope now matches `update.sh`'s `PROTOCOL_FILES`, and it notes that 3.0 → 3.1 needs no bootstrap refresh. All examples use `~/nestwork`.
- Troubleshooting describes the current Python identity resolver (`_identity.py`, `NESTWORK_HOST` / `NESTWORK_AGENT_ID`) instead of a `hostname` fallback that no longer exists.
- Duplication inside the README is merged: the problem paragraph and its bullet list, the fork explanation in Install and the FAQ, and the two hook-coverage statements. Project context is described as on demand; the protocol timeline is chronological and dated; inline `v2.2+` tags are removed.

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

- **Neutral examples only.** Docs, blog posts and tests now use fictional hosts and agent ids (`laptop`, `workstation`, `cloud-vm`, `claude-a7k2`) and a generic project (`my-app`, `~/code/my-app`) instead of names copied from a working instance. New `tests/test_no_private_names.py` fails on real host, agent, employer or private-repo names; it stores only SHA-256 hashes of the blocked tokens so the guard does not republish them, and reads extra plaintext names from `~/.config/nestwork/private-names.txt` when present.

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

---

## v0.2.0 - 2026-04-19

### Protocol v2.0 (breaking)

Introduced the host/agent layout: `agents/<host>/<agent-id>/`.

### Added

- Full installer matrix: Claude Code, Codex CLI, Gemini CLI, OpenClaw, Hermes Agent, and generic markdown-config tools
- Hardened Codex Windows session hook generation for Windows PowerShell 5.1
- Answer-ready GitHub docs, `llms.txt`, and repository-first GEO content for AI agent memory searches
- Tests for installer syntax, identity migration, protocol docs, and GEO content assets

### Changed

- Identity persistence aligned with the protocol v2 two-line `~/.nestwork_id` format

---

## v0.1.0 - 2026-04-17

### Initial release

- Created the initial nestwork protocol template
- `queen/`, `agents/`, `shared/`, and `projects/` repository layout
- Startup instructions through `AGENTS.md` and `CLAUDE.md`

---

## Maintenance conventions

### When to update

- Protocol changes (AGENTS.md sections, `protocol-version`, etc.) → must update
- New scripts or configuration files → must update
- Pure wording edits, typo fixes, individual comments → no update
- Sync operations in private instances (e.g. `mynestwork`) → no update (this file tracks upstream protocol evolution only)

### MINOR vs MAJOR

- MINOR (e.g. v2.1 → v2.2): new optional fields, directories, hook events or config files; **existing agents keep working without any action**
- MAJOR (e.g. v2.0 → v3.0): directory layout changes, agent-id format changes, breaking hook contracts, breaking `nestwork.config.json` schema

MAJOR bumps **should be avoided**. When one is unavoidable, it must ship a downstream migration path and at least one MINOR release of transition.

### Tags and releases

- Every MINOR bump → tag `v0.x.0`, publish a GitHub Release, and link the release notes from the CHANGELOG
- Patches (bug fixes only, no protocol change) → accumulate until the next MINOR release; no separate tag

### Keeping English and Chinese in sync

- `CHANGELOG.md` (this file) and `CHANGELOG.zh.md` **must stay in sync**
- Whenever one changes, update the other (same information, wording tuned independently)

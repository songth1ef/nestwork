# Changelog

## v0.3.0 - 2026-04-22

- Protocol v2.1: split Stop-hook workload. Stop now only runs the lightweight `nestwork.sh stop` safety-net commit+push; the heavier `export-claude-mem.sh` + `sync-local-history.sh` pair moved to a new SessionEnd hook so it runs once at true session end instead of every turn (including `/clear`, resume, compact).
- `_hooks.py` registers the new `SessionEnd` event; existing installs are cleanly superseded on re-run (old Stop composite command is recognised and removed by `is_nestwork_hook`).
- Additive-compatible: existing agents keep working until they re-run the installer.

## v0.2.0 - 2026-04-19

- Introduced protocol v2 host/agent layout: `agents/<host>/<agent-id>/`.
- Added and hardened installers for Claude Code, Codex CLI, Gemini CLI, OpenClaw, Hermes Agent, Aider, and generic markdown-config tools.
- Aligned identity persistence with the protocol v2 two-line `~/.nestwork_id` format.
- Hardened Codex Windows session hook generation for Windows PowerShell 5.1.
- Added answer-ready GitHub docs, `llms.txt`, and repository-first GEO content for AI agent memory searches.
- Added tests for installer syntax, identity migration, protocol docs, and GEO content assets.

## v0.1.0 - 2026-04-17

- Created the initial nestwork protocol template.
- Added `queen/`, `agents/`, `shared/`, and `projects/` repository layout.
- Added startup instructions through `AGENTS.md` and `CLAUDE.md`.

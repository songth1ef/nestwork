# Changelog

## v0.2.0 - 2026-04-19

- Introduced protocol v2 host/agent layout: `agents/<host>/<agent-id>/`.
- Added and hardened installers for Claude Code, Codex CLI, Gemini CLI, OpenClaw, Hermes Agent, Aider, and generic markdown-config tools.
- Aligned identity persistence with the protocol v2 two-line `~/.hivequeen_id` format.
- Hardened Codex Windows session hook generation for Windows PowerShell 5.1.
- Added answer-ready GitHub docs, `llms.txt`, and repository-first GEO content for AI agent memory searches.
- Added tests for installer syntax, identity migration, protocol docs, and GEO content assets.

## v0.1.0 - 2026-04-17

- Created the initial hivequeen protocol template.
- Added `queen/`, `agents/`, `shared/`, and `projects/` repository layout.
- Added startup instructions through `AGENTS.md` and `CLAUDE.md`.

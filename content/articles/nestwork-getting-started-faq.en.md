---
title: nestwork Setup FAQ: Long-Term Memory for Claude Code
description: How to give Claude Code and Codex long-term memory with nestwork: prerequisites, install, verify, uninstall, cost, privacy, upgrades and team use.
keywords: nestwork setup, how to give Claude Code long-term memory, nestwork install, Claude Code persistent memory, Codex memory, AI agent memory tutorial
date: 2026-09-27
---

**How do you give Claude Code long-term memory with nestwork?** Create a private repo from the nestwork template, clone it to each machine, and run the installer for your tool, for example `bash ~/nestwork/scripts/install/claude.sh`. After that, sessions start by pulling the repo and reading your rules plus a small resident summary, and memory the agent writes is committed and pushed so your other machines and tools can read it.

Below are the questions people ask before and right after installing, each checked against the [README](https://github.com/songth1ef/nestwork/blob/main/README.md).

## What do I need before installing?

| Requirement | Why |
|---|---|
| git, and a git host you can push to (GitHub, or a self-hosted server) | Memory lives in a private git repo; sync is pull and push |
| Non-interactive push credentials (SSH key or a credential helper) | Hooks run in the background and cannot answer a password prompt |
| `python3` on `PATH` (Windows: `python3`, `python` or `py`) | The installers use small Python helpers to resolve identity and edit config files |
| bash on macOS/Linux; PowerShell for the Windows installers | The installers and hooks are shell scripts; the hook code also handles Git Bash paths on Windows |
| The agent tool itself | Claude Code, Codex CLI, Gemini CLI, Kimi Code, OpenClaw, Hermes, or any CLI that reads a Markdown file at startup |

You also need to be comfortable with basic git. The README is explicit: git is the core of nestwork, not optional, and if you don't know git, nestwork is not a good fit.

## How do I install it?

Three steps. There is no service to deploy and no account to create beyond your git host.

1. On GitHub, open the [template](https://github.com/songth1ef/nestwork/generate) (Use this template → Create a new repository) and set visibility to **Private**. Use the template rather than a fork: forks are public by default and share history with upstream, which would make every update collide with your private data.
2. Clone it on each machine:

```bash
git clone git@github.com:<your-username>/nestwork.git ~/nestwork
```

3. Run the installer for each tool you use on that machine:

```bash
bash ~/nestwork/scripts/install/claude.sh     # Claude Code, macOS / Linux
bash ~/nestwork/scripts/install/codex.sh      # Codex CLI
```

On Windows, use `.\nestwork\scripts\install\claude.ps1` and `codex.ps1`. Gemini CLI, Kimi Code, OpenClaw and Hermes follow the same pattern with their own script name. Other Markdown-config CLIs use `bash scripts/install/generic.sh <prefix> <config-path>`.

The README does not give an install time, so none is promised here. The installers only write local files: they create the agent's directory, inject a marked bootstrap block into the tool's startup file, and register hooks where the tool supports them.

### What does each tool actually get?

Tool support is not uniform, and the README says so:

| Tool | Entry file | Sync behavior | Author's status |
|---|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` + hooks | Session-start pull; commit and push after every memory write; Stop and SessionEnd hooks | Daily driver |
| Codex CLI | `~/.codex/AGENTS.md` | Follows the bootstrap; commits its directory manually; SessionEnd hook only for optional history | Daily driver |
| Kimi Code | `~/.kimi-code/AGENTS.md` + hooks | Per-write hooks like Claude Code, but hooks cannot inject context | Installer exists, untested by author |
| Gemini CLI, OpenClaw, Hermes | Their own startup file | No hooks; commit at session end | Installer exists, untested by author |

If you rely on one of the less-tested tools, verify it yourself (next question) before trusting it with real work.

## How do I verify it worked?

The README's verification is a cross-device test, and it is the one that matters:

1. Add a non-sensitive, recognizable rule or project-status note to your private repo, then commit and push it.
2. Open an installed agent on a second computer or a cloud host.
3. Ask it to summarize your current rule or project status. It should pull the repo and answer from the shared context without you repeating anything.

Don't use API keys, secrets or employer-confidential details as test content.

If the agent does not seem to load anything on Claude Code, check that the hooks were registered and re-run the installer if they are missing:

```bash
grep -A 5 SessionStart ~/.claude/settings.json
cat ~/.nestwork_host ~/.nestwork_id_claude
```

If commits are not pushed, the README's checklist is: the remote (`git -C ~/nestwork remote -v`), the hooks in `settings.json`, and whether a manual `git push` asks for interactive credentials.

## How do I uninstall?

Every installer has a mirror under `scripts/uninstall/`:

```bash
bash ~/nestwork/scripts/uninstall/claude.sh
```

It only unbinds: the bootstrap block leaves the tool's startup file and nestwork's hooks are deregistered. Your memory in `agents/<host>/<agent-id>/`, the identity files (`~/.nestwork_host`, `~/.nestwork_id_<tool>`) and your own content in the same config files stay put. Re-running the installer restores the same identity. Add `--purge-identity` (PowerShell: `-PurgeIdentity`) if the next install should start as a brand-new agent.

## Does it cost anything, and is it private?

nestwork has no hosted service, subscription or server; it is scripts and Markdown in a repo you own. The costs are the ones you already have: a git host for the private repo, and your agent tool's own usage. `distill.py --run-claude` or `--run-codex` runs a merge through your local CLI, so that uses your plan's quota like any other prompt.

On privacy, the defaults are simple. The repo is private and yours. Memory is plain Markdown, so anyone with access to the repo can read it, and the agent sends what it reads to its model provider as part of normal work. For content that must sync but stay unreadable to the git host, there is an optional git-crypt mode (see [encrypting agent memory](../encrypt-agent-memory-git-crypt/)). API keys and passwords should never be stored in the nest, encrypted or not. To try it without pushing anywhere, clone locally and don't add a remote, or point `origin` at your own git server.

## How do upgrades work?

Your private repo does not follow upstream automatically. Two ways to pull protocol updates, neither of which touches `agents/`, `queen/`, `shared/` or your own project files:

```bash
bash ~/nestwork/scripts/maintenance/update.sh
```

`update.sh` refuses to run with uncommitted changes, shows the incoming diff, asks for confirmation, and commits locally; you push when ready. Alternatively, the included GitHub Action ("Sync Nestwork upstream") opens a PR when run by hand, or weekly if you set the repository variable `NESTWORK_AUTO_SYNC` to `true`. The Claude Code session-start hook also checks upstream's protocol version (cached for 24 hours) and prints a one-line advisory when a newer one exists; it never applies anything.

One catch: updating repo files does not rewrite each machine's tool config. **Coming from 2.x to 3.x, re-run the installer for every tool on every machine** (or `python3 scripts/install/_bootstrap.py`), then open a new session, because existing conversations keep the old instructions. Going from 3.0 to 3.1 needs no bootstrap refresh; topic memory is opt-in.

## Can a team use it?

Carefully. The FAQ answer is yes, starting from a private repo with clear write rules: one memory directory per agent instance and human-managed rules in `queen/`. But know the boundary. nestwork is aimed at individual developers working with many agents, and team-level access control is an explicit non-goal: repo visibility relies on your git host's permissions, so everyone with access can read every agent's memory. Shared `projects/` and `workflow/` files can be written by several agents, where the pre-write pull reduces but cannot fully eliminate conflicts.

## FAQ

### Do I have to change how I use Claude Code?

No. The README says there is nothing new to learn. The main new habit is telling the agent when something is worth recording.

### Can I install it for several tools on one machine?

Yes. Each tool gets its own identity file, such as `~/.nestwork_id_claude` and `~/.nestwork_id_codex`, so installing one never replaces another.

### What if the installer fails with an identity error?

The installers need `python3` on `PATH` to resolve host and agent id. You can pin the values with `NESTWORK_HOST` and `NESTWORK_AGENT_ID`.

### Does it work with Cursor or Copilot?

At the workspace level, by symlinking `AGENTS.md` into `.cursor/rules/`, `.windsurf/rules/`, `.clinerules/` or `.github/copilot-instructions.md`. `gh copilot` is listed as unsupported.

## Related

- [AI agent memory, explained](../ai-agent-memory/)
- [Claude Code memory across machines](../claude-code-memory-across-machines/)
- [Share memory between Claude Code and Codex](../share-memory-claude-code-codex/)
- [AI agent long-term memory in practice](../long-term-memory-in-practice/)
- [nestwork overview](../nestwork-overview/)

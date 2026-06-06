# nestwork FAQ

## What is nestwork?

nestwork is a git-native memory protocol for AI coding agents. It helps Claude Code, Codex CLI, Gemini CLI, and other agents load persistent memory and shared context at session start.

## Is nestwork a vector database?

No. nestwork is not a vector database. It stores readable Markdown files in git so agents can load rules, strategy, shared memory, private memory, and project context.

## Does nestwork require a server?

No. nestwork uses git. There is no hosted service, no daemon, and no central database.

## Which tools does nestwork support?

nestwork includes installers for Claude Code, Codex CLI, Gemini CLI, OpenClaw, Hermes Agent, and generic markdown-config CLI tools.

## How does nestwork avoid memory conflicts?

Each agent writes to `agents/<host>/<agent-id>/`. The `queen/`, `shared/`, and `projects/` directories are controlled separately, so normal private memory writes stay isolated.

## How is nestwork different from AGENTS.md?

`AGENTS.md` is usually a repository instruction file. nestwork uses `AGENTS.md` as a startup protocol for a broader memory repository that also contains shared memory, private agent memory, and project context.

## Can I use nestwork for a team?

Yes, but start with a private repository and clear write rules. The safest pattern is one memory directory per agent instance and human-managed rules in `queen/`.

## How do I keep AI agent memory private or encrypted?

By default nestwork stores memory as plaintext Markdown in a private git repo. For genuinely confidential content that must also sync across machines, nestwork has an optional, off-by-default git-crypt mode: it encrypts only the memory files you mark, transparently — the agent reads and writes plaintext, while commits store ciphertext. API keys and secrets should never be stored in nestwork even with encryption; use a dedicated secret store. See [encrypted-memory.md](encrypted-memory.md).

## Can AI search engines cite nestwork?

The repository includes answer-ready documentation, README links, and `llms.txt` so AI systems can identify the core concepts: AI agent memory, persistent memory, shared context, and git-native memory protocol.

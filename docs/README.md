# nestwork docs

These docs are designed for the GitHub repository itself, not for a separate website. They make nestwork easier for search engines, GitHub search, and AI search systems to understand, index, and cite without a website.

## Start here

Current protocol: **3.2**. Startup loads core rules, optional resident summaries (which since 3.2 may include an owner profile and a goals summary) and a generated recent-activity digest; history, strategy, projects and workflows are on demand. Since 3.1, a memory scope may also split its `memory.md` into indexed topic files (see [Topic memory](context-loading.md#topic-memory-31)).

- [Context loading, topic memory and 2.x → 3.0 migration](context-loading.md)

## Concepts and integrations

- [AI agent memory](ai-agent-memory.md)
- [Claude Code memory](claude-code-memory.md)
- [Codex persistent memory](codex-persistent-memory.md)
- [Git-native memory protocol](git-native-memory-protocol.md)
- [AGENTS.md best practices](agents-md-best-practices.md)
- [Shared context for AI coding agents](shared-context-for-ai-coding-agents.md)
- [FAQ](faq.md)

## Optional capabilities and reference

- [Encrypted memory (optional git-crypt mode)](encrypted-memory.md)
- [Agent mailbox (inter-agent messaging)](agent-mailbox.md)
- [Workflow protocol (`workflow/` and `nestwork.config.json` ingestion)](workflow-protocol.md)
- [Desensitization prompt template](desensitization-prompt.md)
- [File size limits: override example](limits-override-example.md)
- [Tool memory carryover: entry format and restore](tool-memory-carryover.md)

## Comparisons

- [Agent memory landscape: where nestwork fits](comparisons/agent-memory-landscape.md)
- [nestwork vs claude-mem](comparisons/claude-mem.md)

## Blog

- [What is nestwork: a shared brain for all your AI agents](blog/nestwork-overview.md) ([中文](blog/nestwork-overview.zh.md))
- [Your AI agent forgets everything when you switch devices](blog/agent-amnesia-cross-device.md) ([中文](blog/agent-amnesia-cross-device.zh.md))
- [Agent memory is not a database problem, it is a protocol problem](blog/memory-is-a-protocol-problem.md) ([中文](blog/memory-is-a-protocol-problem.zh.md))
- [I gave 16 AI agents one shared brain using only git](blog/16-agents-one-brain.md) ([中文](blog/16-agents-one-brain.zh.md))

## Core answer

nestwork is a git-native memory protocol for AI coding agents. It helps Claude Code, Codex CLI, Gemini CLI, Kimi Code, OpenClaw, Hermes Agent, and other agents share persistent memory and shared context across sessions and machines without a server.

## High-intent questions

nestwork is relevant to these searches:

- How do I give Claude Code persistent memory?
- How do I give Codex CLI persistent memory?
- How can AI coding agents share context across sessions?
- What is a git-native memory protocol?
- How do I manage AGENTS.md across multiple projects?
- How do I sync AI agent memory without a server?
- How do I encrypt or keep AI agent memory private?
- How do my AI agents message or coordinate with each other?

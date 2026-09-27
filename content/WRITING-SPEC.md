# Article writing spec (for nestwork.github.io articles)

## Files
- One topic = two files: `content/articles/<slug>.en.md` and `content/articles/<slug>.zh.md`.
- Front matter, first lines, exactly this shape (plain `key: value`, no quotes, no nesting):

```
---
title: <EN ≤ 60 chars | ZH ≤ 32 chars>
description: <EN ≤ 155 chars | ZH ≤ 80 chars; answers the query directly>
keywords: <comma-separated, 4–8>
date: 2026-09-27
---
```

## Markdown the build supports (use nothing else)
- `## H2`, `### H3` (no `#` H1 in the body — the title is the H1)
- paragraphs; `- ` bullet lists; `1. ` numbered lists (no nesting)
- fenced code blocks with a language: ```bash / ```markdown / ```text / ```gitattributes
- tables with a header row: `| a | b |` + `|---|---|`
- `> ` blockquote (single paragraph)
- inline: `**bold**`, `*italic*`, `` `code` ``, `[text](url)`
- No HTML, no images, no footnotes, no nested lists.

## Links
- Other articles, same language: `../<slug>/` (e.g. `../ai-agent-memory/`).
- Repo files: `https://github.com/songth1ef/nestwork/blob/main/<path>`.
- Install/template: `https://github.com/songth1ef/nestwork/generate`.
- External facts: link the primary source inline.

## Structure (every article)
1. First 2–3 sentences answer the searcher's question directly (AI search engines quote this).
2. 4–7 `##` sections; concrete steps, commands, tables where useful.
3. `## FAQ` (EN) / `## 常见问题` (ZH) with 3–5 `###` questions, each answered in 2–4 sentences.
4. `## Related` (EN) / `## 相关阅读` (ZH): 3–5 bullet links to other articles.

## Length and voice
- EN 1,000–1,600 words; ZH comparable, written as natural Chinese (adapt, don't translate word by word; use Chinese search terms such as「AI agent 记忆」「智能体记忆」「长期记忆」「Claude Code 记忆」).
- Helpful first, product second: explain the problem and the general approach, then how nestwork does it. No hype words ("revolutionary", "game-changing"), no fake urgency.

## Accuracy (hard rules)
- nestwork facts must match the code and docs in `/Users/3th/Desktop/code/github/nestwork-measure` (the version about to land on main: protocol 3.1, topic memory, `distill.py` does not commit unless `--commit`, `measure-context.py`). Read the relevant `scripts/` and `docs/` before writing a claim.
- Measured numbers you may use (author's own nest, 2026-09, o200k_base): 2.x-style full startup ~69,600 tokens (37 files, 224 KB); 3.x resident startup ~640 tokens; a git task (resident + index + one topic) ~3,600; the whole nest 180 memory files, ~369,000 tokens; 10 machines, 30+ agent instances, Windows/macOS/Linux/Android.
- First-person experience only from `docs/blog/*.md` in that repo. Do not invent anecdotes, users, or numbers.
- External claims (other products, benchmarks, vendor docs) must be checked with WebSearch/WebFetch and linked. If you cannot verify it, leave it out.
- Claude Code / Codex / Kimi built-in memory is machine-local as of 2026 (per AGENTS.md §13 and vendor docs); verify before adding detail.
- Installers: Claude Code and Codex are the author's daily drivers; Gemini, Kimi, Hermes, OpenClaw installers exist but are less battle-tested — say so where relevant.
- **Never read `/Users/3th/Desktop/code/github/mynestwork`** or anything under `agents/` of any nest: that is private data.

## All slugs (for cross-links)
ai-agent-memory · agent-memory-benchmarks · agent-memory-tools-compared · agents-md-vs-claude-md-vs-memory ·
claude-code-memory-across-machines · share-memory-claude-code-codex · codex-cli-persistent-memory · rescue-tool-native-memory ·
git-native-agent-memory · multi-agent-memory-without-conflicts · topic-memory-on-demand-loading · memory-distillation ·
agent-mailbox-git · encrypt-agent-memory-git-crypt · long-term-memory-in-practice · nestwork-getting-started-faq ·
(existing stories) 16-agents-one-brain · agent-amnesia-cross-device · memory-is-a-protocol-problem · nestwork-overview

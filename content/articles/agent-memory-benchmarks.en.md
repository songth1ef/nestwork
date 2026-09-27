---
title: Agent Memory Benchmarks — LoCoMo, LongMemEval, BEAM
description: What LoCoMo, LongMemEval and BEAM measure, how LLM judges score them, why vendor numbers don't compare, and which metrics matter for coding agents.
keywords: agent memory benchmark, LoCoMo, LongMemEval, BEAM benchmark, LLM as a judge, AI memory evaluation, coding agent memory
date: 2026-09-27
---

The three agent memory benchmarks you will see quoted most are LoCoMo, LongMemEval and BEAM. All three test whether a system can answer questions about long chat histories, and all three are scored by an LLM judge, so a vendor's number depends heavily on which judge model, which answer model and which retrieval pipeline produced it. They are useful for comparing chat-memory systems under one setup; they say little about what a coding agent needs, such as cross-tool handoff, startup cost and whether the right memory file gets opened.

## The three benchmarks at a glance

| Benchmark | Source | Data | What it asks |
|---|---|---|---|
| LoCoMo | [Maharana et al., 2024](https://arxiv.org/abs/2402.17753) | Very long conversations, ~300 turns and ~9K tokens on average, up to 35 sessions | Question answering, event summarization, multimodal dialogue generation |
| LongMemEval | [Wu et al., ICLR 2025](https://github.com/xiaowu0162/longmemeval) | 500 questions; the S variant is ~115K tokens (~40 sessions), the M variant ~500 sessions | Information extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention |
| BEAM | [BEAM, ICLR 2026](https://github.com/mohammadtavakoli78/BEAM) | 100 conversations from 128K up to 10M tokens, 2,000 validated questions | Ten abilities, including contradiction resolution, event ordering, instruction following and preference following |

### LoCoMo

LoCoMo was built with persona-grounded agents and temporal event graphs to produce very long two-person conversations. Most memory vendors report only its question-answering part. The Mem0 paper, for instance, used the 10 conversations, about 200 questions per conversation, and excluded the adversarial category "because ground truth answers were unavailable" ([arXiv:2504.19413](https://arxiv.org/html/2504.19413)). Even the size is described differently: the original paper reports about 9K tokens per conversation on average, while the Mem0 paper describes its evaluation conversations as roughly 26,000 tokens each. When someone quotes a LoCoMo score, check which categories and which version of the data they used.

### LongMemEval

LongMemEval embeds 500 curated questions in timestamped user–assistant histories. Question types include single-session user and assistant facts, preferences, temporal reasoning, knowledge updates and multi-session reasoning, plus abstention questions where the correct answer is to decline. The authors report that commercial assistants and long-context models showed about a 30% accuracy drop on memorizing information across sustained interactions.

### BEAM

BEAM ("Beyond a Million Tokens") pushes length much further: conversations of 128K, 500K, 1M and 10M tokens. The paper's point is that even models with 1M-token windows, with or without retrieval, struggle as dialogues lengthen. It scores ten ability categories separately rather than giving one headline number.

## How scoring works — and why it moves

Answers to open questions cannot be string-matched, so all three rely on **LLM-as-a-judge**: a model reads the question, the reference answer and the system's answer, and decides whether it is correct. LongMemEval's evaluation script uses GPT-4o as the judge. In the Mem0 paper, answers were generated with GPT-4o-mini and graded by a separate judge LLM.

That creates three knobs that change the score without changing the memory system:

1. **The judge model.** A stricter or more lenient judge grades the same output differently.
2. **The answer model.** A stronger model reading the same retrieved memories answers more questions correctly.
3. **Post-processing.** Reranking or other LLM steps between retrieval and answering can lift scores substantially.

Mem0's own [2026 benchmark roundup](https://mem0.ai/blog/ai-memory-benchmarks-in-2026) is candid about this: "None of these numbers were generated using the same model stack, judge model, or retrieval configuration." The same post lists Zep at 94.7% on LoCoMo by its own claim versus 75.1% in a third-party test, and notes that ByteRover's testing reported Mem0 at 66.9%, matching an older Mem0 algorithm, against Mem0's current self-reported 92.5%. Treat any cross-vendor leaderboard as a reading list, not a ranking — including tables published by a vendor that appears in them.

## What the Mem0 paper actually shows

The Mem0 paper is the origin of many LoCoMo comparisons, and its table is worth reading in full. On the LLM-as-a-judge metric, Mem0 scored 66.88% and its graph variant 68.44%, ahead of the other memory systems tested — Zep 65.99%, LangMem 58.10%, OpenAI's memory 52.90%. But the **full-context baseline**, which simply puts the whole conversation into the prompt, scored 72.90%, the highest in the table. The paper says so directly.

What memory bought was cost and speed: about 1,764 tokens per query against 26,031 for full context, and a p95 latency of 1.44 seconds against 17.12. That is the honest trade-off for chat memory — slightly lower accuracy for an order of magnitude less context — and it is the frame to keep when reading any memory benchmark.

## Letta's filesystem result: 74.0%

In August 2025 Letta [ran LoCoMo with no memory service at all](https://www.letta.com/blog/benchmarking-ai-agent-memory/). The conversation was placed in a file attached to an agent running GPT-4o mini, which could only use `grep`, `search_files`, `open`, `close` and `answer_question`, with tool rules forcing it to search before answering. It scored **74.0%**, above the 68.5% Letta cites for Mem0's best graph variant.

Letta's conclusion is the useful part: "the quality of an agent's memory often depends more on the underlying agentic system's ability to manage context and call tools than on the memory tools themselves." The same caution applies to this number as to any other — it is one run with one model and one judging setup — but it shows that plain files plus an agent that knows how to search are a competitive baseline, not a toy.

## What these benchmarks don't measure

LoCoMo, LongMemEval and BEAM test **chat memory**: can the system recall what a person said, when, and whether it changed? A coding agent's memory problem is different. It mostly carries rules, project state and past decisions; it has to work across tools and machines; and much of its cost is paid at startup, before any question is asked. None of the three benchmarks has a category for "the rule from Claude Code was obeyed in Codex on another laptop."

## Metrics that matter for coding agents

If you are choosing memory for coding agents, measure these on your own setup:

| Metric | Question it answers | How to measure |
|---|---|---|
| Cross-tool handoff | Does a fact recorded in tool A reach tool B on another machine? | Record a non-sensitive rule in one tool, open another tool elsewhere, ask it to state the rule |
| Startup overhead | How many tokens load before the first task? | Count files and tokens read at session start |
| Task-time load | How much extra context does a typical task pull in? | Count tokens for startup plus whatever the task retrieves |
| Routing accuracy | Does the agent open the right memory file for the task? | For a set of tasks, record which files it opened versus which it should have |
| Rule precedence | When two sources conflict, does the authoritative one win? | Plant a conflict between a rule and an old note, check the outcome |
| Reviewability | Can a human see and correct what was stored? | Look at the last week of memory changes as a diff |

For reference, nestwork's `scripts/maintenance/measure-context.py` reports the first three on the author's own nest (10 machines, 30+ agent instances, tokens counted with `o200k_base`): a 2.x-style full startup read 37 files, about 69,600 tokens; the protocol 3.x resident startup is about 640 tokens; a git task that reads the resident tier, the topic index and one topic file is about 3,600; and the whole nest is 180 memory files, about 369,000 tokens. These are one person's measurements, not a benchmark. nestwork does not publish a routing-accuracy number; if you adopt topic memory, that is the metric to track yourself.

## FAQ

### Which agent memory benchmark is the most reliable?

None is reliable in isolation, because the judge and answer models dominate the result. LongMemEval has the most fixed evaluation recipe (a published script with GPT-4o as judge); BEAM tests the longest contexts and reports ten abilities separately. The most reliable comparison is one you run yourself with every system on the same model stack.

### Why does full context beat memory systems on LoCoMo?

LoCoMo conversations are short enough, around 26,000 tokens per conversation in the Mem0 paper's setup, to fit into a modern context window. When everything fits, nothing is lost to retrieval. Memory systems win on tokens and latency, and they become necessary once the history no longer fits — which is what BEAM's 1M and 10M settings test.

### Does Letta's 74.0% mean files beat vector memory?

It means a capable agent searching plain files was competitive on one benchmark with one model. It does not prove files win everywhere; it does show that retrieval tooling and agent behavior matter at least as much as the storage engine.

### Are there benchmarks for coding agent memory?

Not widely adopted ones that we could verify. Until there are, measure handoff, startup overhead, task-time load and routing accuracy on your own repositories and tools.

## Related

- [AI agent memory: four types and their trade-offs](../ai-agent-memory/)
- [Agent memory tools compared](../agent-memory-tools-compared/)
- [Topic memory and on-demand loading](../topic-memory-on-demand-loading/)
- [Long-term memory in practice](../long-term-memory-in-practice/)

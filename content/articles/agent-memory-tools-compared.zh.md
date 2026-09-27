---
title: agent 记忆工具对比：Mem0、Letta、Zep 等
description: 从架构、部署方式、数据归属和适用场景，对比 Mem0、Letta、Zep、Supermemory、claude-mem、工具内置记忆和 nestwork。
keywords: agent 记忆工具 对比, mem0 替代, Letta vs mem0, Zep, Supermemory, claude-mem, nestwork, 智能体记忆
date: 2026-09-27
---

agent 记忆工具大致分三类：一是**记忆服务**，由你自己的应用调用（Mem0、Zep、Supermemory）；二是**agent 运行时**，替跑在里面的 agent 管理记忆（Letta）；三是**编码 agent 的附加层**，让 Claude Code、Codex 这类工具跨会话记住东西（claude-mem、工具内置记忆、nestwork）。如果你在做一个要记住成千上万终端用户的产品，看第一类；如果你想让自己的几个编码 agent 跨机器、跨工具共享规则和项目状态，看第三类。Letta 介于两者之间，而且从 2026 年起也把记忆放进了 git。

## 一张表看完

| 工具 | 架构 | 部署方式 | 记忆存在哪 | 最适合 |
|---|---|---|---|---|
| [Mem0](https://github.com/mem0ai/mem0) | LLM 抽取记忆；向量库，可选图记忆 | 库、自托管服务或托管云 | 你的数据库或 Mem0 云 | 给 AI 应用加"每用户一份"的记忆 |
| [Letta](https://github.com/letta-ai/letta) | 有状态 agent 运行时；记忆块，新版为 git 支撑的记忆文件系统 | 本地 Letta Code、自托管服务或 Letta Cloud | agent 自己的 git 仓库，云端 agent 由 Letta 托管 | 住在 Letta 里、自己管理记忆的 agent |
| [Zep](https://www.getzep.com/) | 时序知识图谱（开源引擎是 [Graphiti](https://github.com/getzep/graphiti)） | Zep Cloud、自带密钥、部署在自有云 | Zep 云或你的 VPC；Graphiti 用你的图数据库 | 把对话和业务数据合在一起的企业级上下文 |
| [Supermemory](https://github.com/supermemoryai/supermemory) | 事实抽取，处理时间变化、矛盾与遗忘；混合检索 | 托管 API 或自托管单文件 | Supermemory 云或你的机器 | 面向应用和助手的记忆 API 与插件 |
| [claude-mem](https://github.com/thedotmack/claude-mem) | 用 hook 捕获工具调用，存入 SQLite + Chroma 向量索引 | 本地 worker 进程 | 每台机器上的本地数据库 | 单机上自动记录编码 agent 的会话 |
| 内置记忆（Claude Code、Codex） | agent 自己写 markdown 笔记 | 自带 | `~/.claude/projects/…/memory/`、`~/.codex/memories/` | 一个工具、一台机器、零配置 |
| [nestwork](https://github.com/songth1ef/nestwork) | 协议：私有 git 仓库里的 markdown，经各工具的指令文件加载 | 模板仓库 + 各工具安装脚本 | 你自己的 git 仓库 | 多个编码 agent 跨机器、跨工具共享规则和状态 |

每一行都是 2026 年 9 月的快照，细节以各项目官方文档为准。

## 逐个来看

### Mem0

Mem0 自称"AI agent 的记忆层"，Apache-2.0 协议，提供三种形态：Python/JavaScript 库、用 Docker 自托管的服务、托管平台。你把对话发过去，LLM 从中抽取记忆，Mem0 存进向量数据库（可选图记忆），按需取回相关条目。它能接入 LangGraph、CrewAI 等框架。

Mem0 的[论文](https://arxiv.org/abs/2504.19413)报告：在 LoCoMo 上每次查询约 1,764 token，全量上下文基线是 26,031，p95 延迟低 91%。需要在产品里做"每用户记忆"时，它是很强的选择。搜"**mem0 替代**"的人通常想要两者之一：一个 API 相近的别家服务（Zep、Supermemory），或者在更小、更个人的场景里干脆不用服务。

### Letta

Letta 前身是 MemGPT，自称"有状态 agent 的平台"，Apache-2.0 协议。在经典 API 里，agent 带着带标签的**记忆块**（如 `human`、`persona`），并用内置工具自己读写。开发重心已经转到 [Letta Code](https://github.com/letta-ai/letta-code)，其新记忆系统 [MemFS](https://docs.letta.com/concepts/memfs) 把每个 agent 的记忆放在一个 git 仓库里：`system/` 下的文件每轮都进提示词，其余按需读取。云端 agent 的仓库由 Letta 托管；Letta Code 会把它 [clone 到本地](https://www.letta.com/blog/context-repositories/)，子 agent 通过 git worktree 并发写入。

**Letta 和 Mem0 怎么选**，主要看 agent 跑在哪。Mem0 是一个记忆组件，装到你自己的 agent 循环上；Letta 本身就是 agent 循环，记忆管理是 agent 思考方式的一部分。如果你愿意在 Letta 里工作，它 git 化的记忆已经相当成熟，和 nestwork 的思路有重叠；区别在于 nestwork 面向的是别家厂商的工具，而不是 Letta 自己的 agent。

### Zep

Zep 现在的定位是"企业数据的统一上下文层"。核心是时序知识图谱：每条事实都有"有效期"，记录它何时成立、何时（如果有的话）被取代。托管服务提供 Zep Cloud、自带密钥加密、以及部署到你自己的 VPC。开源引擎 Graphiti（Apache-2.0）可跑在 Neo4j、FalkorDB 或 Amazon Neptune 上，适合想自己搭外围系统的人。事实会随时间变化、而你又需要跨业务数据查询其历史时，选它。

### Supermemory

Supermemory 是 MIT 协议，自称"记忆与上下文引擎"。它从对话里抽取事实，处理时间变化和矛盾，支持自动遗忘，并在文档和记忆上做混合检索。可以用托管 API，也可以本地跑"一个二进制、零配置"的版本；提供 MCP 服务器，以及 Claude Code、Cursor、Windsurf、VS Code 插件。它的 README 声称在 LongMemEval、LoCoMo、ConvoMem 上排名第一；和所有厂商成绩一样，这些是[厂商自己配置下的自报数字](../agent-memory-benchmarks/)。

### claude-mem

claude-mem 用五个生命周期 hook 捕获 agent 的操作，生成摘要，供之后的会话检索。存储是 SQLite 加 Chroma 向量索引，由本地 worker 提供服务。README 列出支持 Claude Code、OpenClaw、OpenCode 等。数据库在本地，所以记忆留在跑 worker 的那台机器上。nestwork 可以和它并用：claude-mem worker 在 `localhost:37777` 可达时，nestwork 的 Claude Code SessionEnd hook 会把当天的观察导出到 `agents/<host>/<agent-id>/claude-mem-digest.md`，再随 git 同步到其他机器。

### 工具内置记忆

Claude Code 的 auto memory 和 Codex 的 memories 都无需配置、自动写入，也都只在本机：Claude Code 文档说 auto memory 文件"不跨机器或云环境共享"，Codex 把记忆存在 `~/.codex/memories/`。Codex 自己的建议是：必须遵守的规则放 `AGENTS.md`，记忆只当"辅助回忆层"。一个人、一台机器、一个工具时，这往往就够了。

### nestwork

nestwork 是协议，不是服务。你用模板建一个私有仓库，给每个工具跑一次安装脚本，工具的指令文件里就多了一段启动协议：pull 仓库，读一小块常驻层，其他按需取。每个 agent 只写 `agents/<host>/<agent-id>/`；共享记忆只能经过有人审阅的蒸馏改动；冲突由固定的优先级链裁决。在作者的 nest 上（10 台机器、30 多个 agent 实例），常驻启动约 640 token。

Claude Code 和 Codex 是作者日常主力；Gemini CLI、Kimi Code、Hermes、OpenClaw 的安装脚本也有，但实战检验较少。

## nestwork 不适合的场景

说清楚它不做什么：

- **面向终端用户的聊天应用。** 没有按用户的 API，没有多租户存储，没有 SDK。请用 Mem0、Zep 或 Supermemory。
- **在海量对话里做语义检索。** 检索靠 agent 搜标题和关键词，可选用主题索引做路由，没有向量索引。
- **自动记录一切。** nestwork 只存 agent 或你认为值得留的东西。想记录每一次会话，用 claude-mem 或内置记忆，再从中蒸馏。
- **需要权限控制的团队。** 权限完全依赖 git 托管平台，没有额外的 ACL 层。
- **不用 git 的人。** git 就是传输层。README 说得很直接：不会 git，nestwork 就不适合你。
- **密钥。** API key 不该放进去，加不加密都一样。

## 怎么选

1. 做有大量终端用户的产品？从记忆服务开始：Mem0、Zep 或 Supermemory。
2. 想要整个运行时都"懂记忆"的 agent？看 Letta。
3. 一个编码工具、一台机器？内置记忆，需要的话加 claude-mem。
4. 多个编码工具或多台机器，并希望规则和项目状态是你自己拥有、可审阅的文本？用 nestwork 这类文件协议。

它们并不互斥。常见的组合是：内置记忆负责工具本地的零碎笔记，定期蒸馏进一个所有工具都读的 git nest。

## 常见问题

### 最好的 Mem0 替代是什么？

取决于你为什么要换。想要另一个托管记忆 API，比较 Zep（时序图谱）和 Supermemory（事实抽取，可自托管）。想给个人编码 agent 做记忆又不想跑服务，nestwork 这样的文件方案或 Letta 的 git 记忆更轻。

### Letta 和 Mem0 该用哪个？

已经有自己的 agent 或应用、只想加记忆，用 Mem0。想让平台来跑 agent 并替你管理记忆，用 Letta。两者解决的是相邻问题，而不是正面竞争。

### nestwork 能和 Mem0 或 claude-mem 一起用吗？

能。nestwork 只管编码 agent 读写的那些文件。它内置了 claude-mem 摘要导出；一个应用用 Mem0，而开发这个应用的人用 nestwork 管自己的 agent，也完全不冲突。

### 各工具的数据分别存在哪？

托管服务默认存在厂商云里，除非自托管；claude-mem 和内置记忆存在每台本地机器上；Letta 存在 agent 的 git 仓库里；nestwork 存在你自己拥有的 git 仓库里。

## 相关阅读

- [AI agent 记忆：四种类型与取舍](../ai-agent-memory/)
- [agent 记忆基准测试：LoCoMo、LongMemEval 与 BEAM](../agent-memory-benchmarks/)
- [抢救工具自带的记忆](../rescue-tool-native-memory/)
- [多 agent 记忆如何不冲突](../multi-agent-memory-without-conflicts/)
- [nestwork 入门常见问题](../nestwork-getting-started-faq/)

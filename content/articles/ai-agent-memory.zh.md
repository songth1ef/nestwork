---
title: AI agent 记忆：四种类型与取舍
description: AI agent 记忆是智能体在单次会话之外还能依赖的上下文。对比上下文窗口、工具内置记忆、向量检索服务和文件式记忆，以及编码 agent 的特殊需求。
keywords: AI agent 记忆, 智能体长期记忆, 智能体记忆, 长期记忆, Claude Code 记忆, AGENTS.md
date: 2026-09-27
---

AI agent 记忆，指智能体在当前对话之外还能依赖的上下文：必须遵守的规则、关于你和项目的事实、之前做过的决定。智能体长期记忆大致有四种形态——上下文窗口本身、工具内置记忆、基于向量或图的检索服务，以及由协议加载的纯文本文件。对编码 agent 来说，真正决定选型的往往不是检索算法有多聪明，而是：记忆存在哪、哪些工具能读、人能不能审阅。

## 为什么 agent 需要记忆

大模型在两次调用之间不保留任何状态。Claude Code 的文档说得很直白："每个 Claude Code 会话都从一个全新的上下文窗口开始"（[Claude Code 记忆文档](https://code.claude.com/docs/en/memory)）。会话开始时 agent 对你的一切"了解"，都是某种机制放进去的——读了一个文件、上次写下的笔记，或者一次检索。

没有这种机制，你每次都要重讲一遍：代码规范、哪个目录不能碰、上周为什么放弃了某个方案。记忆就是用来消除这种重复的东西。下面四种类型的区别在于：谁来写、存在哪、怎么回到上下文窗口里。

## 类型一：会话内上下文

最简单的记忆就是对话本身。当前会话里说过的内容都在上下文窗口里，直到会话结束或被压缩。

- **优点**：什么都不用装，窗口内记得一字不差。
- **缺点**：会话一关就没了；会话越长越贵，窗口越满注意力越分散。

这是工作记忆，不是长期记忆。其他三种类型，本质上都在回答"下次该往这个窗口里放什么"。

## 类型二：工具内置记忆

如今多数编码 agent 都会给自己记笔记。Claude Code 的 auto memory 把你的偏好和纠正写进 `~/.claude/projects/<project>/memory/`，其中 `MEMORY.md` 索引的前 200 行或前 25 KB 会在每次会话加载。Codex 把记忆存在 `~/.codex/memories/`，在后台根据之前的对话生成（[Codex 记忆文档](https://learn.chatgpt.com/docs/customization/memories?surface=app)）。

- **优点**：零配置，自动写入，针对该工具调好了。
- **缺点**：绑定单个工具、单台机器。Claude Code 文档原文："Auto memory is machine-local … Files are not shared across machines or cloud environments."（auto memory 只在本机，不跨机器、不跨云环境共享。）Codex 文档则建议：把记忆当作"辅助回忆层"，而不是必须始终生效的规则的唯一来源。

一个人、一台机器、一个工具时，内置记忆是很好的默认选项。三者中任何一个变成"多个"，它就不够用了。

## 类型三：检索服务（向量与图记忆）

[Mem0](https://github.com/mem0ai/mem0)、[Zep](https://www.getzep.com/)、[Supermemory](https://github.com/supermemoryai/supermemory) 这类服务通过 API 提供记忆：你把对话发过去，由 LLM 抽取事实，存进向量索引、图数据库或两者兼有，查询时返回相关的条目。Zep 的开源引擎 [Graphiti](https://github.com/getzep/graphiti) 会给每条事实标注"有效期"：何时成立、何时（如果有的话）被取代。

- **优点**：能在大量对话上做语义检索；天然支持"每个终端用户一份记忆"；内置了更新和矛盾处理。
- **缺点**：要自己部署或租用一个服务；写入时多出 LLM 调用；记忆以数据库记录存在，要通过厂商工具查看，而不是直接编辑文本。

如果你在做一个要记住成千上万用户的产品，这就是对的形态。如果你只是一个开发者，想让自己的规则跟着你在不同编辑器间走，它就偏重了。

## 类型四：文件与协议

第四类是 agent 启动时读取的纯文本：`AGENTS.md`、`CLAUDE.md`、`GEMINI.md`，以及建立在它们之上的系统。[AGENTS.md](https://agents.md/) 是一个开放格式，已有超过 6 万个开源项目在用，Codex、Cursor、Jules 等众多工具都会读取；Claude Code 读 `CLAUDE.md`，新版本在没有 `CLAUDE.md` 时也会读 `AGENTS.md`。

- **优点**：可读、可 diff、可审阅；读取不需要网络或服务；任何读 markdown 的工具都能用；放进 git 就自带历史。
- **缺点**：默认没有语义检索；写什么需要有人决定；文件无节制地长大，每次会话都要为它付 token。

| 类型 | 谁写 | 存在哪 | 跨工具 | 跨机器 | 人可审阅 |
|---|---|---|---|---|---|
| 会话内上下文 | 对话本身 | 上下文窗口 | 否 | 否 | 仅当下 |
| 工具内置记忆 | agent 自己 | 工具本地目录 | 否 | 否 | 可以，但要自己去翻 |
| 检索服务 | LLM 抽取 | 向量/图数据库 | 通过 API/SDK | 通过服务 | 通过厂商工具 |
| 文件与协议 | 你和 agent | 你的文件 / git | 是 | 通过 git 或同步 | 是，以 diff 形式 |

## 编码 agent 的特殊需求

大部分记忆研究面向的是要"记住人"的聊天助手。编码 agent 的需求不一样：

1. **跨工具。** 很多人在 Claude Code、Codex、Gemini CLI 之间切换，在一个工具里学到的规则，换到下一个工具也该成立。
2. **跨机器。** 笔记本、台式机、云端开发机。Claude Code 和 Codex 的内置记忆都只留在写下它的那台机器上。
3. **规则优先级。** "禁止直接 push main"必须压过一条旧笔记"已把热修复推到 main"。按相似度检索不知道两条冲突的事实里谁说了算。
4. **可审阅。** 你应该能看到 agent 对你有哪些认知，能改正它，能看到谁在什么时候改了什么。放在版本控制里的纯文本天然做得到。
5. **启动开销低。** 启动时加载的东西每次会话都要付费，所以常驻部分必须小，其余按需取。

## nestwork 的做法

[nestwork](https://github.com/songth1ef/nestwork) 属于第四类：一个面向 AI 编码 agent 的 git 原生记忆协议。记忆是 markdown，放在你用模板创建的私有 git 仓库里；每个工具的指令文件（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.gemini/GEMINI.md` 等）被注入一段简短的启动协议；agent 干活前 pull，写完 push。

- **优先级是显式的**：`queen/agent-rules.md > queen/strategy.md > shared/memory.md > agents/*/*/memory.md > projects/*.md > workflow/*.md`。冲突时取高优先级，不做合并。
- **每个 agent 只写自己的目录**（`agents/<host>/<agent-id>/`），不同机器上并行的 agent 不会互相覆盖。共享记忆只能经过有人审阅的"蒸馏"步骤改动。
- **启动只加载常驻层。** 在作者自己的 nest 上（10 台机器、30 多个 agent 实例）：2.x 式的全量启动要读 37 个文件，约 69,600 token；3.x 协议的常驻启动约 640 token；一次典型的 git 任务（常驻层 + 索引 + 一个主题文件）约 3,600 token。整个 nest 有 180 个记忆文件、约 369,000 token，已经塞不进大多数上下文窗口，所以加载必须有选择。你可以用 `scripts/maintenance/measure-context.py` 测自己的。

Claude Code 和 Codex 是作者日常主力；Gemini CLI、Kimi Code、Hermes、OpenClaw 的安装脚本也有，但实战检验较少。nestwork 不是向量库，也不是聊天记录归档，而且要求你会用 git。

## 常见问题

### AI agent 的短期记忆和长期记忆有什么区别？

短期记忆就是当前会话的上下文窗口，会话结束即消失。长期记忆是存在会话之外、之后再加载回来的东西——文件、数据库、工具的记忆目录。工程上的难点在于决定存什么、加载什么。

### 上下文窗口够大，还需要记忆吗？

需要。窗口大只是能多装，但装进去的每个 token 每次会话都要付费，窗口越满注意力越差。Mem0 的论文里，LoCoMo 上"全量上下文"基线的准确率其实高于他们的记忆系统，但每次查询约 26,000 token，而记忆方案不到 2,000（[arXiv:2504.19413](https://arxiv.org/abs/2504.19413)）。记忆的核心是：少装，但装准。

### 用了文件式记忆，要关掉工具自带的记忆吗？

不用。两者管的是不同层：内置记忆适合工具本地的零碎笔记，文件层负责把规则和决定带到别的工具和机器。nestwork 把内置记忆当作定期蒸馏的来源，而不是替代对象。

### 编码 agent 需要向量数据库吗？

对个人规则和项目状态来说通常不需要——它们体量小，而且精确、可审阅的文本更合适。只有当你要在海量非结构化对话里检索（典型是面向终端用户的产品）时，向量或图服务才值回成本。

## 相关阅读

- [agent 记忆基准测试：LoCoMo、LongMemEval 与 BEAM](../agent-memory-benchmarks/)
- [agent 记忆工具对比](../agent-memory-tools-compared/)
- [AGENTS.md 和 CLAUDE.md 的区别，以及记忆放哪](../agents-md-vs-claude-md-vs-memory/)
- [git 原生的 agent 记忆](../git-native-agent-memory/)
- [主题记忆与按需加载](../topic-memory-on-demand-loading/)

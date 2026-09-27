---
title: AI 长期记忆用起来是什么样：积累、迁移与维护
description: 给 AI agent 加上跨会话的长期记忆后，日常会怎样：上下文如何积累、换机器换工具时发生什么、记忆多了怎么办、要做哪些维护。
keywords: AI 长期记忆 使用体验, 上下文 自动积累, AI agent 记忆, 跨会话 记忆, Claude Code 记忆, nestwork
date: 2026-09-27
---

**给 AI 编码 agent 加上长期记忆，用起来到底是什么感觉？** 大多数时候，你感觉不到它。打开会话，agent 已经知道你的规则，也知道去哪查过去的决定，「你是谁、上次做到哪」这段开场白直接省掉。在 nestwork 里，记忆是私有 git 仓库里的 Markdown：写入即提交、推送，其他机器和工具下次 pull 就能读到；历史只在任务需要时才去查，所以启动一直很轻。

下面回答用了一周之后最常被问到的几个问题：记忆怎么积累、换机器换工具时发生什么、记忆多了怎么办、平时要做哪些维护。

## 上下文会自动积累吗？

一半是。要把「决定留什么」和「把它留下来」分开看。

**决定留什么，仍然是你的事。** nestwork 的 [README](https://github.com/songth1ef/nestwork/blob/main/README.md) 写得很直白：遇到一个决定、一条教训、项目状态的变化，你让 agent 记下来，或者接受它的提议。协议也要求 agent 只保存值得留下的上下文，临时任务细节和一次性的调试笔记不记。

**留下来，是自动的。** 在 Claude Code 和 Kimi Code 上，agent 在自己目录里的每一次 Write/Edit 都被 hook 包住：

1. 写之前：`git pull --rebase`，避免覆盖远端更新；有冲突就拦下这次写入。
2. 写之后：`git add`，提交信息为 `memory: update <host>/<agent-id>`，然后 push，失败最多重试三次。
3. 每轮对话结束：Stop hook 再兜底提交、推送一次，工作区干净时什么也不做。

Codex、Gemini CLI 等没有逐次写入 hook 的工具，按启动文件里的协议，在会话结束时提交自己的目录。在 git log 里看到的效果是一样的：一串小而带日期的记忆提交，每一条都能回滚。

## 每次启动加载多少？

刻意很少。从协议 3.0 起，会话启动只加载常驻层：`queen/agent-rules.md`（你的规则）、`shared/resident.md` 和该 agent 自己的 `resident.md`。其余的，包括策略、`memory.md` 里的历史、`projects/`、`workflow/`，都等任务需要时再检索。

作者在自己的 nest 上实测过（10 台机器、30+ 个 agent 实例，2026 年 9 月，token 用 `o200k_base` 计）：

| 加载内容 | 文件数 | Token |
|---|---|---|
| 2.x 式全量启动（规则、策略、全部记忆、workflow） | 37 | 约 69,600 |
| 3.x 启动，只读常驻层 | 2 | 约 640 |
| 3.x 执行一个 git 任务（常驻 + 索引 + 一个主题） | 4 | 约 3,600 |
| 整个 nest 的全部记忆文件 | 180 | 约 369,000 |

实际意义是：记忆可以一直长，而每次会话的启动成本不跟着涨。常驻文件有字节预算（规则 4096、共享摘要 4096、每个 agent 2048），提交前用 `scripts/maintenance/check-resident.py` 检查。

## 换一台机器会怎样？

clone nest，跑对应工具的安装脚本。新机器会拿到自己的 agent 目录，Claude Code 的 id 带随机后缀，比如 `claude-a7k2`，所以它的私有记忆文件是空的。但它并不是从零开始：共享摘要、`shared/memory.md`、其他所有 agent 的记忆、你的项目和 workflow，都在同一个 clone 里，按需可查。

这正是 nestwork 要解决的问题。作者在[第一篇文章](../16-agents-one-brain/)里写过：他在 A 机器上让 agent 记下「这个项目的部署脚本有个坑」，B 机器上的 agent 第二天又踏踏实实踩了一遍。第一次用 git 跑通时，他在 Windows 上让 agent 记下一个决定，到 Mac 上 pull 一下，Codex 立刻读到了。逐次写入同步上线之后，他的原话是：「跨机器丢记忆、两台机器对撞的事，没再发生过。」

## 换一个工具会怎样？

给新工具装上 nestwork。安装脚本把启动协议注入该工具的配置文件，并给它一个独立身份，于是 Claude Code、Codex 等各有各的目录，却读同一套规则、项目和共享记忆。README 里「跨工具迁移」的场景说得很清楚：记忆在你的 git 仓库里，不在某个厂商那里，换工具的成本接近零。

工具自带的记忆是另一回事。Claude Code 官方文档写明，自动记忆存在 `~/.claude/projects/<project>/memory/`，而且「只存在本机，不会在机器或云环境之间共享」（[Claude Code 记忆文档](https://code.claude.com/docs/en/memory)）。nestwork 协议（AGENTS.md §13）的做法是把它**蒸馏**进 nest，而不是原样镜像：稳定、可迁移的要点进 `workflow/` 或共享记忆；只在换机恢复时才用得上的，进冷存储 `carryover/<tool>.md`，启动时永不加载；变化很快的进度快照直接丢弃。

## 记忆越来越多怎么办？

三种机制，都是显式操作，没有黑箱：

- **行数上限与拆分。** agent 的 `memory.md` 上限 200 行，`shared/memory.md` 500 行，`projects/<name>.md` 150 行。超了就拆成「索引 + 主题文件」。
- **主题记忆（协议 3.1，可选开启）。** 作用域的 `memory.md` 变成一份生成的索引，每个主题文件开头有一句 `description`，写明**什么时候**该读它；agent 只打开与任务匹配的一两个文件。迁移是手动且需要审阅的：按已有标题拆分、原文照搬，再跑 `memory-index.py`。
- **蒸馏。** 多个 agent 学到重叠的东西后，用 `scripts/maintenance/distill.py` 合并进 `shared/`。它从不自动运行；默认只把结果写进工作区、不提交，你先看 `git diff -- shared/` 再决定。共享记忆取并集：只有一个 agent 观察到的内容也会保留，每个 agent 自己的记忆原样不动。

蒸馏出来的内容**不会**自动进入启动加载。只有审过的、稳定的、必须在没人去查时就生效的事实，才放进常驻摘要。

## 平时要做哪些维护？

清单很短，没有一项需要每天做：

| 事项 | 命令或位置 |
|---|---|
| 提交上下文改动前检查启动预算 | `python3 scripts/maintenance/check-resident.py` |
| 重建并校验主题索引 | `python3 scripts/maintenance/memory-index.py`，再加 `--check` |
| 把各 agent 的记忆合并进共享 | `python3 scripts/maintenance/distill.py --run-claude`（或 `--run-codex`），审阅后提交 |
| 看会话实际加载了多少 | `python3 scripts/maintenance/measure-context.py` |
| 让邮箱扫描保持轻量 | `bash scripts/comms/archive.sh 30` |
| 拉取协议更新 | `bash scripts/maintenance/update.sh` |

比任何脚本都重要的是一个习惯：对旧事实保持怀疑。协议写明，是否常驻只决定加载，不决定真假；agent 在依据带日期的项目状态行动之前要先核实。推荐的 `projects/<name>.md` 格式最后一栏是「Last Verified」，就是为此设的。

## 常见问题

### agent 会记住我说过的每一句话吗？

不会，也不应该。nestwork 保存的是你或 agent 决定记下的内容，不是原始对话记录。有一个可选功能可以同步本地的提示词历史，但 README 建议保持关闭。

### 记忆越多，每次会话越慢吗？

启动成本不变，因为只加载常驻文件。增长的只是某个任务主动打开的那部分。

### 记错了怎么撤回？

像改普通文件一样改掉或删掉，或者直接 revert 那次提交。每次写入都是独立的 git 提交，哪条事实什么时候出现、由哪个 agent 写的，一查便知。

### 我能看到 agent 都记了什么吗？

能。都是你自己仓库里的纯 Markdown，任何编辑器都能打开，也可以直接在 git 托管平台上浏览。

## 相关阅读

- [AI agent 记忆是什么](../ai-agent-memory/)
- [主题记忆与按需加载](../topic-memory-on-demand-loading/)
- [记忆蒸馏](../memory-distillation/)
- [Claude Code 记忆跨机器同步](../claude-code-memory-across-machines/)
- [把工具自带的记忆救出来](../rescue-tool-native-memory/)

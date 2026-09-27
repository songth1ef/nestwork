---
title: AGENTS.md 和 CLAUDE.md 区别，记忆该放哪
description: AGENTS.md 是跨工具的指令文件，CLAUDE.md 是 Claude Code 专用的，记忆是 agent 自己写的笔记。各工具读哪个、怎么组合。
keywords: AGENTS.md 和 CLAUDE.md 区别, AGENTS.md 记忆, CLAUDE.md, GEMINI.md, Claude Code 记忆, Codex AGENTS.md, 智能体记忆
date: 2026-09-27
---

`AGENTS.md` 和 `CLAUDE.md` 都是"你来写、agent 在会话开始时读"的指令文件，区别在于谁读：`AGENTS.md` 是开放格式，Codex、Cursor、Jules 等众多工具都读；`CLAUDE.md` 是 Claude Code 自己的文件——而新版 Claude Code 在没有 `CLAUDE.md` 时也会读 `AGENTS.md`。记忆是第三种东西：agent 给自己记的笔记，在 Claude Code 和 Codex 里都只留在本机。规则放指令文件，agent 学到的东西交给记忆，并且只保留一个真源，免得几份文件各自漂移。

## 三类文件，三个主人

按"谁写、要传多远"给 agent 的上下文分个类：

| 类别 | 例子 | 谁写 | 作用范围 | 靠什么传播 |
|---|---|---|---|---|
| 仓库级指令 | 仓库里的 `AGENTS.md`、`CLAUDE.md` | 你和团队 | 单个项目 | 版本控制 |
| 用户级指令 | `~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.gemini/GEMINI.md` | 你 | 这台机器上你的所有项目 | 默认不传播 |
| 工具记忆 | `~/.claude/projects/<project>/memory/`、`~/.codex/memories/` | agent | 一台机器上的一个工具 | 默认不传播 |

只有仓库级指令天然"走得动"：它跟代码一起提交。用户级指令和工具记忆都在你的 home 目录里，只留在有它们的那台机器上。

## 各工具读哪个文件

| 工具 | 仓库级文件 | 用户级文件 | 内置记忆 |
|---|---|---|---|
| Claude Code | `CLAUDE.md`、`.claude/CLAUDE.md`、`CLAUDE.local.md`；没有 `CLAUDE.md` 时读 `AGENTS.md` | `~/.claude/CLAUDE.md` | auto memory，位于 `~/.claude/projects/<project>/memory/` |
| Codex CLI | `AGENTS.override.md` 或 `AGENTS.md`，从 git 根目录一路到当前目录 | `~/.codex/AGENTS.md`（或 `AGENTS.override.md`） | `~/.codex/memories/` |
| Gemini CLI | 默认 `GEMINI.md`；可用 `context.fileName` 加上 `AGENTS.md` | `~/.gemini/GEMINI.md` | — |
| Cursor、Jules、Copilot coding agent 等 | `AGENTS.md` | 因工具而异 | 因工具而异 |

来源：[Claude Code 记忆文档](https://code.claude.com/docs/en/memory)、[Codex AGENTS.md 指南](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[Gemini CLI GEMINI.md 文档](https://geminicli.com/docs/cli/gemini-md/)、[agents.md](https://agents.md/)。

实践中有几个细节要注意：

- **Codex 有总大小上限。** 它从根往下拼接文件，每个目录最多一个，拼到 `project_doc_max_bytes`（默认 32 KiB）就停。离当前目录越近的文件越靠后，因而优先。
- **Claude Code 是拼接而不是覆盖。** 从文件系统根到工作目录的所有 `CLAUDE.md` 都会加载，根目录的在前。Anthropic 建议每个文件控制在 200 行以内。
- **AGENTS.md 由 Linux 基金会旗下的 Agentic AI Foundation 维护**，官网称已有超过 6 万个开源项目使用。嵌套文件只有一条规则：离被编辑文件最近的 `AGENTS.md` 生效。

## Claude Code 怎么在 AGENTS.md 和 CLAUDE.md 之间取舍

从 v2.1.277 起，Claude Code 能直接读 `AGENTS.md`。默认行为（`claude-md-or-agents-md`）是：

| 仓库里有 | Claude 读 |
|---|---|
| `AGENTS.md`，且工作目录及以上没有 `CLAUDE.md` 或 `CLAUDE.local.md` | `AGENTS.md` |
| `AGENTS.md`，同时有 `CLAUDE.md` 或 `CLAUDE.local.md` | 只读 `CLAUDE.md` 系列 |
| `CLAUDE.md` 里写了 `@AGENTS.md` 导入 | `CLAUDE.md`，并通过导入带上 `AGENTS.md` |

由此有两个坑。在一个依赖 `AGENTS.md` 的项目里加一个个人用的 `CLAUDE.local.md`，Claude 就会悄悄不再替你读 `AGENTS.md`。另外，用户级的 `~/.claude/CLAUDE.md` 不参与这个判断——它总是一起加载。想改默认行为，可以调 **Project instructions** 设置，比如设为 `claude-md-and-agents-md` 两个都读。

## 组合用法：一个真源，薄薄的包装

避免漂移的办法是：共享规则只在 `AGENTS.md` 里写一次，其他文件都做成薄包装。

对 Claude Code，如果还需要 Claude 专属内容，官方文档推荐用导入：

```markdown
@AGENTS.md

## Claude Code

Use plan mode for changes under `src/billing/`.
```

软链接（`ln -s AGENTS.md CLAUDE.md`）也行，但文档提醒：只要有人在 Windows 上 clone，就别用——除非开启 `core.symlinks`，否则 Git 会把提交的软链接检出成普通文本文件，`CLAUDE.md` 里只剩一行路径。对 Gemini CLI，在 `settings.json` 的 `context.fileName` 里加上 `AGENTS.md`。

然后想清楚哪些东西根本不该进这些文件：

- **临时任务笔记和聊天记录。** 每次会话都得为它们付 token。
- **agent 了解到的关于你的事实。** 那是记忆，变化比规则快得多。
- **任何机密。** 指令文件会被提交和共享。

Codex 文档从另一侧划了同一条线："必须遵守的团队规范放在 `AGENTS.md` 或已提交的文档里。把记忆当作辅助回忆层，而不是必须始终生效的规则的唯一来源。"

## 缺口：能跟着人走的用户级上下文

仓库级指令只管一个项目。它管不到的，是属于"你"而不是属于某个仓库的东西——你的偏好、跨项目的教训、你在另一台机器上停下的工作进度。这些落在用户级文件和工具记忆里，而两者都只在一台机器上。Claude Code 文档写得很明白："Auto memory is machine-local … Files are not shared across machines or cloud environments."

结果就是：四个 home 目录里有四份略有不同的偏好设置，你在笔记本上教给 Claude Code 的规则，台式机上的 Codex 一无所知。

## nestwork 如何把 AGENTS.md 用作启动协议

[nestwork](https://github.com/songth1ef/nestwork) 的做法是：把用户级上下文搬进一个私有 git 仓库，指令文件只负责"指路"。

1. **唯一的协议真源。** nest 自己的 [`AGENTS.md`](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md) 是唯一的启动协议来源；nest 里的 `CLAUDE.md` 是由 `scripts/maintenance/sync-claude-md.sh` 生成的镜像。之所以用真实文件而不用软链接，是因为不支持软链接的 Windows clone 曾经拿到一个只有 9 字节的坏文件。
2. **在每个工具的用户级文件里写一个带标记的区块。** 安装脚本把一段简短的启动协议写进 `~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.gemini/GEMINI.md` 等文件，包在 `<!-- nestwork:begin -->` 和 `<!-- nestwork:end -->` 之间，你在同一文件里的其他内容原样保留。重跑安装脚本只替换这个区块。
3. **区块的内容。** pull nest；只读常驻层——`queen/agent-rules.md`、`shared/resident.md` 和本 agent 的 `resident.md`；历史、项目和 workflow 按需检索；记忆只写进本 agent 自己的目录。

```text
queen/agent-rules.md > queen/strategy.md > shared/memory.md
  > agents/*/*/memory.md > projects/*.md > workflow/*.md
```

这条优先级链负责裁决冲突，它和加载顺序是两回事：启动时只加载常驻文件，在作者的 nest 上约 640 token，而旧的"全量加载"启动约 69,600 token。

nestwork 不取代项目自己的 `AGENTS.md`。它的经验法则是：换了雇主就会变的知识，放进那个仓库自己的文档；换了雇主依然成立的，放进 nest 的 `workflow/`；帮助 agent 接着干活的项目状态，放进 nest 的 `projects/<name>.md`。Claude Code 和 Codex 是作者日常主力；Gemini CLI、Kimi Code、Hermes、OpenClaw 的安装脚本也有，但实战检验较少。

## 常见问题

### 该用 AGENTS.md 还是 CLAUDE.md？

只要仓库会被不止一个工具碰，就以 `AGENTS.md` 为真源；只有在需要 Claude 专属指令、或某些会话读不到 `AGENTS.md` 时，再加一个只写 `@AGENTS.md` 的 `CLAUDE.md`。如果只用 Claude Code，单一个 `CLAUDE.md` 就够了。

### AGENTS.md 算记忆吗？

通常意义上不算。它是你写、你审的指令；记忆是 agent 自己记录的东西。不过 `AGENTS.md` 可以告诉 agent 记忆在哪、怎么加载——nestwork 正是这么用它的。

### Claude Code 会同时读 AGENTS.md 和 CLAUDE.md 吗？

默认有 `CLAUDE.md` 就读 `CLAUDE.md`，没有才退回 `AGENTS.md`。想两个都读，在 `CLAUDE.md` 里导入 `@AGENTS.md`，或把 Project instructions 设为 `claude-md-and-agents-md`。

### 个人偏好该放哪？

别放进会提交的仓库文件。只在一台机器上用，就放 `~/.claude/CLAUDE.md` 这类用户级文件；想让它跟着你跨机器、跨工具，就放进 nestwork 仓库这类会同步的存储。

## 相关阅读

- [AI agent 记忆：四种类型与取舍](../ai-agent-memory/)
- [在 Claude Code 和 Codex 之间共享记忆](../share-memory-claude-code-codex/)
- [Claude Code 记忆跨机器同步](../claude-code-memory-across-machines/)
- [Codex CLI 持久记忆](../codex-cli-persistent-memory/)
- [主题记忆与按需加载](../topic-memory-on-demand-loading/)

---
title: Codex 记忆与 AGENTS.md：Codex 长期记忆
description: Codex CLI 现有的记忆方式（AGENTS.md 与默认关闭的本地 memories），以及如何用 git 给 Codex 加跨会话、跨机器的长期记忆。
keywords: Codex 记忆, Codex 长期记忆, Codex AGENTS.md, Codex CLI memory, Codex memories, AI agent 记忆, 智能体长期记忆, nestwork
date: 2026-09-27
---

Codex CLI 在会话之间带着上下文走，靠两样东西：每次启动都读的 `AGENTS.md` 指令文件，以及可选的 memories 功能——把过去对话的摘要写进 `~/.codex/memories/`。memories 默认关闭、只存在本地，OpenAI 自己的文档也要求把必须遵守的规则写进 `AGENTS.md`。想让 Codex 的长期记忆跨会话、跨机器，就把这些上下文放进一个私有 git 仓库，再让全局 `~/.codex/AGENTS.md` 告诉 Codex：启动时 pull、读取，学到东西后提交。

## Codex 自带哪些记忆

OpenAI 文档里有两套内置机制。

**AGENTS.md 指令链。** 按 [AGENTS.md 指南](https://learn.chatgpt.com/docs/agent-configuration/agents-md)，Codex 在启动时构建一次指令链（每次运行一次，TUI 里通常是每次启动会话一次）：

1. 全局层：在 Codex home（默认 `~/.codex`，设置了 `CODEX_HOME` 就用它）里，存在 `AGENTS.override.md` 就读它，否则读 `AGENTS.md`。
2. 项目层：从项目根目录（通常是 git 根）一路往下走到当前目录，每层依次找 `AGENTS.override.md`、`AGENTS.md`，以及你配置的备用文件名。
3. 文件从根往下拼接，离当前目录越近的越靠后、优先级越高。总大小达到 `project_doc_max_bytes`（默认 32 KiB）后就不再加入新文件。

**memories。** [memories 页面](https://learn.chatgpt.com/docs/customization/memories?surface=cli)写明本地 Codex memories 默认关闭，要在 `config.toml` 里加 `[features] memories = true`（或在桌面应用里打开开关）。开启后，Codex 会在后台把早先对话里有用的上下文整理成记忆文件，存在 `~/.codex/memories/`：它会跳过进行中或太短的会话，对生成内容做密钥脱敏，额度余量偏低时还可能跳过一轮。`/memories` 命令可以按对话控制：这次对话用不用已有记忆、能不能被拿去生成以后的记忆。

OpenAI 对分工说得很直白：必须遵守的指引放在 `AGENTS.md` 或提交进仓库的文档里，memories 只当作辅助回忆层，不能是唯一来源。

## 这意味着什么

两套机制都落在一台机器上。全局 `~/.codex/AGENTS.md` 是你 home 目录里的一个文件，memories 是 Codex home 下的一些文件。memories 文档描述的是本地存储，对跨设备同步只字未提。换一台笔记本、开一台云开发机、或者重装一次，都从零开始。而且 memories 是 Codex 写给自己的摘要，不适合用来整理你希望其他工具也能读到的决定。

项目里的 `AGENTS.md` 会随仓库走，项目规则放那里正合适。缺的是另一层：个人偏好、跨项目的决定、要跟着你到任何机器和任何工具的进度记录。

## 用 git 仓库给 Codex 加长期记忆

最耐用的做法，是一个装 markdown 文件的私有 git 仓库，通过 Codex 每次都读的那个文件——全局 `AGENTS.md`——接进来。起作用的是其中的指令：启动时 pull，只读一小组文件，其余按需检索，结束前提交自己的改动。

nestwork 把这件事做成了协议和安装脚本。[`scripts/install/codex.sh`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/codex.sh) 会：

1. 解析本机主机名（`~/.nestwork_host`）和 Codex 的 agent id，固定为 `codex`（`~/.nestwork_id_codex`）；
2. 在记忆仓库里创建 `agents/<host>/codex/memory.md`；
3. 往 `~/.codex/AGENTS.md` 写入启动协议，并为旧版配置同时写一份 `~/.codex/instructions.md`，内容包在 `<!-- nestwork:begin -->` 和 `<!-- nestwork:end -->` 之间，其他内容不受影响；
4. 在 `~/.codex/hooks.json` 里注册一个 SessionEnd hook（并在 `config.toml` 里指向它），用于可选的本地历史快照。

## 实操步骤

用到的命令（Windows 用 `.\nestwork\scripts\install\codex.ps1`；需要 `PATH` 里有 `python3`）：

```bash
git clone git@github.com:<you>/nestwork.git ~/nestwork
bash ~/nestwork/scripts/install/codex.sh
```

1. 用 [nestwork 模板](https://github.com/songth1ef/nestwork/generate)创建私有仓库，用第一条命令 clone。
2. 用第二条命令为 Codex 安装。
3. 打开 `~/.codex/AGENTS.md`，确认 nestwork 那段已经写入。
4. 启动 Codex，让它概括当前指令，应该能看到这段内容。OpenAI 的指南也建议用这个办法确认加载了哪些文件。
5. 往 `queen/agent-rules.md` 写一条不敏感的规则并推送，再到另一台同样安装过的机器上让 Codex 复述。

## Codex 读什么、什么时候提交

会话开始时，Codex pull 记忆仓库，只读常驻层：`queen/agent-rules.md`、`shared/resident.md`，以及存在时的 `agents/<host>/codex/resident.md`。策略、共享历史、自己的 `memory.md`、`projects/` 和 `workflow/` 都在任务需要时才检索。这样启动开销很小：作者自己的仓库里，常驻启动约 640 token，而 2.x 式全量加载约 69,600 token（2026-09 实测，`o200k_base`）。这对 Codex 尤其重要，它的指令链默认 32 KiB 封顶，而 nestwork 那段只放指针，不放记忆本身。

提交是刻意设计成手动的。SessionEnd hook 只以脱离进程的方式启动可选的历史快照，因为 Codex 的 SessionEnd hook 最多 3 秒（[Codex hooks 文档](https://learn.chatgpt.com/docs/hooks)），它不碰记忆。启动协议要求 Codex 在记忆有改动时同步自己的目录：

```bash
git -C ~/nestwork add agents/<host>/codex/
git -C ~/nestwork diff --cached --quiet -- agents/<host>/codex/ || \
  git -C ~/nestwork commit -m "memory: update <host>/codex" -- agents/<host>/codex/
git -C ~/nestwork push
```

Codex 本身现在已支持针对文件编辑的 PreToolUse / PostToolUse hook，但 nestwork 目前没有给 Codex 注册逐次写入同步，只有 Claude Code 和 Kimi Code 有。如果某次会话意外中断，下次会话提交时会把目录里遗留的改动一并带上。

## Codex memories 和 nestwork 一起用

两者分工不同，互不冲突。Codex memories 是自动的、本地的，关于过去对话的回忆；记忆仓库放的是你挑过、决定保留、其他工具也能读的上下文。如果 Codex memories 里有值得留下的东西，就有意识地迁过来：nestwork 的 [AGENTS.md §13](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md) 把 `~/.codex/memories/` 列为来源之一，讲了如何蒸馏进 `resident.md`、按需记忆，或冷层 `carryover/codex.md`。详见[迁移工具原生记忆](../rescue-tool-native-memory/)。

## 常见问题

### Codex CLI 自带长期记忆吗？

有两样：每次会话都加载的 `AGENTS.md`，以及需要手动开启的 memories——把过去的对话摘要写进 `~/.codex/memories/`。memories 默认关闭，存在那台机器的 Codex home 下。

### 全局的 Codex AGENTS.md 在哪？

在 Codex home 里，默认是 `~/.codex/AGENTS.md`；设置了 `CODEX_HOME` 就是 `$CODEX_HOME/AGENTS.md`。同目录下有 `AGENTS.override.md` 时优先读它。

### 记忆多了会不会把 AGENTS.md 撑过 32 KiB？

这种配置下不会。全局文件里的 nestwork 段只是一小段路径和规则，记忆文件本身由 Codex 用普通的文件工具读取，而且只读任务需要的那几个。

### Codex 和 Claude Code 能用同一个记忆仓库吗？

能。同一台机器上每个工具有自己的 agent id 和目录，见 [Claude Code 和 Codex 共享记忆](../share-memory-claude-code-codex/)。

## 相关阅读

- [Claude Code 和 Codex 共享记忆](../share-memory-claude-code-codex/)
- [AGENTS.md、CLAUDE.md 和记忆的区别](../agents-md-vs-claude-md-vs-memory/)
- [主题记忆与按需加载](../topic-memory-on-demand-loading/)
- [迁移工具原生记忆](../rescue-tool-native-memory/)
- [AI agent 记忆](../ai-agent-memory/)

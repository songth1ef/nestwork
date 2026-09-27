---
title: Claude Code 和 Codex 共享记忆的做法
description: Claude Code 读 CLAUDE.md，Codex 读 AGENTS.md。让两者指向同一个私有 git 仓库，就能共享记忆，且各写各的目录。
keywords: Claude Code 和 Codex 共享记忆, Claude Code Codex 一起用, Codex AGENTS.md, Claude Code 记忆, AI agent 记忆, 智能体共享记忆, nestwork
date: 2026-09-27
---

Claude Code 和 Codex 各有各的启动文件、各有各的原生记忆，互相都不读对方的。要让 Claude Code 和 Codex 共享记忆，就给两个工具同一条指令：会话开始时 pull 同一个私有 git 仓库，读同一套规则和共享记忆，新记忆只写进属于自己的目录。用 nestwork 的话，就是对同一个 clone 跑两个安装脚本：Claude Code 靠 hook 同步每一次记忆写入，Codex 在会话结束时提交自己的目录。

## 两个工具启动时各读什么

两者查找的位置不同，这正是它们默认看不到彼此上下文的原因。

| | Claude Code | Codex CLI |
|---|---|---|
| 全局指令文件 | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md`（存在 `AGENTS.override.md` 时读它） |
| 项目指令文件 | `CLAUDE.md`、`.claude/CLAUDE.md`、`CLAUDE.local.md`；也能读 `AGENTS.md` | 从项目根目录一路到当前目录的 `AGENTS.md` |
| 原生记忆 | auto memory，位于 `~/.claude/projects/<project>/memory/` | memories，位于 `~/.codex/memories/`，默认关闭 |
| hook 配置位置 | `~/.claude/settings.json` | `~/.codex/hooks.json` 或 `config.toml` |

来源：Anthropic 的[记忆文档](https://code.claude.com/docs/en/memory)，OpenAI 的 [AGENTS.md 指南](https://learn.chatgpt.com/docs/agent-configuration/agents-md)和 [memories 页面](https://learn.chatgpt.com/docs/customization/memories?surface=cli)。

仓库里的 `AGENTS.md` 已经能让两个工具共用同一套**项目**规则：新版 Claude Code 在项目没有 `CLAUDE.md` 时会直接读 `AGENTS.md`，也可以在 `CLAUDE.md` 里用 `@AGENTS.md` 导入。但项目文件装不下与这个项目无关的东西：你的个人偏好、跨仓库的决定、另一个工具昨天在另一台机器上学到的东西。原生记忆也帮不上忙，Claude Code 的 auto memory 和 Codex 的 memories 是两份各自躺在本地磁盘上的存储。

## 一个仓库，两个入口文件

做法是把跨项目的上下文放进一个单独的私有 git 仓库，让两个工具的全局入口都指向它。nestwork 的安装脚本会往两个工具的全局文件里写入同一段启动协议：

- `scripts/install/claude.sh` 写进 `~/.claude/CLAUDE.md`；
- `scripts/install/codex.sh` 写进 `~/.codex/AGENTS.md`，并为旧版 Codex 同时写一份 `~/.codex/instructions.md`。

这段内容包在 `<!-- nestwork:begin -->` 和 `<!-- nestwork:end -->` 之间，重装时你在这些文件里写的其他内容都会保留。它告诉 agent：先 pull 仓库，读常驻文件（核心规则、共享常驻摘要、自己的常驻摘要），历史记录只在任务需要时检索。

## 身份分开，目录分开

在同一台机器上装两个工具，得到的是两个 agent，而不是一个。身份解析脚本 [`scripts/install/_identity.py`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/_identity.py) 在 `~/.nestwork_host` 里记一个主机名，并为每个工具单独记一个 agent id：

- `~/.nestwork_id_claude`，例如 `claude-a7k2`（Claude 带随机后缀，同一台机器装多个也不会重名）
- `~/.nestwork_id_codex`，就是 `codex`

于是在一台叫 `desktop` 的机器上，记忆仓库里会有两块写入区：

```text
agents/desktop/claude-a7k2/memory.md
agents/desktop/codex/memory.md
```

每个 agent 只写自己的目录；两者都读 `queen/agent-rules.md`、`shared/`、`projects/` 和 `workflow/`，任务需要时也可以去查对方的 `memory.md`。“单写者”规则是共享能安全进行的前提：两个工具从不往同一个文件追加，日常使用里就没有需要合并的东西。

## 在一台机器上配置

用到的命令（Windows 用对应的 `.ps1` 脚本）：

```bash
git clone git@github.com:<you>/nestwork.git ~/nestwork
bash ~/nestwork/scripts/install/claude.sh
bash ~/nestwork/scripts/install/codex.sh
```

1. 用 [nestwork 模板](https://github.com/songth1ef/nestwork/generate)创建私有仓库，用第一条命令 clone。
2. 对同一个 clone 跑两个安装脚本。
3. 打开 Claude Code，让它记下一个小的、不敏感的决定，hook 会自动推送。
4. 在任意目录打开 Codex，问它刚才定了什么。它会按启动协议 pull 仓库，在 Claude 的目录或共享记忆里找到这条记录。

其他机器照做即可，每台机器会多出自己的 `agents/<host>/` 目录。

## 唯一的实质差别：什么时候提交

两个工具的接线方式不一样，这决定了另一边多快能看到变化。

**Claude Code** 有五个 hook（见 [`_hooks.py`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/_hooks.py)）：SessionStart 负责 pull；PreToolUse 在 Write/Edit 写记忆前先 pull，冲突时拦下写入；PostToolUse 写完立刻提交推送；Stop 每轮兜底；SessionEnd 处理可选的导出。Claude 写下的记忆几秒后就在远端了。

**Codex** 只有一个 hook（见 [`_codex_hooks.py`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/_codex_hooks.py)）。安装脚本往 `~/.codex/hooks.json` 加一条 SessionEnd，并在 `config.toml` 里指向这个文件。这个 hook 只以脱离进程的方式启动可选的本地历史快照，因为 Codex 的 SessionEnd hook 最多只允许 3 秒（[Codex hooks 文档](https://learn.chatgpt.com/docs/hooks)）。它不提交记忆。Codex 的记忆改动按启动协议里的手动步骤提交，agent 在收尾时执行：

```bash
git -C ~/nestwork add agents/<host>/codex/
git -C ~/nestwork diff --cached --quiet -- agents/<host>/codex/ || \
  git -C ~/nestwork commit -m "memory: update <host>/codex" -- agents/<host>/codex/
git -C ~/nestwork push
```

Codex 本身现在已支持针对文件编辑的 PreToolUse / PostToolUse hook，但 nestwork 的 Codex 安装脚本目前没有注册逐次写入同步。实际效果是：Codex 写的记录在它会话结束提交后才到 Claude 那边；Claude 写的记录在 Codex 下次启动时被拉到。想更快，就直接让 Codex 立刻执行上面的提交步骤。

## 共享层要小，要有意为之

两个工具各写各的，时间一长还是会各说各话。nestwork 用一条硬性的优先级链：`queen/agent-rules.md > queen/strategy.md > shared/memory.md > agents/*/*/memory.md > projects/*.md > workflow/*.md`，冲突时听高优先级的，不做折中拼接。`shared/` 只在显式蒸馏时改动（`scripts/maintenance/distill.py`），把各 agent 学到的东西合并起来，经过审阅，写成文件等你检查；只有加 `--commit` 才会提交。

Claude Code 和 Codex 是作者每天都在用的两个工具，所以这个组合是项目里验证最充分的路径。Gemini CLI、Kimi Code、OpenClaw、Hermes 的安装脚本按同样方式工作，但实战检验较少。

## 常见问题

### 直接让两者共用项目里的 AGENTS.md 不行吗？

项目规则可以：Codex 读 `AGENTS.md`，Claude Code 能直接读或从 `CLAUDE.md` 导入。但项目文件不管个人偏好、跨项目决定和其他机器上的记录，这些正是共享记忆仓库要装的东西。

### 两个 agent 会写同一个文件吗？

日常记忆写入不会。Claude 写 `agents/<host>/claude-xxxx/`，Codex 写 `agents/<host>/codex/`；`shared/` 只在蒸馏时改，`queen/` 只由你本人改。

### 为什么 Claude Code 自动同步，Codex 要手动提交？

因为 nestwork 的 Codex 安装脚本只注册了一个用于可选历史快照的 SessionEnd hook，而 Codex 的 SessionEnd hook 最多 3 秒。Codex 的记忆提交来自 agent 收尾时执行的启动协议指令。

### Codex 自带的 memories 会和这个冲突吗？

不会。Codex memories 默认关闭，存在 `~/.codex/memories/`。OpenAI 自己的文档也建议把必须遵守的规则放在 `AGENTS.md`，把 memories 当作辅助回忆层，分工是一致的。

## 相关阅读

- [Claude Code 记忆跨设备同步](../claude-code-memory-across-machines/)
- [给 Codex CLI 加长期记忆](../codex-cli-persistent-memory/)
- [AGENTS.md、CLAUDE.md 和记忆的区别](../agents-md-vs-claude-md-vs-memory/)
- [多 agent 共享记忆不冲突](../multi-agent-memory-without-conflicts/)
- [记忆蒸馏](../memory-distillation/)

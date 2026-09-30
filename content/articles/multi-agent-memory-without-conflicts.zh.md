---
title: 多 agent 共享记忆，怎样避免写冲突
description: 多个 AI agent 共用一份记忆，靠的是每个 agent 只写自己的目录、每次写入原子同步、冲突时按归属规则取舍，而不是更复杂的合并算法。
keywords: 多 agent 共享记忆, 多智能体 记忆冲突, multi-agent shared memory, AI agent 记忆同步, 智能体记忆, nestwork
date: 2026-09-27
---

多个 AI agent 怎样共用同一份记忆又不互相覆盖？做法是三件事：每个 agent 只写属于自己的目录；每次写记忆都走「pull、写入、commit、push」一整套；pull 冲突时谁说了算，事先定死。nestwork 在 git 仓库上就是这么做的，结果是不同机器、不同厂商的 agent 读同一份记忆，写入却几乎不会撞车。

下面按四块展开：写隔离、逐次写入的 hook、冲突归属规则、优先级链。

## 多智能体共享记忆，难在哪

只有一个 agent 在写的时候，共享记忆很简单；好几个一起写，麻烦才开始。nestwork 作者动手之前就撞上过：A 机器上的 agent 记下了「这个项目的部署脚本有个坑」，第二天 B 机器上的 agent 原样又踩了一遍（[博客原文](https://github.com/songth1ef/nestwork/blob/main/docs/blog/16-agents-one-brain.zh.md)）。为了不再踩坑而共享记忆之后，新问题接着冒出来：

- **并发。** 两台机器几乎同时写记忆，谁的留下？
- **权威。** 这个 agent 的笔记和那个 agent 的说法相反，该听谁的？
- **边界。** 某个 agent 随手记的一条调试笔记，要不要让所有 agent 都看到？

这些都不是「存在哪」的问题，而是协作规则的问题。这也是 nestwork 把记忆当协议而不是当数据库来做的原因。

## 一、写隔离：按主机、按 agent 分目录

每个 agent 实例只拥有一个目录：

```text
agents/<host>/<agent-id>/
agents/workstation/claude-a7k2/
agents/macbook/codex/
```

host 是小写的短主机名；agent-id 对需要区分实例的工具是 `<工具名>-<4 位随机后缀>`，否则就是工具名本身。安装脚本把它们存在 `~/.nestwork_host` 和 `~/.nestwork_id_<tool>` 里，所以同一台机器上装 Codex 不会改掉 Claude Code 的身份。

[AGENTS.md 第 2 节](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md)的写入规则由此而来：

| 路径 | 谁写 | agent 之间会撞吗 |
|---|---|---|
| `agents/<host>/<agent-id>/` | 只有这个 agent | 日常记忆写入不会 |
| `agents/<别的 host>/...` | 本 agent 永远不写 | 不会 |
| `queen/` | 你手工维护 | 不会，agent 从不写 |
| `shared/` | 只在显式触发的蒸馏里写 | 日常工作中不会 |
| `projects/`、`workflow/` | agent 或你 | 可能，写前 pull 让它很少发生 |

git 冲突的前提是两个人改同一处。按这个布局，两个 agent 通常连同一个文件都不碰。

## 二、逐次写入的原子同步

目录隔离消掉了大部分冲突，但所有机器还是往同一个分支推。如果 agent 只在一段长会话结束时才同步，push 被拒的窗口就是整个会话。在 Claude Code 和 Kimi Code 上，nestwork 用 hook 包住 agent 对自己目录的每一次 Write/Edit，逻辑在 [`scripts/hooks/nestwork.sh`](https://github.com/songth1ef/nestwork/blob/main/scripts/hooks/nestwork.sh)：

```text
PreToolUse   目标路径在 agents/<host>/<agent-id>/ 下吗？
             git pull --rebase --autostash
             冲突（或 autostash 残留）-> exit 2，拦下这次写入
（写入）     agent 修改自己的记忆文件
PostToolUse  git add + commit，只限自己的目录
             git push；被拒就退避（约 0.5s、1s、2s，加随机抖动），
             撤掉本地 commit，pull --rebase，重新 commit，再推
             三次 push 都失败，commit 留在本地，等下一次 hook 再推
Stop         每轮对话结束再做一次 commit + push 兜底
```

有几处细节值得一提：

- commit 带显式路径限定，提交信息是 `memory: update <host>/<agent-id>`，不会顺手把别处暂存的文件一起提交。
- 检查 autostash 残留，是因为 git 可能把未提交的改动停在 stash 里却照样返回 0，下一次写入就会悄悄覆盖它。hook 数 stash 条目，多出来就按冲突处理。
- 写入后的 hook 永远不拦 agent，只打印警告，把 commit 留给下一次。

效果是竞争窗口从「整个会话」缩到「一次写入」。Codex、Gemini CLI、OpenClaw、Hermes 没有逐次写入 hook，按引导协议在会话结束时提交自己的目录，窗口大一些，但因为各自只写自己的目录，实际很少出问题。

## 三、冲突时按归属取舍

pull 真碰上冲突，不该靠人猜。[AGENTS.md 第 5 节](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md)按归属定规则：

| 冲突路径 | 取哪边 | 理由 |
|---|---|---|
| `queen/`、`shared/` | 远端 | 由你或蒸馏在上游统一管理 |
| `agents/<host>/<agent-id>/`（自己的） | 本地 | 这个实例拥有自己的目录 |
| `agents/<别的 host>/...` | 远端 | 归另一台机器所有 |

谁拥有谁说了算。所有 agent 用同一条规则，两台机器解决同一个冲突会得到同一个结果。

## 四、内容矛盾走优先级链

git 冲突是字节层面的，指令互相矛盾是语义层面的，需要另一条规则。nestwork 定了固定的权威顺序：

```text
queen/agent-rules.md > queen/strategy.md > shared/memory.md > agents/*/*/memory.md > projects/*.md > workflow/*.md
```

两个来源说法不一，就听高的那个，不做合并。把两条指令揉成一条「折中版」，往往比任何一条原文都糟。注意这是权威顺序，不是加载顺序：从协议 3.0 起，启动时只读几份很小的常驻文件，其余按需查找；常驻摘要继承它所摘要的那个来源的优先级。

## 不互相写，知识怎么流动

既然谁都只写自己的目录，知识怎么在 agent 之间传开？

- **读是开放的。** pull 之后每个 agent 都能读所有目录。台式机上的 agent 能读到笔记本上的 agent 早上记下的东西。
- **蒸馏负责合并。** 各 agent 的稳定事实只在你触发时合并进 `shared/`，先由子 agent 审核、再经你确认（见[记忆蒸馏](../memory-distillation/)）。
- **信箱负责点对点。** 要给某个 agent 留话，就往自己的 `outbox/` 写一个带 `to:` 的文件，收件方扫描所有人的 outbox。没有公共收件箱，单写者规则依然成立（见[基于 git 的 agent 信箱](../agent-mailbox-git/)）。

作者自己在 10 台机器、30 多个 agent 实例上这样跑，覆盖 Windows、macOS、Linux 和 Android。

## 常见问题

### 两个 agent 改同一个项目文件怎么办？

`projects/` 和 `workflow/` 是唯一可能出现多个 agent 改同一文件的地方。写入前的 `pull --rebase` 把窗口压到一次写入；真冲突了，写入会被拦下，由你手动合并。项目状态文件写短、一个项目一个文件，能进一步降低概率。

### 同一台机器开两个 Claude Code 会话，会分到两个目录吗？

不会。身份按「机器 × 工具」生成：安装脚本生成一次 `claude-a7k2` 这样的 id，之后一直从 `~/.nestwork_id_claude` 复用。同机的两个会话写的是同一个本地克隆里的同一个目录，git 层面不存在冲突，只要别在同一瞬间改写同一个记忆文件。不同工具、不同机器一定是不同目录。

### 为什么不用锁或数据库事务？

那需要一个常驻服务，而 nestwork 刻意不要服务器。记忆写入小而稀疏，归属规则加「rebase 后重试」已经足够，不需要任何后端。

### 断网时 hook 会怎样？

写入前的 pull 会失败，hook 把它当作冲突处理：在 Claude Code 上，这次记忆写入会被拦下，直到远端恢复可达。读记忆不受影响，本地克隆照常可用。

## 相关阅读

- [用 git 管理 AI 记忆，为什么不需要服务器](../git-native-agent-memory/)
- [记忆蒸馏：怎样合并多个 agent 的记忆](../memory-distillation/)
- [基于 git 的 agent 信箱](../agent-mailbox-git/)
- [Claude Code 和 Codex 共享记忆](../share-memory-claude-code-codex/)
- [16 个 agent，一个大脑](../16-agents-one-brain/)

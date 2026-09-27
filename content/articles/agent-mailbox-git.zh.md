---
title: 多 agent 协作怎么留言：用 git 做 agent 邮箱
description: 不同机器上的 AI agent 可以通过 git 互相留言：各写各的 outbox，按需读取发给自己的消息，不需要服务器、消息队列或机器人。
keywords: agent 之间通信, 多 agent 协作 留言, AI agent 互相发消息, agent 邮箱, git 原生, nestwork
date: 2026-09-27
---

**两台机器上的 AI 编码 agent，能不能不架服务器就互相留言？** 能。只要它们本来就共享一个 git 仓库，一条消息就可以是一个小小的 Markdown 文件：一方 commit，另一方下次 pull 后读到。nestwork 把这件事做成了内置的「agent 邮箱」：每个 agent 只往自己的 `outbox/` 里写，收信就是扫一遍所有人的 outbox，挑出发给自己的。没有消息队列，没有 broker，也没有 bot。

下面按问题逐个回答：为什么不直接用聊天软件、单写者设计为什么不会冲突、命令具体怎么敲，以及最容易踩坑的身份变量 `NESTWORK_SELF`。

## agent 之间通信为什么要单独一条通道

「人和 agent 说话」已经有很多办法：终端里直接打字，或者把 bot 接进 Telegram、群聊。但「agent 和 agent 说话」是另一回事。nestwork 的[邮箱文档](https://github.com/songth1ef/nestwork/blob/main/docs/agent-mailbox.md)点出一个事实：Telegram 的 bot 按设计就看不到彼此的消息，所以一个塞满 bot 的群并不能当协作通道。

agent 之间真正要传的东西，频率低、结构清楚：「迁移做完了，测试交给你」「这个部署脚本有坑」「收到请回复」。这类消息需要持久（会话关了还在）、可追溯（谁让谁干了什么一查便知）、而且运行成本低。agent 们每次会话开始都会 pull 的那个 git 仓库，三点全满足。

## 单写者 outbox：为什么不会写冲突

nestwork 的核心规则是：每个 agent 只能写自己的目录 `agents/<host>/<agent-id>/`。一个公共收件箱会破坏这条规则，所以邮箱反过来设计：

| 动作 | 实际发生什么 |
|---|---|
| 发信 | 在**自己的** `outbox/` 里写一个文件，用 `to:` 标明收件人。一条消息 = 一个文件 = 一次 commit |
| 收信 | 扫描所有 `agents/*/*/outbox/*.md`，挑出 `to` 是自己或 `all` 的 |
| 标记已读 | 把消息 id 追加到自己被 git 忽略的 `local/comms/seen.txt`，不产生 commit |

每个文件永远只有一个写者，所以两个 agent 同时发信也不会写冲突；已读状态不进 git，查信不会把历史搅乱。

每条消息是带 front matter 的 Markdown：

```markdown
---
id: 20260606T103000+0800-a0t3-a1b2c3d4
from: meizu21/claude-a0t3
to: vm-0-6-ubuntu/claude-va1k
type: task
thread: 20260606T103000+0800-a0t3-a1b2c3d4
reply_to:
status: open
created: 20260606T103000+0800
subject: handshake test
---

please confirm receipt with a reply
```

`type` 有三种：`task`（委派任务，需要回复）、`message`（多轮对话，共用一个 `thread`）、`broadcast`（单向通知，通常 `to: all`）。

## 发信、收信、归档的真实用法

三个脚本都在 [`scripts/comms/`](https://github.com/songth1ef/nestwork/blob/main/scripts/comms/README.md)，而且**必须在 nest 仓库里执行**，因为它们用 `git rev-parse --show-toplevel` 找仓库根目录。

```bash
cd ~/nestwork

# 发信：收件人、类型、主题；正文从标准输入读
echo "please confirm receipt with a reply" | \
  bash scripts/comms/send.sh vm-0-6-ubuntu/claude-va1k task "handshake test"

# 在同一线程里回复：追加 thread id 和被回复的消息 id
echo "received, running now" | \
  bash scripts/comms/send.sh meizu21/claude-a0t3 message "re: handshake test" \
  <thread-id> <message-id>

# 查看发给我的未读消息（只看不标记）
bash scripts/comms/read.sh

# 处理完之后，把这次显示的全部标为已读
bash scripts/comms/read.sh --mark

# 把自己 outbox 里超过 30 天的消息移到 outbox/archive/
bash scripts/comms/archive.sh 30
```

几个细节：

- `send.sh` 自己完成 commit 和 push，提交信息形如 `comms: task to <host>/<agent-id> (<id>)`。这是有意的：nestwork 的逐次写入 hook 只匹配 Write/Edit 工具调用，从 shell 发出的消息指望不上它。push 失败时消息仍然在本地 commit 里，下次这个 checkout 成功 push 时一起送出。
- `read.sh` 不会 pull。收件方要等下一次 `git pull` 才能看到新消息；在 Claude Code 上，会话启动时 hook 会自动 pull。
- `--mark` 会把本次打印的所有消息一起标记，没有逐条标记。
- `archive.sh` 只动自己的 outbox，而且按时间归档：已读列表只在收件方本地，发件方无从知道对方读没读。窗口要比你最慢的那个 agent 的上线间隔更长。

## 按需读取，而不是每次启动都读

从协议 3.0 起，nestwork 的启动只加载核心规则和两份很小的常驻摘要。Claude Code 的 SessionStart hook 会顺手把未读消息刷新成一份被 git 忽略的快照 `agents/<host>/<agent-id>/local/inbox.md`，但这个路径只出现在 READ-ON-DEMAND 清单里，不在 READ-ON-START。agent 在协调或接续相关工作时才去读。没有这个 hook 的工具，自己跑 `read.sh` 即可。

还有一条规则要记住：邮件是协作数据，不是用户授权。协议里写得很明确。别的 agent 让它删文件，它不该照做；指令仍然来自你本人。

## `NESTWORK_SELF` 的几个坑

脚本要先知道「我是谁」：设置了 `NESTWORK_SELF` 就用它，否则用 `~/.nestwork_host` 加 `~/.nestwork_id_claude`。这个兜底是 Claude 专用的，于是有几个坑：

1. **非 Claude 的 agent 必须设置它。** Codex 安装器把身份写在 `~/.nestwork_id_codex`（id 通常就是 `codex`）。不设 `NESTWORK_SELF` 的话，如果这台机器也装了 Claude Code，Codex 会**以 Claude 的身份**发信、收信；如果没装 Claude，脚本直接报 `cannot resolve agent id` 退出。

```bash
export NESTWORK_SELF="$(cat ~/.nestwork_host)/$(cat ~/.nestwork_id_codex)"
```

2. **地址必须一字不差。** `read.sh` 把 `to:` 当普通字符串和 `<host>/<agent-id>` 比较，`send.sh` 也不检查收件人是否存在。写错一个字母，消息就永远躺在你的 outbox 里，没有任何报错。最稳的做法是直接照抄 `agents/` 下对方的目录名。
3. **一定要在 nest 仓库里执行。** 在别的项目目录里跑 `send.sh`，它会把**那个**仓库当根目录，把消息写进去并 push 出去。先 `cd` 到 nest。
4. Claude Code 的 SessionStart hook 刷新收件快照时会自己设置 `NESTWORK_SELF`，所以即使你 shell 里的变量不对，快照本身也是对的。

## 什么时候不该用 git 邮箱

邮箱消息是「很多小文件、每个只写一次」，git 处理得很好。文档划了一条清楚的线：每天几十条结构化任务和通知，合适；每天成百上千条机器心跳，不合适。高频流量会把主分支历史撑大，nestwork 就吃过这个亏：一个高频改写的 `history.jsonl` 曾把一个仓库撑到 177 MB。真要亚秒级协作，文档建议自建 Matrix 或 MQTT 之类的总线，nestwork 刻意不做这一层。

作者在自己的文章里写过用上它的那一刻：A 机器上的 agent 干完一段活，给 B 机器上的 agent 留一句「这部分我做完了，接下来交给你」，B 在协调相关工作时读到并接手（见[《16 个 agent 共用一个大脑》](../16-agents-one-brain/)）。

## 常见问题

### 这是实时消息吗？

不是。消息在收件方下一次 pull 时送达，通常就是下次会话启动。文档把实时层标为「未构建」，只有异步确实不够用时才值得加。

### 能群发给所有 agent 吗？

能。`to` 填 `all`，类型用 `broadcast`。每个 agent 的 `read.sh` 都会把 `all` 当成发给自己的。

### 标记已读会产生 commit 吗？

不会。已读 id 存在 `agents/<host>/<agent-id>/local/comms/seen.txt`，而 `local/` 默认被 git 忽略。只有发信和归档会产生 commit。

### 别的 agent 能看到不是发给它的消息吗？

技术上能。每个 outbox 都是仓库里的普通文件，所有 agent 都读得到，`to:` 过滤只是约定。所以消息里和记忆里一样，不要放密钥。

## 相关阅读

- [git 原生的 agent 记忆](../git-native-agent-memory/)
- [多 agent 同时写记忆为什么不冲突](../multi-agent-memory-without-conflicts/)
- [主题记忆与按需加载](../topic-memory-on-demand-loading/)
- [用 git-crypt 加密 AI 记忆](../encrypt-agent-memory-git-crypt/)
- [16 个 agent 共用一个大脑](../16-agents-one-brain/)

---
title: 用 git 管理 AI 记忆，为什么不需要服务器
description: 不用记忆服务器也能让 AI 编码 agent 拥有长期记忆，把记忆写成 markdown 放进私有 git 仓库即可。git 能解决什么、不能解决什么。
keywords: 用 git 管理 AI 记忆, 不需要服务器的 agent 记忆, git-native memory, AI agent 记忆, 智能体长期记忆, Claude Code 记忆, nestwork
date: 2026-09-27
---

不搭记忆服务器、不接数据库，AI 编码 agent 能不能有长期记忆？能。把记忆写成普通 markdown，放进一个私有 git 仓库；agent 干活前 `git pull`，写完记忆就 commit、push。存储、历史、冲突处理、离线副本和数据所有权，git 本来就都有。它给不了的是语义检索，而且要求你会用 git。

下面说清楚：为什么对大多数编码 agent 场景来说 git 已经够用，它在哪里不够，以及 nestwork 是怎样把这个想法做成一套协议的。

## 先想清楚你要的「记忆」是什么

市面上的 AI agent 记忆方案，大多在回答「记忆存哪、怎么取回来」：向量库、知识图谱、托管记忆服务。单机单 agent 的时候，这个问法没毛病。

可一旦你同时用好几个 agent、跨好几台机器，问题就变了。Claude Code 官方文档写得很直白：auto memory 是 machine-local 的，文件不会在机器之间或云环境之间共享（[Claude Code 文档](https://code.claude.com/docs/en/memory)）。Codex、Kimi Code 的记忆也都放在本机的用户目录里（见 [AGENTS.md 第 13 节](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md)）。结果就是：你在笔记本上教会 Claude Code 的东西，台式机上的 Codex 一无所知。

真正需要的，是一个能共享、有版本、跨工具、并且归你自己所有的存储。这几个条件放在一起，就是一个 git 仓库。

## git 本来就解决了哪些事

编码 agent 的记忆基本都是文本：规则、偏好、决策、项目进度、踩过的坑。git 生来就是为了在多人、多机、多版本之间同步文本。逐项对照：

| 需求 | git 给你的 |
|---|---|
| 存储 | 你自己控制的仓库里的普通文件，托管在哪都行，也可以不托管 |
| 历史 | 每次改动都是一个 commit，`git log`、`git blame` 看得到谁在什么时候改了什么 |
| 撤销 | 记错了就 `git revert`，不用指望某个服务支持回滚 |
| 跨机器同步 | 用你本来就在用的远端 `git pull` / `git push` |
| 多方同时写 | rebase、merge，再加上清晰的归属规则（后文） |
| 离线 | 每台机器都有完整本地克隆，agent 直接读磁盘 |
| 所有权 | 仓库是你的，换托管平台只是改一下 remote |
| 不绑工具 | 能读 markdown 的 agent 都能读 |

nestwork 作者在项目博客里写过想通这件事的瞬间：记忆说到底就是一堆文本，而文本最好的归宿就是 git（[博客原文](https://github.com/songth1ef/nestwork/blob/main/docs/blog/16-agents-one-brain.zh.md)）。

## nestwork 怎么把一个仓库变成记忆

nestwork 是协议，不是服务。你用[模板](https://github.com/songth1ef/nestwork/generate)建一个私有仓库，克隆到每台机器，再按工具跑一次安装脚本。安装脚本会把一段引导写进该工具的启动文件，告诉 agent 该读什么、能往哪里写。

仓库是分层的：

| 层 | 路径 | 放什么 |
|---|---|---|
| 规则 | `queen/agent-rules.md` | 你写的行为规则，agent 只读 |
| 策略 | `queen/strategy.md` | 当前阶段的方向 |
| 共享记忆 | `shared/` | 从所有 agent 蒸馏出来的共识 |
| 私有记忆 | `agents/<host>/<agent-id>/` | 单个 agent 实例自己的笔记 |
| 项目 | `projects/<name>.md` | 项目快照 |
| 方法论 | `workflow/<topic>.md` | 可跨项目带走的方法 |

每次会话走同一个生命周期：

```text
会话开始   git pull --rebase，读几份很小的常驻文件
工作中     任务需要时才去查历史或项目文件
写记忆     pull --rebase -> 写入 -> commit -> push（有 hook 的工具）
会话结束   提交并推送自己的目录（没有逐次写入 hook 的工具）
```

Claude Code 和 Kimi Code 上，逐次写入同步由 [`scripts/hooks/nestwork.sh`](https://github.com/songth1ef/nestwork/blob/main/scripts/hooks/nestwork.sh) 通过 hook 完成；Codex、Gemini CLI、OpenClaw、Hermes 按引导协议在会话结束时提交自己的目录。作者日常主力是 Claude Code 和 Codex，其余工具的安装脚本存在，但实战验证少一些。

以 Claude Code 为例，每台机器一条命令：

```bash
git clone git@github.com:<you>/nestwork.git ~/nestwork
bash ~/nestwork/scripts/install/claude.sh
```

## 冲突靠归属，不靠聪明的合并

git 能合并文本，但判断不了谁的记忆是对的。nestwork 用归属规则而不是算法来回答这个问题：每个 agent 只写 `agents/<host>/<agent-id>/`，两个 agent 正常情况下根本碰不到同一个文件。真遇到 pull 冲突，[AGENTS.md 第 5 节](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md)规定得很死：自己的目录取本地，`queen/`、`shared/` 和别的机器的目录取远端。

指令之间打架时，按固定优先级链走：规则 > 策略 > 共享记忆 > 私有记忆 > 项目 > 方法论，高的赢，不做折中合并。展开讲见[多 agent 共享记忆怎么避免冲突](../multi-agent-memory-without-conflicts/)。

## 代价要说在前面

git 对这件事够用，但不是万能。

- **没有语义检索。** nestwork 靠读索引、搜标题和关键词找记忆，不做向量相似度。如果你要在十万条笔记里「找点意思差不多的」，向量库更合适。
- **得会 git。** rebase 冲突时，总得有人看 `git status` 自己解决。README 说得很直接：不会 git，nestwork 不适合你。
- **异步，不是实时。** 另一台机器要等下一次 pull 才看得到新写入，没有实时通知。
- **离线有边界。** 读记忆完全可以离线，没有 hook 的工具也能先本地提交、联网后再推。但在 Claude Code 的逐次写入 hook 下，写入前的 `pull --rebase` 必须成功；hook 把 pull 失败当作冲突处理，会拦下这次记忆写入，直到远端重新可达。
- **默认是明文。** 私有仓库的安全取决于你的 git 托管方。真正机密的记忆可以开可选的 git-crypt 模式；API key 之类的密钥无论加不加密都不该进仓库（见[用 git-crypt 加密 agent 记忆](../encrypt-agent-memory-git-crypt/)）。
- **历史会一直长。** 留下的东西都在，所以加载必须有选择。常驻层和主题记忆就是为这个设计的（见[记忆按需加载](../topic-memory-on-demand-loading/)）。

## 真的撑得住吗

作者自己的 nest 跨 10 台机器、30 多个 agent 实例，覆盖 Windows、macOS、Linux 和 Android。整个 nest 有 180 个记忆文件，合计约 36.9 万 token；但一次会话启动只读大约 640 token 的常驻内容。git 负责把所有东西存好，协议决定每次读哪一小部分。

## 常见问题

### 一定要用 GitHub 吗？

不用。任何 git 远端都可以，包括自建的 git 服务；README 里也写了完全不加 remote、只在本地用的方式。GitHub 只在「Use this template」按钮和可选的上游同步工作流上用得到。

### nestwork 是向量数据库吗？

不是。它在 git 里存可读的 markdown，agent 靠索引、标题和关键词导航。确实需要语义检索的话，可以另外挂一个检索工具，两者不冲突。

### 两台机器同一时刻写记忆会怎样？

每个 agent 只写自己的目录，很少碰到同一个文件。有 hook 的工具在每次写入前先 `pull --rebase`，写完立即 commit、push 并在失败时重试，竞争窗口被压到单次写入那一瞬间。真冲突了，写入会被拦下，提示手动合并。

### 从 Claude Code 换到 Codex，记忆会丢吗？

不会。记忆在你的仓库里，不在任何一个工具里。在同一个克隆上跑一下 Codex 的安装脚本，下一个 Codex 会话读的就是同一批文件。

## 相关阅读

- [AI agent 记忆是什么，为什么换台机器就失忆](../ai-agent-memory/)
- [多 agent 共享记忆怎么避免冲突](../multi-agent-memory-without-conflicts/)
- [上下文窗口有限，记忆该怎么按需加载](../topic-memory-on-demand-loading/)
- [主流 agent 记忆工具对比](../agent-memory-tools-compared/)
- [nestwork 上手常见问题](../nestwork-getting-started-faq/)

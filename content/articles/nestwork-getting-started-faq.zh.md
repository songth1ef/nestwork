---
title: nestwork 安装教程：给 AI agent 加长期记忆
description: 用 nestwork 给 Claude Code、Codex 加长期记忆：前置条件、安装与卸载、怎么验证生效、费用、隐私、升级和团队使用，逐条问答。
keywords: nestwork 安装, 给 AI agent 加长期记忆 教程, Claude Code 记忆, Claude Code 长期记忆, Codex 记忆, AI agent 记忆
date: 2026-09-27
---

**怎么用 nestwork 给 Claude Code 加上长期记忆？** 用 nestwork 模板建一个私有仓库，clone 到每台机器，再运行对应工具的安装脚本，比如 `bash ~/nestwork/scripts/install/claude.sh`。之后每次会话启动都会先 pull 仓库、读你的规则和一份很小的常驻摘要；agent 写下的记忆会被提交并推送，其他机器和工具都能读到。

下面是安装前后最常见的问题，每一条都对照 [README](https://github.com/songth1ef/nestwork/blob/main/README.zh.md) 核对过。

## 安装前需要准备什么？

| 前置条件 | 原因 |
|---|---|
| git，以及一个能 push 的 git 托管（GitHub 或自建服务器） | 记忆就存在私有 git 仓库里，同步靠 pull 和 push |
| 不需要交互输入的推送凭证（SSH key 或 credential helper） | hook 在后台运行，没法回答密码提示 |
| `PATH` 上有 `python3`（Windows 上 `python3`、`python` 或 `py` 均可） | 安装脚本用几个 Python 小工具解析身份、修改配置文件 |
| macOS/Linux 用 bash，Windows 用 PowerShell 版安装脚本 | 安装脚本和 hook 都是 shell 脚本；hook 代码也处理了 Windows 上 Git Bash 的路径 |
| agent 工具本身 | Claude Code、Codex CLI、Gemini CLI、Kimi Code、OpenClaw、Hermes，或任何启动时读 Markdown 配置的 CLI |

另外你得会基本的 git。README 说得很明确：git 是 nestwork 的核心，不可替换；不熟悉 git 的话，nestwork 不适合你。

## 怎么安装？

三步。不用部署任何服务，除了 git 托管账号也不用注册别的。

1. 在 GitHub 上打开[模板](https://github.com/songth1ef/nestwork/generate)（Use this template → Create a new repository），可见性选 **Private**。用模板而不是 fork：fork 默认公开，而且和上游共享历史，以后每次更新都会和你的私有数据打架。
2. 在每台机器上 clone：

```bash
git clone git@github.com:<your-username>/nestwork.git ~/nestwork
```

3. 为这台机器上用到的每个工具运行安装脚本：

```bash
bash ~/nestwork/scripts/install/claude.sh     # Claude Code，macOS / Linux
bash ~/nestwork/scripts/install/codex.sh      # Codex CLI
```

Windows 上用 `.\nestwork\scripts\install\claude.ps1`、`codex.ps1`。Gemini CLI、Kimi Code、OpenClaw、Hermes 同理，把脚本名换成工具名。其他读 Markdown 配置的 CLI 用 `bash scripts/install/generic.sh <prefix> <config-path>`。

「几分钟能装好」这件事 README 没给具体时间，这里也不承诺数字。可以确定的是安装脚本只写本地文件：建好该 agent 的目录，往工具的启动文件里注入一段带标记的启动块，在工具支持的地方注册 hook。

### 各个工具实际得到什么？

各工具的支持程度并不一样，README 写得很坦白：

| 工具 | 入口文件 | 同步方式 | 作者使用情况 |
|---|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` + hooks | 启动时 pull；每次写记忆后提交并推送；另有 Stop、SessionEnd hook | 日常主力 |
| Codex CLI | `~/.codex/AGENTS.md` | 按启动块协议手动提交自己的目录；SessionEnd hook 只用于可选的历史同步 | 日常主力 |
| Kimi Code | `~/.kimi-code/AGENTS.md` + hooks | 和 Claude Code 一样有逐次写入 hook，但 hook 不能注入上下文 | 有安装脚本，作者未实测 |
| Gemini CLI、OpenClaw、Hermes | 各自的启动文件 | 没有 hook，会话结束时提交 | 有安装脚本，作者未实测 |

如果你主要用的是后几种，正式用之前先按下一节自己验证一遍。

## 怎么验证已经生效？

README 给的验证方法是跨设备测试，这也是真正要紧的那一项：

1. 在私有仓库里加一条非敏感、好认的规则或项目状态，commit 并 push。
2. 在第二台电脑或云服务器上打开已接入的 agent。
3. 让它总结当前的规则或项目状态。它应当先拉取仓库，再依据共享上下文作答，不需要你重复交代背景。

测试内容不要用 API key、密钥或雇主机密。

如果 Claude Code 看起来什么都没加载，先确认 hook 注册了，没有就重新跑安装脚本：

```bash
grep -A 5 SessionStart ~/.claude/settings.json
cat ~/.nestwork_host ~/.nestwork_id_claude
```

如果提交没被推送，按 README 的顺序查：remote 是否正确（`git -C ~/nestwork remote -v`）、`settings.json` 里的 hook、手动 `git push` 是否需要交互式输入凭证。

## 怎么卸载？

每个安装脚本在 `scripts/uninstall/` 下都有对应的卸载脚本：

```bash
bash ~/nestwork/scripts/uninstall/claude.sh
```

卸载**只解除绑定**：从工具启动文件里移除启动块，摘掉 nestwork 注册的 hook。`agents/<host>/<agent-id>/` 里的记忆、身份文件（`~/.nestwork_host`、`~/.nestwork_id_<tool>`）、同一配置文件里你自己写的内容，全部原样保留。重新安装即以原身份恢复。想让下次安装成为一个全新的 agent，加 `--purge-identity`（PowerShell 用 `-PurgeIdentity`）。

## 要钱吗？隐私怎么保证？

nestwork 没有托管服务、没有订阅、没有服务器，就是一个你自己仓库里的脚本和 Markdown。花费只有你本来就有的：放私有仓库的 git 托管，以及 agent 工具本身的用量。`distill.py --run-claude` 或 `--run-codex` 会通过本机 CLI 跑一次合并，和普通提问一样消耗你的套餐额度。

隐私方面，默认设置很简单：仓库是私有的、归你所有。记忆是明文 Markdown，能访问仓库的人都能读；agent 在正常工作中会把读到的内容发给模型服务商。对于既要同步、又不能让托管方读到的内容，有一个可选的 git-crypt 模式（见[用 git-crypt 加密 AI 记忆](../encrypt-agent-memory-git-crypt/)）。API key 和密码无论加不加密，都不要存进 nest。只想试试、不想推到任何地方的话，本地 clone 后不加 remote，或者把 `origin` 指向你自己的 git 服务器。

## 怎么升级？

你的私有仓库不会自动跟随上游。拉取协议更新有两条路，都不会动 `agents/`、`queen/`、`shared/` 和你自己的项目文件：

```bash
bash ~/nestwork/scripts/maintenance/update.sh
```

`update.sh` 在有未提交改动时拒绝运行；它会展示即将进来的 diff、请你确认、在本地提交，push 由你决定。另一条路是仓库自带的 GitHub Action（Sync Nestwork upstream）：默认手动触发时开 PR；把仓库变量 `NESTWORK_AUTO_SYNC` 设为 `true` 就每周自动跑一次。Claude Code 的会话启动 hook 还会检查上游协议版本（缓存 24 小时），有新版本时打印一行提示，但从不自动应用。

有一个坑：更新仓库文件不会改写每台机器上的工具配置。**从 2.x 升到 3.x，要在每台机器上为每个工具重跑一遍安装脚本**（或 `python3 scripts/install/_bootstrap.py`），然后开一个新会话，因为已有的对话还带着旧指令。3.0 升 3.1 不需要刷新启动块，主题记忆是按需开启的。

## 团队能用吗？

能，但要想清楚。官方 FAQ 的回答是可以，前提是从私有仓库起步、写入规则清楚：每个 agent 实例一个记忆目录，`queen/` 里的规则由人来管。但边界也要知道：nestwork 面向的是同时使用多个 agent 的个人开发者，团队级权限控制明确不在目标之内。仓库可见性完全依赖 git 托管的权限，能访问仓库的人能读到所有 agent 的记忆。共享的 `projects/`、`workflow/` 可能被多个 agent 同时写，写前 pull 能大幅降低冲突，但不能完全消除。

## 常见问题

### 装了之后，用 Claude Code 的方式要变吗？

不用。README 说没有新东西要学。唯一新增的习惯是：遇到值得记住的事，告诉 agent 记下来。

### 一台机器能给多个工具都装上吗？

能。每个工具有自己的身份文件，比如 `~/.nestwork_id_claude` 和 `~/.nestwork_id_codex`，装一个不会覆盖另一个。

### 安装时报身份解析错误怎么办？

安装脚本需要 `PATH` 上有 `python3` 来解析主机名和 agent id。也可以用 `NESTWORK_HOST`、`NESTWORK_AGENT_ID` 两个环境变量手动指定。

### Cursor、Copilot 能用吗？

可以在工作区级别接入：把 `AGENTS.md` 软链接到 `.cursor/rules/`、`.windsurf/rules/`、`.clinerules/` 或 `.github/copilot-instructions.md`。`gh copilot` 被列为不支持。

## 相关阅读

- [AI agent 记忆是什么](../ai-agent-memory/)
- [Claude Code 记忆跨机器同步](../claude-code-memory-across-machines/)
- [Claude Code 和 Codex 共享记忆](../share-memory-claude-code-codex/)
- [AI 长期记忆用起来是什么样](../long-term-memory-in-practice/)
- [nestwork 全景介绍](../nestwork-overview/)

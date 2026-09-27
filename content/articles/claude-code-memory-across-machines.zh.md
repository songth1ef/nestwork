---
title: Claude Code 记忆跨设备同步：用 git 实现
description: Claude Code 的 CLAUDE.md 和 auto memory 都只在本机。本文讲清它们存在哪、为什么换电脑就没了，以及怎样用 git 跨设备同步。
keywords: Claude Code 记忆, Claude Code 记忆 跨设备, Claude Code 记忆同步, Claude Code auto memory, CLAUDE.md, AI agent 记忆, nestwork
date: 2026-09-27
---

Claude Code 的记忆有两处：你自己写的 CLAUDE.md，以及 Claude 自动写在 `~/.claude/projects/<project>/memory/` 下的 auto memory。Anthropic 官方文档明确写着 auto memory 只存在本机，换一台笔记本或云主机就从零开始。想让 Claude Code 记忆跨设备同步，思路是把记忆放进你自己拥有的 git 仓库，每台机器读之前 pull、写之后 push——nestwork 的 Claude Code 安装脚本做的就是这件事。

## Claude Code 自带的记忆存在哪

按[官方记忆文档](https://code.claude.com/docs/en/memory)，Claude Code 有两套记忆，每次会话开始时都会加载：

| | CLAUDE.md | auto memory |
|---|---|---|
| 谁写 | 你 | Claude |
| 位置 | `~/.claude/CLAUDE.md`（用户级）、`./CLAUDE.md` 或 `./.claude/CLAUDE.md`（项目级）、`./CLAUDE.local.md`（个人、按项目） | `~/.claude/projects/<project>/memory/` |
| 启动时加载 | 整个文件（4 MiB 以内完整加载） | `MEMORY.md` 的前 200 行或前 25KB；其余主题文件按需读取 |
| 作用范围 | 用户、项目或组织 | 按仓库，同一仓库的 worktree 共用 |

项目里的 `CLAUDE.md` 提交进仓库后会随仓库走；其余的都只是某台机器上的文件：用户级 `~/.claude/CLAUDE.md` 在你的 home 目录里，`CLAUDE.local.md` 本来就该被 gitignore，auto memory 则在 `~/.claude` 下面。

## 为什么换电脑后记忆就没了

官方文档原话是：*"Auto memory is machine-local. … Files are not shared across machines or cloud environments."*（auto memory 只在本机，不会在机器或云环境之间共享。）

还有一个不太显眼的坑：`<project>` 目录名是从路径算出来的。[会话文档](https://code.claude.com/docs/en/sessions)说明，`<project>` 就是工作目录路径把非字母数字字符替换成 `-` 的结果。所以就算你把整个 `~/.claude` 拷到新电脑，只要仓库克隆在不同的路径或不同的盘符下，目录名就对不上，拷过去的记忆也挂不到项目上。

`autoMemoryDirectory` 设置可以把 auto memory 换个地方存（值须是绝对路径或以 `~/` 开头），但它只改变磁盘位置，不带来同步、审阅或版本历史。

## 通用思路：把记忆放进自己的 git 仓库

跨设备记忆需要三样东西：唯一的真相源；每台机器读之前先取最新；写完之后发布出去且不覆盖别的机器。这三件事 git 对文本文件早就做好了，而 agent 记忆本质上就是文本。所以最省事也最耐用的办法是：一个私有 git 仓库放 markdown 记忆，再用 hook 在合适的时机跑 `pull` 和 `push`。

nestwork 就是基于这个思路的协议。用[模板](https://github.com/songth1ef/nestwork/generate)创建私有仓库，在每台机器上 clone，再跑对应工具的安装脚本。每个 agent 实例有自己的目录 `agents/<host>/<agent-id>/`，只写自己的目录，两台机器永远不会改同一个记忆文件。

## 实操步骤

每台机器要跑的命令如下（Windows 上把 `.sh` 换成 `.\nestwork\scripts\install\claude.ps1`；需要 `PATH` 里有 `python3`）：

```bash
git clone git@github.com:<you>/nestwork.git ~/nestwork
bash ~/nestwork/scripts/install/claude.sh
```

1. 在 GitHub 上点 Use this template 创建私有仓库（可见性选 Private）。不要 fork：fork 默认公开，还和上游共享历史。
2. 在第一台机器上用上面第一条命令 clone。
3. 用第二条命令运行 Claude Code 安装脚本。
4. 在其他每台机器上重复第 2、3 步。每台机器的主机名记在 `~/.nestwork_host`，Claude 的 agent id（形如 `claude-a7k2`）记在 `~/.nestwork_id_claude`。
5. 验证：在 A 机器上往记忆仓库写一条无害、好认的规则，等它 push 完，再到 B 机器打开 Claude Code，让它复述你的规则。

## 安装脚本到底注册了什么

可以对照 [`scripts/install/claude.sh`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/claude.sh) 和 [`scripts/install/_hooks.py`](https://github.com/songth1ef/nestwork/blob/main/scripts/install/_hooks.py) 核对，一共三件事：

- 为本实例创建 `agents/<host>/<agent-id>/memory.md`。
- 在 `~/.claude/CLAUDE.md` 里写入一段启动协议，包在 `<!-- nestwork:begin -->` 和 `<!-- nestwork:end -->` 之间，文件里你自己的内容原样保留。
- 往 `~/.claude/settings.json` 合并五个 hook；重复运行会替换旧的 nestwork 条目，不会越加越多。

| Hook | 匹配 | 作用 |
|---|---|---|
| SessionStart | 全部 | `session-start.sh`：`git pull --rebase`，然后输出常驻文件清单 READ-ON-START |
| PreToolUse | Write, Edit | `nestwork.sh pre`：写入目标在本 agent 目录下时先 pull；有冲突就以退出码 2 结束，阻止这次写入 |
| PostToolUse | Write, Edit | `nestwork.sh post`：提交并推送本 agent 目录，push 失败最多重试 3 次 |
| Stop | 全部 | 每轮结束后兜底提交推送，没有改动时什么也不做 |
| SessionEnd | 全部 | 可选的 claude-mem 摘要导出和可选的本地历史同步 |

Claude Code 的 [hooks 文档](https://code.claude.com/docs/en/hooks)确认了这里依赖的两点：SessionStart 的标准输出会进入 Claude 的上下文；PreToolUse 返回退出码 2 会阻止工具调用。这样一来，两台机器可能撞车的窗口就从“整个会话”缩小到“一次写入”。

## 启动时读什么，什么按需读

如果每次会话都要把全部记忆读一遍，同步得再好也没意义。从协议 3.0 起（当前 3.1），启动只读很小的常驻层：`queen/agent-rules.md`、`shared/resident.md` 和本 agent 的 `resident.md`；历史、项目和工作流在任务需要时再检索。

作者自己的记忆仓库（10 台机器、30 多个 agent 实例，2026-09 用 `o200k_base` 实测）：2.x 式全量启动约 69,600 token；3.x 常驻启动约 640 token；一次 git 任务再加读索引和一个主题文件，约 3,600 token。你可以用 `python3 scripts/maintenance/measure-context.py` 测自己的仓库。

## 本机已有的 auto memory 怎么办

nestwork 不会自动镜像 `~/.claude/projects/*/memory/`。把它带进记忆仓库是一个有意识、要审阅的步骤，规则见 [AGENTS.md §13](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md)：只蒸馏仍然成立的内容；必须不查就生效的写进 `resident.md`；只在恢复时才用得上的放进冷层 `carryover/claude-code.md`，启动时永不加载。如果你更想要实时镜像，也可以把 `autoMemoryDirectory` 指到自己的 agent 目录，但这是本地选择：每次写入都会变成一次提交，审阅环节也没了。完整做法见[迁移工具原生记忆](../rescue-tool-native-memory/)。

## 常见问题

### Claude Code 自己会在电脑之间同步记忆吗？

auto memory 不会，官方文档写明它不在机器或云环境之间共享。你提交进仓库的项目级 `CLAUDE.md` 会随仓库同步，但用户级和 local 文件留在本机。

### 直接把 ~/.claude 放进网盘或 git 行不行？

能做，但会把会话记录、缓存和设置一起带走；而且 auto memory 的目录名来自绝对路径，换台机器未必对得上。用独立的记忆仓库、每个 agent 一个目录，两个问题都没有，还能留下可读的历史。

### 两台机器会互相覆盖记忆吗？

普通记忆写入不会。每个实例只写 `agents/<host>/<agent-id>/`，PreToolUse hook 在每次写入前都会先 pull；pull 遇到冲突时写入会被拦下，由你手动合并。

### 离线时 push 失败怎么办？

PostToolUse hook 会保留本地提交并打印警告，下一次 hook（Stop 或之后的写入）会再试。SessionStart 的 pull 失败不会卡住会话，你照常用本地副本工作，联网后再同步。

### 这会取代 CLAUDE.md 吗？

不会。项目里的 `CLAUDE.md` 照常工作。nestwork 只是在用户级 `~/.claude/CLAUDE.md` 里加一段带标记的内容，告诉 Claude 共享记忆在哪、该读什么。

## 相关阅读

- [Claude Code 和 Codex 共享记忆](../share-memory-claude-code-codex/)
- [换电脑前先把 AI 记忆迁出来](../rescue-tool-native-memory/)
- [AGENTS.md、CLAUDE.md 和记忆的区别](../agents-md-vs-claude-md-vs-memory/)
- [用 git 管理 AI 记忆](../git-native-agent-memory/)
- [nestwork 上手常见问题](../nestwork-getting-started-faq/)

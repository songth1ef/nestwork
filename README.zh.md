# hivequeen

[English](README.md) | 中文

版本：v0.2.0 | 协议：2.0

模板即继承，clone 即连接，所有 agent 共用同一个大脑。hivequeen 是 git 原生的 AI agent memory 协议，用于 Claude Code、Codex CLI、Gemini CLI 等 AI coding agents 的 persistent memory 与 shared context，无需插件，无需服务器。

## hivequeen 是什么？

hivequeen 是一个面向 AI coding agents 的持久记忆系统。它通过 git-native memory protocol，把长期规则、项目上下文、共享记忆和每个 agent 的私有记忆组织在同一个 GitHub 仓库里。

适合这些问题：

- 如何让 Claude Code 拥有长期记忆？
- 如何让 Codex CLI 跨 session 保留上下文？
- 如何让多个 AI coding agents 共享项目上下文？
- 如何不用服务器实现 AI agent memory？

英文 answer-ready docs：

- [AI agent memory](docs/ai-agent-memory.md)
- [Claude Code memory](docs/claude-code-memory.md)
- [Codex persistent memory](docs/codex-persistent-memory.md)
- [Git-native memory protocol](docs/git-native-memory-protocol.md)
- [AGENTS.md best practices](docs/agents-md-best-practices.md)
- [Shared context for AI coding agents](docs/shared-context-for-ai-coding-agents.md)
- [FAQ](docs/faq.md)

---

## 工作原理

```
hivequeen 仓库（你的私有母体）
├── queen/          ← 只读规则与策略（由你维护）
├── agents/         ← 每个 agent 只写自己的目录
├── shared/         ← 所有 agent 的编译记忆（只读）
└── projects/       ← 项目上下文文件
```

每台 clone 了你的母体的机器都共享同一个大脑。
每个 agent 实例只写自己的 `agents/<host>/<agent-id>/` 目录，所以正常记忆写入会彼此隔离。

```
session 开始  →  git pull  →  加载上下文
session 结束  →  git commit agents/<host>/<agent-id>/  →  git push
```

---

## 快速开始

### 1. 创建你的私有母体

点击 GitHub 上的 **Use this template → Create a new repository**，
visibility 选 **Private** — 你的记忆只属于你。

> **为什么不用 Fork？** Fork 默认是公开的，且与上游仓库保持关联。
> 从模板创建的私有仓库完全归你所有。
>
> 当 hivequeen 发布更新时，`git merge upstream/main` 会与你刻意定制的
> `queen/strategy.md`、`agents/`、`shared/` 产生冲突。
> `update.sh` 脚本只同步协议层，你的私有数据完全不受影响。

### 2. Clone 到每台机器

```bash
git clone git@github.com:<你的用户名>/hivequeen.git ~/hivequeen
```

### 3. 安装到你的 agent 工具

**Claude Code（macOS / Linux）**
```bash
bash ~/hivequeen/scripts/install/claude.sh
```

**Claude Code（Windows）**
```powershell
.\hivequeen\scripts\install\claude.ps1
```

**Codex（macOS / Linux）**
```bash
bash ~/hivequeen/scripts/install/codex.sh
```

**Codex（Windows）**
```powershell
.\hivequeen\scripts\install\codex.ps1
```

**OpenClaw（macOS / Linux）**
```bash
bash ~/hivequeen/scripts/install/openclaw.sh
```

**OpenClaw（Windows）**
```powershell
.\hivequeen\scripts\install\openclaw.ps1
```

**Hermes Agent（macOS / Linux）**
```bash
bash ~/hivequeen/scripts/install/hermes.sh
```

**Hermes Agent（Windows）**
```powershell
.\hivequeen\scripts\install\hermes.ps1
```

**Gemini CLI（macOS / Linux）**
```bash
bash ~/hivequeen/scripts/install/gemini.sh
```

**Gemini CLI（Windows）**
```powershell
.\hivequeen\scripts\install\gemini.ps1
```

**Aider（macOS / Linux）**
```bash
bash ~/hivequeen/scripts/install/aider.sh
```

**Aider（Windows）**
```powershell
.\hivequeen\scripts\install\aider.ps1
```

**其他 markdown-config 类 CLI**（Qwen Code、OpenCode、Trae、Kimi Code 等）——
见 [支持的工具](#支持的工具) 与 `install/generic.sh`。

每台机器都执行一次。同一个母体，不同的 agent ID，共享同一个大脑。

### Prompt 示例

懒得手动走流程？把下面任一条粘进 Claude Code 会话即可：

- **从零开始**
  > 阅读 https://github.com/songth1ef/hivequeen 的 README，按 Quickstart
  > 帮我从 template 新建私有 queen 仓库，clone 到本机，并完成 Claude Code 接入。

- **发现可配置功能**
  > 阅读 https://github.com/songth1ef/hivequeen 的 README，列出 hivequeen
  > 所有可配置功能（hooks、可选同步、过滤等），并根据我当前机器场景建议
  > 要不要开启。

---

## 自定义

### 你的规则
编辑 `queen/agent-rules.md` — 适用于所有 agent 的行为边界。

### 你的策略
编辑 `queen/strategy.md` — 当前目标与决策方向。

### 你的项目
添加 `projects/<项目名>.md` — 处理该项目时自动加载的上下文。

---

## 编译共享记忆

当各 agent 积累了足够记忆后，用下面两种方式之一合入 `shared/memory.md`：

```bash
# 纯拼接：把 agents/*/memory.md 拼接，commit，push
bash ~/hivequeen/scripts/maintenance/compile.sh

# LLM 版：打印一段蒸馏 prompt，喂给任一 agent 会话，
# 让 agent 输出合并后的 shared/memory.md 再提交
python3 ~/hivequeen/scripts/maintenance/distill.py
```

两种方式都不会修改原始的 agent memory。所有 agent 在下次 `git pull`
时自动看到新的 `shared/memory.md`。

---

## 目录结构

```
hivequeen/
├── AGENTS.md                   bootstrap 唯一来源（Codex、OpenClaw、Gemini 等）
├── CLAUDE.md                   AGENTS.md 的逐行镜像（Claude Code 认这个名字）
├── SOUL.md                     Hermes 的简短人格文件
├── queen/
│   ├── agent-rules.md          行为规则 — agent 只读
│   └── strategy.md             决策方向 — agent 只读
├── agents/
│   └── <工具>-<主机名>/
│       └── memory.md           该 agent 的私有记忆
├── shared/
│   └── memory.md               跨 agent 编译记忆
├── projects/
│   └── <项目>.md               项目上下文
└── scripts/
    ├── install/                   按工具分的安装器
    │   ├── claude.{sh,ps1}
    │   ├── codex.{sh,ps1}
    │   ├── gemini.{sh,ps1}
    │   ├── hermes.{sh,ps1}
    │   ├── openclaw.{sh,ps1}
    │   ├── aider.{sh,ps1}
    │   ├── generic.{sh,ps1}       任何 markdown-config CLI
    │   ├── _bootstrap.py          共享 bootstrap 注入器
    │   └── _hooks.py              共享 hook 注册器（Claude Code）
    ├── hooks/                     运行时 hook
    │   ├── hivequeen.sh           pre/post/stop 统一入口
    │   ├── _match-file.py         stdin 文件匹配器
    │   ├── export-claude-mem.sh   claude-mem 可选桥接
    │   ├── sync-local-history.sh  本地历史同步（wrapper，可选）
    │   └── sync-local-history.py  本地历史同步（worker，可选）
    └── maintenance/               运维
        ├── compile.sh             聚合 agents/* 到 shared/（纯拼接）
        ├── distill.py             LLM 版：打印记忆蒸馏 prompt
        ├── sync-claude-md.sh      从 AGENTS.md 重新生成 CLAUDE.md
        └── update.sh              拉取 upstream 协议层
```

---

## 文件行数限制

每个文件有行数上限，超出后拆分为 topic 文件，原文件改为带链接的索引。

| 文件 | 最大行数 |
|---|---|
| `queen/agent-rules.md` | 80 |
| `queen/strategy.md` | 80 |
| `agents/<host>/<agent-id>/memory.md` | 200 |
| `shared/memory.md` | 500 |
| `projects/<name>.md` | 150 |

**示例 — `agents/macbook/claude/memory.md` 达到上限后拆分：**

```
agents/macbook/claude/
├── memory.md          ← 变为索引
├── user_profile.md
├── feedback_collab.md
└── project_hivequeen.md
```

拆分后的 `memory.md`：
```markdown
# MEMORY — claude-macbook

- [用户档案](user_profile.md) — 角色、技术栈、偏好
- [协作习惯](feedback_collab.md) — 工作方式、修正记录
- [项目：hivequeen](project_hivequeen.md) — 目标、决策
```

agent 先读索引，按需跟进相关 topic 文件。

---

## 为什么不会产生冲突？

每个 agent 独占 `agents/` 下的一个目录，没有两个 agent 会写同一个文件。正常使用下，git 冲突从结构上就不可能发生。

| 路径 | 谁写 | 可能冲突？ |
|---|---|---|
| `queen/` | 你（人工） | 不会 |
| `agents/<host>/<agent-id>/` | 仅该 agent | 正常记忆写入不会 |
| `shared/` | 仅 `compile.sh` | 不会 |

---

## 支持的工具

### 原生安装器（配置路径明确、已验证）

| 工具 | 厂商 | 入口文件 | 安装方式 |
|---|---|---|---|
| Claude Code | Anthropic | `~/.claude/CLAUDE.md` + hooks | `bash scripts/install/claude.sh` |
| Codex CLI | OpenAI | `~/.codex/AGENTS.md` + `~/.codex/instructions.md` 兼容入口 | `bash scripts/install/codex.sh` |
| Gemini CLI | Google | `~/.gemini/GEMINI.md` | `bash scripts/install/gemini.sh` |
| OpenClaw | 开源 | `~/.openclaw/workspace/AGENTS.md` | `bash scripts/install/openclaw.sh` |
| Hermes Agent | 开源 | `~/.hermes/SOUL.md` | `bash scripts/install/hermes.sh` |
| Aider | 开源 | `~/.aider-hivequeen.md`（通过 `.aider.conf.yml` 的 `read:` 接入） | `bash scripts/install/aider.sh` |

只有 Claude Code 注册了 session hook，实现原子逐次写入同步。其他工具遵循
bootstrap config 里写入的「会话结束提交」协议。

### 可选：捕获本地 Claude Code 历史

Claude Code 会在 `~/.claude/` 下保留 prompt 历史和 plan 产物。
可以把它们镜像进 `agents/<host>/<id>/local/`，让 queen 跨机器携带这份上下文。

按 host 独立启用，无需 env，也无需首次 install 之后重装。在 queen 里
为当前机器对应的 host 目录创建 `agents/<host>/settings.json`：

```json
{ "sync_local_history": true }
```

默认 `false`（或文件不存在）。这个开关随 queen 一起进入 git 版本控制，
所以每台机器的 host 目录各自保留自己的开关状态。

启用后，Claude Code 的 Stop hook 会同步：

| 源 | 目标 | 说明 |
|---|---|---|
| `~/.claude/history.jsonl` | `local/history.jsonl` | 脱敏：删除 `pastedContents`，`$HOME` 路径归一化，常见 token（`sk-*`、`ghp_*`、`Bearer …`）替换为 `<REDACTED>` |
| `~/.claude/plans/` | `local/plans/` | plan 模式产物，原样镜像 |

`todos/` 和 `tasks/` 刻意排除 —— 超过 99% 是按 session UUID 预分配的空文件，
信号密度过低。

### 通过 `install/generic.sh` 接入（需自行确认 config 路径）

任何「启动时读一份 markdown 作为 system prompt」的 CLI 都可以一行命令接入。
先通过工具的 `--help` 或文档确认它读取的指令文件路径，然后：

```bash
bash scripts/install/generic.sh <prefix> <config-path>
```

示例 —— 路径仅作参考，实际请确认后再运行：

| 工具 | 厂商 | 推荐 prefix |
|---|---|---|
| Qwen Code | 阿里通义 | `qwen` |
| OpenCode | 开源 | `opencode` |
| CodeBuddy Code | 腾讯 | `codebuddy` |
| iFlow CLI | 阿里心流 | `iflow` |
| Trae CLI / Solo | 字节跳动 | `trae` |
| Qoder | 阿里 | `qoder` |
| Kimi Code CLI | 月之暗面 | `kimi` |
| 通义灵码 CLI | 阿里云 | `lingma` |

> **提示**：Qwen Code 是 Gemini CLI 的 fork，可能直接认 `~/.gemini/GEMINI.md` —
> 先试 `install/gemini.sh`。

### Workspace 级（IDE 插件，软链接）

| 工具 | 目标路径 | 安装方式 |
|---|---|---|
| Cursor | `.cursor/rules/hivequeen.md` | `ln -s AGENTS.md .cursor/rules/hivequeen.md` |
| Windsurf | `.windsurf/rules/hivequeen.md` | `ln -s AGENTS.md .windsurf/rules/hivequeen.md` |
| Cline（VS Code） | `.clinerules/hivequeen.md` | `ln -s AGENTS.md .clinerules/hivequeen.md` |
| GitHub Copilot（repo 级） | `.github/copilot-instructions.md` | `ln -s AGENTS.md .github/copilot-instructions.md` |

### 不支持（原因）

| 工具 | 原因 |
|---|---|
| GitHub Copilot CLI（`gh copilot`） | Q&A 模式，没有持久化指令文件机制 |
| Antigravity | IDE 为主，CLI 入口是项目级的，对外 bootstrap 机制未公开 |
| CloudBase AI CLI | 本身是网关，调用下游 CLI —— 在下游工具上装 hivequeen 即可 |
| ChatDev | 模拟「虚拟软件公司」的工作流编排，不是持久化单 agent 循环 |

---

## 用 `install/generic.sh` 接入新工具

对于任何启动时读取单个 markdown 文件作为 system prompt 的 CLI：

1. 确认它的 config 路径（通过 `--help` 或官方文档）
2. 选一个短 prefix 作为 `agent-id` 前缀
3. 运行：

```bash
bash scripts/install/generic.sh <prefix> <config-path>
```

脚本会：
- 创建本机该工具的私有记忆目录 `agents/<prefix>-<hostname>/memory.md`
- 把 hivequeen bootstrap 块注入到 `<config-path>` 的
  `<!-- hivequeen:begin -->` / `<!-- hivequeen:end -->` 标记之间，保留用户已有内容
- **不注册 hooks**：只有 Claude Code 有 hook 系统。其他工具靠 bootstrap 块里写的
  git commit/push 指令，由 agent 在会话结束时自行执行

---

## 跟踪上游更新

两条路径，都不碰你的私有数据（`agents/`、`queen/`、`shared/`、`projects/`）。

### 自动（推荐）

你私有仓库里的 `.github/workflows/sync-upstream.yml` 每天 03:00 UTC
运行一次（也可手动 **Run workflow**），对比协议层与 upstream 模板，
发现差异就开 PR 到你的 `main`。你 review diff 后合并。

GitHub 禁止 `GITHUB_TOKEN` push 修改 workflow 文件的 commit，所以 CI
路径**不覆盖** `.github/workflows/`，workflow 变更要走下面的手动路径。

### 手动

```bash
bash ~/my-queen/scripts/maintenance/update.sh
```

覆盖 `scripts/`、`.github/workflows/`、`AGENTS.md`、`CLAUDE.md`、
`SOUL.md` 和双语 README。

---

## 灵感来源

《安德的游戏》中的虫族蜂巢意识。每个个体都连接到同一个女王。
没有独立记忆，没有冲突的自我。一个分布式智能体。

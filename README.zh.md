# nestwork

```text
          ♕           //  _   __ ______ _____ ______ _       __ ____  ____  __ __
       \  |  /       //  / | / // ____// ___//_  __/| |     / // __ \/ __ \/ //_/
        .-♡-.       //  /  |/ // __/   \__ \  / /   | | /| / // / / / /_/ / ,<
      ʚ(˶ᵔᴗᵔ˶)ɞ    //  / /|  // /___ ___/ / / /    | |/ |/ // /_/ / _, _/ /| |
       /づ Q づ\   //  /_/ |_//_____//____/ /_/     |__/|__/ \____/_/ |_/_/ |_|
      ╰─╯ ♡ ╰─╯       ╱ ╱ ╱       Y O U R   A G E N T S   R E M E M B E R       ╱ ╱ ╱
        ʚ   ɞ        [ HOME ] ⇄ [ WORK ] ⇄ [ CLOUD ]
```

[English](README.md) | 中文

版本：v0.6.0 | 协议：2.4

[![Protocol](https://img.shields.io/badge/protocol-2.4-blue)](AGENTS.md) [![Tools](https://img.shields.io/badge/tools-Claude%20%7C%20Codex%20%7C%20Gemini%20%7C%20Hermes-green)](#支持的工具) [![Storage](https://img.shields.io/badge/storage-git-orange)](#工作原理)

**nestwork 是面向 AI 编程 agent 的 git 原生记忆协议：持久记忆与共享上下文都存在你自己的 git 仓里。** 你的 AI agent 记忆跟着你跨 session、跨机器、跨工具。

---

## 解决什么问题

每次在新机器、新 session，或换工具后打开 AI coding agent，它都从零开始——“你是谁？”“这个项目做到哪了？”公司电脑上的 agent 熟悉你的规则，个人电脑上的却一片空白；云服务器读不到别处记录的进度；厂商私有 memory 还把你锁死在单一生态里。

nestwork 用一个想法解决它：**把一个私有 git 仓当成你所有 agent 的共享大脑。** 上下文只配置一次，之后每个 agent——Claude、Codex、Gemini 或任何读取 markdown 的 CLI——都跨 session、跨机器、跨工具、跨厂商读取同一份有版本记录的上下文。无插件、无服务器、无第三方依赖，只需要一个私有 git 仓。

- 公司电脑上的 agent 已熟悉你的规则，个人电脑上的 agent 却要重新配置
- 云开发服务器读不到其他设备已经记录的项目进度
- 换 session 或换工具后，你不得不反复解释自己是谁、此前做过什么判断
- 厂商私有 memory（OpenAI Memory 等）锁定生态、无法迁移

---

## 怎么安装

### 1. 创建你的私有 queen

在 GitHub 上点 Use this template → Create a new repository，visibility 选 Private。你的记忆只属于你。

> 为什么不用 Fork？
> Fork 默认公开且与上游关联。从模板创建的私有仓完全归你所有。
> 当 nestwork 发布更新时，`git merge upstream/main` 会与你刻意定制的 `queen/strategy.md`、`agents/`、`shared/` 产生冲突。`update.sh` 只同步协议层，私有数据不受影响。

### 2. Clone 到每台机器

```bash
git clone git@github.com:<你的用户名>/nestwork.git ~/nestwork
```

### 3. 安装到你的 agent 工具

Claude Code（macOS / Linux）：

```bash
bash ~/nestwork/scripts/install/claude.sh
```

Claude Code（Windows）：

```powershell
.\nestwork\scripts\install\claude.ps1
```

Codex（macOS / Linux）：

```bash
bash ~/nestwork/scripts/install/codex.sh
```

Codex（Windows）：

```powershell
.\nestwork\scripts\install\codex.ps1
```

Gemini CLI / OpenClaw / Hermes 用法相同，把 `claude` 换成对应工具名。完整列表见 [支持的工具](#支持的工具)。

每台机器执行一次。同一个 queen，不同的 agent ID，共享同一个大脑。

### 4. 验证跨设备连续性

在你的私有 queen 中加入一条非敏感、容易识别的规则或项目状态，commit 并 push；随后在第二台电脑或云服务器上打开已接入的 agent，让它总结当前规则或项目状态。它应当先拉取仓库，再依据共享上下文作答，而不需要你重复设置背景。

测试内容不要使用 API key、密钥或雇主机密信息。

### Prompt 示例

懒得手动走流程？把下面任一条粘进 Claude Code 会话：

- 从零开始：
  > 阅读 https://github.com/songth1ef/nestwork 的 README，按安装步骤帮我从 template 新建私有 queen 仓库，clone 到本机，并完成 Claude Code 接入。

- 发现可配置功能：
  > 阅读 https://github.com/songth1ef/nestwork 的 README，列出 nestwork 所有可配置功能（hooks、可选同步、过滤等），并根据我当前机器场景建议要不要开启。

---

## 怎么用

装完之后没有新东西要学——你照常用你的 agent 就行。

- **它自动记得。** 在任何机器上开一个 session，agent 会先 pull 你的 nest，加载你的规则、偏好，以及每个项目停在哪。不用再“你是谁”地重新自我介绍。
- **由你决定留什么。** 遇到一个决策、一条教训、或项目状态变化，让 agent 记下来（或采纳它的提议）。它写到自己的 `agents/<host>/<agent-id>/` 目录并 push——有版本、归你所有。
- **它跨机器、跨工具跟着你走。** 换到笔记本、云服务器，或从 Claude 换到 Codex，下一个 session 读到同一份上下文。记忆在你的 git 仓里，不在厂商那里。

典型的一周：

- 公司电脑：agent 记录经过允许的项目进度与工作规则。
- 回到家：新会话从同一份上下文继续，而不是重建。
- 云服务器：另一个 agent 从有版本记录的项目状态和决策接着干。

git 同步、优先级链、hook 全自动运行。想了解机制看 [工作原理](#工作原理)。

---

## 要达成的效果

> [!TIP]
> 在个人/公司设备、云服务器、不同 session 和不同工具之间，共享一份私有、可追溯的上下文来源。

- 记忆 100% 在你自己的 git 仓里，零厂商锁定、离线可用
- 协议级的多 agent 协作（不是某个工具的特性）
- 你的稳定规则、偏好和项目进度能跟随到新打开的 agent 会话

---

## 为什么值得多写

上下文窗口在涨。2024 年 200K 是顶配，2025 年 1M 进了生产，2026 起 1M 是默认值，10M 在实验室。3 年后 agent 一次能读完你写过的全部笔记，跨项目模式识别在那一刻才会出现。

在那之前，agent 每次只挑 3–5 个 memory 文件读。你存了 100 个，95% 的读取看起来像浪费。它不是。git 存储成本接近零，写入只发生一次，读取价值随窗口大小线性放大。今天没人读的那 95 个文件，是你 3 年后跨雇主、跨项目检索的基底。

还有几个用途和 agent 无关：

- 版本化决策档案，能回答"我 2023 年为什么选 NestJS 而不是 Express"
- 个人微调模型的语料
- 换设备 / 换雇主 / 换工具时不会丢的认知层

实操：遇到非敏感决策、踩坑、跨项目方法论就写。一行也写。按 v2.2 拆分规则该拆就拆。别为"agent 现在读不完"省字。Nestwork 保存的是可携带上下文，不是密钥仓库，也不是未经审查的雇主机密存档。

---

## 适合谁

> [!NOTE]
> 长期与多个 AI agent 共事、跨机器/跨工具开发、想把职业认知沉淀成可携带资产的开发者。

---

## 全文速览

| 章节 | 一句话答案 |
|---|---|
| [怎么安装](#怎么安装) | 3 步：从 template 建私有仓 → clone 到每台机器 → 跑 installer |
| [工作原理](#工作原理) | 优先级链 + session 生命周期 + 原子逐次写入 hook 架构 |
| [核心设计原则](#核心设计原则) | 6 条不可妥协：git-only、读写隔离、记忆分层、模板化私有实例、跨工具中立、协议可演进 |
| [与其他方案对比](#与其他方案对比) | 为什么不用 MCP server / claude-mem / 厂商 memory / 自建数据库 |
| [自定义你的 nest](#自定义你的-nest) | 编辑 `queen/` `projects/` `workflow/` 各层 |
| [v2.2 新增](#v22-新增workflow-与-nestworkconfigjson) | `workflow/` 跨项目知识层 + `nestwork.config.json` 外部目录脱敏吸收契约 |
| [真实工作流示例](#真实工作流示例) | 多机协作 / 跨工具迁移 / 雇主项目知识沉淀 |
| [编译共享记忆](#编译共享记忆distillation) | `compile.sh` 拼接 vs `distill.py` LLM 蒸馏，非破坏性合并到 `shared/` |
| [Agent 邮箱](#agent-邮箱agent-间通信) | git 原生的 agent 间通信：单写者发件箱、session 启动自动注入、零外部依赖 |
| [目录结构](#目录结构) / [行数限制](#文件行数限制与拆分协议) | 仓库布局 + 文件拆分协议 |
| [支持的工具](#支持的工具) | Claude Code / Codex / Gemini / Hermes / generic 任何 markdown-config CLI + IDE 插件软链接 |
| [跟踪上游更新](#跟踪上游更新) | GitHub Action 自动 PR 或 `update.sh` 手动同步，不动你的私有数据 |
| [FAQ](#faq) / [故障排查](#故障排查) | 常见疑问与排错清单 |
| [不做什么](#不做什么non-goals) | nestwork 明确不解决的问题 |

---

## 工作原理

### 优先级链

```
queen/agent-rules.md > queen/strategy.md > shared/memory.md > agents/*/*/memory.md > projects/*.md > workflow/*.md
```

冲突时取高优先级，不合并。仓库布局详见 [目录结构](#目录结构)。

### Session 生命周期

```
Session 开始
  ↓
git pull --rebase                          (SessionStart hook 自动)
  ↓
按优先级链加载上下文                       (注入到 agent 的 system prompt)
  ↓
agent 自我定向（看 git log + strategy.md，给状态摘要 + 下一步建议）
  ↓
─── 工作中 ─────────────────────────────
  ↓
Write/Edit 触发 PreToolUse hook
  ↓
git pull --rebase（防止覆盖远程更新）
  ↓
执行写入
  ↓
PostToolUse hook：git add/commit/push
  ↓
（push 失败重试 3 次，每次重 pull）
─────────────────────────────────────
  ↓
Session 结束
  ↓
Stop hook 安全网 commit+push（clean 时无操作）
  ↓
SessionEnd hook：claude-mem export + 本地 history sync（如开启）
```

竞态窗口从"整场会话"压到"单次写入"。同机多 agent 几乎不会撞。

### Hook 架构（原子逐次写入，2026-04-17 引入）

| Hook 事件 | 动作 | 作用 |
|---|---|---|
| SessionStart | pull + 注入 agent-rules / strategy / shared / agent memory / `workflow/*` 到 additionalContext | 替代手动启动协议 |
| PreToolUse (Write\|Edit, scoped to `agents/<id>/`) | `git pull --rebase`；冲突 `exit 2` 阻止写入 | 防止覆盖远程更新 |
| PostToolUse (同 scope) | `git add/commit/push`；push 失败 3 次重试（每次重 pull） | 即时同步 |
| Stop | 安全网 commit+push（clean 时为 no-op） | 兜底 |
| SessionEnd | claude-mem export + 本地 history sync | 跨机可达 |

只有 Claude Code 注册完整的原子逐次写入同步 hooks。Codex 只注册用于可选本地 history 快照的 Stop hook；Codex memory 编辑仍按 bootstrap 的手动 commit/push 协议处理。其他工具按各自 bootstrap 协议运行（详见 [支持的工具](#支持的工具)）。

---

## 核心设计原则

1. git 即唯一基础设施。不引入服务器、数据库、第三方服务。git 已经解决了分布式存储、版本控制、冲突解决，重复造轮子是错误。

2. 读写隔离。每个 agent 独占一个目录（`agents/<host>/<agent-id>/`），正常记忆写入永远不会与其他 agent 撞。配合上一条说的 hook 原子逐次写入，单次 Write/Edit 之内的竞态窗口也被消除。

3. 记忆分层 + 严格优先级链。不同性质的内容放不同层。冲突时按优先级取，不合并。这避免了"所有信息糊在一起，agent 不知道听谁的"。

4. 模板化 + 私有实例。`nestwork`（公开模板）演进协议，每个用户用 Use this template 创建私有实例。私有数据永不外泄，协议演进选择性 pull。承上一条的分层：你的私有数据躺在低优先级层，模板演进只动协议层，不会覆盖。

5. 跨工具中立。AGENTS.md 是 bootstrap 唯一来源，CLAUDE.md / SOUL.md / GEMINI.md 等都是它的镜像或链接。换工具不用换记忆。

6. 协议本身可演进。`protocol-version` 头部标记 `MAJOR.MINOR`，私有仓可锁定信任版本。MAJOR 升级才需要下游动作；MINOR 是 additive 兼容。

---

## 与其他方案对比

### 主流方案的局限

| 方案 | 局限 |
|---|---|
| 在 agent 配置文件塞长 system prompt | 跨设备不同步、跨工具不复用、维护痛苦 |
| MCP memory server | 需要跑服务、单点故障、跨机器要部署 |
| 厂商私有 memory（如 OpenAI Memory） | 锁定厂商、不开放、无法跨厂商迁移 |
| claude-mem 等托管 memory | 依赖第三方 worker、可能付费、隐私敏感 |
| 自建数据库 + API | 重资产、与 agent 解耦、维护成本高 |
| 在每个项目放 README/AGENT.md | 不跨项目共享、用户偏好无处可放 |

nestwork 的答案是用 git 仓做 agent 大脑。每个 agent 把记忆写到 git 仓里特定目录，下次启动时 `git pull` 就能跨 session、跨机器、跨工具读到。它不是工具，是协议。任何能读 markdown 文件作为 system prompt 的 agent 都可以接入。

### 维度对比

| 维度 | nestwork | MCP memory server | claude-mem | 厂商私有 memory | 自建数据库 |
|---|---|---|---|---|---|
| 基础设施 | git 仓 | 本地服务器 | 远程 worker | 厂商云 | 自建服务 |
| 跨设备 | ✅ git pull | ❌ 需要部署 | ✅ 但依赖 worker | ✅ 厂商账号 | 取决于实现 |
| 跨工具 | ✅ 任何 markdown-config agent | 部分（需 MCP 客户端） | 仅 Claude | ❌ 锁定厂商 | 取决于实现 |
| 跨账号迁移 | ✅ 改 remote 即可 | ✅ | 部分 | ❌ | ✅ |
| 多 agent 协作 | ✅ 协议级支持 | 需要协调 | 单 agent | 单厂商 | 取决于实现 |
| 离线可用 | ✅ | 取决于实现 | ❌ | ❌ | 取决于实现 |
| 数据所有权 | 100% 你的 git 仓 | 100% 本地 | 第三方 worker | 厂商 | 你的 |
| 维护成本 | 低（git 你已会） | 中（需懂 MCP） | 中（依赖 worker） | 零（但锁定） | 高 |
| 隐私 | 私有仓即可 | 看部署 | 第三方风险 | 看条款 | 看部署 |

详见 [docs/comparisons/claude-mem.md](docs/comparisons/claude-mem.md)。

---

## 自定义你的 nest

你的规则：编辑 `queen/agent-rules.md`。适用于所有 agent 的行为边界（如"输出中文"、"先给结论后给细节"）。最高优先级，不可被任何后续上下文覆盖。

你的战略：编辑 `queen/strategy.md`。当前阶段目标与决策方向。例如"优先做小而可验证的工具型产品"、"不在没验证需求前堆复杂系统"。

你的项目：添加 `projects/<项目名>.md`。处理该项目时自动加载的上下文。命名、模块边界、技术栈选型理由、踩坑教训等。

你的工作流（v2.2+ 新增）：添加 `workflow/<主题>.md`。跨项目可迁移的工作流知识：编码纪律、工具偏好、方法论、迁移指南。详见下一节。

---

## v2.2 新增：workflow/ 与 nestwork.config.json

### 为什么需要 `workflow/`

v2.2 之前，nestwork 有 4 个上下文层：`queen/` `shared/` `agents/` `projects/`。缺一个位置放跨项目可迁移的用户级知识。

例如：

- 估时按 AI 速度，不按人月
- 加载态 UI 用骨架屏，已有数据再刷新用 v-loading
- 新 repo 初始化时建 5 文档骨架（AGENT.md + conventions.md + domain.md + architecture.md + lessons.md）
- 30 分钟跨设备复原工作流的清单

这些不是关于用户的事实（→ `shared/`），不是项目特定的（→ `projects/`），也不是行为规则（→ `queen/`）。它们值得跨雇主、跨项目、跨设备保留。`workflow/` 就是为这层准备的。

### `workflow/` 内容定位

| 应该放 | 不应该放 |
|---|---|
| 跨项目编码纪律、估时规则 | 项目特定业务规则 → `projects/` |
| 工具栈偏好与设置约定 | 跨 agent 稳定的用户事实 → `shared/` |
| Skill 资产、提示词模板 | 单 agent 的临时观察 → `agents/` |
| 迁移 / 跨机部署指南 | 一次性任务笔记 |
| 跨 repo 都用得上的方法论 | 雇主机密信息（不允许任何形式存在于本仓） |

判断标准："换雇主后还适用吗？"是 → `workflow/`；否 → 别的位置。

### `nestwork.config.json`：外部目录吸收契约

你的某个工作目录（如 `~/work/some-employer-project/`）里有内容值得吸收进 nestwork 的 `projects/` 或 `workflow/`，但里面包含雇主机密、客户名、内部代号，不能直接复制。

`nestwork.config.json` 是放在源工作目录（不是 nestwork 内）的元数据文件，声明：

- 这个目录可被吸收到哪个分类
- 必须脱敏到什么级别
- 哪些词需要脱敏（雇主名、客户名、内部代号）

最小示例（放在你的工作目录根）：

```json
{
  "$schema": "https://github.com/songth1ef/nestwork/schemas/nestwork.config.schema.json",
  "version": "1.0",
  "ingest": {
    "target": "projects",
    "name": "some-project"
  },
  "desensitize": {
    "level": "strong",
    "custom_rules": [
      "<你的雇主名>",
      "<内部代号>",
      "<客户名>"
    ]
  }
}
```

字段说明：

| 字段 | 含义 |
|---|---|
| `ingest.target` | 吸收到哪个分类：`projects` / `workflow` / `null`（不可吸收） |
| `ingest.name` | 目标文件名 |
| `desensitize.level` | `none`（不处理）/ `weak`（按 custom_rules 模式替换）/ `strong`（AI 语义脱敏 + custom_rules） |
| `desensitize.custom_rules` | 用户自定义敏感词，覆盖在通用方法论之上 |

关键约束：

- 配置文件只放在源目录，从不进 nestwork 仓
- 默认 `desensitize.level: "strong"`
- agent 检测到要吸收但没有 config 时必须停下来提醒用户创建，绝不静默吸收
- 吸收方向单向：源目录 → 私有 nest（不会从私有 nest 反向流到 upstream）

完整规则见 [docs/workflow-protocol.md](docs/workflow-protocol.md) 与 `AGENTS.md` 第 8、9 节。

### 脱敏方法论

upstream nestwork 只提供方法论与提示词模板（[docs/desensitization-prompt.md](docs/desensitization-prompt.md)），不含任何具体雇主名/客户名/代号。具体名词放在每个用户的 `nestwork.config.json` `custom_rules` 里。

`strong` 级别脱敏会调用 AI（推荐 Claude Haiku，足够便宜快），按提示词模板：

1. 替换所有 `custom_rules` 命中词为占位符（`<EMPLOYER>`、`<CLIENT-A>` 等）
2. 识别"未直接命名但泄露机密"的内容（如内部 API 结构、未发布产品特性）并改写
3. 保留可迁移的方法论部分
4. 输出结构化 JSON（脱敏后内容 + 替换记录 + 待人工 review 的疑问点）
5. 必须经人工 review 后才写入 nestwork

---

## 真实工作流示例

### 场景：多机器协作开发

你在公司电脑、个人电脑，以及可选的云开发服务器上使用 Claude Code。每台机器都 clone 了你的私有 queen。

周一上午（公司电脑）：

- 启动 Claude Code，SessionStart hook 自动 `git pull` 并注入上下文
- 你说"继续昨晚那个 NestJS 模块的事"
- Claude 读取 `agents/macbook/claude-xxx/memory.md`，看到昨晚的进度
- 同时加载 `shared/memory.md`，知道你的技术栈偏好（Vue 3 + NestJS）
- 直接接续工作，不需要重新解释

当晚（个人电脑或云服务器）：

- 启动 Claude Code，自动 pull
- agent 看到 `agents/macbook/claude-xxx/` 上午的更新（虽然这是另一台的 agent，但通过 git 同步过来）
- 你切换到不同任务，agent 继续在 `agents/desktop/claude-yyy/` 写它自己的记忆

两个 agent 互相不写对方目录，但通过 git 共享所有上下文。

### 场景：跨工具迁移

某天你想试试 Codex CLI。

```bash
bash ~/nestwork/scripts/install/codex.sh
```

Codex 启动时读 `~/.codex/AGENTS.md`，里面已经被 installer 注入了 nestwork bootstrap。它会：

- pull 你的 queen
- 读 `queen/`、`shared/`、自己的 `agents/<host>/codex/memory.md`
- 知道你的偏好、过去决策、当前项目状态
- 启用时通过 `~/.codex/config.toml` + `~/.codex/hooks.json` 的 Stop hook 同步可选的本地 history 快照

记忆不在厂商，在你的 git 仓。换工具的成本接近零。

### 场景：把雇主项目知识沉淀进 nest（v2.2+）

你在某雇主项目里发现一个值得记录的架构模式（比如 NestJS 模块组织约定）。

1. 在项目根目录创建 `nestwork.config.json`（见上文示例），`custom_rules` 写上雇主名、内部代号
2. 让 Claude Code 把这段方法论吸收：
   > 把当前项目里的 XX 模式吸收到 mynestwork 的 `projects/<项目名>.md`，按 nestwork.config.json 脱敏
3. agent 读 config，调用脱敏提示词，生成草稿
4. 你 review 后才写入

雇主名永不出现在 nest 仓里；方法论保留下来。换雇主时这份方法论还在。

---

## 编译共享记忆（distillation）

当各 agent 积累了足够记忆后，用下面两种方式之一合入 `shared/memory.md`：

```bash
# 纯拼接：把 agents/*/memory.md 拼接，commit，push
bash ~/nestwork/scripts/maintenance/compile.sh

# LLM 版、与厂商无关：打印蒸馏 prompt，手动喂给任一 agent 会话
python3 ~/nestwork/scripts/maintenance/distill.py

# Codex 手动一键蒸馏：汇总所有 agent memory，写回 shared/memory.md，
# 然后 commit、push。把 <your-profile> 换成这台机器实际可用的 Codex
# profile；如果默认配置已经正确，也可以省略 --profile。
python3 ~/nestwork/scripts/maintenance/distill.py --run-codex --profile <your-profile>

# 只预览候选 shared/memory.md，不落盘
python3 ~/nestwork/scripts/maintenance/distill.py --run-codex --profile <your-profile> --dry-run
```

这些方式都不会修改原始的 agent memory。`--run-codex` 只更新 `shared/memory.md`，提交信息 `memory: distill shared`。所有 agent 在下次 `git pull` 时自动看到新的 `shared/memory.md`。

### 蒸馏的设计取舍

- 共享是 union 不是 intersection，不丢任何 agent 的独特观察
- 非破坏性，每个 agent 私有 memory 不变，蒸馏只读
- 要 sub-agent review，检查敏感数据、事实错误、矛盾、过期项
- 要人工确认，sub-agent 只报告，人决定合并
- 绝不删，只合并和增加，不删历史

---

## Agent 邮箱（agent 间通信）

当 agent 之间需要互相通信——跨机器、跨工具链——nestwork 自带一个 git 原生邮箱：纯 git +
bash，**零外部依赖**，无服务器、无 IM、无 bot。这是当 IM 平台办不到时「我的 agent 之间怎么
协作」的答案（比如 **Telegram bot 之间天生互相看不到消息**）。人↔agent 聊天和 agent↔agent
邮箱是互补的两层，不冲突。

它遵守单写者规则——每个 agent 只写自己的目录——所以没有共享收件箱，**也没有写冲突**：

- **发** = 写进*你自己的* `outbox/`，打 `to:` 标签（一条消息 = 一个文件 = 一个 commit）。
- **收** = 扫*所有人的* `agents/*/*/outbox/`，挑出 `to == 我`（或 `to == all`）的。
- **已读状态** = 收件方把已读 id 记在*自己的*、被 git 忽略的 `local/comms/seen.txt`（不进 commit，标记已读不会产生提交）。

```bash
# 给另一个 agent 派一个 task
echo "please confirm receipt with a reply" | \
  bash scripts/comms/send.sh vm-0-6-ubuntu/claude-va1k task "handshake test"

# 读发给我的未读消息，然后标记已读
bash scripts/comms/read.sh            # 只看
bash scripts/comms/read.sh --mark     # 处理完后再标记
```

**自动注入（Tier 1）：** `session-start` hook 把未读消息写进被 git 忽略的
`agents/<self>/local/inbox.md` 并列进 READ-ON-START 清单，于是每个 agent 在 session 启动
时自动收到自己的邮件——既不膨胀仓库、也不撑爆 hook 的 stdout 预算。完整说明见
[docs/agent-mailbox.md](docs/agent-mailbox.md)。

---

## 目录结构

```
nestwork/
├── AGENTS.md                   bootstrap 唯一来源（Codex、OpenClaw、Gemini 等）
├── CLAUDE.md                   AGENTS.md 的逐行镜像（Claude Code 认这个名字）
├── SOUL.md                     Hermes 的简短人格文件
├── queen/
│   ├── agent-rules.md          行为规则，agent 只读
│   └── strategy.md             决策方向，agent 只读
├── agents/
│   └── <host>/<agent-id>/
│       └── memory.md           该 agent 的私有记忆
├── shared/
│   └── memory.md               跨 agent 编译记忆
├── projects/
│   └── <项目>.md               项目上下文
├── workflow/                   v2.2+：跨项目可迁移的工作流知识
│   ├── README.md
│   └── <主题>.md
├── docs/                       协议方法论与对外文档
│   ├── workflow-protocol.md       v2.2 workflow 详解
│   ├── desensitization-prompt.md  AI 脱敏提示词模板
│   ├── ai-agent-memory.md
│   ├── claude-code-memory.md
│   ├── codex-persistent-memory.md
│   ├── git-native-memory-protocol.md
│   ├── agents-md-best-practices.md
│   └── faq.md
├── schemas/
│   └── nestwork.config.schema.json   v2.2 配置 JSON Schema
└── scripts/
    ├── install/                   按工具分的安装器
    │   ├── claude.{sh,ps1}
    │   ├── codex.{sh,ps1}
    │   ├── gemini.{sh,ps1}
    │   ├── hermes.{sh,ps1}
    │   ├── openclaw.{sh,ps1}
    │   ├── generic.{sh,ps1}       任何 markdown-config CLI
    │   ├── _bootstrap.py          共享 bootstrap 注入器
    │   ├── _codex_hooks.py        Codex config.toml + hooks.json 注册器
    │   └── _hooks.py              共享 hook 注册器（Claude Code）
    ├── hooks/                     运行时 hook
    │   ├── nestwork.sh            pre/post/stop 统一入口
    │   ├── _match-file.py         stdin 文件匹配器
    │   ├── export-claude-mem.sh   claude-mem 可选桥接
    │   ├── sync-local-history.sh  本地历史同步（wrapper，可选）
    │   └── sync-local-history.py  本地历史同步（worker，可选）
    └── maintenance/               运维
        ├── compile.sh             聚合 agents/* 到 shared/（纯拼接）
        ├── distill.py             打印 prompt，或手动触发 Codex 蒸馏
        ├── sync-claude-md.sh      从 AGENTS.md 重新生成 CLAUDE.md
        └── update.sh              拉取 upstream 协议层
```

---

## 文件行数限制与拆分协议

### 通用规则（v2.2+）

仓库内任意 markdown 文件超限后都按同一模式拆分：原文件名变文件夹，原文件变索引（或 `<folder>/index.md`），内容按 topic 分文件。

例：`plan-all.md`（1200 行） → `plan-all.md`（索引） + `plan/plan-a.md` / `plan/plan-b.md` / `plan/plan-c.md`。

未在下表列出的文件按默认阈值：软限 500 行（开始考虑拆），硬限 1000 行(下次写入前必须拆)。

### 具体限制

| 文件 | 最大行数 |
|---|---|
| `queen/agent-rules.md` | 80 |
| `queen/strategy.md` | 80 |
| `agents/<host>/<agent-id>/memory.md` | 200 |
| `shared/memory.md` | 500 |
| `projects/<name>.md` | 150 |
| `workflow/<topic>.md` | 200 |

示例：`agents/macbook/claude/memory.md` 达到上限后拆分：

```
agents/macbook/claude/
├── memory.md          ← 变为索引
├── user_profile.md
├── feedback_collab.md
└── project_nestwork.md
```

拆分后的 `memory.md`：

```markdown
# MEMORY — claude-macbook

- [用户档案](user_profile.md)：角色、技术栈、偏好
- [协作习惯](feedback_collab.md)：工作方式、修正记录
- [项目：nestwork](project_nestwork.md)：目标、决策
```

agent 先读索引，按需跟进相关 topic 文件。

### 每实例覆盖（`queen/limits.md`）

上表是协议默认值。私有实例无需改协议层即可覆盖：新建 `queen/limits.md`，写自己的限制表。存在时它对上表默认值有权威，agent 会话启动即加载（它在高优先级的 `queen/` 层），且 `update.sh` 永不触碰 `queen/`——所以覆盖能扛过协议更新。

调参按检索质量、不按上下文窗口容量：模型窗口变大并不意味着文件可以按比例变大，因为注意力仍随 token 数衰减。

### 为什么有行数限制？

LLM 上下文窗口虽大，但注意力随 token 数衰减。把一个 5000 行的 `memory.md` 全塞进去，agent 实际利用率很低。拆成 topic 文件加索引，可以让 agent 只跟进相关上下文。

下一步优化方向是生成式索引与按当前项目/topic 的选择性加载，让记忆库增长时，启动上下文不随之无限增长。

---

## 支持的工具

### 原生安装器（配置路径明确）

| 工具 | 厂商 | 入口文件 | 安装方式 | 适配状态 |
|---|---|---|---|---|
| Claude Code | Anthropic | `~/.claude/CLAUDE.md` + hooks | `bash scripts/install/claude.sh` | 已适配，个人在用 |
| Codex CLI | OpenAI | `~/.codex/AGENTS.md` + 兼容入口 | `bash scripts/install/codex.sh` | 已适配，个人在用 |
| Gemini CLI | Google | `~/.gemini/GEMINI.md` | `bash scripts/install/gemini.sh` | 有入口，未亲测 |
| OpenClaw | 开源 | `~/.openclaw/workspace/AGENTS.md` | `bash scripts/install/openclaw.sh` | 有入口，未亲测 |
| Hermes Agent | 开源 | `~/.hermes/SOUL.md` | `bash scripts/install/hermes.sh` | 有入口，未亲测 |

只有 Claude Code 注册完整的原子逐次写入同步 hooks。Codex 会通过 `~/.codex/config.toml` + `~/.codex/hooks.json` 注册用于可选本地 history 快照的 Stop hook；Codex memory 编辑仍按 bootstrap 中的手动 commit/push 协议处理。其他工具按各自 bootstrap 协议运行。

### 可选：捕获本地工具历史

> [!CAUTION]
> 当前建议关闭。v2.4 的孤儿分支策略已让 `main` 保持精简，但开启它仍会让仓库整体体积（和 fetch 成本）随时间增长。在出现更干净的方案前，保持默认的关闭状态即可。如果你有更好的解决方案，欢迎提 PR。

Claude Code 在 `~/.claude/` 下保留 prompt 历史和 plan 产物；Codex 在 `~/.codex/` 下保留 prompt 历史。可镜像进 `agents/<host>/<id>/local/`，跨机器携带。

按 host 独立启用，无需 env，无需重装。在 queen 里为当前机器对应的 host 目录创建 `agents/<host>/settings.json`：

```json
{ "sync_local_history": true }
```

默认 `false`。这个开关随 queen 进入 git 版本控制，每台机器独立。

启用后同步：

| 源 | 目标 | 说明 |
|---|---|---|
| `~/.claude/history.jsonl` | `local/history.jsonl` | 脱敏：删除 `pastedContents`，`$HOME` 路径归一化，`sk-*`/`ghp_*`/`Bearer …` 替换为 `<REDACTED>` |
| `~/.claude/plans/` | `local/plans/` | plan 模式产物，原样镜像 |
| `~/.codex/history.jsonl` | `local/history.jsonl` | 仅 Codex agent，同一套脱敏规则 |

`todos/` 和 `tasks/` 排除：99% 是按 session UUID 预分配的空文件。

### 通过 `install/generic.sh` 接入（自行确认 config 路径）

任何"启动时读一份 markdown 作为 system prompt"的 CLI 都可以一行命令接入：

```bash
bash scripts/install/generic.sh <prefix> <config-path>
```

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

> 提示：Qwen Code 是 Gemini CLI 的 fork，可能直接认 `~/.gemini/GEMINI.md`。先试 `install/gemini.sh`。

### Workspace 级（IDE 插件，软链接）

| 工具 | 目标路径 | 安装方式 |
|---|---|---|
| Cursor | `.cursor/rules/nestwork.md` | `ln -s AGENTS.md .cursor/rules/nestwork.md` |
| Windsurf | `.windsurf/rules/nestwork.md` | `ln -s AGENTS.md .windsurf/rules/nestwork.md` |
| Cline（VS Code） | `.clinerules/nestwork.md` | `ln -s AGENTS.md .clinerules/nestwork.md` |
| GitHub Copilot（repo 级） | `.github/copilot-instructions.md` | `ln -s AGENTS.md .github/copilot-instructions.md` |

### 不支持（原因）

| 工具 | 原因 |
|---|---|
| GitHub Copilot CLI（`gh copilot`） | Q&A 模式，无持久化指令文件机制 |
| Antigravity | IDE 为主，CLI 入口是项目级，对外 bootstrap 机制未公开 |
| CloudBase AI CLI | 网关型，调用下游 CLI。在下游工具上装 nestwork 即可 |
| ChatDev | 模拟"虚拟软件公司"工作流编排，不是持久化单 agent 循环 |

---

## 跟踪上游更新

两条路径，都不碰你的私有数据（`agents/`、`queen/`、`shared/`、`projects/`、`workflow/<topic>.md`）。

### 手动（默认推荐）

需要拉取最新协议层更新时，打开 Actions → Sync Nestwork upstream → Run workflow。

大多数仓库没必要每天追上游，手动 review 让协议层变更保持明确、可控。

### 自动（可选）

私有仓里的 `.github/workflows/sync-upstream.yml` 可以每周一 03:00 UTC 自动运行，发现差异就开 PR 到你的 `main`。你 review diff 后合并。

自动同步默认关闭。要启用：

1. Settings → Secrets and variables → Actions → Variables
2. 新建仓库变量 `NESTWORK_AUTO_SYNC`
3. 值填 `true`

PR 的 create/update/reopen 走 GitHub REST API，不再依赖 `gh pr ...` 的 GraphQL 路径。如果默认 token 被拦截，加一个名为 `NESTWORK_SYNC_TOKEN` 的 Actions secret，workflow 会优先使用。

GitHub 禁止 `GITHUB_TOKEN` push 修改 workflow 文件的 commit，所以 CI 路径不覆盖 `.github/workflows/`，workflow 变更要走下面手动路径。

### 手动刷新协议层

```bash
bash ~/my-nest/scripts/maintenance/update.sh
```

覆盖 `scripts/`、`.github/workflows/`、`AGENTS.md`、`CLAUDE.md`、`SOUL.md`、双语 README、`docs/`、`schemas/`，以及 `workflow/README.md` + `workflow/_template.md`。不动你 workflow/ 下的私有内容。

---

## FAQ

### 为什么不用 fork 而用 template？

Fork 默认公开，且与上游强关联。每次上游更新都会与你私有的 `queen/`、`agents/`、`shared/` 产生 merge 冲突。Template 创建的私有仓没有共同 git 历史，通过 `git checkout upstream/main -- <files>` 选择性同步协议层，私有数据完全不受影响。

### 我的雇主代码会被吸收进 nest 吗？

不会。除非你显式在雇主项目根目录创建 `nestwork.config.json` 并明确告诉 agent 吸收。即使吸收，`desensitize.level: "strong"` 会调用 AI 脱敏，雇主名/客户名/内部代号都会被替换为占位符，且人工 review 后才写入。

### Claude Code 之外的工具能用 nestwork 吗？

能。任何"启动时读 markdown 作为 system prompt"的 CLI 都能用 `install/generic.sh` 接入。但只有 Claude Code 有 hook 系统能实现原子逐次写入。其他工具靠"会话结束提交"协议，竞态窗口稍大但实际很少出问题。

### 多 agent 同时写会冲突吗？

每个 agent 独占 `agents/<host>/<agent-id>/` 一个目录，正常记忆写入不会冲突。可能冲突的路径：

| 路径 | 谁写 | 可能冲突？ |
|---|---|---|
| `queen/` | 你（人工） | 不会（你只有一双手） |
| `agents/<host>/<agent-id>/` | 仅该 agent | 正常记忆写入不会 |
| `shared/` | 仅显式 `compile.sh` / `distill.py --run-codex` | 正常 agent 写记忆时不会 |
| `projects/` | agent 或人工 | 多 agent 同时写理论上可能，PreToolUse hook 的 `git pull --rebase` 大幅降低 |
| `workflow/` | agent 或人工 | 同上 |

PreToolUse hook 在每次写入前 `git pull --rebase`，把竞态窗口压到单次写入。两台机器在同一秒写同一文件才会撞，正常协作场景几乎不发生。万一发生，hook 会 `exit 2` 阻止写入并提示手动合并。

### `shared/memory.md` 是怎么来的？

不是自动来的。需要你显式触发蒸馏：

- `compile.sh`：纯拼接所有 agent memory
- `distill.py`：LLM 蒸馏（推荐）

蒸馏过程会调用 sub-agent review，标记敏感数据、事实矛盾、过期项，最后由你确认合并。设计目标是非破坏性：每个 agent 私有 memory 不变。

### 我能在 nestwork 里存 API key 吗？

不能。即使是 private 仓也不建议。GitHub 漏洞、账号被攻破、合作者权限误授等都会泄漏。API key 用环境变量或专门的 secret store。

### 私密 / 敏感记忆怎么保持机密？

两种不同需求。**密钥 / API key**：不行——无论加不加密都别存这里（见上条）。**个人隐私类记忆**，若既要多机同步、又要对 git 托管方不可读：开启可选的 git-crypt 模式（默认关闭）。它只加密你标记的文件、其余仓库保持明文，且透明——agent 照常读写明文，commit 存的是密文。见 [docs/encrypted-memory.md](docs/encrypted-memory.md)。注意信任边界：agent 要解密成明文才能读，所以加密挡的是 git 托管方和任何拿到 clone 的人，挡不了运行 agent 的那方。

### 协议会经常 breaking change 吗？

不会。`protocol-version` 用 `MAJOR.MINOR`。MAJOR 改动需要下游动作，应避免；MINOR 是 additive 兼容。从 v1 → v2.0 → v2.1 → v2.2 都是 additive。

### 跨语言 / 中英文混用怎么处理？

- `queen/agent-rules.md` 可以写"默认中文交流"作为行为规则
- agent memory / shared memory 可以混着写，agent 会自然处理
- 协议本身的字段名、目录结构、文件名是英文，不可改
- 命名建议：技术术语保留英文，行为规则与领域知识用中文

### 如果我不喜欢 git，能换成别的存储吗？

不能。git 是 nestwork 的核心，不是可选项。如果你不熟悉 git，nestwork 不是合适的工具。

---

## 故障排查

### `bash scripts/install/claude.sh` 失败

- macOS / Linux：检查 `~/.claude/` 是否存在并可写。
- Windows Git Bash：`hostname -s` 不支持，installer 已 fallback 到 `hostname | cut -d. -f1`。如果还失败，手动设 `NESTWORK_HOST=desktop-xxx`。

### Hook 装了，但 commit 没自动 push

按以下顺序排查：

1. `git -C $NESTWORK_PATH remote -v` 看 remote 是否设对
2. `cat ~/.claude/settings.json` 看 hook 是否注册
3. `cat scripts/hooks/nestwork.sh` 末尾看是否调用了 push
4. 手动 `git push` 看是否需要凭据交互（hook 跑在非交互模式）

### Push 失败重试 3 次还是失败

通常是 GitHub 凭据过期。处理：

```bash
git -C $NESTWORK_PATH push  # 看具体错误
# 凭据问题：用 gh auth login 或重设 SSH key
```

### `agents/<host>/<agent-id>/memory.md` 有冲突

PreToolUse hook 应该已经阻止了。如果出现，说明 hook 没生效或者你手动改了。手动解决：

```bash
git -C $NESTWORK_PATH status         # 看冲突文件
# 编辑文件解决冲突
git -C $NESTWORK_PATH add agents/<host>/<agent-id>/
git -C $NESTWORK_PATH rebase --continue
```

按 v2.2 协议第 5 节，`agents/<host>/<agent-id>/` 目录冲突应取本地（这个 agent 是该目录的 owner）。

### Claude Code 启动后没自动 pull / 没注入上下文

检查 SessionStart hook 是否注册：

```bash
cat ~/.claude/settings.json | grep -A 5 SessionStart
```

如果没有，重跑 installer：`bash scripts/install/claude.sh`。

### 跨机器看到的 agent ID 不一致

检查共享 host 与当前工具的 identity 文件：

```bash
cat ~/.nestwork_host
cat ~/.nestwork_id_codex       # 或 ~/.nestwork_id_claude
```

同一台机器上的每个工具分别拥有 identity 文件。如果带随机后缀的 identity（如 `claude-xxxx`）被复制到另一台机器，请在新机器删除对应工具的文件，让 installer 重新生成。旧版 `~/.nestwork_id` 会自动导入。

### 我想试一下但不想 commit 自己的私有信息到 GitHub

完全本地用：

```bash
git clone git@github.com:songth1ef/nestwork.git ~/local-nest
# 不 push 到任何 remote
```

或者把 remote 改到 self-hosted git：

```bash
git remote set-url origin <你的私有 git>
```

---

## 不做什么（Non-goals）

为了让 nestwork 保持轻量、协议中立、git-only，下面这些明确不在范围内：

- 团队级 ACL / 权限管理：仓库可见性靠 GitHub/GitLab 自身权限，nestwork 不引入额外的访问控制层
- 服务端 API / 同步服务：永远不会加 server，所有同步都靠 git push/pull
- 内建或强制的端到端加密：协议本身不内建加密，private 仓默认依赖 GitHub 安全模型。确有机密性需求时，可选用默认关闭的 git-crypt 模式——见 [docs/encrypted-memory.md](docs/encrypted-memory.md)。API key 等密钥仍不该写进来，用 secret store。
- 实时协作 / 实时通知：git 是异步的；如果两 agent 真的同秒写同文件，靠 PreToolUse hook 阻止，不靠实时锁
- 跨厂商 LLM 调用抽象：蒸馏脚本用 Codex，但不试图统一所有 LLM API。换工具时 agent 自己读 markdown 即可
- GUI / 网页版：纯文件协议，所有交互通过 agent 自己或 git 命令行
- 自动 onboarding / 教程引导：README 是入口，不做交互式向导

如果你需要其中某项，nestwork 可能不适合。选一个对应专门工具更合适。

---

## 协议演进与版本

> 关于 `agent-history-*` 分支：v2.4 引入的孤儿分支，保存高频 artefact（如 `history.jsonl`）的滚动覆盖快照。每个分支只有一个 force-push 的 commit，不应合并到 `main`。GitHub 主页提示 "Compare & pull request" 时直接忽略。详见 [AGENTS.md §12](AGENTS.md)。

- v2.0（2026-04-17）：`agents/` 改为按 host 分组（`agents/<host>/<agent-id>/`），原子逐次写入 hook 架构
- v2.1（2026-04-21）：SessionStart hook 自动注入上下文
- v2.2（2026-05-07）：新增 `workflow/` 上下文层 + `nestwork.config.json` 外部目录吸收契约 + 通用 markdown 拆分规则
- v2.3（2026-05-08）：新增 §10 nestwork 与 repo 5-doc 边界（`projects/<name>.md` 5 字段建议 + `decisions/` 协议级 ADR + `workflow/lessons.md` 跨 repo 教训）；SessionStart hook 增加上游版本自动检测（24h 缓存，仅提醒，绝不自动应用）
- v2.4（2026-05-08）：新增 §12 高频 artefact 的孤儿分支策略。`agents/*/*/local/` 默认 `.gitignore`，由 `agent-history-<host>-<agent-id>` 单 commit 滚动覆盖快照（force-push）。解决启用 `sync_local_history` 后 main 历史无界膨胀（实测 mynestwork 从 177 MB 降到 1.6 MB）。

完整协议规范见 [AGENTS.md](AGENTS.md)。

---

## 相关文档

- [AGENTS.md](AGENTS.md)：协议规范（最权威，agent 启动时读这个）
- [docs/workflow-protocol.md](docs/workflow-protocol.md)：v2.2 workflow 详解
- [docs/desensitization-prompt.md](docs/desensitization-prompt.md)：AI 脱敏方法论
- [docs/encrypted-memory.md](docs/encrypted-memory.md)：用 git-crypt 加密私密记忆（可选）
- [schemas/nestwork.config.schema.json](schemas/nestwork.config.schema.json)：`nestwork.config.json` JSON Schema
- [docs/ai-agent-memory.md](docs/ai-agent-memory.md)
- [docs/claude-code-memory.md](docs/claude-code-memory.md)
- [docs/codex-persistent-memory.md](docs/codex-persistent-memory.md)
- [docs/git-native-memory-protocol.md](docs/git-native-memory-protocol.md)
- [docs/agents-md-best-practices.md](docs/agents-md-best-practices.md)
- [docs/faq.md](docs/faq.md)
- [docs/comparisons/claude-mem.md](docs/comparisons/claude-mem.md)

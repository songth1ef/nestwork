---
title: 记忆蒸馏，怎样合并多个 agent 的记忆
description: 记忆蒸馏把多个 agent 的私有笔记合并成一份经过审核的共享记忆。本文讲什么该进共享记忆、审核流程，以及 distill.py 怎么用。
keywords: 记忆蒸馏, 合并多个 agent 的记忆, memory distillation AI agents, consolidate agent memory, 共享记忆, 智能体长期记忆, distill.py, nestwork
date: 2026-09-27
---

AI agent 的「记忆蒸馏」是什么？就是把多个 agent 各自的私有笔记，变成一份共享记忆的那一步：读遍所有 agent 的记忆，滤掉临时性的内容，检查剩下的有没有敏感信息和互相矛盾，合并，再由人确认，才算进入共享。在 nestwork 里，蒸馏永远是显式触发的、不破坏原始记忆的，而且 `scripts/maintenance/distill.py` 默认只把结果写进工作区等你审，不会自己提交。

下面依次讲：为什么需要蒸馏、什么该进共享记忆、审核流程，以及 `distill.py` 的三种模式。

## 多个 agent 为什么需要蒸馏这一步

每个 agent 只写自己的目录，写入就不会撞车（见[多 agent 共享记忆怎么避免冲突](../multi-agent-memory-without-conflicts/)）。代价是知识会散落各处：笔记本上的 Claude Code 记下你喜欢小步提交；台式机上的 Codex 换了个说法记了同一件事；第三个 agent 记了一条别人都没见过的教训。

每个 agent 都能读所有目录，但每次会话去翻 30 份私有记忆，按需加载就白做了。蒸馏产出一个地方，也就是 `shared/`，存放去重、审核过的跨 agent 稳定事实。它在优先级链里排在私有记忆之上，一条事实一旦被蒸馏进去，所有 agent 都把它当作共同基线。

## 什么该进共享记忆

[AGENTS.md 第 7 节](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md)划了线：

| 该进 | 不该进 |
|---|---|
| 跨 agent 的稳定事实（用户身份、技术栈、偏好） | 临时任务细节 |
| 验证过的协作模式 | 一次性的调试笔记 |
| 有长期影响的决策 | 只和某个 agent 相关的上下文 |

合并时守三条规矩：

- **取并集，不取交集。** 只有一个 agent 观察到的东西也保留，不会因为别人没看到就丢掉。
- **不破坏原件。** 每个 agent 的私有记忆原样不动。蒸馏只读它们，只写 `shared/`。
- **不自动常驻。** 蒸馏结果落在按需层。要不要提升到常驻摘要，是另一个单独的决定。

两条都成立、只是情况不同的观察（比如不同机器上的不同配置），并列保留，不强行合成一条。

## 什么时候蒸馏

只在你要求时。触发方式是人明确发起，或者人自己配置的定时任务。agent 在会话结束时发现值得共享的东西，也**不**直接写 `shared/`，而是记在自己的目录里，等下一次蒸馏来取。这样 30 个 agent 就不会想改共享记忆就改。

## 流程：子 agent 审核 + 人工确认

协议规定的八步：

1. 读所有 agent 的记忆；主题模式的作用域连同主题文件一起读。
2. 读当前的 `shared/`：单文件模式读 `memory.md`，主题模式读索引和所有共享主题文件。
3. 派一个子 agent 审核：敏感信息、事实错误、互相矛盾、过期条目。它只出报告，不写文件。
4. 把审核报告交给人确认。
5. 合并：去重、统一一致的事实、保留有分歧的观察。
6. 历史证据留在按需层；当前摘要里被取代的事实直接替换，并注明来源和范围，而不是无限追加。
7. 主题模式下只写有变化的主题文件，重新生成索引，跑 `memory-index.py --check`。结构性变更（改名、合并、删除、新的顶层目录）在审核报告里单独列出。
8. 用 `memory: distill shared` 提交。

第 3、4 步正是工具默认不提交的原因：结果必须先让人看过。

## `distill.py` 的三种模式

[`scripts/maintenance/distill.py`](https://github.com/songth1ef/nestwork/blob/main/scripts/maintenance/distill.py) 收集所有非空的 agent 记忆，拼出合并提示词。怎么跑取决于参数：

| 模式 | 命令 | 做什么 |
|---|---|---|
| 提示词（默认） | `distill.py` | 打印一份现成的合并提示词，贴进任意 agent 会话 |
| Claude 执行 | `distill.py --run-claude` | 通过 `claude -p` 执行合并并写入结果 |
| Codex 执行 | `distill.py --run-codex [--profile <p>]` | 通过 `codex exec` 执行合并并写入结果 |

两种执行模式互斥，`--profile` 只对 Codex 生效。默认的提示词模式刻意不绑厂商；脚本注释里写着，只绑一家的蒸馏器，订阅一停就跑不了了。

两种执行模式都和 nest 自己的引导隔离开：Claude 执行时不给任何工具、不加载任何设置来源，免得 `CLAUDE.md` 里的启动协议把这次运行变成一份会话启动摘要；Codex 执行时在一个空的临时目录里用只读沙箱。

然后是控制写入的参数：

```bash
python3 scripts/maintenance/distill.py --run-claude --dry-run   # 只打印候选结果，不写
python3 scripts/maintenance/distill.py --run-claude             # 写入 shared/，不提交
git diff -- shared/                                             # 审
git commit -m "memory: distill shared" -- shared/
```

默认不提交，运行结束会提示你先看 `git diff -- shared/` 再提交。加 `--commit` 会在一次运行里完成 pull、写入、以 `memory: distill shared` 提交并推送；再加 `--no-push` 则只在本地提交。只有在你已经接受跳过审核时才用 `--commit`，比如你自己配置的定时任务。`--no-commit` 为兼容仍然保留，但已经没有实际作用。

## 主题模式：只写有变化的主题

如果 `shared/memory.md` 里有主题索引标记（见[记忆按需加载](../topic-memory-on-demand-loading/)），`distill.py` 会自动切到主题模式：

- 各 agent 的主题文件一并作为输入。
- 要求模型只输出有变化或新增的主题文件，每个都完整写在 `<<<FILE shared/<topic>.md` 和 `>>>END` 之间。
- 脚本会拒绝不合法的路径（只允许小写短横线命名、最多一层子目录、不能是 `memory.md` 或 `resident.md`），也拒绝没有 `description` 的文件。
- 写入这些文件后重新生成索引；索引检查有问题就中止。

提示词明确禁止改名、合并或删除主题，那是需要人审的决定。每跑一次都把拆好的 nest 重写回单文件，等于把拆分撤销，这也是纯拼接脚本 `compile.sh` 在主题模式的 `shared/` 上拒绝运行的原因。

单文件模式下，脚本要求结果以 `# SHARED MEMORY` 开头，并在超过 500 行时警告，这是协议给 `shared/memory.md` 定的上限。

## 工具自带记忆也走同一条管线

Claude Code、Codex、Kimi Code 自己的记忆都只存在本机，nestwork 把它们搬进 nest 用的也是蒸馏（[AGENTS.md 第 13 节](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md)）：输入换了，管线不变，照样是读取、过滤、审核、合并、提交。那里的过滤问题是「这条什么时候会失效？」，而且明确禁止原样复制工具的记忆目录，因为重复的内容迟早会各自走样。详见[抢救工具自带的记忆](../rescue-tool-native-memory/)。

## 常见问题

### 蒸馏会删掉各 agent 的记忆吗？

不会。它只读私有记忆、只写 `shared/`，每个 agent 的目录原封不动，随时可以回头看原始观察。

### 能定时自动蒸馏吗？

可以，前提是你自己配置。定时任务一般用 `--run-claude --commit` 或 `--run-codex --commit`，这会跳过人工审核；协议只在你接受这个取舍时才允许这么做。

### `compile.sh` 和 `distill.py` 有什么区别？

`compile.sh` 把各 agent 记忆直接拼接进 `shared/memory.md` 并提交推送，不用模型、不去重。`distill.py` 用模型合并去重，结果留给你审。`shared/` 一旦启用主题记忆，`compile.sh` 就拒绝运行。

### 用提示词模式时，谁来审结果？

你，以及你贴提示词进去的那个 agent 会话。照第 3、4 步做：让子 agent 检查敏感信息、错误、矛盾和过期条目，看完它的报告，再写入并提交。

## 相关阅读

- [多 agent 共享记忆怎么避免冲突](../multi-agent-memory-without-conflicts/)
- [上下文窗口有限，记忆该怎么按需加载](../topic-memory-on-demand-loading/)
- [抢救工具自带的记忆](../rescue-tool-native-memory/)
- [用 git 管理 AI 记忆，为什么不需要服务器](../git-native-agent-memory/)
- [记忆是协议问题，不是数据库问题](../memory-is-a-protocol-problem/)

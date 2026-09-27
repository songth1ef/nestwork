---
title: 换电脑 AI 记忆丢失？迁移工具原生记忆
description: Claude Code 的 auto memory 和 Codex 的 memories 都只存在本机。换电脑、换工具或丢账号之前，如何备份并迁移 AI 记忆。
keywords: 迁移 AI 记忆, 换电脑 AI 记忆丢失, Claude Code auto memory 备份, Codex memories 备份, AI agent 记忆, Claude Code 记忆, nestwork carryover
date: 2026-09-27
---

Claude Code、Codex、Kimi Code 自己记下的记忆都存在本地磁盘上，换新电脑、重装系统或者不再用这个工具时，它们就跟着没了。要保住这些记忆，就得在那之前把仍然成立的内容取出来，放到你自己拥有、有版本记录的地方（比如私有 git 仓库），并且记下每条记录属于哪个项目，方便以后恢复。nestwork 把这件事叫 *carryover*：把原生记忆蒸馏进你 agent 目录下的一个冷文件，而不是整个目录镜像过去。

## 原生记忆存在哪

| 工具 | 原生记忆位置 | 怎么挪 | 跨设备同步？ |
|---|---|---|---|
| Claude Code | `~/.claude/projects/<project>/memory/` | `autoMemoryDirectory` 设置 | 不同步：“Auto memory is machine-local”（[文档](https://code.claude.com/docs/en/memory)） |
| Codex CLI | `~/.codex/memories/`（需手动开启） | 只能用 `CODEX_HOME` 把 Codex 数据整体挪走 | 文档未提同步，存在 Codex home 下（[文档](https://learn.chatgpt.com/docs/customization/memories?surface=cli)） |
| Kimi Code | 运行数据在 `~/.kimi-code/` | 只能用 `KIMI_CODE_HOME` 整体挪走 | 文档未提同步，数据存在本地（[文档](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/data-locations.html)） |

说得最直白的是 Claude Code 文档：auto memory 文件“不会在机器或云环境之间共享”。三家都没有提供把这部分记忆搬到另一台设备的内置办法。

## 三种丢法

nestwork 关于 carryover 的[设计决策](https://github.com/songth1ef/nestwork/blob/main/decisions/2026-07-28-tool-memory-carryover.md)列了三种情况：

1. **换新机器。** agent 学会的构建命令、约定、踩过的坑，新磁盘上一概没有。
2. **工具没了。** 工具会停更、会被替代，或者你自己换了。记忆只存在工具里，工具结束，记忆也就结束。
3. **账号没了。** 记忆绑定在账号而不是磁盘上时，封号、地区限制、订阅到期都可能把它一并带走。

根源都是归属权：你的上下文放在哪、能活多久，由厂商决定。

## 为什么直接拷目录不够

把 `~/.claude` 或 `~/.codex` 拷进 U 盘总比什么都不做强，但有两个问题。

一是恢复不到正确的位置。Claude Code 用工作目录路径命名项目文件夹，把非字母数字字符替换成 `-`（[会话文档](https://code.claude.com/docs/en/sessions)）。同一个仓库在新机器上换了路径或盘符，文件夹名就变了，拷过去的记忆挂不到任何项目上。

二是原样镜像会把所有东西都带过去：重复的条目、过期的进度记录、别处已经记过的事实。同一件事从此存在两处，慢慢就对不上了。

## nestwork 的做法：蒸馏，不镜像

[AGENTS.md §13](https://github.com/songth1ef/nestwork/blob/main/AGENTS.md) 把原生记忆当作现有蒸馏流程的又一个输入：读取、筛选、人工审阅、合并、提交。筛选只问一个问题：**这条什么时候会失效？**

| 什么时候失效 | 放到哪里 |
|---|---|
| 记忆仓库里已经有了 | 跳过 |
| 它自己写明的删除条件已经触发 | 不迁，并建议删掉源头 |
| 变化很快的进度快照 | 不迁，一提交就过期 |
| 只在换机器时失效，且必须不查就生效 | `agents/<host>/<agent-id>/resident.md`，控制在字节预算内 |
| 只在换机器时失效，且只在恢复时用得上 | `agents/<host>/<agent-id>/carryover/<tool>.md` |
| 永不失效（可迁移的方法、跨工具的坑） | `workflow/<topic>.md`，先脱敏 |
| 项目一变就失效 | 那个仓库自己的文档；只提建议，不跨仓库写 |

最容易判断错的是“常驻还是按需”。问自己：这条是否必须在没人去找它的时候也生效？通用的边界规则可能算；本地某个工具怎么装的，不算。常驻文件要争夺很小的启动预算（默认每个 agent 的常驻文件 2,048 字节），拿不准就选按需。

## 冷层，以及目录名问题

`carryover/` 是冷层，会话启动时永远不加载；`memory.md` 可以用一行指向它，但不能把内容内联进来。只有在新机器上恢复、或者专门查某件事时才读它。

因为项目文件夹名来自路径，每条 carryover 记录都要同时写下原目录名和它对应的仓库：

```markdown
## <一句话标题>

- **source**: `~/.claude/projects/<project-dir>/memory/<file>.md`
- **original project dir**: `<project-dir>` (repository: `<repo path>`)
- **carried on**: YYYY-MM-DD
- **criterion**: cold — needed only on restore

<正文，保留原来的 Why / How-to-apply 结构>
```

恢复时，按新机器上仓库的路径重新算出文件夹名，再把内容写回去。这是唯一一个流回工具原生存储的步骤，而且是手动的。

## 迁移步骤

1. 先在这台机器上为该工具安装 nestwork（例如 `bash ~/nestwork/scripts/install/claude.sh`），让你的 agent 目录存在。
2. 列出工具里有什么：Claude Code 看 `~/.claude/projects/*/memory/`，Codex 看 `~/.codex/memories/`。
3. 让 agent 按 §13 蒸馏：用上表给每条归类，起草 `carryover/<tool>.md` 和可能的常驻条目。
4. 亲自审一遍草稿，去掉敏感内容；API key 和密钥永远不进记忆仓库。
5. 让它提交。Claude Code 的逐次写入 hook 会立刻推送；Codex 则由 agent 执行启动协议里的提交步骤。
6. 确认记忆仓库里已经有了，再决定要不要删源头。原生记忆不在版本控制下，删了就找不回来。

如果你更想要实时副本而不是定期蒸馏，Claude Code 可以把 `autoMemoryDirectory` 指到你的 agent 目录。§13 允许这样做，但只作为本地选择而非默认：只有部分工具支持，每次写入都会变成一次提交，审阅环节也没了。

## 常见问题

### 直接拷文件夹能备份 Claude Code 的 auto memory 吗？

能，重装之前做一下很值得。只是要记下每个项目文件夹对应的仓库路径，因为文件夹名是从这个路径算出来的，新机器上仓库放在别处，名字就不同。

### nestwork 会自动同步我的原生记忆吗？

不会。日常流向是单向且有意为之的：你决定时，把原生记忆蒸馏进记忆仓库。不会有任何东西自动写回工具的存储。

### 为什么 carryover 不进启动上下文？

因为它大多只在恢复时有用。每次会话都加载，就会把启动预算浪费在“某工具怎么装的”这类记录上，挤掉真正每次都要生效的规则。

### Codex 的 memories 怎么迁？

直接读 `~/.codex/memories/` 下的文件，把有价值的蒸馏进 `carryover/codex.md` 或你的常驻文件即可。OpenAI 自己也建议把必须遵守的规则写进 `AGENTS.md`，而不是依赖 memories。

## 相关阅读

- [Claude Code 记忆跨设备同步](../claude-code-memory-across-machines/)
- [给 Codex CLI 加长期记忆](../codex-cli-persistent-memory/)
- [记忆蒸馏](../memory-distillation/)
- [用 git-crypt 加密 agent 记忆](../encrypt-agent-memory-git-crypt/)
- [长期记忆的实践](../long-term-memory-in-practice/)

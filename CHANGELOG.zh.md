# 更新日志

[English](CHANGELOG.md) | 中文

记录 nestwork 协议与代码的所有变更。**长期维护**。

格式约定：

- 倒序排列，最新版本在最上面
- 每个版本：`## vX.Y.Z - YYYY-MM-DD`
- 条目按性质分类：协议变更（Protocol） / 新增（Added） / 变更（Changed） / 修复（Fixed） / 废弃（Deprecated） / 移除（Removed）
- 协议变更必须显式标注 `Protocol vX.Y` —— `MAJOR.MINOR`，MAJOR 升级要求下游动作，MINOR 是 additive 兼容
- 私有数据保护：所有变更不应破坏 `agents/` `queen/` `shared/` `projects/` `workflow/<topic>.md` 的私有内容

---

## Unreleased

### 文档修正（协议 3.0）

- 校准中英文 README 的版本历史、升级说明和保存/加载区别；v0.6.0 软件版本与 3.0 协议版本独立编号。
- 修正 Claude/AGENTS.md 指南、邮箱文档、常驻结转表、限制覆盖示例和获客博客的旧启动行为。邮箱快照仍刷新，但仅按需读取。
- 补充文档一致性检查，保护当前协议说明、常驻路径、迁移步骤及邮箱读取层级。

### Protocol v3.0 — resident / on demand

- Startup reads core rules and optional shared/agent `resident.md` only. Existing memory, strategy, projects and workflows remain on demand; no automatic legacy fallback.
- Reinstall the marked tool bootstrap after updating scripts. See `docs/context-loading.md` for migration and byte-budget checks. Historical data is preserved.
- Memory write limits explicitly apply inside Nestwork, not user project artifacts. Current tasks no longer require unrelated status reports.


### Protocol v2.5

- **工具原生记忆结转（AGENTS.md §13）。** 每个编码 agent 都维护自己的记忆，而截至 2026-07 **全部是机器本地的**——Claude Code（`~/.claude/projects/<project>/memory/`，官方文档原话「不跨机器、不跨云环境共享」）、Codex（`~/.codex/memories/`）、Kimi Code（`~/.kimi-code/`）。这让积累的上下文有三条失效路径：换台机器从零开始、工具停服时记忆随之消失、账号级记忆随账号丢失（停用、区域限制、订阅到期）而消失。**共同根因是「归属」**——厂商决定你的上下文存在哪、能活多久，而 nestwork 在上一层已经解决了同一个问题。新增保留路径 `agents/<host>/<agent-id>/carryover/<tool>.md`，接收经 §7 流程（读取 → 判据过滤 → 人审 → 合并 → 提交）**蒸馏**过的工具原生记忆，**不是原样镜像**——原样镜像会把重复条目和已过期的笔记一起搬进来，制造 §2 明令禁止的「同一记忆两份」漂移。`carryover/` 是**冷层**：绝不在会话启动时注入，`memory.md` 至多用一行指针引用它。分诊按「这条什么时候不再成立？」归类，并显式区分冷热——**必须在没人主动去查的情况下也生效**的条目进 `memory.md`，其余进 `carryover/`。每条记录同时保存原 project 目录名**与**其对应仓库，因为部分工具由仓库绝对路径推导该目录名，换台机器就对不上。Additive：不改动任何既有路径、hook 或优先级链行为。取舍与被否方案见 `decisions/2026-07-28-tool-memory-carryover.md`。

### 新增（Added）

- **`distill.py` 新增第二个 runner：`--run-claude`（`claude -p`），与 `--run-codex` 并存。** 蒸馏是一个 agent 的记忆抵达另一台机器的**唯一**通道，而它此前绑死在单一厂商的 CLI 上——那家订阅一到限额，某私有实例的 weekly distillation cron 就静默失败，`shared/memory.md` 停更 **49 天**，期间整整一台新机器的记忆无人知晓。两个 runner 互斥，各读各的 `NESTWORK_DISTILL_{CLAUDE,CODEX}_MODEL`，`--profile` 仍只对 Codex 生效（与 Claude 同用会告警，而不是静默忽略）。**Codex 通道原样保留**——修自己这边的断供，不该顺手替 codex 用户做减法。Claude runner 固定带 `--tools '' --setting-sources ''`：不带这两个，distiller 会加载 nest 自己的 CLAUDE.md 启动协议，输出变成会话摘要而不是 `shared/memory.md` 候选——现象看起来像「LLM 答非所问」而不是「少了个 flag」，因此写进了测试断言。
- **`docs/limits-override-example.md`**——下面那条「每实例行数上限覆盖」的「照抄我」模板。agent 读的是 `queen/limits.md`，复制是一个显式动作。**刻意 ship 成示例而不是生效文件**：若每个实例都带一份生效的 `queen/limits.md`，等于把该实例的数值就地冻结，而 `update.sh` 永不触碰 `queen/`，日后 §6 协议默认值的调整就再也传不到它。**放在 `docs/` 而不是 `queen/` 则是同一枚硬币的反面**——`docs/` 是 `update.sh` **会**同步的，所以默认值演进时这份示例能持续送达，而 `queen/` 完完全全归用户所有。内含「按检索质量而非上下文窗口容量调参」的理由，以及一份调参日志，好把有意调整和随手误改区分开。
- **`scripts/uninstall/` 按工具卸载器**——与 `scripts/install/` 镜像（claude / codex / gemini / hermes / openclaw / generic，`.sh` + `.ps1` 双版本）。卸载**只解除绑定**：从工具启动文件移除 bootstrap 标记块、摘掉 nestwork 注册的 hooks（Claude settings.json、Codex hooks.json）。记忆（`agents/<host>/<agent-id>/`）、身份文件（`~/.nestwork_host`、`~/.nestwork_id_<tool>`）及标记块之外的用户内容一概不动；重装即以原身份恢复。可选 `--purge-identity` / `-PurgeIdentity` 连同该工具 agent id 一起清除。共享助手 `_unbootstrap.py` / `_unhooks.py` / `_codex_unhooks.py` 复用安装器自身的匹配逻辑——安装器会覆盖替换的条目，卸载器就能移除。配套 `tests/test_uninstall.py` 往返测试（install → uninstall 保留用户内容与用户 hooks）。
- **每实例文件行数上限覆盖（`queen/limits.md`）。** 私有实例无需改协议层即可覆盖 AGENTS.md §6 的默认限制表——新建 `queen/limits.md` 写自己的表；存在时它有权威，agent 会话启动即加载（高优先级 `queen/` 层），且 `update.sh` 永不触碰 `queen/`，覆盖能扛过协议更新。Additive，不 bump protocol-version。调参按检索质量、不按上下文窗口容量。（AGENTS.md §6 + README「文件行数限制」节。）
- **`scripts/comms/archive.sh`** —— 把发件人自己 outbox 里超过 N 天（默认 30）的旧消息移入 `outbox/archive/`，让 `read.sh` 的扫描成本随时间保持有界。移动后自动 commit + push。
- **端到端测试**：v2.4 孤儿分支快照（`tests/test_snapshot_local_orphan.py`）、agent 邮箱（`tests/test_comms.py`）、`compile.sh` 内容保真（`tests/test_compile.py`）。
- **原子 per-write hook 端到端测试**（`tests/test_nestwork_hook.py`）：pre 快进拉取、pre 在分叉冲突时阻断（exit 2）、autostash 残留防护、post commit+push、远端并发推进后的 push 重试路径、post 忽略非 agent 路径、Stop 安全网（脏/干净两种状态）。
- **优先级链一致性测试**：所有 markdown 文件中出现的优先级链必须完整展示六层，杜绝局部副本再次悄悄过期。
- **ADR：GEO 文档重复策略**（`decisions/2026-06-11-geo-docs-duplication-with-drift-tests.md`，proposed）——保留 README/AGENTS/docs stub 间的刻意重复，用「从单一事实源推导期望值」的一致性测试控制漂移，而不是去重或引入构建步骤。

### 变更（Changed）

- **README 从 933 行减到 769 行（英文）、930 减到 768（中文）。** 有五节是在把协议**第三次**讲一遍——目录结构、文件行数限制、编译共享记忆、Agent 邮箱、`workflow/` 深入说明——而 `AGENTS.md` 和对应的 `docs/` 页早就更详细地写着同样的内容（`docs/agent-mailbox.md` 有 144 行，README 那节只有 32 行）。现在各留一段摘要 + 指针。**GEO 重复策略未受影响**：没有删除任何内容，每个主题的自包含页面仍在它该在的那一处。目的是可维护性而非篇幅——加 §13 时要改 7 个文件 10 处，而那份重复策略 ADR 预算的是「大约五处」；这次收回到 `AGENTS.md` + 镜像 + 两份 CHANGELOG。
- **退役 README 里的版本切片章节。** 90 行的「v2.2 新增：workflow/ 与 nestwork.config.json」熬过了三个协议版本，导致读者看到 v2.2 被当成最新的东西，而 v2.3–v2.5 都没有对应节。内容已挪到常设的「上下文层」标题下；版本切片属于本文件。新增测试 `test_readmes_have_no_version_scoped_sections` 拒绝以后再出现 `## vX.Y 新增` 这类标题。
- **两份 README 的目录树已修正。** 它已经漂了：`agents/*/carryover/`、`decisions/`、`tests/`、`scripts/comms/` 全都缺失，逐文件罗列的脚本清单也旧到会误导。现在展示全部顶层分层，并在 agent 目录上标出冷热区分。

### 修复（文档）

- **Kimi Code 在整个答案引擎面上是缺失的。** 它 2026-07-21 就作为安装器发布了，却只出现在 README 正文里——两份 README 的工具 badge、`llms.txt`、`docs/README.md`、`docs/ai-agent-memory.md`、`docs/shared-context-for-ai-coding-agents.md`、`docs/faq.md` 全都还在宣传一份没有它的清单。这正是 GEO 重复策略 ADR 预言过的漂移，而且发生在**过期副本危害最大的那一处**。新增测试 `test_advertised_tool_list_covers_every_installer` 从 `scripts/install/*.sh` 反推期望清单，以后发布新工具却不更新文档会让测试变红，而不是默默向答案引擎提供错误信息。

- **邮箱投递自包含。** `send.sh` 现在自己 commit + push 消息（带 rebase 重试），不再依赖 per-write hook——那些 hook 只匹配 Write/Edit 工具调用，经 Bash 调用的发送从来不会被自动提交，非 Claude 工具链更是没有任何兜底 hook。文档已改为描述真实机制。
- **邮箱已读状态移到被 git 忽略的 `local/comms/seen.txt`。** 标记已读不再在 `main` 上产生提交。旧版已提交的 `comms/seen.txt` 首次读取时自动导入，之后可 `git rm`。
- **CI 同步范围与 `update.sh` 对齐。** `sync-upstream.yml` 的 `PROTOCOL_PATHS` 之前只同步 scripts/AGENTS/CLAUDE/SOUL/README，`docs/`、`schemas/`、CHANGELOG 和 workflow/projects/decisions 模板从未经 CI 传播；现在两份清单一致（CI 仍排除 `.github/workflows/`——GITHUB_TOKEN 无法推送 workflow 文件），且双方都新增了 `VERSION` 与 `llms.txt`。
- `export-claude-mem.sh` 改为通过 argv 向 Python 传递 worker URL 和日期，不再做 heredoc 内的 shell 插值，杜绝用户可控的 `CLAUDE_MEM_URL` 注入脚本的可能。
- **安装脚本加固。** 所有 `scripts/install/*.sh` 改用 `set -euo pipefail`，且当身份解析未返回两行非空输出时报错退出（之前解析失败会静默产生 agent-id 为空的 `agents/<host>/` 路径）。`.ps1` 安装脚本对解析输出强制数组上下文（单行结果之前会按*字符*而非按行索引）并校验行数与非空。
- `update.sh` 改用 `git diff --quiet` 检测协议层漂移（不再把完整 diff 捕获进变量），并按路径逐个应用上游文件——某个文件在上游缺失时跳过并提示，而不是让整次更新中途中断。
- **`sync_local_history` 脱敏改为递归覆盖所有字符串字段。** 之前只处理 `project` 和 `display` 两个字段；history.jsonl 的 schema 因工具/版本而异，其他字段里的 token 会原样通过。`pastedContents` 仍整体丢弃。
- `distill.py --run-codex` 失败时输出 Codex 自身的 stderr 和实际使用的 flag 列表，不再只给一个裸的 `CalledProcessError` 字符串——之前 Codex CLI 版本间的 flag 不兼容无法定位。

### 修复（Fixed）

- **`distill.py` 在非 UTF-8 locale 上被中文记忆直接打死。** 两个 runner 都只用 `text=True` 捕获子进程输出，而它按**本地编码**解码——zh-CN Windows 上就是 GBK，agent 记忆天然多非 ASCII，于是整个 run 在解析候选之前就抛 `UnicodeDecodeError`。现已双双钉死 `encoding="utf-8", errors="replace"`。本地复现过：让 runner fixture 输出中文，改前必崩、改后通过。
- **Kimi Code 装完等于没装：上下文一条都没加载。** `scripts/install/kimi.{sh,ps1}` 把 bootstrap 块写进了 `~/.kimi-code/NESTWORK.md`——而 Kimi Code 根本不读这个文件名。它的指令文件只有两个：`$KIMI_CODE_HOME/AGENTS.md`（用户级，默认 `~/.kimi-code/AGENTS.md`）和 `<project>/AGENTS.md`。所有可见信号都显示安装成功：脚本打印 OK、hooks 注册并正常触发（SessionStart 拉取、逐次写入同步、Stop 兜底）、`git pull` 也按时在跑——但 agent 每次会话都是零 nestwork 上下文启动。Kimi Code 又不支持从 hook 注入上下文（hook 只能返回权限决策），所以那个文件是唯一通道，而它是静默失效的。安装脚本现在写入 `AGENTS.md`，并清理旧版 `NESTWORK.md` 里的残留块（标记之外的用户内容原样保留）；卸载脚本两个文件都清。新增测试 `test_installer_entry_file_matches_readme_and_uninstaller`：入口文件从各安装脚本自己的 `_bootstrap.py` 调用推导，要求 README「支持的工具」表那一行**和**对应卸载脚本都与之一致——此前 README 宣传的是同一个错误路径，两份副本互相印证着一个已经失效的功能，而硬编码断言只会给这种一致性盖章。已安装用户：重跑 `bash scripts/install/kimi.sh`（或 `.\scripts\install\kimi.ps1`）。
- **`update.sh` 不再把上游明文提交进 git-crypt 加密的 nest。** `git checkout <tree-ish> -- <path>` 会把上游 blob 原样写进 index、绕过 clean filter——全仓加密的实例跑一次更新，提交里全是上游明文。应用步骤现在对协议路径补跑 `git add --renormalize` 重过 clean filter（未加密实例为 no-op）。
- **`compile.sh` 不再损坏记忆内容。** 之前用 `printf "%b"` 输出，会把 agent 记忆正文里的反斜杠序列（`\n`、`\t`、`C:\temp`、正则）当转义解释；现在内容原样直通。头部剥离不再假设固定 3 行头，也不再把安装模板的第二行 blockquote 泄漏进 `shared/memory.md`。
- **pre-write hook 的 autostash 防护。** `git pull --rebase --autostash` 在 stash 回放冲突时仍然 exit 0——git 把未提交改动留在 stash、工作树复位为干净，随后的 Write 会把它静默覆盖。hook 现在检测 stash 残留条目（与 locale 无关）并阻断写入、给出恢复提示。
- **发布元数据对齐；测试套件恢复绿色。** `VERSION` 与 README 版本行停在 v0.3.0 而 CHANGELOG 已发布 v0.6.0，且 `test_docs_consistency.py` 仍断言 `Protocol: 2.1`——套件之前是红的。该测试现在从 `VERSION` + `AGENTS.md` 推导版本/协议期望（不再硬编码易漂移的值），并强制 CLAUDE.md 为 AGENTS.md 的字节级镜像。
- AGENTS.md §9 补充 `desensitize.placeholder_overrides` 字段说明（schema 中已存在但字段表缺失）；§11 把 upstream 检查缓存路径更正为 hook 实际使用的 `~/.cache/nestwork/upstream-check`。
- `docs/git-native-memory-protocol.md` 与 `docs/shared-context-for-ai-coding-agents.md` 中自 v2.2 起过期的 5 层优先级链补上 `workflow/*.md`；清理 `docs/workflow-protocol.md` 中失效的「(to be added in a later step)」占位语；`session-start.sh` 不再自称不存在的协议 v2.5。
- 英文 CHANGELOG 的 v0.3.0 条目重排为与中文一致的结构（显式 `Protocol v2.1` / `Compatibility` 标题），内容不变，符合本文件自身的双语对齐约定。

## v0.6.0 - 2026-05-08

### Protocol v2.4

为"高频追加 + delta 压缩极差"的 artefact（典型：启用 `sync_local_history` 后的 `history.jsonl`）提供独立的存储路径，避免主仓 history 无界膨胀。

- **AGENTS.md §12 新增** —— 高频 artefact 走 per-agent 孤儿分支
  `agent-history-<host>-<agent-id>`：每次写入通过 `git commit-tree` +
  `git update-ref` 重建为单 commit（无 parent）force-push 覆盖前一次快照。
  分支命名天然单写者（host + agent-id），force-push 永不冲突。
- **`agents/*/*/local/` 默认 `.gitignore`** —— main 不再吸收高频 artefact，
  备份完全走孤儿分支。
- **新增 `scripts/hooks/snapshot-local-orphan.sh`** —— 快照构建脚本，
  使用 `GIT_INDEX_FILE` 临时索引避免污染主工作树；只有 tree hash 变化时
  才创建新 commit；force-push 失败不阻塞 agent。
- **`scripts/hooks/sync-local-history.sh` 在 python sync 后自动 invoke
  snapshot 脚本** —— 用户无需任何配置改动；启用 `sync_local_history` 即
  享受新机制。
- **跨机恢复**：`git fetch origin agent-history-<host>-<agent-id>` →
  `git restore --source=...`，单条命令。

### 实测效果

下游实例 mynestwork 在启用 `sync_local_history` 半个月后 .git 膨胀到 177 MB
（411 个 history.jsonl commit）。通过 `git filter-repo` 清理历史 + 改用本机制
后，仓库降到 1.6 MB（**-99%**），备份完整保留在 4 个孤儿分支上。

### 新增

- `scripts/hooks/snapshot-local-orphan.sh`

### 变更

- `scripts/hooks/sync-local-history.sh` —— 末尾追加对 snapshot 脚本的调用
- `.gitignore` —— 加 `agents/*/*/local/`

### 升级提示（私有实例）

升级到 v2.4 后，新写入的 `local/` 自动走孤儿分支，main 不再增长。**已存在的
历史膨胀需要手动清理一次**：
1. `pip install git-filter-repo`
2. `git filter-repo --path-glob 'agents/*/*/local/*' --invert-paths --refs main --force`
3. `git push origin main --force`
4. `git gc --aggressive --prune=now`

destructive 操作前请备份 `.git`。

---

## v0.5.0 - 2026-05-08

### Protocol v2.3

新增"nestwork 与 repo 5-doc 边界"以及"上游版本自动检测"，澄清跨 repo 与 repo 内职责，让下游能被动感知协议演进。

- **AGENTS.md §10 新增** —— 明确 nestwork（跨 repo 协调层）与每个 repo 内 5-doc 骨架（`AGENT.md` / `docs/conventions.md` / `docs/domain.md` / `docs/architecture.md` / `docs/lessons.md`）的分工边界。判断标准："换雇主后还在吗" → 在 → repo；不在 → workflow/。
- **`projects/<name>.md` 5 字段建议**（§10.1）—— `Current Goal` / `Current State` / `Next Action` / `Do Not` / `Last Verified`。建议非强制，模板：`projects/_template.md`。
- **`decisions/` 协议级 ADR**（§10.2）—— 仅记录关于 nestwork 自身或协议的决策（项目级 ADR 留 repo）。文件命名 `YYYY-MM-DD-<slug>.md`。模板：`decisions/_template.md`，说明：`decisions/README.md`。
- **`workflow/lessons.md` 跨 repo 教训**（§10.3）—— repo 级 `docs/lessons.md` 走 5-doc；跨 repo 可迁移的教训蒸馏到此。upstream 不发货此文件，按需自建。
- **AGENTS.md §11 新增** —— SessionStart hook 增加上游版本自动检测：24h 缓存、3 秒超时、网络失败静默跳过、仅在 upstream MAJOR.MINOR 大于 local 时通过 context bundle 提醒；用户始终可控，**绝不自动应用**。

### 新增

- `projects/_template.md` —— 5 字段项目快照模板
- `decisions/_template.md` —— 协议级 ADR 模板
- `decisions/README.md` —— 协议级 ADR 范围、命名、状态生命周期说明

### 变更

- `scripts/hooks/session-start.sh` —— 加上游版本检查（advisory only）
- `scripts/maintenance/update.sh` —— PROTOCOL_FILES 加入 `projects/_template.md` / `decisions/_template.md` / `decisions/README.md`

---

## v0.4.0 - 2026-05-07

### Protocol v2.2

新增"工作流上下文层"与"外部目录吸收契约"，支持把跨项目可迁移的用户级知识沉淀进 nest，并定义雇主目录如何安全地被 agent 吸收。

- **新增 `workflow/` 顶级目录** —— 跨项目可迁移的工作流知识（编码纪律、工具偏好、方法论、迁移指南）。优先级最低，详见 `AGENTS.md` 第 8 节。
- **新增 `nestwork.config.json` 契约** —— 外部工作目录通过此文件声明吸收规则与脱敏级别，文件**只放在源目录、永不进 nest 仓**。详见 `AGENTS.md` 第 9 节。
- **通用 markdown 拆分规则** —— 任意 md 文件超限后按统一模式拆：原文件名变文件夹，原文件变索引（或 `<folder>/index.md`）。未列入限制表的文件按默认（软限 500 / 硬限 1000）。详见 `AGENTS.md` 第 6 节。
- **优先级链扩展** —— `queen/agent-rules.md > queen/strategy.md > shared/memory.md > agents/*/*/memory.md > projects/*.md > workflow/*.md`。

### 新增

- `docs/workflow-protocol.md` —— `workflow/` 完整规则与三层模型说明
- `docs/desensitization-prompt.md` —— AI 脱敏提示词模板（仅方法论，无具体名词）
- `schemas/nestwork.config.schema.json` —— `nestwork.config.json` 的 JSON Schema
- `workflow/README.md` + `workflow/_template.md` —— workflow 目录骨架
- `CHANGELOG.zh.md`（本文件）—— 中文维护的更新日志

### 变更

- `update.sh` 同步范围加入 `docs/`、`schemas/`、`workflow/README.md`、`workflow/_template.md`；**不动**用户私有 workflow 内容
- `README.md` / `README.zh.md` 加 workflow/ 章节、目录树更新、文件大小表加 workflow 行
- `AGENTS.md` 与 `CLAUDE.md` 同步升级到 protocol-version 2.2

### 兼容性

- Additive 兼容。已有 agent 不需要做任何动作。
- 老版本协议（v2.1）的私有仓可以选择性 pull v2.2 协议层，私有数据零影响。

---

## v0.3.0 - 2026-04-22

### Protocol v2.1

拆分 Stop hook 工作量，新增 SessionEnd hook。

- Stop 只跑轻量的 `nestwork.sh stop`（安全网 commit+push）
- `export-claude-mem.sh` + `sync-local-history.sh` 移到新的 SessionEnd hook，仅在真正会话结束时跑一次，不再随 `/clear`、resume、compact 重复执行
- `_hooks.py` 注册新的 `SessionEnd` 事件；已有安装在重跑 installer 时自动迁移（`is_nestwork_hook` 识别并清理旧的 Stop 复合命令）

### 兼容性

- Additive 兼容。已有 agent 继续工作直到下次重跑 installer。

---

## v0.2.0 - 2026-04-19

### Protocol v2.0（重大变更）

引入 host/agent 嵌套布局：`agents/<host>/<agent-id>/`。

### 新增

- 完整 installer 矩阵：Claude Code、Codex CLI、Gemini CLI、OpenClaw、Hermes Agent，以及通用 markdown-config 工具
- Codex Windows session hook 在 Windows PowerShell 5.1 下的健壮性
- AI agent memory 搜索的 GEO 内容、`llms.txt`、面向回答的 GitHub 文档
- Installer 语法、身份迁移、协议文档、GEO 内容资产的测试

### 变更

- 身份持久化对齐 protocol v2 的双行 `~/.nestwork_id` 格式

---

## v0.1.0 - 2026-04-17

### 首版

- 创建初始 nestwork 协议模板
- `queen/`、`agents/`、`shared/`、`projects/` 仓库布局
- 通过 `AGENTS.md` 和 `CLAUDE.md` 提供启动指令

---

## 维护约定

### 谁来更新

- 协议变更（AGENTS.md 第 8/9 节、`protocol-version` 等）→ 必须更新
- 新增脚本、新增配置文件 → 必须更新
- 文档纯措辞修订、typo 修复、个别注释 → 不更新
- 私有实例（如 `mynestwork`）的同步操作 → 不更新（这里只记 upstream 协议演进）

### 何时升 MINOR vs MAJOR

- MINOR（如 v2.1 → v2.2）：新增可选字段、新增目录、新增 hook 事件、新增配置文件，**已有 agent 不动作仍可继续工作**
- MAJOR（如 v2.0 → v3.0）：目录布局变化、agent-id 格式变化、hook 契约 breaking、`nestwork.config.json` schema breaking

MAJOR 升级**应避免**。如果非升不可，必须给下游迁移路径与至少一个 MINOR 版本的过渡期。

### 何时打 tag / 发 release

- 每次 MINOR 升级 → 打 git tag `v0.x.0`，发 GitHub Release，CHANGELOG 链接 release notes
- patch（仅修 bug、不动协议）→ 累积到下次 MINOR 时一起发，不单独打 tag

### 中英文同步

- `CHANGELOG.zh.md`（本文件）与 `CHANGELOG.md` **应保持同步**
- 任何一方更新时另一方也更新（信息内容相同，措辞独立优化）

# Project: hivequeen

## 一句话
git 原生的 AI agent 上下文协议。Use this template 即继承，clone 即连接，所有 agent 共用同一个大脑。

## 仓库
https://github.com/songth1ef/hivequeen

## 技术栈
Shell / PowerShell / Markdown / git

## 核心架构
- `queen/` — 只读规则层，人工维护
- `agents/<host>/<agent-id>/` — 每个 agent 独占写入目录，降低正常记忆写入冲突
- `shared/` — 从所有 agent 编译而来的共享记忆
- `projects/` — 当前文件所在，项目级上下文

## 分发模型
用户 Use this template → clone 到任意机器 → 运行 install 脚本 → 自动接入母体

## 当前状态
核心协议已实现，安装脚本覆盖 Claude Code + Codex（macOS/Linux/Windows）

## 待完成
- [x] Gemini CLI 安装脚本
- [x] compile.sh 的 LLM 提炼版本（目前是 `scripts/maintenance/distill.py`）
- [x] 更多工具的软链接安装支持

## 设计约束
- 不做中心化服务，不引入外部依赖
- agent 只能写 `agents/<自己的host>/<自己的id>/`，不得写 `queen/` 或 `shared/`
- 文件超过行数限制时必须拆分为 topic 文件 + 索引

## 竞品对比关键点
现有方案（claude-mem、DiffMem 等）都是插件思维，hivequeen 是协议思维。
唯一同时具备：git session 同步 + 分层优先级规则 + 多工具支持 + template 分发模型。

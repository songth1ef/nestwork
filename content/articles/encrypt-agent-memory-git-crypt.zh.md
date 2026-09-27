---
title: AI 记忆加密：用 git-crypt 保护 agent 记忆
description: 用 git-crypt 加密放在 git 里的 AI agent 记忆：本机读写明文，托管平台只存密文。附实测步骤、主题记忆规则和局限。
keywords: AI 记忆 加密, git-crypt 使用, agent 记忆 隐私, 私有 AI 记忆, git-crypt 教程, nestwork
date: 2026-09-27
---

**AI agent 的记忆放在 GitHub 的 git 仓库里，怎么保证别人读不到？** 只对记忆文件启用 git-crypt。agent 在你的机器上照常读写明文，文件在 commit 时被自动加密，托管平台上存的是密文。nestwork 把它写成一个可选、默认关闭的模式，步骤已在 git-crypt 0.8.0 上实测过。

动手之前要先知道它管不到什么：提交信息和文件名仍是明文；钥匙丢了记忆就没了；已经 push 过的明文会留在历史里，除非改写历史；模型服务商照样看得到明文。下面一条条说。

## 先判断：你真的需要加密吗？

nestwork 默认把记忆作为 Markdown 存在私有仓库里，对大多数人已经够了。[加密记忆文档](https://github.com/songth1ef/nestwork/blob/main/docs/encrypted-memory.md)对「什么时候不该用」说得很直接：

| 你担心的是 | 正确做法 |
|---|---|
| 记忆里有私密内容，既要多机同步，又不能让托管方读到 | git-crypt，只加密少量文件 |
| 私密内容不需要同步 | 干脆不提交，放在本地不同步的目录 |
| 仓库丢失、账号被封 | 备份和镜像；加密对可用性毫无帮助 |
| 没有真正的隐私顾虑 | 保持关闭，别凭空多出一把钥匙这个单点 |

nestwork 作者自己就是这么用的：仓库是自己建的私有仓库，「更深的秘密再叠一层 git-crypt」，落到 GitHub 上的是密文（见[《16 个 agent 共用一个大脑》](../16-agents-one-brain/)）。

## git-crypt 使用步骤：给 nest 开启加密

在仓库根目录执行。第一步是备份，因为后面几步出错时往往悄无声息。

```bash
# 0. 完整备份（回滚用）
git bundle create ~/repo-pre-crypt.bundle --all
cp -a . ~/repo-dir-backup

# 1. 安装 git-crypt
brew install git-crypt          # Debian/Ubuntu: apt-get install -y git-crypt

# 2. 用默认 key 初始化（不要加 -k <name>）
git-crypt init

# 3. 把 key 导出到仓库之外，永远不要提交它
git-crypt export-key ~/myrepo-gitcrypt.key

# 4. 声明哪些文件加密（单文件记忆的写法）
printf 'shared/memory.md filter=git-crypt diff=git-crypt\nagents/**/memory.md filter=git-crypt diff=git-crypt\n' > .gitattributes

# 5. 重新 add 触发加密，然后提交
git add .gitattributes shared/memory.md $(find agents -name memory.md)
git commit -m "security: encrypt memory files with git-crypt"

# 6. 确认存进去的是密文
git cat-file -p HEAD:shared/memory.md | head -c 12 | od -c   # 应看到 \0 G I T C R Y P T \0
```

`.gitattributes` 本身必须是明文，git 要读它。git-crypt 官方也提醒：这些规则要在添加敏感文件**之前**就位（[git-crypt README](https://github.com/AGWA/git-crypt)）。

其他机器 clone 之后，执行一次：

```bash
git-crypt unlock /path/to/myrepo-gitcrypt.key
```

之后完全透明：nestwork 的 hook 照常 pull、commit、push；clean filter 是确定性的，同样的明文得到同样的密文，不会冒出无意义的 diff。

## 主题记忆：加密整个目录，而不只是索引

上面的规则假设每个作用域只有一个 `memory.md`。协议 3.1 允许作用域改用主题记忆：`memory.md` 只是一份生成的索引，事实写在 `shared/<topic>.md` 这类文件里，而这些文件按上面的规则会留在明文。改成覆盖整个目录：

```gitattributes
shared/** filter=git-crypt diff=git-crypt
agents/** filter=git-crypt diff=git-crypt
```

`**` 匹配任意层级，所以主题子目录、每个 agent 邮箱的 `outbox/` 也都在内。这一点用 git-crypt 0.8.0 验证过：两个目录下的每个文件都以 `GITCRYPT` 密文存储，目录外的文件保持明文。改完之后，对任一主题文件再跑一遍第 6 步的检查。

两个实际后果：

- `scripts/maintenance/memory-index.py` 和 `distill.py` 读的是工作区，只能在已解锁的 clone 上跑；没解锁时它们读到的是密文。
- `agents/**` 加密后，会话启动时加载的每个 agent 的 `resident.md` 也被加密了。所以每台跑 agent 的机器都必须解锁，否则 agent 一启动拿到的就是读不懂的上下文。

## 文档里点名的三个坑

1. **命名 key 会静默失效。** `git-crypt init -k <name>` 配置的 filter 叫 `git-crypt-<name>`，和 `.gitattributes` 里的 `filter=git-crypt` 对不上。看起来一切正常，存进去的仍是明文。单 key 场景必须用不带参数的 `git-crypt init`。
2. **`git show` 会骗人。** 在已解锁的 clone 上，`git show`、`git diff` 会经过 filter 显示明文。验证密文只能用 `git cat-file -p` 看原始 blob。
3. **改写历史后丢失 upstream。** 改写历史（见下一节）后分支失去 upstream 跟踪，nestwork 写入前的 `git pull --rebase` 失败，所有记忆写入都会被拦下。在执行改写的那台机器上跑 `git branch --set-upstream-to=origin/main main` 即可。

## 明文已经 push 了？只能改写历史

`git-crypt init` 只保护之后的提交。之前提交的内容，在托管方的历史里依然可读。要清掉就得改写历史，比如用 [git-filter-repo](https://github.com/newren/git-filter-repo)：

```bash
git-filter-repo --force --invert-paths --path shared/memory.md --path-glob 'agents/*/*/memory.md'
git remote add origin <url>                      # filter-repo 会删掉 remote
git push --force origin main
git branch --set-upstream-to=origin/main main
```

路径要按你实际加密的范围调整；用了主题记忆的话，记忆不只在 `memory.md` 里。被移除的路径连当前提交里也会被改写掉，所以先检查工作区，必要时从第 0 步的目录备份里把文件拷回来，再从第 2 步重新做一遍。

代价是实打实的：其他所有 clone 的历史都分叉了，每台机器都要 `git fetch && git reset --hard origin/main && git-crypt unlock <key>`。

## 加密藏不住的东西

- **提交信息。** git-crypt 不加密文件名、提交信息和其他元数据，也不隐藏文件大小和修改时间（[git-crypt README](https://github.com/AGWA/git-crypt)）。nestwork 自己的提交信息是固定格式，比如 `memory: update <host>/<agent-id>`、`comms: task to <host>/<agent-id> (<id>)`，会暴露机器名、agent id 和活动时间，但不暴露内容。你手写的提交信息，托管方都看得到。
- **文件名。** 一个叫 `health.md` 的主题文件本身就说明了主题；复制进未加密索引的主题描述也一样可读。高敏感场景，文档建议用无意义的文件名加统一的提交信息。
- **模型服务商。** agent 要读就得解密，明文会进入 API 请求。加密防的是托管平台和拿到 clone 的人，不防运行 agent 的那一方。
- **被偷的电脑。** key 和已解锁的 clone 在同一台设备上且没有口令保护，小偷两样都拿到了。

## 密钥备份，以及为什么凭证不能写进记忆

导出的 key 才是真正要守的资产。文档给的规矩：一个加密仓库一把 key，复制到每台机器；key 永远不进仓库，也不进任何镜像；至少两处离线备份，比如密码管理器附件加离线介质；不要通过聊天或邮件传。所有副本都丢了，密文就永远打不开，仓库的所有备份也随之作废。

另外，git-crypt 不支持撤销访问：它的 README 写明，曾经拿到 key 的人，即使之后轮换了 key，也仍能读旧的历史。

不管加不加密，API key、token、密码都不应该写进 agent 记忆。nestwork 的 README 说得很直白：私有仓库也可能因平台漏洞、账号被盗、协作者权限配错而泄露；而且 agent 会把记忆以明文放进模型请求。凭证放环境变量或专门的密钥管理工具，记忆里只写「凭证从哪来」。

## 常见问题

### git-crypt 会让 nestwork 变慢吗？

文档说明加密对 hook 是透明的，clean filter 是确定性的，但没有公布耗时数据，这里也不给数字。

### 能只加密某一个 agent 的记忆吗？

能。这些都是普通的 `.gitattributes` 规则，可以只覆盖一个作用域，比如某个 agent 目录。文档本来就建议加密范围越小越好。

### 加密后 `update.sh` 还能用吗？

用当前版本的更新脚本就行：它不经过你的 smudge filter 解出上游文件，再经过你的 clean filter 暂存。更新前先 commit 或 stash 本地改动，更新后检查 `VERSION` 不为空、加密文件仍是密文。

### 安装脚本会自动开启加密吗？

不会。这是手动、自愿开启的流程，协议刻意不内置加密。

## 相关阅读

- [git 原生的 agent 记忆](../git-native-agent-memory/)
- [用 git 做 agent 邮箱](../agent-mailbox-git/)
- [nestwork 安装常见问题](../nestwork-getting-started-faq/)
- [AI 长期记忆用起来是什么样](../long-term-memory-in-practice/)
- [换台设备，AI agent 就失忆](../agent-amnesia-cross-device/)

---
name: reef-pr
description: 将当前分支的变更创建为 GitHub PR。读取 commits 和 OpenSpec 上下文，生成 PR 描述并提交。用户说「创建 PR」「发起 PR」「pull request」「提 PR」「提交 PR」时触发。
allowed-tools: Bash(git:*), Bash(gh:*)
deepstorm:
  tool: reef
---

# 创建 Pull Request

## 前置条件

- GitHub CLI (gh) 已安装并登录
- 当前分支有已提交的 commits
- `git push` 未阻塞（有远程权限）

## 上下文约定

当前分支名即 OpenSpec change 名（由 jira-start 阶段三创建分支时建立）：

```bash
BRANCH=$(git branch --show-current)
CHANGE_DIR="openspec/changes/$BRANCH"
```

## 工作流

### 1. 收集上下文

先检查未提交变更。如有则提示「请先 commit 再创建 PR」，中止流程。

```bash
BRANCH=$(git branch --show-current)
FORK_POINT=$(git merge-base main HEAD 2>/dev/null)
echo "Branch: $BRANCH"; git status -sb
echo "Commits:"; git log "$FORK_POINT"..HEAD --oneline
echo "Changes:"; git diff "$FORK_POINT"..HEAD --stat
ls -d openspec/changes/$BRANCH/*.md 2>/dev/null
```

如有 OpenSpec change，读取 `proposal.md` 和 `tasks.md` 作为描述素材。

### 2. 构建 PR 信息

**标题：** OpenSpec proposal 标题优先，否则取第一个 commit 标题。≤ 70 字符。

**正文：**

```markdown
## Summary
{2-4 行概括变更动机，优先从 proposal.md 提取}
## 关联
JIRA: {commit body / proposal.md / jira-start 元数据}
OpenSpec: openspec/changes/{branch-name}/
## 变更清单
{git diff --stat 输出}
## Test plan
- [ ] {前端路径含 src/main/web/ 则加}
- [ ] {后端路径含 src/main/java/ 则加}
- [ ] {手动验证步骤，如有}
```

### 3. 展示并确认

展示 PR 标题和正文。问用户：

- 「需要加 reviewer 和 label 吗？」
- 「创建 Draft PR？」
- 「没问题，创建」— 执行步骤 4
- 「修改一下标题/描述」— 修改后执行

### 4. 推送并创建 PR

先检查是否已有打开的 PR：

```bash
EXISTING_PR=$(gh pr view --json url 2>/dev/null)
```

如有则询问「已有 PR，是否更新描述？」，用户确认后用 `gh pr update` 更新；否则正常创建：

```bash
# 首次推送当前分支
git push -u origin $(git branch --show-current)

# 创建 PR（如有 reviewer/label/draft 则追加对应参数）
gh pr create \
  --title "<标题>" \
  --body "<正文>" \
  [--reviewer "<用户>"] \
  [--label "<标签>"] \
  [--draft]
```

### 5. 输出结果

返回 PR 链接。

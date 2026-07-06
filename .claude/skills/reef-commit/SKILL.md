---
name: reef-commit
description: 根据当前变更和 OpenSpec 上下文，生成规范的提交信息并创建新提交。用户说「提交代码」「commit」「git push」「提交」「推送」等触发
allowed-tools: Bash(git:*), Bash(./gradlew:*), Bash(pnpm:*)
deepstorm:
  tool: reef
---

# 智能生成提交信息

根据当前变更、OpenSpec 任务定义及仓库历史 PR 风格，生成中文提交信息，创建新的 git 提交。

## 提交信息风格规范（基于历史 PR 总结）

### 标题

1. 不使用 conventional commit 前缀（无 `feat:`、`fix:`、`chore:` 等）
2. 一句话说清做了什么，可含英文术语
3. 命名来源优先级：OpenSpec proposal/design 标题 → 分支名语义化 → 变更内容总结
4. 每行 ≤ 70 字符

### 正文（根据任务复杂度决定）

| 复杂度 | 正文策略 |
|--------|---------|
| 简单（单文件/小修补/配置改动） | 仅标题 |
| 中等 | 标题 + 一段说明 |
| 复杂（多模块/架构级/前后端/破坏性变更） | 标题 + `本次提交改动如下：` + 要点列表 |

有参考文档加 `参考资料：`，关联 Issue 在尾部隔空行加 `JIRA: {完整 URL}`。文件数仅作参考（50 个重命名仍属简单）。

## 工作流

### 1. 检测变更

```bash
git status --short
```

若无任何变更则提示用户并退出。

### 2. 审查待提交文件

展示变更清单，检查敏感文件：

```bash
git diff --stat
```

如包含 `.env`、凭据、证书或大型二进制文件，让用户确认或排除后再继续。

### 2.4 分支范围检查

检查当前分支是否涉及多个业务领域。如果跨领域，给出拆分建议并中止提交。

```bash
BRANCH=$(git branch --show-current)
FORK_POINT=$(git merge-base main HEAD 2>/dev/null || echo "")
echo "检查分支范围（基准: main）..."
SCOPE_HOOK="packages/reef/hooks/reef-scope-gate.sh"
if [ -f "$SCOPE_HOOK" ]; then
  bash "$SCOPE_HOOK" || {
    echo ""
    echo "提示：如需继续提交，请使用 'reef-scope-split.sh' 拆分分支"
    echo "或临时禁用 scope 检查（不推荐）：deepstorm/scope-config.json → enabled: false"
    exit 1
  }
fi
```

### 2.5 运行单元测试

```bash
git status --short
```

如有变更则全量运行测试：

```bash
./gradlew test
(cd src/main/web && pnpm test -- --run)
```

- 测试全部通过 → 继续
- 任一测试失败 → 提示用户修复后再提交

### 3. 收集上下文

```bash
BRANCH=$(git branch --show-current)
FORK_POINT=$(git merge-base main HEAD 2>/dev/null)
echo "Branch: $BRANCH"; git diff "$FORK_POINT"..HEAD --stat
ls -d openspec/changes/*/ 2>/dev/null | grep -v archive
[ -f "openspec/changes/$BRANCH/proposal.md" ] && head -5 "openspec/changes/$BRANCH/proposal.md"
# 从 proposal/commit 提取 Issue 引用
grep -iE '(issue|jira|lc-|proj-)' "openspec/changes/$BRANCH/proposal.md" 2>/dev/null | head -3
git log "$FORK_POINT"..HEAD --format="%B" 2>/dev/null | grep -ioP '[A-Z]+-\d+' | head -1
```

### 4. 生成提交信息

**标题：** 优先 OpenSpec proposal 标题 → 分支名（kebab-case 转中文）→ 变更总结。依赖更新用 `更新 {依赖} 至 {版本}`，问题修复用 `解决{问题描述}的问题`。

**正文：** 中/复杂变更用 `本次提交改动如下：` + 3-6 条要点。尾部隔空行加 `JIRA: {完整 URL}`（优先从 proposal.md/jira-start 元数据中获取 JIRA 链接），如有 PRD 链接加 `Ref: {URL}`。

### 5. 展示并确认

展示完整提交信息，用户确认即可提交；支持 `--amend` 合并；用户可要求修改后重新生成。

### 6. 执行提交

```bash
git add -A && git commit -m "<完整提交信息>"
# 用户要求 amend 时: git commit --amend -m "<完整提交信息>"
```

### 7. 推送（仅在用户要求时）

```bash
# 新提交（有远程跟踪）：git push
# Amend：git push --force-with-lease
# 首次推送：git push -u origin $(git branch --show-current)
```

## 约束规则

默认新提交，用户要求才 `--amend`。每行 ≤ 70 字符。无变更则退出。

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

### 2. 分支名与任务相关性检查

在审查待提交文件之前，先检查当前分支是否与待提交的任务相关。如果当前在 `main`/`master` 分支上则**必须**创建新分支；如果分支名与任务内容明显不匹配（如命名随意、与 OpenSpec 任务不符），建议创建新分支。

```bash
BRANCH=$(git branch --show-current)
echo "当前分支: $BRANCH"

# 检测是否需要创建新分支
MUST_NEW_BRANCH=false

# 条件一：在 main 或 master 上必须创建新分支
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "⚠️ 当前在 $BRANCH 分支上，不允许直接提交，必须创建新分支"
  MUST_NEW_BRANCH=true
fi

# 条件二：检查分支名是否包含 temp、wip、test、tmp、dev 等临时名称
TEMP_PATTERN='^(temp|wip|test|tmp|dev)(/.*)?$'
if echo "$BRANCH" | grep -qE "$TEMP_PATTERN"; then
  echo "⚠️ 当前分支名 ($BRANCH) 看起来是临时分支，建议创建有意义的新分支"
fi

# 收集 OpenSpec 任务上下文
for dir in openspec/changes/*/; do
  if [ -f "$dir/proposal.md" ]; then
    TASK_NAME=$(basename "$dir")
    echo "发现 OpenSpec 任务: $TASK_NAME"
  fi
done
```

**判断规则（LLM 自行推理执行）：**

1. **如果 MUST_NEW_BRANCH=true**（当前在 main/master）：
   - 直接进入步骤 3「创建新分支」，无需询问用户
2. **如果分支名明显不相关**（如 `temp-xxx`、`test-foo`、或随意命名与当前变更毫无关联）：
   - 向用户说明：「当前分支 $BRANCH 与待提交的变更内容似乎不匹配，是否创建一个新分支？」
   - 用户同意 → 进入步骤 3「创建新分支」
   - 用户不同意 → 继续当前分支
3. **如果分支名合理**（如与 OpenSpec 任务同名，或包含功能描述的 kebab-case）：
   - 直接继续

### 3. 创建新分支

当需要创建新分支时，按以下逻辑确定分支名：

**分支名生成规则（优先级从高到低）：**
1. **OpenSpec 任务名**：如果检测到 `openspec/changes/<task>/proposal.md`，使用 `<task>` 作为分支名
2. **用户输入**：询问用户想要的分支名
3. **AI 推导**：根据变更内容总结生成 kebab-case 分支名（例如 `feat/add-user-auth`、`fix/login-timeout`）

```bash
# 暂存当前未提交变更
STASHED=false
if [ -n "$(git status --porcelain)" ]; then
  git stash push -m "reef-commit-auto-stash"
  STASHED=true
fi

# 创建并切换到新分支（基于 main）
git checkout main
git pull origin main 2>/dev/null || true
git checkout -b <new-branch-name>

# 恢复暂存的变更
if [ "$STASHED" = true ]; then
  git stash pop
fi

echo "✅ 已切换到新分支: <new-branch-name>"
```

> **注意**：创建新分支后，后续步骤（审查文件、范围检查、测试等）在新分支上继续执行。

### 4. 审查待提交文件

展示变更清单，检查敏感文件：

```bash
git diff --stat
```

如包含 `.env`、凭据、证书或大型二进制文件，让用户确认或排除后再继续。

### 5. 分支范围检查

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

### 6. 运行单元测试

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

### 6.5 OpenSpec 验证与归档检查

> 提交前检查关联的 OpenSpec change 是否已完成验证和归档。如果 `openspec/` 目录不存在或无活跃 change 则跳过本步骤。

**判断流程（LLM 自行推理执行）：**

1. **查找关联的 OpenSpec change：**
   ```bash
   BRANCH=$(git branch --show-current)
   echo "当前分支: $BRANCH"

   for dir in openspec/changes/*/; do
     CHANGE_NAME=$(basename "$dir")
     if [ -f "$dir/.openspec.yaml" ] && [ "$CHANGE_NAME" != "archive" ]; then
       echo "发现活跃 OpenSpec change: $CHANGE_NAME"
       cat "$dir/.openspec.yaml"
     fi
   done
   ```

2. **匹配规则：** 扫描 `openspec/changes/*/` 下活跃 change（不包含 `archive/`），与当前分支名比对；无匹配则跳过；多匹配则让用户选择。

3. **检查归档状态：** 读取 `.openspec.yaml` 中 `status` 字段。`archived` → 跳过后续检查；否则继续。

4. **运行验证：** 确认 `tasks.md` 全部 checkbox 已完成 → 通过 Skill 工具自动调用 `/opsx:verify`。有 CRITICAL 问题则中止；仅 WARNING/SUGGESTION 则通过。

5. **运行归档：** 验证通过后 → 通过 Skill 工具自动调用 `/opsx:archive`。执行失败则提示用户手动处理。

6. **确认已就绪：** 校验状态并向用户报告。

> **提示：** verify/archive 执行后产生额外文件变更的，后续步骤会重新检测并纳入提交。

### 7. 收集上下文

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

### 8. 生成提交信息

**标题：** 优先 OpenSpec proposal 标题 → 分支名（kebab-case 转中文）→ 变更总结。依赖更新用 `更新 {依赖} 至 {版本}`，问题修复用 `解决{问题描述}的问题`。

**正文：** 中/复杂变更用 `本次提交改动如下：` + 3-6 条要点。尾部隔空行加 `JIRA: {完整 URL}`（优先从 proposal.md/jira-start 元数据中获取 JIRA 链接），如有 PRD 链接加 `Ref: {URL}`。

### 9. 展示并确认

展示完整提交信息，用户确认即可提交；支持 `--amend` 合并；用户可要求修改后重新生成。

### 10. 执行提交

```bash
git add -A && git commit -m "<完整提交信息>"
# 用户要求 amend 时: git commit --amend -m "<完整提交信息>"
```

### 11. 推送（仅在用户要求时）

```bash
# 新提交（有远程跟踪）：git push
# Amend：git push --force-with-lease
# 首次推送：git push -u origin $(git branch --show-current)
```

## 约束规则

默认新提交，用户要求才 `--amend`。每行 ≤ 70 字符。无变更则退出。

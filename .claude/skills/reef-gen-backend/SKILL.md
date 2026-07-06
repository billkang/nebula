---
name: reef-gen-backend
description: 后端代码编写流程（FastAPI + Python 3.10+）。编写或生成后端代码时自动加载，编码规范详情引用 reef:reef-style-backend。
when_to_use: 用户要求编写或修改后端代码；创建新的后端文件；用户说"生成后端代码""写接口""加表"等
user-invocable: false
allowed-tools: Bash(git:*), Bash(uv:*)
deepstorm:
  tool: reef
  configKey: reef.backend.language
---

# 后端代码编写流程

编码规范详情（实体层次、数据访问、业务逻辑、API 模式、多租户红线、代码风格）请通过 Skill tool 加载 **`reef:reef-style-backend`** 获取。

## 工作流

### 1. 找参考实现

在动手之前，先在已有代码中找一个同类实现。优先搜索当前模块目录：

```bash
# 替换 <module> 为当前模块名
find app/ tests/ -path "*/<module>/*" -type f

# 找最近修改的同类文件（使用 fork-point 避免全量历史）
FORK_POINT=$(git merge-base "$(git reflog --date=local | grep "checkout: moving from.* to $(git rev-parse --abbrev-ref HEAD)$" | head -1 | sed -n 's/.*from \([^ ]*\) to .*/\1/p' || echo main)" HEAD)
git diff "$FORK_POINT"..HEAD --diff-filter=M --name-only
```

**规则**：不凭空写新文件。先读一个真实存在的同类文件，理解模式后再动手。写新模块时参考已有模块的完整实现。

### 2. 查阅规范

加载 `reef:reef-style-backend` 技能，阅读 `quick-reference.md` 和必要示例。

涉及库/框架 API 用法时，使用 context7 获取最新文档：`resolve-library-id` → `query-docs`。

### 3. 编写代码

阅读本技能目录下的 `steps.md` 了解当前技术栈的编码步骤顺序和规范。编写过程中逐单元对照 `reef:reef-style-backend` 中对应章节检查。

**注释语言**：代码注释统一使用中文，专有名词/技术术语（如 REST、DTO、HTTP、JPA 等）保留英文。

### 4. 数据库迁移

如果涉及新表或字段变更（新增实体、新增字段、修改字段类型），加载 `reef:reef-style-backend` 技能，阅读其数据库迁移章节创建变更文件。

迁移脚本参考（Alembic）：加载 `reef:reef-style-backend` 后阅读 `examples/` 目录中的示例。

### 5. 运行验证

写完后运行验证：

```bash
# 快速验证
ruff check .

# 最终验证（提交前）
ruff check . && mypy . && python -m pytest
```

### 6. 提交前自检

加载 `reef:reef-style-backend` 技能，逐项检查所有规范要求。**未通过不得提交。**

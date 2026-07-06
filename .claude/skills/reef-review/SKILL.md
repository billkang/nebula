---
name: reef-review
description: 对当前分支变更执行前后端代码审查。自动检测变更范围，派发 Sub‑Agent 执行审查并生成结构化报告。
allowed-tools: Bash(git:*), Agent
deepstorm:
  tool: reef
---

# 统一代码审查（Sub‑Agent 模式）

自动检测变更类别，派发对应 Sub‑Agent 执行审查。

## 工作流

### Step 1: 检测变更范围

```bash
# 获取 fork-point（检测当前分支基于哪个分支创建）
FORK_POINT=$(git merge-base "$(git reflog --date=local | grep "checkout: moving from.* to $(git rev-parse --abbrev-ref HEAD)$" | head -1 | sed -n 's/.*from \([^ ]*\) to .*/\1/p' || echo main)" HEAD)
echo "FORK_POINT=$FORK_POINT"
echo "变更文件统计:"
git diff "$FORK_POINT"..HEAD --stat

# 按类别提取文件清单
FILE_LIST=$(git diff "$FORK_POINT"..HEAD --name-only)
FILE_COUNT=$(echo "$FILE_LIST" | wc -l | tr -d ' ')
BACKEND_FILES=$(git diff "$FORK_POINT"..HEAD --name-only -- app/ tests/)
FRONTEND_FILES=$(git diff "$FORK_POINT"..HEAD --name-only -- src/)
INFRA_FILES=$(git diff "$FORK_POINT"..HEAD --name-only | grep -v '^app/ tests/' | grep -v '^src/')
SECURITY_FILES=$(git diff "$FORK_POINT"..HEAD --name-only -- app/ tests/ src/ | grep -iE 'auth|tenant|security|oauth|token|password|permission' || true)
```

判断哪些类别有变更：

| 类别 | 判断条件 |
|------|---------|
| 后端 | `BACKEND_FILES` 非空 |
| 前端 | `FRONTEND_FILES` 非空 |
| 基础配置 | `INFRA_FILES` 非空 |
| 安全敏感 | `SECURITY_FILES` 非空 |
| 无匹配 | 全部为空 |

据此决定派发哪些 agent：

| 有变更的类别 | 派发 agent |
|-------------|-----------|
| 仅后端 | `backend-code-audit` |
| 仅前端 | `frontend-code-audit` |
| 仅基础配置 | `infra-code-audit` |
| 后端 + 基础配置 | 并行 `backend-code-audit` + `infra-code-audit` |
| 前端 + 基础配置 | 并行 `frontend-code-audit` + `infra-code-audit` |
| 全栈 | 并行 `backend-code-audit` + `frontend-code-audit` |
| 全栈 + 基础配置 | 并行 `backend-code-audit` + `frontend-code-audit` + `infra-code-audit` |
| **安全敏感变更** | 在以上基础上 **额外** 并行 `security-code-audit` |
| 无匹配 | 输出提示，不派发 agent |

> 安全敏感变更判定：SECURITY_FILES 非空 或 变更涉及权限/认证逻辑（由调用的 fork-point 范围决定）。

### Step 2: 派发 Sub‑Agent

每个 agent 按各自类别的文件清单构造 prompt。后端 agent 的清单含后端源文件，前端和 infra agent 只含自己的文件。

| Agent | prompt 中的文件清单 |
|-------|-------------------|
| `backend-code-audit` | 后端文件 |
| `frontend-code-audit` | 前端文件 |
| `infra-code-audit` | 基础配置文件 |
| `security-code-audit` | 安全敏感文件 + 所有变更文件中有安全风险的 diff |

```
Fork point: {FORK_POINT}
变更文件数: {count}
变更文件清单:
{file_list}
```

Agent 的 system prompt（定义在 `.claude/agents/` 目录中）包含完整的 Checklist + Rules + 输出格式。

| Agent | 定义文件 |
|-------|---------|
| `reef-review-backend` | `../../agents/reef-review-backend.md` |
| `reef-review-frontend` | `../../agents/reef-review-frontend.md` |
| `reef-review-infra` | `../../agents/reef-review-infra.md` |
| `reef-review-security` | `../../agents/reef-review-security.md` |

多 agent 场景全部使用 `run_in_background: true` 并行执行。每个 agent 设置超时 300 秒（5 分钟），超时未返回则标记为超时，继续等待其他 agent。

### Step 3: 汇总报告

1. 等待所有已派发的 agent 返回（收到全部 task-notification 后才汇总）。任一 agent 超时 300 秒未返回则标记为超时，继续等待其他 agent
2. 分章节输出各 agent 的审查报告：

```
## 后端代码审查报告
{后端 agent 输出}

## 前端代码审查报告
{前端 agent 输出}

## 基础配置审查报告
{infra agent 输出}

## 安全审查报告
{security agent 输出（仅安全敏感变更时）}
```

3. 最终结论取最低评分。若某 agent 失败（API Error / 超时等），标注失败原因，忽略其评分。仅有派发过的 agent 输出对应章节。

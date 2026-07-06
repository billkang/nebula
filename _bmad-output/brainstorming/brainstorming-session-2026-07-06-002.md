# Brainstorming Session

> 日期：2026-07-06
> 参与者：Bill, Claude
> 路径：Path B · 开放讨论

## 讨论主题

Nebula 项目 Monorepo 结构改造

## 需求要点

### 目标

将当前扁平的项目结构改造为 Monorepo 架构，实现两端（Build Engine / Runtime Engine）的代码共享和统一构建管理。

### 核心改动

1. **创建 `packages/` 目录**，按职责组织代码
2. **现有代码迁移**：
   - `backend/` → `packages/build-engine/backend/`
   - `frontend/` → `packages/build-engine/frontend/`
   - `nebula-runtime/` → `packages/runtime-engine/`
3. **新增共享包**：
   - `packages/shared-python/`（包名：`nebula-shared`）— 共享 Python 代码（models / config / utils）
   - `packages/shared-ui/`（包名：`@nebula/shared-ui`）— 共享前端 UI 组件

### 工具链

| 层 | 工具 | 职责 |
|----|------|------|
| 前端 | pnpm workspace | TypeScript / React 包的依赖管理和 workspace 引用 |
| 后端 | uv workspace | Python 包的依赖管理和 workspace 引用 |
| 总入口 | Makefile + scripts/ | 统一命令（dev / build / test / clean） |

## 关键决策

| 决策 | 结论 |
|------|------|
| 目录结构 | `packages/build-engine/{backend,frontend}` / `packages/runtime-engine/` / `packages/shared-python/` / `packages/shared-ui/` |
| 迁移方式 | 直接按新目录布置代码，保留原目录 clean 后删除 |
| 前端共享包命名 | `@nebula/shared-ui` |
| Python 共享包命名 | `nebula-shared`（import 为 `nebula_shared`） |
| 项目入口 | `Makefile` 统一入口，复杂逻辑委托 `scripts/dev.sh` |
| 分支冲突 | 无并行分支修改这些目录 |
| 当前范围 | 仅 Monorepo 结构改造 + 共享代码组织，启动命令 / Docker 等不在此次讨论范围 |

## 边界范围

- ✗ 不在此次变更处理：开发启动命令、Docker 构建、生产部署
- ✗ 不在此次变更处理：Runtime Engine 的前端界面开发（仅创建 shared-ui 供后续使用）
- ✗ 不引入 Nx 等重型 monorepo 工具

## 后续步骤

1. SDD：生成 proposal → specs → design → tasks
2. 实现：按 tasks 逐项迁移和改造
3. 验证：各包独立测试和工作空间引用测试

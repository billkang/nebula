## Context

Nebula 项目当前代码散布在 `backend/`、`frontend/`、`nebula-runtime/` 三个顶级目录中。两端（Build Engine / Runtime Engine）都是 Python（FastAPI）+ React 技术栈，存在潜在的共享代码（配置模式、工具函数、UI 组件），但当前没有任何包管理或 workspace 机制来支撑共享。

项目入口也不统一（`start.sh`、`Makefile` 独立存在），New hire 需要了解约定才能上手。

## Goals / Non-Goals

**Goals:**
- 建立 `packages/` 目录结构，按平台职责组织代码
- 配置 pnpm workspace 管理前端包（`build-engine/frontend`、`shared-ui`）
- 配置 uv workspace 管理 Python 包（`build-engine/backend`、`runtime-engine`、`shared-python`）
- 创建 `shared-python`（`nebula-shared`）和 `shared-ui`（`@nebula/shared-ui`）共享包骨架
- 创建统一 `Makefile` 入口（dev / test / clean）
- 迁移后原有导入路径保持不变（`from app.config import settings`）

**Non-Goals:**
- 不涉及开发启动命令重构（由 `dev-startup-simplify` 分支处理）
- 不涉及 Docker 构建流程变更（由 `dev-startup-simplify` 分支处理）
- 不涉及 Runtime Engine 前端界面开发（仅建立 shared-ui 结构）
- 不改变业务逻辑代码
- 不引入 CI/CD 流程变更（如 GitHub Actions 配置不做调整）
- 不改动 `projects/` 目录下的项目产物结构和生成逻辑
- 不改动 `docker/` 目录下的现有 Dockerfile
- 不对现有 `requirements.txt` 做依赖升级或版本变更（仅迁移到 pyproject.toml，保持依赖不变）
- 本次不进行 shared-python 和 shared-ui 包的内容填充（仅建立结构骨架）

## Decisions

### D1: 使用 pnpm workspace + uv workspace，不引入 Nx

- **选择**：pnpm workspace（前端）+ uv workspace（后端）+ Makefile（总入口）
- **原因**：项目已使用 `uv` 和 `npm`，不引入额外工具；pnpm/uv 各自在其生态中原生支持 monorepo；Makefile 做顶层编排
- **替代方案**：Nx — 太重，Python 支持弱，学习成本高

### D2: Python 包统一使用 src layout

- **选择**：所有 Python 包使用 `src/app/` 目录结构
- **原因**：uv workspace 推荐模式；避免 `PYTHONPATH` 污染；与共享包 `nebula_shared` 命名空间一致
- **替代方案**：flat layout（保持原样）— 直接搬目录改动最小，但不符合 uv workspace 最佳实践

### D3: 内部导入路径 `from app.xxx` 保持不变

- **选择**：两端都使用 `app` 作为内部包名，不添加前缀
- **原因**：两个引擎是独立部署进程，不会在同一进程内互相导入 `app`，无命名冲突；避免大规模机械改 import 语句
- **注意**：共享包必须使用 `nebula_shared` 前缀导入

### D4: pyproject.toml 包名差异化

- **选择**：`build-engine-backend`、`runtime-engine`、`nebula-shared`
- **原因**：pip/uv 需要不同的包名来区分 workspace 成员，但 editable install 后内部 import 路径不受包名影响

### D5: Makefile 委托复杂逻辑到 scripts/

- **选择**：Makefile 做入口编排，条件分支/后台进程管理/trap 清理/hash 比对等委托给 `scripts/` 下的 shell 脚本
- **原因**：Makefile 不适合做复杂流程控制

### D6: 共享包初始为结构骨架

- **选择**：`shared-python` 和 `shared-ui` 初始只建立目录结构、包配置和少量基础代码
- **原因**：当前两端代码无实质重叠，等后续开发中自然填充共享内容

### D7: pytest 在 pyproject.toml 中配置

- **选择**：每个 Python 包的 `pyproject.toml` 写入 `[tool.pytest.ini_options]`，添加 `pythonpath = ["src"]`
- **原因**：src layout 下 pytest 默认找不到 `app` 包，需要显式配置；cc `uv run pytest` 时也必须正确解析

## Change Scope Matrix

| 操作 | 目录/文件 | 影响 |
|------|----------|------|
| MOVE | `backend/` → `packages/build-engine/backend/` | 路径变更，src layout 化 |
| MOVE | `frontend/` → `packages/build-engine/frontend/` | 路径变更，内部结构不变 |
| MOVE | `nebula-runtime/` → `packages/runtime-engine/` | 路径变更，src layout 化 |
| CREATE | `packages/shared-python/` | 新建 Python 共享包骨架 |
| CREATE | `packages/shared-ui/` | 新建前端共享包骨架 |
| CREATE | `root pnpm-workspace.yaml` | 前端 workspace 配置 |
| CREATE | `root pyproject.toml` | uv workspace 配置 |
| CREATE/UPDATE | 各 Python 包的 `pyproject.toml` | 替代 requirements.txt |
| CREATE/UPDATE | `Makefile` | 新增 dev/test/clean 目标 |
| CREATE | `scripts/` | 存放委托脚本 |
| DELETE | `backend/` | 迁移后移除原目录 |
| DELETE | `frontend/` | 迁移后移除原目录 |
| DELETE | `nebula-runtime/` | 迁移后移除原目录 |
| KEEP | `start.sh` | 保留不动（留给 dev-startup-simplify 处理） |

## API Contract

（无新增 API 或端点变更 — 本次仅为代码组织重构）

## Risks / Trade-offs

- **[风险] start.sh 路径迁移**：迁移后 `start.sh` 中原路径（`backend/`, `frontend/`）需适配新结构 → **已处理**：`start.sh` 已随本次变更新为 monorepo 路径（`packages/build-engine/backend/`, `packages/build-engine/frontend/`）。后续启动命令重构由 `dev-startup-simplify` 分支处理。
- **[风险] parallel imports of 'app'**：虽然两端都是 `app` 包名且不同进程运行，但如果未来某个脚本需要同时 import 两个包的代码，会产生混淆 → **缓解**：这种情况极少发生，发生时可通过 `importlib` 或重命名规避
- **[风险] uv sync 后本地未调用导致测试失败**：开发者在子包内直接 `pytest` 而非 `uv run pytest` 可能找不到依赖 → **缓解**：Makefile 的 `test` 目标确保从正确上下文调用

## Open Questions

（均已在前序讨论中确认，无待决事项）

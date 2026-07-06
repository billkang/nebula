## Why

当前 Nebula 项目（Build Engine + Runtime Engine 双平台）代码散布在 `backend/`、`frontend/`、`nebula-runtime/` 三个顶级目录中，缺少统一的代码组织结构和共享机制。两端都是 Python（FastAPI）+ React 技术栈，存在明显的可共享代码（Pydantic models、配置、工具函数、UI 组件），但当前无任何 workspace 或包管理机制来支撑共享。项目入口也不标准（`start.sh`、`Makefile` 各管各的）。

Monorepo 改造将建立标准化的包组织结构和 workspace 机制，让共享变得自然，同时通过 `Makefile` + `scripts/` 提供统一的开发命令入口。

## What Changes

- **创建 `packages/` 目录**，按平台职责组织代码：
  - `packages/build-engine/{backend,frontend}/` — Build Engine（原 `backend/`、`frontend/`）
  - `packages/runtime-engine/` — Runtime Engine（原 `nebula-runtime/`）
  - `packages/shared-python/` — Python 共享代码包（`nebula-shared`）
  - `packages/shared-ui/` — 前端共享 UI 包（`@nebula/shared-ui`）
- **设置 pnpm workspace** — 管理前端包（`build-engine/frontend`、`shared-ui`）
- **设置 uv workspace** — 管理 Python 包（`build-engine/backend`、`runtime-engine`、`shared-python`）
- **创建 `Makefile`** — 统一入口（`dev`、`build`、`test`、`clean`）
- **创建 `scripts/` 目录** — 存放 Makefile 委托的 shell 脚本
- **更新导入路径** — 调整各包的内部 imports 以匹配新目录结构和 workspace 引用
- **移除原顶级目录** — 迁移完成后清理 `backend/`、`frontend/`、`nebula-runtime/`

## Capabilities

### New Capabilities

- `monorepo-structure`: 建立 `packages/` 目录结构和 workspace 配置，定义包之间的依赖关系和引用规则
- `shared-python-package`: 创建 `nebula-shared` Python 共享包，提供两端公共的 models / config / utils
- `shared-ui-package`: 创建 `@nebula/shared-ui` 前端共享 UI 包，提供两端公共的 React 组件和 hooks
- `package-manager-setup`: 配置 pnpm workspace 和 uv workspace，确保依赖安装、构建、测试命令在各包中可用
- `makefile-entry`: 创建统一 `Makefile`，提供 `dev`、`build-engine`、`build-runtime`、`test`、`clean` 等入口，复杂逻辑委托给 `scripts/` 目录

### Modified Capabilities

- （无现有 spec 被修改 — 这是基础设施重构，不改变业务需求）

## Known Limitations

- **src layout 的 IDE 适配成本**：VSCode 需配置 `python.analysis.extraPaths` 或 workspace 级别的 `PYTHONPATH`，否则 IDE 会报"找不到导入"但运行时正常。不熟悉的开发者可能困惑。
- **两个 `app` 包的隐式混淆风险**：`build-engine/backend` 和 `runtime-engine` 在同一 workspace 中都使用 `app` 作为包名。虽然在独立进程中运行不会冲突，但如果某段代码意外跨包引用 `from app.xxx import yyy`，编译阶段无法检测到错误。
- **`packages/build-engine/backend/src/app/` 路径过深**：日常开发中 `cd` 命令和 IDE 文件树展示层级较深，长期使用可能产生摩擦。v2 可考虑用 `dev-shell` 脚本或 symlink 缓解。
- **共享包可能沦为僵尸骨架**：如果后续开发节奏中没有主动向 `shared-python` 和 `shared-ui` 迁移共享代码的习惯，这两个包可能长期停留在"结构骨架"状态。
- **start.sh 路径已适配**：`start.sh` 的路径引用已随本次变更新为 monorepo 路径（`packages/build-engine/backend/`、`packages/build-engine/frontend/`）。启动命令的进一步重构由 `dev-startup-simplify` 分支处理。

## Impact

- **后端（Build Engine）**: `packages/build-engine/backend/`，导入路径需调整为 workspace 引用 `nebula-shared`
- **前端（Build Engine）**: `packages/build-engine/frontend/`，导入路径调整为 workspace 引用 `@nebula/shared-ui`
- **运行时引擎**: `packages/runtime-engine/`，导入路径调整为 workspace 引用 `nebula-shared`
- **共享包**: 新增 `shared-python/` 和 `shared-ui/`，需要对应的 `pyproject.toml` 和 `package.json`
- **开发工具**: 新增 pnpm workspace YAML、uv workspace TOML、Makefile 和 scripts/
- **依赖**: pnpm / uv 的 workspace 配置，无新增外部依赖

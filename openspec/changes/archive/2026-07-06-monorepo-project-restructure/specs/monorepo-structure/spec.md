## 新增需求

### 需求：标准化 packages 目录结构
系统 SHALL 将所有代码统一组织在 `packages/` 目录下，包含以下五个子包：
- `packages/build-engine/backend/` — 构建引擎后端 API
- `packages/build-engine/frontend/` — 构建引擎前端（React）
- `packages/runtime-engine/` — 运行时引擎
- `packages/shared-python/` — Python 共享代码包（包名：`nebula-shared`）
- `packages/shared-ui/` — 前端共享 UI 包（包名：`@nebula/shared-ui`）

#### 场景：目录结构已创建
- **WHEN** 重构后用户列出项目根目录
- **THEN** `packages/` 目录存在且包含上述五个子包
- **AND** 原有的 `backend/`、`frontend/`、`nebula-runtime/` 顶级目录已移除

### 需求：Python 包使用 src layout
所有 Python 包（`build-engine/backend`、`runtime-engine`、`shared-python`）SHALL 使用 src layout：
- 源码位于 `src/<包名>/` 下
- `pyproject.toml` 位于包根目录

#### 场景：构建引擎后端使用 src layout
- **WHEN** 查看 `packages/build-engine/backend/`
- **THEN** `src/app/` 目录存在
- **AND** `pyproject.toml` 位于 `packages/build-engine/backend/pyproject.toml`
- **AND** `from app.config import settings` 导入语句依然正确解析

#### 场景：运行时引擎使用 src layout
- **WHEN** 查看 `packages/runtime-engine/`
- **THEN** `src/app/` 目录存在
- **AND** `pyproject.toml` 位于 `packages/runtime-engine/pyproject.toml`

### 需求：内部导入路径保持不变
每个包内部的代码 SHALL 继续使用 `from app.xxx import yyy` 写法，不增加命名空间前缀。

#### 场景：后端导入不变
- **WHEN** 迁移后运行后端服务
- **THEN** `from app.config import settings` 和 `from app.api.router import api_router` 等导入语句均能正确解析

#### 场景：运行时导入不变
- **WHEN** 迁移后运行运行时服务
- **THEN** `from app.config import settings` 和 `from app.api.runtime import runtime_router` 等导入语句均能正确解析

### 需求：前端保持原目录结构
前端 React 应用 SHALL 移动到 `packages/build-engine/frontend/`，保持其内部结构不变（Vite 配置不变）。

### 需求：迁移完成后清理旧目录
当所有代码和文件已迁移到新位置后，原有的 `backend/`、`frontend/`、`nebula-runtime/` 顶级目录 SHALL 被删除。

#### 场景：旧目录已清理
- **WHEN** 迁移完成后检查项目根目录
- **THEN** `backend/`、`frontend/`、`nebula-runtime/` 目录不存在

### 需求：start.sh 保留在根目录且路径适配
根目录的 `start.sh` 文件 SHALL 保留在项目根目录，其内部路径 SHALL 更新为适配新 monorepo 结构。

#### 场景：start.sh 仍在根目录
- **WHEN** 迁移完成后检查项目根目录
- **THEN** `start.sh` 仍位于项目根目录
- **AND** 其中的路径引用已更新为 `packages/build-engine/backend/` 和 `packages/build-engine/frontend/`

#### 场景：迁移后前端可正常工作
- **WHEN** 在 `packages/build-engine/frontend/` 下执行 `npm run dev`
- **THEN** Vite 开发服务器在预期端口启动

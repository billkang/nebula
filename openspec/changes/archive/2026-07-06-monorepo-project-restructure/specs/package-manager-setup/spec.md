## 新增需求

### 需求：pnpm workspace 已配置
项目根目录 SHALL 包含 `pnpm-workspace.yaml`，包含所有前端包。

#### 场景：pnpm workspace 文件存在
- **WHEN** 检查项目根目录
- **THEN** `pnpm-workspace.yaml` 存在
- **AND** 其中列出 `packages/build-engine/frontend` 和 `packages/shared-ui`
- **AND** 从根目录执行 `pnpm install` 成功

### 需求：uv workspace 已配置
项目根目录 SHALL 包含根 `pyproject.toml`，定义 uv workspace 并包含所有 Python 包。

#### 场景：uv workspace 配置存在
- **WHEN** 检查项目根目录
- **THEN** 根 `pyproject.toml` 存在，包含 `[tool.uv.workspace]` 段
- **AND** 配置列出 `packages/build-engine/backend`、`packages/runtime-engine` 和 `packages/shared-python`
- **AND** 从根目录执行 `uv sync` 成功

### 需求：每个 Python 包有合法的 pyproject.toml
每个 Python 包（`build-engine/backend`、`runtime-engine`、`shared-python`）SHALL 有独立的 `pyproject.toml`，包含：
- 正确的项目名和版本
- 本地声明的依赖（不依赖全局 requirements.txt）
- 与 uv workspace 兼容的 editable install 配置

#### 场景：构建引擎后端 pyproject 存在
- **WHEN** 检查 `packages/build-engine/backend/pyproject.toml`
- **THEN** 声明了 `[project] name`（如 `build-engine-backend`）
- **AND** 列出所有必需依赖（FastAPI、uvicorn、sqlalchemy 等）

#### 场景：运行时引擎 pyproject 存在
- **WHEN** 检查 `packages/runtime-engine/pyproject.toml`
- **THEN** 声明了 `[project] name`
- **AND** 列出所有必需依赖

### 需求：依赖与现有 requirements.txt 等价
每个包的 `pyproject.toml` SHALL 声明与当前 `requirements.txt` 等价的依赖，确保功能无回归。

#### 场景：后端依赖匹配
- **WHEN** 比较 `packages/build-engine/backend/pyproject.toml` 与 `backend/requirements.txt`
- **THEN** 所有运行时依赖均已包含

### 需求：pyproject.toml 配置 pytest
每个 Python 包的 `pyproject.toml` SHALL 包含 `[tool.pytest.ini_options]`，配置 `pythonpath = ["src"]`，确保 pytest 在 src layout 下能正确运行。

#### 场景：pytest 可在 src layout 下运行
- **WHEN** 在任一 Python 包下执行 `uv run pytest`
- **THEN** 测试能找到 `app` 包下待测模块
- **AND** `from app.config import settings` 等导入正常

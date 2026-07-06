## 1. 创建 packages 目录结构

- [x] 1.1 创建 `packages/build-engine/backend/src/app/` 结构，将 `backend/app/` 和 `backend/tests/` 迁移到新位置
- [x] 1.2 创建 `packages/build-engine/frontend/`，将 `frontend/` 迁移到新位置，内部结构不变
- [x] 1.3 创建 `packages/runtime-engine/src/app/` 结构，将 `nebula-runtime/app/` 和 `nebula-runtime/tests/` 迁移到新位置
- [x] 1.4 创建 `packages/shared-python/` 骨架（src/nebula_shared/{models,config,utils}/）
- [x] 1.5 创建 `packages/shared-ui/` 骨架（src/components/, src/hooks/）

## 2. 配置 pnpm workspace

- [x] 2.1 在根目录创建 `pnpm-workspace.yaml`，包含 `packages/build-engine/frontend` 和 `packages/shared-ui`
- [x] 2.2 为 `packages/shared-ui/` 创建 `package.json`（包名 `@nebula/shared-ui`）
- [x] 2.3 在 `packages/build-engine/frontend/package.json` 中添加 `@nebula/shared-ui` workspace 依赖
- [x] 2.4 根目录执行 `pnpm install` 验证 workspace 引用正常

## 3. 配置 uv workspace

- [x] 3.1 在根目录创建 `pyproject.toml`，定义 `[tool.uv.workspace]` 包含三个 Python 包
- [x] 3.2 为 `packages/build-engine/backend/` 创建 `pyproject.toml`（包名 `build-engine-backend`）
- [x] 3.3 为 `packages/runtime-engine/` 创建 `pyproject.toml`（包名 `runtime-engine`）
- [x] 3.4 为 `packages/shared-python/` 创建 `pyproject.toml`（包名 `nebula-shared`）
- [x] 3.5 根目录执行 `uv sync`，验证 workspace 解析和各包 editable install 正常

## 4. 配置 pytest（src layout 适配）

- [x] 4.1 在 `packages/build-engine/backend/pyproject.toml` 中添加 `[tool.pytest.ini_options]`，设置 `pythonpath = ["src"]`
- [x] 4.2 在 `packages/runtime-engine/pyproject.toml` 中添加 `[tool.pytest.ini_options]`，设置 `pythonpath = ["src"]`
- [x] 4.3 从 `packages/build-engine/backend/` 执行 `uv run pytest`，确认所有测试通过
- [x] 4.4 从 `packages/runtime-engine/` 执行 `uv run pytest`，确认所有测试通过

## 5. 迁移辅助文件（非代码文件）

- [x] 5.1 将 `backend/seed.py` 迁移到 `packages/build-engine/backend/`（与 src 同级）
- [x] 5.2 将 `backend/alembic/` 和 `backend/alembic.ini` 迁移到 `packages/build-engine/backend/`（与 src 同级）
- [x] 5.3 将 `backend/.env.example` 迁移到 `packages/build-engine/backend/`
- [x] 5.4 将 `nebula-runtime/.env.example` 迁移到 `packages/runtime-engine/`
- [x] 5.5 将 `nebula-runtime/Dockerfile` 和 `nebula-runtime/docker-compose.yml` 迁移到 `packages/runtime-engine/`

## 6. 创建 Makefile 和 scripts 目录

- [x] 6.1 更新根目录 `Makefile`，添加 `dev`、`test`、`clean` 目标，保留原有 Docker 目标
- [x] 6.2 创建 `scripts/` 目录，添加占位 README，后续脚本由 dev-startup-simplify 填充
- [x] 6.3 从根目录执行 `make test`，验证并行测试正常运行

## 7. 创建共享包初始代码

- [x] 7.1 在 `nebula_shared/config/base.py` 中创建 `BaseConfig` 类（pydantic_settings 基类）
- [x] 7.2 在 `nebula_shared/models/common.py` 中创建基础 Pydantic model 示例
- [x] 7.3 在 `nebula_shared/utils/helpers.py` 中创建工具函数占位
- [x] 7.4 在 `@nebula/shared-ui` 中创建占位组件导出（`index.ts`）

## 8. 清理旧目录

- [x] 8.1 确认所有代码已成功迁移后删除原 `backend/` 目录
- [x] 8.2 确认所有代码已成功迁移后删除原 `frontend/` 目录
- [x] 8.3 确认所有代码已成功迁移后删除原 `nebula-runtime/` 目录
- [x] 8.4 从项目根目录运行 `make test`，确认完整测试通过

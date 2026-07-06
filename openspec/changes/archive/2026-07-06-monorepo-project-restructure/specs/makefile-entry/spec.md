## 新增需求

### 需求：Makefile 提供 dev 目标
Makefile SHALL 提供 `dev` 目标，用于本地开发启动服务。

#### 场景：make dev 启动服务
- **WHEN** 从项目根目录执行 `make dev`
- **THEN** 它执行 `start.sh`（或在后续版本中执行 `scripts/dev.sh`）
- **AND** 服务正常启动

### 需求：Makefile 提供 test 目标
Makefile SHALL 提供 `test` 目标，并行运行所有包的测试。

#### 场景：make test 运行所有测试
- **WHEN** 从项目根目录执行 `make test`
- **THEN** 在 `packages/build-engine/backend/` 和 `packages/runtime-engine/` 下运行 `pytest`
- **AND** 在 `packages/build-engine/frontend/` 下运行 `npm test`（如果该脚本存在）
- **AND** 报告各包的通过/失败状态

### 需求：Makefile 提供 clean 目标
Makefile SHALL 提供 `clean` 目标，清理构建产物。

#### 场景：make clean 清理产物
- **WHEN** 从项目根目录执行 `make clean`
- **THEN** 所有 `__pycache__/` 目录、`.pytest_cache/`、`.venv/`、`node_modules/` 和 `*.pyc` 文件被移除

### 需求：现有 Docker 构建目标保持不变
原有的 `build-coder-image`、`build-builder-image` 和 `build-images` 目标 SHALL 在 Makefile 中保持不变。

#### 场景：Docker 目标仍可用
- **WHEN** 执行 `make build-coder-image`
- **THEN** 它产生与重构前相同的 Docker 镜像

### 需求：复杂逻辑委托到 scripts/
复杂的初始化逻辑 SHALL 不直接嵌入 Makefile，而是委托给 `scripts/` 目录下的脚本。

#### 场景：scripts/ 目录存在
- **WHEN** 重构后检查项目根目录
- **THEN** `scripts/` 目录存在
- **AND** Makefile 中各目标适当委托脚本而非内联实现

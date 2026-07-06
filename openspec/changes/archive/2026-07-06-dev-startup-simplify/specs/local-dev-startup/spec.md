## 新增需求

### 需求：一键启动
项目根目录 SHALL 提供 `scripts/start.sh` 脚本，一条命令启动前后端服务。

#### 场景：macOS/Linux 首次完整启动
- **WHEN** 用户在新克隆的仓库中运行 `./scripts/start.sh`，且已安装 `uv` 和 `pnpm`
- **THEN** 脚本 SHALL：
  - 在 `packages/build-engine/backend/` 中用 `uv venv` 创建 `.venv`
  - 通过 `uv sync` 从 `pyproject.toml` 安装后端依赖
  - 若 `packages/build-engine/backend/.env` 不存在，从 `.env.example` 复制
  - 执行 `alembic upgrade head`
  - 执行 `python seed.py`
  - 若 `node_modules/` 不存在，通过 `pnpm install` 安装前端依赖
  - 在 `http://localhost:8000` 启动后端
  - 在 `http://localhost:5173` 启动前端
  - 打印包含 URL 和登录凭证的摘要信息
  - 捕获 `SIGINT`/`SIGTERM` 以停止两个服务

#### 场景：增量启动（依赖已安装）
- **WHEN** 用户再次运行 `./scripts/start.sh`
- **THEN** 脚本 SHALL：
  - 若 `.venv` 存在则跳过 venv 创建
  - 若 `pyproject.toml` hash 未变则跳过依赖安装
  - 若 `.env` 已存在则跳过
  - 若 marker `.alembic_done` 存在则跳过 `alembic upgrade head`
  - 若 marker `.seed_done` 存在则跳过 `seed.py`
  - 若 `node_modules/` 存在则跳过 `pnpm install`
  - 正常启动两个服务

### 需求：依赖 hash 追踪
启动脚本 SHALL 追踪 `pyproject.toml` 的内容 hash，检测依赖是否需要更新。

#### 场景：依赖发生变化
- **WHEN** 两次运行之间 `pyproject.toml` 被修改
- **THEN** 脚本 SHALL 检测到 hash 变化并重新执行 `uv sync`

### 需求：Python 版本不匹配检测
启动脚本 SHALL 检测 Python 版本变化并自动重建虚拟环境。

#### 场景：Python 版本变化
- **WHEN** 系统 Python 版本与创建 `.venv` 时使用的版本不一致
- **THEN** 脚本 SHALL 删除 `.venv` 并用当前 Python 版本重建

### 需求：Windows 启动脚本
项目根目录 SHALL 提供 `scripts/start.ps1` 脚本，为 Windows 用户提供等价功能。

#### 场景：Windows 完整启动
- **WHEN** Windows 用户运行 `.\scripts\start.ps1`，且已安装 `uv` 和 `pnpm`
- **THEN** 脚本 SHALL 执行与 `scripts/start.sh` 相同的启动序列，使用 PowerShell 语法处理：
  - Python 路径：`.venv\Scripts\python`
  - uv 路径：从 PATH 获取 `uv`
  - 后台进程：通过 `Start-Job` 管理

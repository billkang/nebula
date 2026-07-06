# Dev Startup Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One-command local dev startup (macOS/Linux + Windows) plus Docker Compose for build-engine production deployment.

**Architecture:** `Makefile` as root entry point (`make dev` → `script./scripts/start.sh`). Shell scripts manage local dev lifecycle (venv → deps → config → migrate → seed → run). Docker Compose at `docker/docker-compose.yml` orchestrates build-engine containers (FastAPI + nginx).

**Monorepo context:** Project has been restructured — see `Makefile`, `pyproject.toml` (uv workspace), `pnpm-workspace.yaml`.

**Tech Stack:** bash (macOS/Linux), PowerShell (Windows), uv (Python venv/pkg), Docker Compose, nginx

## Global Constraints

- Python 3.11+; Node.js 18+
- All scripts must check for `uv` and `pnpm` on PATH
- Frontend uses pnpm (workspace:* protocol for shared-ui dep)
- Marker files: `.alembic_done`, `.seed_done`, `.requirements.hash` in `packages/build-engine/backend/`
- `.venv` Python version: compare `.venv/pyvenc.cfg` vs `python3 --version`
- Docker images: `python:3.12-slim` (backend), `node:20-alpine` (build), `nginx:alpine` (serve)
- Ports: 5173 (frontend dev), 8000 (backend dev), 80 (production nginx)
- Backend existing at `packages/build-engine/backend/`
- Frontend existing at `packages/build-engine/frontend/`
- `.dockerignore` already exists at root (no changes needed)
- `Makefile` already exists with targets: `dev`, `test*`, `clean`, `build-*`
- All commit messages in Chinese, verb-initial format

---

### Task 1: Enhance `script./scripts/start.sh` — add Python version check & prerequisite checks

**Files:**
- Modify: `script./scripts/start.sh` (exists, needs enhancements)

**Changes needed:**
1. Add `uv`/`pnpm` prerequisite check at the top
2. Add Python version mismatch detection (.venv rebuild)
3. Change `npm` → `pnpm` for frontend install and run commands
4. Add `warn()` function (used by step 2's version mismatch message)
5. Rest is already correct (uv sync, marker files, correct monorepo paths)

- [ ] **Step 1: Insert prerequisite check after ROOT_DIR**

Insert at line ~15, just after the `ok()` function definitions:

```bash
# ── 前置检查 ───────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    echo "错误: 未找到 uv，请先安装: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
if ! command -v pnpm &>/dev/null; then
    echo "错误: 未找到 pnpm，请先安装: npm install -g pnpm"
    echo "  或使用 corepack: corepack enable && corepack prepare pnpm@latest --activate"
    exit 1
fi
```

- [ ] **Step 2: Add Python version check before venv creation**

Insert after the "后端" section header, before the venv check:

```bash
# Python 版本检测 — venv 是否需重建
if [ -d ".venv" ]; then
    if [ -f ".venv/pyvenv.cfg" ]; then
        VENV_VERSION=$(grep "^version = " .venv/pyvenv.cfg | cut -d' ' -f3)
        SYS_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2)
        if [ -n "$VENV_VERSION" ] && [ -n "$SYS_VERSION" ] && [ "$VENV_VERSION" != "$SYS_VERSION" ]; then
            warn "Python 版本变更: venv($VENV_VERSION) → 系统($SYS_VERSION)，正在重建..."
            rm -rf ".venv"
        fi
    fi
fi
```

- [ ] **Step 3: Verify the script**

```bash
bash -n script./scripts/start.sh
```

Expected: no syntax errors.

- [ ] **Step 4: Commit**

```bash
git add script./scripts/start.sh
git commit -m "增强 start.sh 添加版本检测和前置检查"
```

---

### Task 2: Create `scripts/start.ps1` — Windows one-click startup

**Files:**
- Create: `scripts/start.ps1`
- Mode: executable

**Note:** Uses `Start-Job` for background processes (hides live output). Acceptable for MVP.

- [ ] **Step 1: Write the PowerShell script**

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Nebula 一键启动脚本 (Windows / PowerShell)
.DESCRIPTION
    自动完成环境初始化并同时启动前后端服务
#>

$GREEN = "Green"
$YELLOW = "Yellow"
$BLUE = "Blue"

function info  { Write-Host "[INFO] $args" -ForegroundColor $BLUE }
function ok    { Write-Host "[OK]   $args" -ForegroundColor $GREEN }
function warn  { Write-Host "[WARN] $args" -ForegroundColor $YELLOW }

$ROOT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# ── 前置检查 ───────────────────────────────────────────
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 未找到 uv，请先安装:"
    Write-Host "  powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
    exit 1
}
if (-not (Get-Command "pnpm" -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 未找到 pnpm，请先安装:"
    Write-Host "  npm install -g pnpm"
    Write-Host "  或使用 corepack: corepack enable && corepack prepare pnpm@latest --activate"
    exit 1
}

# ═══════════════════════════════════════════════════════
# 后端
# ═══════════════════════════════════════════════════════
Write-Host "`n━━━ 后端 (Backend) ━━━" -ForegroundColor $YELLOW
Set-Location "$ROOT_DIR\packages\build-engine\backend"

# Python 版本检测
if (Test-Path ".venv\pyvenv.cfg") {
    $venvVersion = (Select-String "^version = " ".venv\pyvenv.cfg").Line.Split("=")[1].Trim()
    $sysVersion = (python --version 2>&1).Split(" ")[1]
    if ($venvVersion -and $sysVersion -and $venvVersion -ne $sysVersion) {
        warn "Python 版本变更: venv($venvVersion) → 系统($sysVersion)，正在重建..."
        Remove-Item -Recurse -Force ".venv" -ErrorAction SilentlyContinue
    }
}

# 1. 虚拟环境
if (-not (Test-Path ".venv")) {
    info "创建 Python 虚拟环境 (uv)..."
    uv venv --quiet
    ok "虚拟环境已创建"
} else {
    ok "虚拟环境已存在"
}

# 2. 依赖安装（通过 pyproject.toml hash 判断变更）
$REQ_HASH_FILE = ".requirements.hash"
$hashAlgo = [System.Security.Cryptography.HashAlgorithm]::Create("MD5")
$stream = [System.IO.File]::OpenRead("pyproject.toml")
$hashBytes = $hashAlgo.ComputeHash($stream)
$stream.Close()
$currentHash = [BitConverter]::ToString($hashBytes) -replace '-', ''
$hashAlgo.Dispose()

$shouldInstall = $true
if (Test-Path $REQ_HASH_FILE) {
    $storedHash = Get-Content $REQ_HASH_FILE
    if ($storedHash -eq $currentHash) { $shouldInstall = $false }
}

if ($shouldInstall) {
    info "安装 Python 依赖..."
    uv sync --quiet
    Set-Content $REQ_HASH_FILE $currentHash
    ok "依赖已安装"
} else {
    ok "依赖已安装，跳过"
}

# 3. 环境配置
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    ok "已从 .env.example 生成 .env"
} else {
    ok ".env 已存在"
}

# 4. 数据库迁移
if (-not (Test-Path ".alembic_done")) {
    info "执行数据库迁移..."
    uv run alembic upgrade head
    New-Item -ItemType File -Path ".alembic_done" -Force | Out-Null
    ok "数据库迁移完成"
} else {
    ok "数据库迁移已执行，跳过"
}

# 5. 初始化数据
if (-not (Test-Path ".seed_done")) {
    info "初始化内置用户..."
    uv run python seed.py
    New-Item -ItemType File -Path ".seed_done" -Force | Out-Null
    ok "内置用户初始化完成"
} else {
    ok "内置用户已初始化，跳过"
}

# ═══════════════════════════════════════════════════════
# 前端
# ═══════════════════════════════════════════════════════
Write-Host "`n━━━ 前端 (Frontend) ━━━" -ForegroundColor $YELLOW
Set-Location "$ROOT_DIR\packages\build-engine\frontend"

if (-not (Test-Path "node_modules")) {
    info "安装前端依赖..."
    pnpm install
    ok "前端依赖安装完成"
} else {
    ok "前端依赖已安装"
}

# ═══════════════════════════════════════════════════════
# 启动服务
# ═══════════════════════════════════════════════════════
Write-Host "`n━━━ 启动服务 ━━━" -ForegroundColor $YELLOW

Set-Location "$ROOT_DIR\packages\build-engine\backend"
info "启动后端 (http://localhost:8000)..."
$backendJob = Start-Job -ScriptBlock {
    Set-Location "$using:ROOT_DIR\packages\build-engine\backend"
    uv run uvicorn app.main:app --reload --port 8000
}
Start-Sleep -Seconds 2

Set-Location "$ROOT_DIR\packages\build-engine\frontend"
info "启动前端 (http://localhost:5173)..."
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:ROOT_DIR\packages\build-engine\frontend"
    pnpm run dev
}

Write-Host "`n══════════════════════════════════════════" -ForegroundColor $GREEN
Write-Host "  ✅ Nebula 已启动！" -ForegroundColor $GREEN
Write-Host "`n  后端 API   → http://localhost:8000" -ForegroundColor $GREEN
Write-Host "  API 文档   → http://localhost:8000/docs" -ForegroundColor $GREEN
Write-Host "  前端       → http://localhost:5173" -ForegroundColor $GREEN
Write-Host "`n  登录账号：" -ForegroundColor $GREEN
Write-Host "    admin / 123456  (管理员)" -ForegroundColor $GREEN
Write-Host "    pm    / 123456  (产品经理)" -ForegroundColor $GREEN
Write-Host "`n  按 Ctrl+C 停止所有服务" -ForegroundColor $GREEN
Write-Host "══════════════════════════════════════════`n" -ForegroundColor $GREEN

try {
    # 实时输出轮询（每 500ms 刷新后台日志）
    while ($backendJob.State -eq 'Running' -or $frontendJob.State -eq 'Running') {
        Receive-Job $backendJob 2>&1 | Out-Host
        Receive-Job $frontendJob 2>&1 | Out-Host
        Start-Sleep -Milliseconds 500
    }
    # 捕获最终输出
    Receive-Job $backendJob 2>&1 | Out-Host
    Receive-Job $frontendJob 2>&1 | Out-Host
} finally {
    info "正在停止服务..."
    $backendJob, $frontendJob | Stop-Job -ErrorAction SilentlyContinue
    $backendJob, $frontendJob | Remove-Job -Force -ErrorAction SilentlyContinue
    ok "服务已停止"
}
```

- [ ] **Step 2: Commit**

```bash
git add scripts/start.ps1
git commit -m "新增 start.ps1 Windows 一键启动脚本"
```

---

### Task 3: Create `docker/docker-compose.yml` — build-engine production deployment

**Files:**
- Create: `docker/docker-compose.yml`
- Create: `packages/build-engine/frontend/Dockerfile`
- Create: `packages/build-engine/backend/Dockerfile`
- Create: `packages/build-engine/backend/scripts/start-backend.sh`

Uses repo root as build context (both frontend and backend are pnpm/uv workspace members that need root lockfiles and workspace configs).

- [ ] **Step 1: Create `packages/build-engine/backend/scripts/start-backend.sh`**

```bash
#!/bin/sh
set -e
cd /app/packages/build-engine/backend
uv run alembic upgrade head
uv run python seed.py
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 2: Create `packages/build-engine/backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./
COPY packages/shared-python/ packages/shared-python/
COPY packages/build-engine/backend/ packages/build-engine/backend/
RUN uv sync --frozen --no-dev --directory packages/build-engine/backend
RUN chmod +x /app/packages/build-engine/backend/scripts/start-backend.sh
WORKDIR /app/packages/build-engine/backend
EXPOSE 8000
CMD ["/app/packages/build-engine/backend/scripts/start-backend.sh"]
```

- [ ] **Step 3: Create `packages/build-engine/frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY pnpm-lock.yaml pnpm-workspace.yaml ./
COPY packages/shared-ui/ ./packages/shared-ui/
COPY packages/build-engine/frontend/ ./packages/build-engine/frontend/
RUN pnpm install --frozen-lockfile
RUN pnpm --filter ./packages/build-engine/frontend run build

FROM nginx:alpine
COPY --from=builder /app/packages/build-engine/frontend/dist /usr/share/nginx/html
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 4: Create `docker/docker-compose.yml`**

```yaml
services:
  backend:
    build:
      context: ..
      dockerfile: packages/build-engine/backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./nebula.db
      - CORS_ORIGINS=http://localhost:80
      - JWT_SECRET=${JWT_SECRET:-change-me-in-production}
      - JWT_EXPIRY_HOURS=24
      - ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-123456}
      - PM_USERNAME=${PM_USERNAME:-pm}
      - PM_PASSWORD=${PM_PASSWORD:-123456}
    healthcheck:
      test: python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('localhost',8000))"
      interval: 3s
      timeout: 2s
      retries: 6
      start_period: 10s

  frontend:
    build:
      context: ..
      dockerfile: packages/build-engine/frontend/Dockerfile
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
```

Key design decisions:
- **`context: ..`** — from `docker/` resolves to repo root, required for both pnpm and uv workspace builds
- **No `version` field** — Compose V2 ignores it
- **No volume** — SQLite data is ephemeral until PostgreSQL migration
- **docker-compose.yml lives in `docker/`** — keeps root clean, alongside builder/coder configs
- **Healthcheck** — backend uses Python `socket` stdlib (no curl), frontend waits for `service_healthy`

- [ ] **Step 5: Commit**

```bash
git add docker/docker-compose.yml packages/build-engine/frontend/Dockerfile packages/build-engine/backend/Dockerfile packages/build-engine/backend/scripts/start-backend.sh
git commit -m "新增 build-engine Docker 部署: 后端镜像 + 前端镜像 + compose 编排"
```

---

### Task 4: Update `.gitignore` — add marker files

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Append marker ignores**

Add under the `# Dev script state markers` comment (create section if needed):

```
# Dev script state markers
.alembic_done
.seed_done
.requirements.hash
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "更新 .gitignore 加入 marker 文件忽略规则"
```

---

### Task 5: Update Makefile — ensure build-engine target

**Files:**
- Modify: `Makefile`

Current Makefile already has `dev`, `test*`, `clean`, `build-*` targets. Need to:
- Add `build-engine` target for Docker Compose build
- Fix `test-frontend`: `npm test` → `pnpm test` (frontend uses pnpm workspace)

- [ ] **Step 1: Add build-engine target to Makefile**

Add near the Docker builds section:

```makefile
# ── build-engine Docker Compose ────────────────────────────
.PHONY: build-engine up-engine down-engine

build-engine:
	cd docker && docker compose build

up-engine:
	cd docker && docker compose up -d

down-engine:
	cd docker && docker compose down
```

- [ ] **Step 2: Commit**

```bash
git add Makefile
git commit -m "更新 Makefile 添加 build-engine docker-compose 入口"
```

---

### Task 6: Update `README.md` — rewrite quick start

**Files:**
- Modify: `README.md`

Rewrite the "快速开始" section:
1. Prerequisites (add `uv`)
2. **一键启动（推荐）** — `make dev` or `./scripts/start.sh`
3. **分步启动（可选）** — manual steps
4. **Docker 部署** — `make up-engine`
5. Verification + FAQ

- [ ] **Step 1: Edit README quick start**

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "更新 README 快速开始适配 monorepo 和 Makefile"
```

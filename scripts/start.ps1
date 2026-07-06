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

$ROOT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent

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
if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 未找到 node，请先安装 Node.js >= 18"
    exit 1
}
$nodeVer = [int]((node --version) -replace '^v', '' -replace '\..*', '')
if ($nodeVer -lt 18) {
    warn "Node.js 版本过低 ($(node --version))，建议 >= 18"
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
    Receive-Job $backendJob 2>&1 | Out-Host
    Receive-Job $frontendJob 2>&1 | Out-Host
} finally {
    info "正在停止服务..."
    $backendJob, $frontendJob | Stop-Job -ErrorAction SilentlyContinue
    $backendJob, $frontendJob | Remove-Job -Force -ErrorAction SilentlyContinue
    ok "服务已停止"
}

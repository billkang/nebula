#!/usr/bin/env bash
#
# start.sh — Nebula 一键启动脚本
# 自动完成环境初始化并同时启动前后端服务
#
set -e

# ── 颜色 ──────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

# ── 停止已有服务 ────────────────────────────────────
stop_service_on_port() {
    local port=$1
    local name=$2
    local pids
    pids=$(lsof -ti "tcp:$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        warn "发现 ${name}(:${port}) 正在运行 (PID: $(echo "$pids" | tr '\n' ' '))，正在停止..."
        kill $pids 2>/dev/null || true
        sleep 1
        pids=$(lsof -ti "tcp:$port" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            kill -9 $pids 2>/dev/null || true
            sleep 1
        fi
        ok "${name}(:${port}) 已停止"
    fi
}

stop_service_on_port 8000  "后端"
stop_service_on_port 5173  "前端"

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
if ! command -v node &>/dev/null; then
	echo "错误: 未找到 node，请先安装 Node.js >= 18"
	exit 1
fi
NODE_VERSION=$(node --version | sed 's/^v//' | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ] 2>/dev/null; then
	warn "Node.js 版本过低 ($(node --version))，建议 >= 18"
fi

# ── 清理函数（捕获 Ctrl+C） ───────────────────────────
cleanup() {
    echo ""
    info "正在停止服务..."
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
    ok "服务已停止"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── 入口 ────────────────────────────────────────────────
echo ""
echo -e "${BLUE}════════════════════════════════${NC}"
echo -e "${BLUE}  星云 · Nebula 一键启动${NC}"
echo -e "${BLUE}════════════════════════════════${NC}"
echo ""

# ============================================================
# 后端
# ============================================================
echo -e "${YELLOW}━━━ 后端 (Backend) ━━━${NC}"
cd "$ROOT_DIR/packages/build-engine/backend"

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

# 1. 虚拟环境
if [ ! -d ".venv" ]; then
    info "创建 Python 虚拟环境 (uv)..."
    uv venv --quiet
    ok "虚拟环境已创建"
else
    ok "虚拟环境已存在"
fi

# 2. 依赖安装（通过 requirements.txt hash 判断变更）
REQ_HASH_FILE=".requirements.hash"
if command -v md5 &>/dev/null; then
    CURRENT_HASH=$(md5 -q pyproject.toml)
else
    CURRENT_HASH=$(md5sum pyproject.toml | awk '{print $1}')
fi

if [ ! -f "$REQ_HASH_FILE" ] || [ "$(cat "$REQ_HASH_FILE")" != "$CURRENT_HASH" ]; then
    info "安装 Python 依赖..."
    uv sync --quiet
    echo "$CURRENT_HASH" > "$REQ_HASH_FILE"
    ok "依赖已安装"
else
    ok "依赖已安装，跳过"
fi

# 3. 环境配置
if [ ! -f ".env" ]; then
    cp .env.example .env
    ok "已从 .env.example 生成 .env（请修改 JWT_SECRET 等生产配置）"
else
    ok ".env 已存在"
fi

# 4. 数据库迁移（idempotent）
if [ ! -f ".alembic_done" ]; then
    info "执行数据库迁移..."
    uv run alembic upgrade head
    touch ".alembic_done"
    ok "数据库迁移完成"
else
    ok "数据库迁移已执行，跳过"
fi

# 5. 初始化数据（idempotent）
if [ ! -f ".seed_done" ]; then
    info "初始化内置用户..."
    uv run python seed.py
    touch ".seed_done"
    ok "内置用户初始化完成"
else
    ok "内置用户已初始化，跳过"
fi

# ============================================================
# 前端
# ============================================================
echo ""
echo -e "${YELLOW}━━━ 前端 (Frontend) ━━━${NC}"
cd "$ROOT_DIR/packages/build-engine/frontend"

if [ ! -d "node_modules" ]; then
    info "安装前端依赖..."
    pnpm install
    ok "前端依赖安装完成"
else
    ok "前端依赖已安装"
fi

# ============================================================
# 启动服务
# ============================================================
echo ""
echo -e "${YELLOW}━━━ 启动服务 ━━━${NC}"

cd "$ROOT_DIR/packages/build-engine/backend"
info "启动后端 (http://localhost:8000)..."
uv run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# 轮询等待后端就绪（最多 30 秒）
info "等待后端就绪..."
for i in $(seq 1 30); do
	if python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost',8000)); s.close()" 2>/dev/null; then
		ok "后端就绪"
		break
	fi
	sleep 1
done

cd "$ROOT_DIR/packages/build-engine/frontend"
info "启动前端 (http://localhost:5173)..."
pnpm run dev &
FRONTEND_PID=$!

# ── 输出汇总 ─────────────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Nebula 已启动！${NC}"
echo -e "${GREEN}${NC}"
echo -e "${GREEN}  后端 API   → http://localhost:8000${NC}"
echo -e "${GREEN}  API 文档   → http://localhost:8000/docs${NC}"
echo -e "${GREEN}  前端       → http://localhost:5173${NC}"
echo -e "${GREEN}${NC}"
echo -e "${GREEN}  登录账号：${NC}"
echo -e "${GREEN}    admin / 123456  (管理员)${NC}"
echo -e "${GREEN}    pm    / 123456  (产品经理)${NC}"
echo -e "${GREEN}${NC}"
echo -e "${GREEN}  按 Ctrl+C 停止所有服务${NC}"
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo ""

wait

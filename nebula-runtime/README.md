# Nebula Runtime

星云平台运行时引擎 — 加载 Build Artifact 并运行业务应用的轻量运行平台。

## 架构定位

```
┌──────────────────────────────┐
│    nebula-platform            │
│    (构建引擎：对话/文档/编码)  │
│         ↓ Build Artifact     │
│         ↓ HTTP Push          │
├──────────────────────────────┤
│    nebula-runtime  ← 本仓库   │
│    (加载 Artifact → 启动容器) │
│         ↓                    │
│    PM 浏览器预览              │
└──────────────────────────────┘
```

nebula-runtime 是独立于 nebula-platform 的轻量代码库：
- 不含构建引擎逻辑（对话、文档生成、编码调度）
- 可独立部署，升级不影响已部署的业务代码
- 一行命令启动

## 快速开始

### 前置条件

- Python 3.12+
- Docker（用于运行业务应用容器）

### 安装

```bash
pip install -r requirements.txt
```

### 配置

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

主要配置项：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `RUNTIME_PORT` | 8001 | API 服务端口 |
| `ARTIFACTS_DIR` | ./artifacts | Artifact 存储目录 |
| `PLATFORM_URL` | （空） | 上游 nebula-platform 地址（可选） |

### 启动

```bash
uvicorn app.main:app --port 8001 --reload
```

或使用 Docker Compose：

```bash
docker-compose up
```

## API 文档

### 健康检查

```
GET /health
→ {"status": "ok"}
```

### Runtime API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/runtime/start` | 加载 Artifact 并启动应用 |
| POST | `/api/v1/runtime/stop` | 停止当前运行的应用 |
| GET | `/api/v1/runtime/status` | 查询运行状态 |
| GET | `/api/v1/runtime/logs` | 获取运行日志 |
| POST | `/api/v1/runtime/push` | 接收平台推送的 Artifact |
| GET | `/api/v1/runtime/versions` | 列出可用 Artifact 版本 |

### Artifact Registry API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/registry/artifacts?project_id=` | 列出项目 Artifact 版本 |
| GET | `/api/v1/registry/artifacts/:project/:version` | 获取版本详情 |
| POST | `/api/v1/registry/artifacts/:project` | 注册新的 Artifact（上传 tar.gz） |
| DELETE | `/api/v1/registry/artifacts/:project/:version` | 删除指定版本 |

### 启动应用

```bash
POST /api/v1/runtime/start
{
  "project_id": "proj-abc",
  "version": "v1"
}
→ {
  "status": "running",
  "url": "http://localhost:54321",
  "container_id": "abc123...",
  "project_id": "proj-abc",
  "version": "v1"
}
```

## 与 nebula-platform 集成

1. 在 nebula-platform 的 `.env` 中配置 `RUNTIME_URL=http://localhost:8001`
2. 平台构建完成后自动推送 Artifact 到 runtime
3. PM 在平台前端可点击"在 Runtime 中预览"直接查看运行效果

## 项目结构

```
nebula-runtime/
├── app/
│   ├── main.py              ← FastAPI 应用入口
│   ├── config.py            ← 环境配置
│   ├── api/
│   │   ├── runtime.py       ← 运行时 API
│   │   └── registry.py      ← Artifact Registry API
│   └── services/
│       ├── container_service.py  ← Docker 容器管理
│       └── registry_service.py   ← Artifact 注册管理
├── tests/
│   ├── test_registry_service.py
│   ├── test_runtime_api.py
│   └── test_integration.py
├── artifacts/               ← Artifact 存储（gitignored）
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 测试

```bash
pytest tests/ -v
```

## Context

星云 MVP 阶段产出的 Build Artifact 目前只能以文件形式存储在 `projects/<id>/artifacts/` 目录下，没有独立的运行时环境来加载和预览。PM 无法在浏览器中看到代码的实际运行效果，交付验收只能依赖代码审查。

当前架构中，nebula-platform 承担所有职责（构建 + 运行），但两者混杂在一起不利于：
1. 平台自身的升级迭代不影响已部署的业务代码
2. 客户独立部署运行环境时不需要整个平台
3. 运行环境的审计和安全边界

## Goals / Non-Goals

**Goals:**

- 创建独立于 nebula-platform 的 `nebula-runtime` 代码库
- nebula-runtime 能加载版本化的 Build Artifact 并启动 Docker 容器运行业务应用
- PM 能通过浏览器直接访问运行中的应用
- Artifact Registry 实现版本化管理，支持选择版本和回退
- 提供运行时 API 供平台和外部系统集成
- nebula-runtime 一行命令可启动（docker-compose up）

**Non-Goals:**

- nebula-runtime 不做代码修改（修改在 platform 沙箱中完成，见 code-sandbox change）
- nebula-runtime 不含构建引擎逻辑（对话、文档生成、编码调度）
- v1 不实现多租户隔离（一个 runtime 实例服务一个项目）
- v1 不做运行时监控告警（后续 Phase 5 补充）
- v1 不实现 LangGraph 集群运行（预留接口，暂不实现）

## Decisions

### 1. 技术栈：Python + FastAPI（与 platform 保持一致）

**决策：** nebula-runtime 使用 Python + FastAPI 作为运行时 API 框架。

与 nebula-platform 使用同一技术栈，降低维护成本。Docker SDK for Python 操作容器，FastAPI 提供 REST API。
前端不引入 React——运行时不需要管理界面，健康检查和版本管理通过 API 即可。

**备选方案：**
- Go（性能更好，镜像更小）→ 但增加了技术栈维护成本，v1 收益不大
- Node.js（事件驱动）→ Python 仍然是大头，统一栈更简单

### 2. 容器管理：Docker SDK for Python

**决策：** 使用 `docker-py`（Docker SDK for Python）管理容器生命周期。

nebula-runtime 与 Docker daemon 同一主机部署，通过 Unix socket 通信。
启动/停止容器、获取日志、检查状态均通过 SDK 完成。

```
runtime → docker-py → /var/run/docker.sock → Docker daemon → container
```

**备选方案：**
- subprocess 调用 docker CLI → 解析 stdout 不稳定，错误处理繁琐
- HTTP API 直接调 docker → 需要手动管理连接和认证

### 3. Artifact 存储：文件系统（v1），暂不引入外部存储

**决策：** v1 使用本地文件系统存储 Artifact，目录结构与 platform 保持一致。

```
artifacts/<project-id>/<version>/
  ├── src/
  ├── requirements.txt
  ├── Dockerfile
  └── manifest.json
```

Artifact 从 platform 通过 API push 到 runtime，或通过共享卷映射。
后续如果需要分布式部署，可迁移到对象存储（S3/MinIO）。

### 4. 网络拓扑：nebula-runtime 与 platform 分离但可通过网络通信

```
┌──────────────────┐          ┌──────────────────┐
│ nebula-platform  │  HTTP    │ nebula-runtime   │
│ (port 8000)      │ ──────→  │ (port 8001)      │
│                  │          │                  │
│ build → push     │          │ load → run       │
│ artifact         │          │ application      │
└──────────────────┘          └────────┬─────────┘
                                       │ Docker
                                       ▼
                              ┌──────────────────┐
                              │ Business App     │
                              │ (random port)    │
                              │ PM browser → :80 │
                              └──────────────────┘
```

PM 访问路径：`http://runtime-host/runtime/` → 反向代理到业务应用的容器端口。

### 5. 单个 runtime 实例：一次运行一个应用

**决策：** v1 一个 nebula-runtime 实例同时最多运行一个应用。启动新应用时自动停止当前应用。

简化状态管理，避免端口冲突和资源竞争。后续可按需启动多个 runtime 实例。

## 项目结构

```
nebula-runtime/
  ├── Dockerfile                    ← 运行时引擎自身镜像
  ├── docker-compose.yml            ← 一行命令启动
  ├── requirements.txt              ← 依赖声明
  ├── .env.example                  ← 环境变量模板
  ├── app/
  │   ├── __init__.py
  │   ├── main.py                   ← FastAPI 应用入口
  │   ├── config.py                 ← pydantic-settings 配置
  │   ├── api/
  │   │   ├── __init__.py
  │   │   ├── runtime.py            ← 运行时 API（start/stop/status/logs）
  │   │   └── registry.py           ← Artifact Registry API
  │   ├── services/
  │   │   ├── __init__.py
  │   │   ├── container_service.py   ← Docker 容器管理
  │   │   └── registry_service.py    ← Artifact Registry 管理
  │   └── models/
  │       └── __init__.py
  ├── artifacts/                     ← Artifact 存储目录（gitignored）
  └── tests/
      ├── __init__.py
      ├── test_container_service.py
      └── test_registry_service.py
```

## 核心流程

### Artifact 推送流程

```
Platform 构建完成
  → POST /api/v1/runtime/push (multipart: tar.gz + manifest)
  → Runtime 解压到 artifacts/<project-id>/<version>/
  → 校验 manifest.json 完整性
  → 返回版本号 + 确认
  → 状态: ready
```

### 应用启动流程

```
Client (Platform / PM)
  → POST /api/v1/runtime/start { "project_id": "...", "version": "..." }
  → 如有运行中的应用 → 先 stop + remove
  → 从 artifacts/ 读取 Artifact
  → docker build -t nebula-app-<project-id> .
  → docker run -d --cpus=1 --memory=512m -p <port>:<app-port> nebula-app-<project-id>
  → 等待健康检查通过（最多 30s）
  → 返回访问 URL
  → 状态: running
```

### 交付验收流程

```
PM 在 Platform 上完成构建
  → Platform 推送 Artifact 到 Runtime
  → Runtime 自动/手动启动应用
  → PM 浏览器访问运行中的应用
  → PM 确认 ✓ / 驳回 ✗
    ├── 确认 → Artifact 标记为 "delivered"，设计文档版本锁定
    └── 驳回 → 回退到 Platform 沙箱修改 → 重新构建 → 推送新版本
```

## Risks / Trade-offs

| 风险 | 缓解措施 |
|---|---|
| Docker build 可能因 Artifact 中的 Dockerfile 错误而失败 | 启动前验证 Dockerfile 语法；失败时返回完整 build log |
| 容器端口冲突（多个应用共存） | v1 一次只运行一个应用，端口由 runtime 自动分配 |
| Docker daemon 不可用 | 启动时前置检查 docker info；不可用时报错而非静默失败 |
| 容器资源泄漏（启动后忘记停止） | runtime 启动新应用时自动停掉旧应用；提供 stop API |
| Artifact 磁盘占用过大 | v1 不做配额限制，但删除 API 可清理旧版本 |
| Artifact 文件结构不完整 | Registry 接收时自动校验 manifest.json + 必要文件存在性 |
| Runtime API 鉴权缺失 | v1 仅在内部网络使用（与 platform 同网段），暂不加认证。后续引入 token |

## Migration Plan

1. **创建 nebula-runtime 代码库** — 从零新建，不修改现有 platform 代码
2. **实现注册服务** — Registry API + 文件存储
3. **实现容器服务** — Docker SDK 集成 + 容器生命周期管理
4. **实现运行时 API** — start/stop/status/logs/push/versions
5. **为 platform 增加推送能力** — 在 platform 构建完成后增加 push 到 runtime 的步骤
6. **集成测试** — 端到端验证：platform 构建 → push → runtime 加载 → 应用可访问

### 回退策略

- nebula-runtime 是新项目，不影响现有 MVP 代码
- 如果集成有问题，platform 仍可按原有方式使用（只是没有运行时预览）
- 回退只需停止 runtime 服务，不涉及数据库迁移或代码回滚

## Open Questions

- [ ] runtime 反向代理方案：使用 nginx/traefik 还是直接暴露容器端口给 PM？
- [ ] nebula-runtime 的 docker-compose.yml 是否应该包含 PostgreSQL 和 Redis 服务？
- [ ] 是否需要在 runtime 中也存储 nebula-platform 的项目元数据（轻量级），还是完全独立查询？
- [ ] Artifact push 使用 HTTP multipart 上传还是先共享存储再传引用？

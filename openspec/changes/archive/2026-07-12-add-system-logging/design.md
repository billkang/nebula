## Context

Nebula 的 build-engine 后端和前端均缺乏有效的日志记录能力。后端使用 `logging.getLogger(__name__)` 但无配置（日志被静默丢弃），前端无任何日志或错误捕获机制。本次变更为 build-engine 增加全栈日志能力，支撑开发阶段的调试排错。

### 现状
- 后端 5 个模块有 `logger.*()` 调用但静默失效
- 全局异常处理程序返回 JSON 但不记录
- 无请求/响应日志中间件
- 前端零日志输出、零错误边界
- `.env` 无日志相关配置

### 架构决策基础
- 标准库 `logging`，不引入新依赖
- build-engine 范围（runtime-engine 后续扩展）
- 日志写入文件 + 控制台同步输出

## Goals / Non-Goals

**Goals:**
- 后端启动时自动配置日志系统（级别、格式、文件输出）
- 请求级日志中间件记录 method/path/status/duration/IP/user
- 异常日志化（全局异常处理记录 traceback）
- 前端日志工具支持 console + 后端上报双重输出
- 前端 Error Boundary 捕获渲染错误
- 日志上报 API（JWT 鉴权）
- 环境变量控制日志级别和目录

**Non-Goals:**
- runtime-engine 日志（本次仅 build-engine）
- 共享日志模块（shared-python 延迟到后续版本）
- JSON 结构化日志（本次人类可读格式）
- 分布式追踪 / 日志告警
- 前端用户行为分析 / 事件埋点

## Decisions

### D1: Logging initialization in lifespan

**Decision:** 在 `main.py` 的 `lifespan()` 函数中调用 `setup_logging()` 初始化日志系统。

**Rationale:** `lifespan()` 在应用启动时执行，早于任何请求处理。此时配置日志系统可以确保所有模块的 `getLogger(__name__)` 调用立即生效。

**Alternative considered:** 模块级 `import time` 初始化。问题：Python 模块导入顺序不可控，日志配置可能晚于某些模块的 `getLogger()` 调用。

### D2: LogConfig module location

**Decision:** 新增 `app/core/logging.py` 作为日志配置模块。创建 `app/core/` 目录。

**Rationale:** 日志配置是基础设施层，与 `config.py`（应用配置）同级。`core/` 目录可以承载后续的工具类功能。

**Files:**
- `src/app/core/__init__.py`（新）
- `src/app/core/logging.py`（新）

### D3: Structured logging middleware approach

**Decision:** 自定义 ASGI 中间件，在响应完成后写一条日志。中间件通过 `call_next` 包裹请求处理流程，记录 start_time → 等待响应 → 记录 end_time 和 status_code。

**Rationale:** 这种方式能正确处理 SSE 流式响应——中间件不介入流式内容，只在流结束后获取最终状态和时间。

**Key implementation approach:**
```
class RequestLogMiddleware:
    async def __call__(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = int((time.time() - start) * 1000)
        # 读取 response 的 status_code（对 SSE 也是最终的）
        log_entry = {method, path, status, duration, ip, user_id}
        logger.info(...)
        return response
```

**Body capture (DEBUG only):**
- Body capture 通过包装 `request.body()` 和 `response.body_iterator` 实现
- 截断至 10KB 避免日志膨胀
- 仅在 `LOG_LEVEL=DEBUG` 时启用

### D4: Frontend logger architecture

**Decision:** 前端日志采用双层设计：

```
┌──────────────┐     console.*    ┌─────────────┐
│              │ ──────────────→  │  DevTools    │
│  logger.ts   │                  │  Console     │
│  (队列 + 批  │                  └─────────────┘
│   量发送)    │     POST /api/v1/logs (batch)
│              │ ──────────────→  ┌─────────────┐
└──────────────┘                  │  后端日志文件 │
                                  └─────────────┘
```

**Batch strategy:** 10 entries or 5 seconds (whichever comes first).
**Page close:** `navigator.sendBeacon()` for best-effort flush.
**Silent degradation:** API call failures are caught and logged to console only.

### D5: Log entry format (backend)

```
2026-07-12 14:30:00,123 | INFO  | app.middleware.logging | GET /api/v1/projects → 200 (45ms) | ip=127.0.0.1 user=admin
2026-07-12 14:30:01,456 | ERROR | app.services.project_service | Failed to create project directory
Traceback (most recent call last):
  File "...", line ..., in create_project
    ...
```

### D6: Business stage logging (biz_logger)

**Decision:** Add a `biz_logger` helper in `app/core/logging.py` that provides structured business stage markers.

The biz_logger uses a dedicated `nebula.biz` logger so business logs can be independently filtered (e.g., `grep '\[BIZ\]' nebula-2026-07-12.log`).

**Log format:**
```
2026-07-12 14:30:00,123 | INFO  | nebula.biz | [BIZ] [CREATE_PROJECT] START | project_name="用户注册" username=admin
2026-07-12 14:30:00,234 | INFO  | nebula.biz | [BIZ] [CREATE_PROJECT] [translate-name] | name="用户注册" → change_name=user-registration
2026-07-12 14:30:01,456 | INFO  | nebula.biz | [BIZ] [CREATE_PROJECT] [db-record] | project_id=abc-123
2026-07-12 14:30:02,789 | INFO  | nebula.biz | [BIZ] [CREATE_PROJECT] END status=ok | project_id=abc-123 duration_ms=2890
```

**API:**
```python
def biz_stage_start(stage: str, **metadata): ...
def biz_stage_end(stage: str, status: str = "ok", **metadata): ...
def biz_step(stage: str, step: str, **metadata): ...
```

**Stage markers defined:**
| Stage Marker | Source File | Trigger |
|---|---|---|
| `CREATE_PROJECT` | `project_service.py` | `create_project()` called |
| `SPEC_GEN` | `doc_service.py` | `generate_docs()` called |
| `CODE_GEN` | `build_service.py` | `build()` executed |
| `AGENT_PHASE` | `chat_service.py` | Agent phase transitions |

### D7: Per-project log file

**Decision:** When a project is created, set up a dedicated `TimedRotatingFileHandler` for that project's business logs.

**File location:** `projects/{username}-{change_name}/logs/{change_name}.log`

**Implementation:**
1. `setup_project_logging(project_dir, change_name)` creates a handler with filter that only captures `nebula.biz` messages containing the project's `change_name`
2. Called from `ProjectService.create_project()` after successful directory creation
3. Project log uses same daily rotation and 30-day retention as system log
4. Business logs (`[BIZ]`) go to both system log AND project log simultaneously

**Why per-project handler instead of separate logger:**
- A single logger (`nebula.biz`) is simpler — no need to manage per-project logger instances
- The handler's filter checks metadata (project_id / change_name) to decide which entries to accept
- All business logging goes through the same `biz_stage_start/step/end` API regardless

### D8: Environment variables

```python
# config.py additions
log_level: str = "INFO"    # DEBUG | INFO | WARNING | ERROR | CRITICAL
log_dir: str = "./logs"    # relative or absolute path
```

`.env` additions:
```
LOG_LEVEL=INFO
LOG_DIR=./logs
```

## Change Scope Matrix

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/app/core/__init__.py` | **新增** | core 包初始化 |
| `src/app/core/logging.py` | **新增** | `setup_logging()` 函数 + `biz_logger` 业务阶段日志工具 |
| `src/app/middleware/logging.py` | **新增** | `RequestLogMiddleware` ASGI 中间件 |
| `src/app/main.py` | **修改** | lifespan 中调用 `setup_logging()`；添加中间件；异常处理记录日志 |
| `src/app/config.py` | **修改** | 增加 `log_level` 和 `log_dir` 字段 |
| `src/app/api/router.py` | **修改** | 注册 logs router |
| `src/app/api/logs.py` | **新增** | `POST /api/v1/logs` 日志上报端点 |
| `src/app/schemas/log.py` | **新增** | 日志上报请求/响应 Schema |
| `src/app/services/project_service.py` | **修改** | `create_project()` 增加 `[BIZ] [CREATE_PROJECT]` 阶段标记 |
| `src/app/services/doc_service.py` | **修改** | `generate_docs()` 增加 `[BIZ] [SPEC_GEN]` 阶段标记 |
| `src/app/services/build_service.py` | **修改** | `build()` 增加 `[BIZ] [CODE_GEN]` 阶段标记 |
| `src/app/services/chat_service.py` | **修改** | `send_message()` 增加 `[BIZ] [AGENT_PHASE]` 阶段过渡标记 |
| `.env` / `.env.example` | **修改** | 增加 LOG_LEVEL、LOG_DIR |
| `src/utils/logger.ts` | **新增** | 前端日志工具（info/warn/error + 批量上报） |
| `src/components/ErrorBoundary.tsx` | **新增** | 全局 React Error Boundary |
| `src/api/client.ts` | **修改** | 请求/响应日志埋点 |
| `src/App.tsx` | **修改** | 包裹 Error Boundary |
| `src/main.tsx` | **不修改** | 无需变更 |

## API Contract

### POST /api/v1/logs

```json
// Request (single)
{
  "level": "info",
  "message": "User logged in",
  "timestamp": "2026-07-12T14:30:00Z",
  "stack": null
}

// Request (batch)
[
  {"level": "info", "message": "...", "timestamp": "...", "stack": null},
  {"level": "error", "message": "...", "timestamp": "...", "stack": "..."}
]

// Response (200)
{
  "data": {"accepted": true}
}

// Response (401 - no auth)
{
  "detail": "Not authenticated"
}
```

### Python Schema

```python
class LogEntry(BaseModel):
    level: Literal["debug", "info", "warning", "error", "critical"]
    message: str
    timestamp: datetime
    stack: str | None = None

class LogResponse(BaseModel):
    accepted: bool = True
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **日志文件磁盘占用** | 30 天保留 + 每日轮转；`LOG_DIR` 可挂载到外部卷 |
| **DEBUG 模式下请求体记录敏感数据** | Body capture 仅在 DEBUG 级别生效；生产环境默认 INFO |
| **前端日志批量发送的网络开销** | 10 条/5 秒批量；用户不活跃时几乎无网络请求 |
| **sendBeacon 兼容性** | `navigator.sendBeacon` 在所有现代浏览器支持；降级：静默丢弃 |
| **日志上报 API 被滥用** | JWT 鉴权 + 仅限登录用户；日志内容不信任，纯文本写入 |

## Migration Plan

无需数据迁移。部署步骤：
1. 创建 `app/core/` 和日志配置文件
2. 更新 `config.py` 和 `.env.example`
3. 修改 `main.py` 和 router
4. 添加 middleware 和 logs API
5. 添加前端 logger、Error Boundary
6. 更新 `client.ts`
7. 测试验证日志输出

## Open Questions

- 无（grill-me 已全部确认）

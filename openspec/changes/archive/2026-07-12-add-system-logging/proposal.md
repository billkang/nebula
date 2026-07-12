## Why

Nebula 系统的后端和前端目前均缺乏有效的日志记录机制。后端 5 处 `logger.*()` 调用因缺少日志配置而静默丢弃；前端异常被空 `catch {}` 静默吞掉，且无错误边界。这导致开发阶段排查问题只能靠猜测，严重影响开发效率和 bug 定位速度。本次增加全栈日志能力，为开发调试和系统行为分析提供基础支撑。

## What Changes

- **后端日志配置引导**: 新增日志初始化代码，在 FastAPI 应用启动时配置日志级别、格式和文件输出
- **日志级别环境变量**: `.env` 新增 `LOG_LEVEL`（默认 `INFO`）和 `LOG_DIR`（默认 `./logs`）
- **请求日志中间件**: 新增 ASGI 中间件，记录每个请求的 method、path、status_code、duration
- **异常日志化**: 全局异常处理程序记录完整 traceback
- **前端日志工具**: 新增 `logger` 工具函数（`info/warn/error`），统一前端日志输出格式
- **Error Boundary**: 新增 React Error Boundary 组件，捕获渲染错误并记录
- **API 客户端日志**: 前端 API 调用层记录请求/响应摘要
- **日志上报接口**: 后端新增 `POST /api/v1/logs` 接口，供前端上报日志到后端统一写入文件
- **业务主流程日志**: 在项目创建、SDD 文档生成、代码生成三大业务阶段增加结构化日志，使用 `[BIZ] [STAGE] [STEP]` 标记格式，记录各阶段的进入/退出/耗时/状态
- **项目独立日志文件**: 每个项目在 `projects/{username}-{change_name}/logs/` 下拥有独立的日志文件，仅记录该项目全生命周期的业务阶段日志

## Capabilities

### New Capabilities
- `backend-logging`: 后端日志配置、请求日志中间件、异常日志化，支持按级别和文件输出
- `frontend-logging`: 前端日志工具、Error Boundary、API 客户端日志记录
- `log-reporting-api`: 前端日志上报的后端 API 端点

### Modified Capabilities
<!-- No existing specs are being modified -->

## Design Decisions (grill-me 确认)

| # | 决策点 | 结论 |
|---|--------|------|
| 1 | 日志框架 | 标准库 `logging`，不引入 `loguru` |
| 2 | 前端日志策略 | 双重输出：开发时 `console.*` + 通过 API 上报后端写入文件 |
| 3 | Error Boundary | 先做一个全局兜底组件，页面级按需追加 |
| 4 | 日志文件位置 | `LOG_DIR` 默认 `./logs`，build-engine 和 runtime-engine 各自独立目录 |
| 5 | 日志上报鉴权 | `POST /api/v1/logs` 复用 JWT 鉴权 |
| 6 | 文件轮转 | `midnight` 每日轮转，保留 30 天，文件名格式 `nebula-{日期}.log`，同时输出到控制台 |
| 7 | 请求日志字段 | `INFO` 记录 Method + Path + Status + Duration + Client IP + User ID；`DEBUG` 额外记录 Request/Response Body |

## Impact

| 层 | 影响 |
|----|------|
| **Backend** | 新增 `app/core/logging.py` 日志配置模块（含 `biz_logger` 业务日志工具）；修改 `app/main.py` 初始化时加载日志配置并注册中间件；新增 `app/api/logs.py` 日志上报路由；修改 `project_service.py`、`doc_service.py`、`build_service.py`、`chat_service.py` 增加业务阶段日志标记 |
| **Frontend** | 新增 `src/utils/logger.ts` 日志工具；新增 `src/components/ErrorBoundary.tsx`；修改 `src/api/client.ts` 增加请求日志 |
| **Biz Logging** | 修改 `project_service.py`、`doc_service.py`、`build_service.py`、`chat_service.py`，注入 `[BIZ] [STAGE] [STEP]` 业务阶段标记 |
| **Project Logs** | 每个项目在 `projects/{username}-{change_name}/logs/{change_name}.log` 独立记录完整任务过程 |
| **Config** | `.env` / `.env.example` 新增 `LOG_LEVEL`、`LOG_DIR` |
| **Dependencies** | 无新增依赖（后端用标准库 `logging`，前端无新增依赖） |
| **DB** | 无 |
| **Permission** | 无 |
| **Tenant** | 无 |

## Known Limitations

- **同步日志 I/O 性能**：标准库 `TimedRotatingFileHandler` 的写文件操作是同步的，高并发场景下可能阻塞请求处理线程。v2 可按需引入异步日志或对接外部日志服务。
- **循环日志风险**：前端日志上报会调用 API client，而 API client 的日志逻辑又会记录该请求，产生 `POST /api/v1/logs → 200` 的自循环日志条目。实现时应过滤日志上报接口的请求日志。
- **URL 参数敏感信息暴露**：请求日志会记录完整 URL path 和 query params（含 token），即使 body capture 只在 DEBUG 级别启用。当前不处理，用户需知晓此限制。v2 可引入敏感字段过滤规则。
- **低频问题回溯能力**：30 天日志保留期对低频、偶发 bug 的排查可能不足。如需更长的回溯窗口，可增大保留天数或对接外部日志归档服务。

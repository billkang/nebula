## 1. 配置与环境变量

- [x] 1.1 `src/app/config.py` 增加 `log_level` 和 `log_dir` 字段
- [x] 1.2 `.env` / `.env.example` 增加 `LOG_LEVEL` 和 `LOG_DIR` 配置项

## 2. 后端日志核心

- [x] 2.1 创建 `src/app/core/` 包（`__init__.py`）
- [x] 2.2 创建 `src/app/core/logging.py`：实现 `setup_logging()` 函数，配置 `TimedRotatingFileHandler`（每日轮转、保留30天）、`StreamHandler`（控制台输出）、日志格式（`时间 | 级别 | 模块 | 消息`）
- [x] 2.3 修改 `src/app/main.py`：在 `lifespan()` 中调用 `setup_logging()`

## 3. 请求日志中间件

- [x] 3.1 创建 `src/app/middleware/logging.py`：实现 `RequestLogMiddleware` ASGI 中间件，记录 method/path/status/duration/IP/user_id
- [x] 3.2 `main.py` 注册 `RequestLogMiddleware`（CORS 中间件之后）
- [x] 3.3 DEBUG 级别 body 捕获支持（request/response body，截断 10KB）

## 4. 异常日志化

- [x] 4.1 `main.py` 中 `validation_error_handler` 增加异常日志记录
- [x] 4.2 `main.py` 中 `generic_error_handler` 增加完整 traceback 日志记录

## 5. 日志上报 API

- [x] 5.1 创建 `src/app/schemas/log.py`：定义 `LogEntry`、`LogResponse` Schema
- [x] 5.2 创建 `src/app/api/logs.py`：实现 `POST /api/v1/logs` 端点（JWT 鉴权、单条/批量兼容、best-effort 校验）
- [x] 5.3 修改 `src/app/api/router.py`：注册 logs router

## 6. 前端日志工具

- [x] 6.1 创建 `src/utils/logger.ts`：实现 `logger.info/warn/error()`，console 输出 + 批量队列 + 后端上报
- [x] 6.2 批量发送策略（10条/5秒触发） + `navigator.sendBeacon()` 页面关闭保底
- [x] 6.3 后端不可达时静默降级（不抛异常、console 继续输出）

## 7. 前端 Error Boundary

- [x] 7.1 创建 `src/components/ErrorBoundary.tsx`：类组件 Error Boundary，捕获渲染错误并调用 `logger.error()`
- [x] 7.2 展示 fallback UI（"Something went wrong" + Reload 按钮）
- [x] 7.3 修改 `src/App.tsx`：用 Error Boundary 包裹应用内容

## 8. API 客户端日志

- [x] 8.1 修改 `src/api/client.ts`：每次请求/响应记录 INFO 级别日志（method、path、status）
- [x] 8.2 4xx/5xx 响应及网络错误记录 ERROR 级别日志

## 9. 业务阶段日志 — 代码注入

- [x] 9.1 `project_service.py`：`create_project()` 增加 `[BIZ] [CREATE_PROJECT]` 阶段标记（START → translate-name → db-record → fs-init → openspec-init → END）
- [x] 9.2 `doc_service.py`：`generate_docs()` 增加 `[BIZ] [SPEC_GEN]` 阶段标记（START → write-context → create-change → proposal/specs/design/tasks → END）
- [x] 9.3 `build_service.py`：`build()` 增加 `[BIZ] [CODE_GEN]` 阶段标记（START → container-build → verify-artifacts → push-runtime → END）
- [x] 9.4 `chat_service.py`：`send_message()` 增加 `[BIZ] [AGENT_PHASE]` 阶段过渡标记（每次 phase 变化时记录 from/to）

## 10. 项目独立日志文件

- [x] 10.1 `core/logging.py`：新增 `setup_project_logging(project_dir, change_name)` 函数，配置 per-project `TimedRotatingFileHandler`
- [x] 10.2 `project_service.py`：`create_project()` 成功后调用 `setup_project_logging()`
- [x] 10.3 biz_logger 支持按 project_id 过滤写入项目日志

## 11. 测试

- [x] 11.1 后端：`setup_logging()` 单元测试（日志级别、文件输出、控制台输出）
- [x] 11.2 后端：请求日志中间件测试（request + SSE + DEBUG body capture）
- [x] 11.3 后端：`POST /api/v1/logs` 端点的鉴权和功能测试
- [x] 11.4 后端：异常处理程序日志化测试
- [x] 11.5 后端：`setup_project_logging()` 单元测试（per-project 日志文件创建和过滤）
- [x] 11.6 后端：`[BIZ]` 业务阶段标记集成测试（CREATE_PROJECT → SPEC_GEN → CODE_GEN 全链路）
- [x] 11.7 前端：Error Boundary 渲染测试
- [x] 11.8 前端：logger 工具单元测试
- [x] 11.9 端到端验证：build-engine 启动后日志文件创建、API 日志写入、前端日志上报、项目日志独立

## 12. 文档与收尾

- [x] 12.1 `.env.example` 添加日志相关配置注释
- [x] 12.2 检查现有 `logger.*()` 调用是否正常输出（provider.py, translation.py, project_service.py, docker_backend.py）
- [x] 12.3 确认日志文件结构：系统级 `logs/nebula-*.log` + 项目级 `projects/*/logs/*.log`

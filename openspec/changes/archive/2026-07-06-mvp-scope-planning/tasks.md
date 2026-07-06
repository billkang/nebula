## 1. 后端基础框架

- [ ] 1.1 初始化 FastAPI 项目结构（main.py、config.py、database.py）
- [ ] 1.2 配置 SQLAlchemy + Alembic，创建初始 migration
- [ ] 1.3 配置 .env 加载（pydantic-settings），含 DB 连接串、JWT secret
- [ ] 1.4 实现全局错误处理 + 统一响应格式

## 2. 用户认证（user-auth）

- [ ] 2.1 创建 User SQLAlchemy 模型（id/username/email/password/role/timestamps）
- [ ] 2.2 实现密码哈希（passlib bcrypt）+ JWT 签发（python-jose）
- [ ] 2.3 实现 POST /api/v1/auth/register 注册接口
- [ ] 2.4 实现 POST /api/v1/auth/login 登录接口
- [ ] 2.5 实现 GET /api/v1/auth/me 当前用户信息接口
- [ ] 2.6 实现 JWT 认证中间件（依赖注入方式）
- [ ] 2.7 创建 seed 脚本（初始化 admin + pm 内置用户）
- [ ] 2.8 编写 auth 相关 pytest 测试

## 3. 项目管理（project-management）

- [ ] 3.1 创建 Project SQLAlchemy 模型（id/name/description/owner_id/timestamps）
- [ ] 3.2 实现 GET /api/v1/projects 项目列表接口
- [ ] 3.3 实现 POST /api/v1/projects 创建项目接口
- [ ] 3.4 实现 GET /api/v1/projects/:id 项目详情接口
- [ ] 3.5 实现 DELETE /api/v1/projects/:id 删除项目接口（仅 admin）
- [ ] 3.6 实现 Alembic migration
- [ ] 3.7 编写 project 相关 pytest 测试

## 4. 前端基础框架

- [ ] 4.1 初始化 React + Vite + TypeScript + Tailwind 项目
- [ ] 4.2 配置路由（react-router-dom）：登录/注册/项目列表/对话/文档
- [ ] 4.3 配置 zustand 全局状态（用户信息、当前项目）
- [ ] 4.4 配置 @tanstack/react-query + API client 封装
- [ ] 4.5 实现 AppLayout（含 Sidebar 导航）
- [ ] 4.6 实现登录页 UI 和登录逻辑
- [ ] 4.7 实现注册页 UI 和注册逻辑

## 5. 对话 Agent（pm-chat-agent）

- [ ] 5.1 创建 Session + Message SQLAlchemy 模型
- [ ] 5.2 实现 LangGraph StateGraph（五段式状态机：greeting/collecting/clarifying/confirming/generating）
- [ ] 5.3 实现各阶段 node 函数（greeting_node / collect_node / clarify_node / confirm_node / generate_node）
- [ ] 5.4 实现条件路由（根据 State 内容决定流转方向）
- [ ] 5.5 实现对话消息的持久化存储
- [ ] 5.6 实现 Agent State 中的需求摘要和 Out of Scope 收集
- [ ] 5.7 实现 POST /api/v1/projects/:id/sessions/:sid/messages 消息发送 + Agent 响应
- [ ] 5.8 实现对话历史加载接口（GET /api/v1/sessions/:id/messages）
- [ ] 5.9 编写 Agent 相关 pytest 测试

## 6. 前端对话界面

- [ ] 6.1 实现项目对话页 layout（消息列表 + 输入框）
- [ ] 6.2 实现 MessageBubble 组件（区分用户/Agent 消息）
- [ ] 6.3 实现 MessageInput 组件（文本输入 + 发送按钮）
- [ ] 6.4 实现需求确认卡片组件（ConfirmCard：展示 Summary + Out of Scope）
- [ ] 6.5 实现对话时 Agent 状态的视觉反馈（输入中动画等）
- [ ] 6.6 对接 Chat API 实现消息发送与接收

## 7. 文档生成（doc-generation）

- [ ] 7.1 实现 OpenSpec CLI 调用服务（doc_service.py：生成 proposal/specs/design/tasks）
- [ ] 7.2 设计需求上下文从 Agent State 到 OpenSpec 输入的转换逻辑
- [ ] 7.3 实现 POST /api/v1/projects/:id/docs/generate 触发文档生成接口
- [ ] 7.4 实现 GET /api/v1/projects/:id/docs 文档列表接口
- [ ] 7.5 实现 GET /api/v1/projects/:id/docs/:type 文档详情接口
- [ ] 7.6 实现前端文档概览页（展示文档结构树）
- [ ] 7.7 实现前端文档查看器（Markdown 渲染）
- [ ] 7.8 对话确认后前端显示"生成文档"按钮

## 8. 编码执行器（coding-executor）

- [ ] 8.1 实现 executor_service.py：从 tasks.md 提取编码指令
- [ ] 8.2 实现 subprocess 调用本地 Claude Code 的执行逻辑
- [ ] 8.3 实现 POST /api/v1/projects/:id/execute 触发编码接口
- [ ] 8.4 实现 GET /api/v1/projects/:id/execute/status 编码状态接口
- [ ] 8.5 实现编码执行前的前置检查（claude --version）
- [ ] 8.6 实现失败重试逻辑
- [ ] 8.7 实现前端编码执行状态展示

## 9. 构建验证器（build-verifier）

- [ ] 9.1 实现 build_service.py：测试执行（pytest）+ 完整性校验
- [ ] 9.2 实现 manifest.json 生成和 tar 打包
- [ ] 9.3 创建 projects/<id>/artifacts/ 目录结构
- [ ] 9.4 实现 POST /api/v1/projects/:id/build 触发构建接口
- [ ] 9.5 实现 GET /api/v1/projects/:id/build/status 构建状态接口
- [ ] 9.6 实现 GET /api/v1/projects/:id/artifacts Artifact 列表接口
- [ ] 9.7 实现前端构建进度展示

## 10. 端到端集成

- [ ] 10.1 集成测试：完整的用户注册 → 创建项目 → 对话 → 文档生成 → 编码 → 构建链路
- [ ] 10.2 配置 Vite proxy / CORS 解决开发环境跨域
- [ ] 10.3 编写 README（启动方式、配置说明）
- [ ] 10.4 最终构建验证 + 完整链路手动测试

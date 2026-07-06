## ADDED Requirements

### Requirement: 编码执行触发
文档生成并通过用户确认后，系统 SHALL 支持触发编码执行，调用本地 Claude Code。

#### Scenario: 触发编码
- **WHEN** 用户确认文档并选择"开始编码"
- **THEN** 系统调用本地 Claude Code 执行编码任务

### Requirement: 代码输出目录
编码产出的代码 SHALL 写入 `projects/<project-id>/src/` 目录，与 change 目录（spec）分离。

#### Scenario: 代码写入
- **WHEN** Claude Code 执行完成
- **THEN** 代码写入 `projects/<project-id>/src/`
- **AND** `openspec/` 目录中的 spec 文件不受影响

### Requirement: 本地 Claude Code 执行
系统 SHALL 在本地调用 Claude Code CLI 执行编码指令。

#### Scenario: 指令生成
- **WHEN** 进入编码阶段
- **THEN** 系统将 tasks.md 转化为 Claude Code 可执行的编码指令
- **AND** 启动 Claude Code 进程执行

#### Scenario: 执行状态反馈
- **WHEN** Claude Code 正在执行
- **THEN** 前端显示编码执行中的进度信息

### Requirement: 执行失败处理
Claude Code 执行失败时，系统 SHALL 提供错误信息和重试能力。

#### Scenario: 编码失败
- **WHEN** Claude Code 返回错误或超时
- **THEN** 系统展示错误原因，允许用户重试

### Requirement: 源码即交付
v1 编码执行产出的代码 SHALL 为可直接运行的 Python/FastAPI 项目代码。

#### Scenario: 产出验证
- **WHEN** 编码执行完成
- **THEN** 产出代码包含完整的项目骨架（入口、路由、模型）
- **AND** 代码符合项目约定的代码风格（PEP 8、type hints、ruff 格式化）

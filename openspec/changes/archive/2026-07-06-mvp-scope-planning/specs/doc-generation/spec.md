## ADDED Requirements

### Requirement: 文档生成触发
对话收敛且用户确认范围后，系统 SHALL 在前端展示"生成文档"按钮，由用户点击触发 OpenSpec 文档生成。

#### Scenario: 确认后显示按钮
- **WHEN** 对话确认范围后
- **THEN** 前端显示"生成设计文档"按钮

#### Scenario: 用户点击生成
- **WHEN** 用户点击"生成设计文档"按钮
- **THEN** 系统调用 OpenSpec CLI，依次生成 proposal → specs → design → tasks

### Requirement: OpenSpec 输出
系统 SHALL 调用 OpenSpec CLI 生成设计文档，输出到项目关联的 change 目录。

#### Scenario: 完整文档生成
- **WHEN** OpenSpec CLI 执行完成
- **THEN** 生成 proposal.md + specs/ + design.md + tasks.md

#### Scenario: 生成失败处理
- **WHEN** OpenSpec CLI 执行过程中出错
- **THEN** 系统向前端返回错误信息，提示用户重试

### Requirement: 文档展示
系统 SHALL 在 Web 界面中展示 OpenSpec 生成的设计文档（只读）。

#### Scenario: 查看文档
- **WHEN** 文档生成完成
- **THEN** 前端展示 proposal、specs、design、tasks 的概览
- **AND** 用户可展开查看各文档的详细内容

### Requirement: 需求来源对接
OpenSpec 生成的 proposal SHALL 包含前述对话中定义的需求范围和 Out of Scope 清单。

#### Scenario: 上下文传递
- **WHEN** 触发文档生成
- **THEN** Agent 中收集的需求摘要和 Out of Scope 作为上下文传入 OpenSpec

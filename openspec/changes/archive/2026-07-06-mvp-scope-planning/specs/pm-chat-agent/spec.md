## ADDED Requirements

### Requirement: 对话启动
进入项目后，系统 SHALL 自动启动 LangGraph StateGraph 对话 Agent，进入 greeting 阶段。

#### Scenario: 进入项目自动问候
- **WHEN** 用户进入项目的对话页
- **THEN** Agent 发送欢迎消息，引导用户描述需求

### Requirement: 五段式对话流
对话 Agent SHALL 实现五段式状态机：greeting → collecting_reqs → clarifying_details → confirming_scope → trigger_doc_generation。

#### Scenario: greeting 阶段
- **WHEN** 对话处于 greeting 阶段
- **THEN** Agent 发送欢迎语并提示用户描述需求

#### Scenario: collecting_reqs 阶段
- **WHEN** 用户描述需求后
- **THEN** Agent 进入 collecting_reqs，收集目标、场景、期望产出等核心信息
- **AND** Agent 可追问 2-3 个问题补全信息

#### Scenario: clarifying_details 阶段
- **WHEN** 需求信息中有模糊点或需要权衡的内容
- **THEN** Agent 进入 clarifying_details，针对性追问

#### Scenario: confirming_scope 阶段
- **WHEN** 信息已充分
- **THEN** Agent 汇总"做什么"和"不做什么"清单，请求用户确认

#### Scenario: 用户推翻范围
- **WHEN** 用户确认时表示方向不对
- **THEN** Agent 回到 collecting_reqs 阶段重新收集

#### Scenario: 触发文档生成
- **WHEN** 用户确认范围正确
- **THEN** Agent 进入 trigger_doc_generation，结束对话
- **AND** 前端显示"生成文档"按钮供用户点击触发 OpenSpec

### Requirement: 对话状态持久化
系统 SHALL 保存对话历史，用户再次进入项目时可查看历史消息。

#### Scenario: 历史对话加载
- **WHEN** 用户重新进入一个已有对话记录的项目
- **THEN** 系统加载该项目的历史对话消息

### Requirement: 需求摘要生成
对话收敛后，Agent SHALL 整理需求摘要供确认。

#### Scenario: 确认前展示摘要
- **WHEN** Agent 进入 confirming_scope 阶段
- **THEN** Agent 展示需求摘要 + Out of Scope 清单
- **AND** 用户可确认或提出修改

### Requirement: State 数据结构
Agent State SHALL 包含 messages（对话历史）、phase（当前阶段）、req_summary（需求摘要）、out_of_scope（排除项）。

#### Scenario: State 正确流转
- **WHEN** 对话推进
- **THEN** State 中的 phase 按五段式状态机正确流转
- **AND** 每个阶段 Agent 行为符合阶段定义

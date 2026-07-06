## ADDED Requirements

### Requirement: 创建项目
系统 SHALL 允许已登录用户创建新项目，每个项目独立管理文档和代码。

#### Scenario: 成功创建项目
- **WHEN** 已登录用户填写项目名称和描述并提交
- **THEN** 系统创建项目，跳转到该项目对话页

#### Scenario: 未登录创建项目
- **WHEN** 未登录用户尝试创建项目
- **THEN** 系统返回未授权错误

### Requirement: 项目列表
系统 SHALL 展示当前用户可访问的所有项目列表。

#### Scenario: 查看项目列表
- **WHEN** 已登录用户访问项目列表页
- **THEN** 系统展示所有项目的名称、描述和创建时间

#### Scenario: 无项目时
- **WHEN** 用户是首次使用、尚无项目
- **THEN** 系统展示空状态提示和"创建第一个项目"引导按钮

### Requirement: 进入项目
系统 SHALL 允许用户选择一个项目进入其对话工作区。

#### Scenario: 进入项目对话
- **WHEN** 用户点击项目卡片
- **THEN** 系统跳转到该项目的对话页，加载历史消息

### Requirement: 多项目隔离
不同项目 SHALL 有独立的对话记录、设计文档和代码产物。

#### Scenario: 项目间数据不混合
- **WHEN** 用户在项目 A 中产生对话和文档
- **THEN** 项目 B 中 SHALL NOT 可见项目 A 的任何数据

### Requirement: 删除项目
系统 SHALL 允许 admin 角色删除项目。

#### Scenario: admin 删除项目
- **WHEN** admin 用户删除一个项目
- **THEN** 系统删除该项目及其所有关联数据

#### Scenario: member 删除项目
- **WHEN** member 用户尝试删除项目
- **THEN** 系统拒绝操作，提示权限不足

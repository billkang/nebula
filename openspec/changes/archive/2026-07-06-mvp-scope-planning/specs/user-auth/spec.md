## ADDED Requirements

### Requirement: 用户注册
系统 SHALL 提供用户注册功能，允许新用户创建账号。

#### Scenario: 成功注册
- **WHEN** 用户填写用户名、邮箱、密码并提交注册
- **THEN** 系统创建用户账号，返回成功消息，跳转到登录页

#### Scenario: 邮箱重复
- **WHEN** 用户注册时使用的邮箱已被注册
- **THEN** 系统提示"该邮箱已被注册"，拒绝创建

#### Scenario: 密码强度不足
- **WHEN** 用户密码长度少于 6 位
- **THEN** 系统提示"密码长度至少 6 位"

### Requirement: 用户登录
系统 SHALL 支持用户通过用户名/邮箱 + 密码登录，发放 JWT Token。

#### Scenario: 成功登录
- **WHEN** 用户输入正确的用户名/邮箱和密码
- **THEN** 系统返回 JWT Token，跳转到项目列表页

#### Scenario: 错误密码
- **WHEN** 用户输入错误的密码
- **THEN** 系统返回"用户名或密码错误"

### Requirement: 内置用户
系统 SHALL 提供内置用户，初始化后可直接使用，无需注册。

#### Scenario: 初始用户存在
- **WHEN** 系统首次启动
- **THEN** 数据库中 SHALL 存在 admin 和 pm 两个内置用户

#### Scenario: 内置用户登录
- **WHEN** 用户使用内置账号凭据登录
- **THEN** 系统 SHALL 验证通过，返回 JWT Token

### Requirement: 角色权限
系统 SHALL 实现两级角色：admin（全权限）和 member（使用平台）。

#### Scenario: admin 权限
- **WHEN** admin 用户执行任何操作
- **THEN** 系统 SHALL 允许所有操作

#### Scenario: member 权限限制
- **WHEN** member 用户尝试管理用户
- **THEN** 系统 SHALL 拒绝访问

### Requirement: 角色分配
新注册用户 SHALL 默认为 member 角色，admin 角色仅通过预置或手动指定。

#### Scenario: 注册角色
- **WHEN** 新用户完成注册
- **THEN** 系统 SHALL 为其分配 member 角色

#### Scenario: admin 不受注册影响
- **WHEN** 新用户注册
- **THEN** 系统 SHALL NOT 创建新的 admin 角色用户

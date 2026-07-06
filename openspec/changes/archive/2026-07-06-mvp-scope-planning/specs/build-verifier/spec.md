## ADDED Requirements

### Requirement: 测试执行
编码完成后，系统 SHALL 在 `projects/<project-id>/src/` 目录下运行 pytest，验证代码正确性。

#### Scenario: 测试通过
- **WHEN** pytest 运行且全部通过
- **THEN** 测试步骤标记为通过

#### Scenario: 测试失败
- **WHEN** pytest 运行存在失败用例
- **THEN** 系统展示失败测试详情，提示用户修复后重试

### Requirement: 产物完整性校验
系统 SHALL 验证 `projects/<project-id>/` 目录包含必要文件。

#### Scenario: 必要文件存在
- **WHEN** 构建验证器执行完整性检查
- **THEN** 确认 `src/` 目录非空、`requirements.txt` 存在、`Dockerfile` 存在

#### Scenario: 缺少必要文件
- **WHEN** 检查发现缺少必要文件
- **THEN** 系统提示缺少的文件列表

### Requirement: Build Artifact 打包
测试和校验通过后，系统 SHALL 产出版本化的 Build Artifact。

#### Scenario: 打包 Artifact
- **WHEN** 测试通过且完整性校验通过
- **THEN** 系统生成 manifest.json（记录版本号、入口、依赖）
- **AND** 将 `src/` + `requirements.txt` + `Dockerfile` + `manifest.json` 打包为 tar

#### Scenario: Artifact 存储
- **WHEN** Artifact 打包完成
- **THEN** 存储到 `projects/<project-id>/artifacts/v1/`

### Requirement: 构建状态展示
系统 SHALL 在前端展示构建验证的步骤和状态。

#### Scenario: 进度展示
- **WHEN** 构建验证器正在执行
- **THEN** 前端展示当前步骤（测试中/校验中/打包中）和完成状态

## Why

星云 MVP 已能生成可独立运行的业务代码并打包为 Build Artifact，但目前 Artifact 只能停留在文件系统中，无法让 PM 在浏览器中实际看到代码的运行效果。缺少一个轻量的运行时引擎来加载 Artifact、启动业务应用、提供在线预览——这是 PM 交付验收闭环中"可见可跑"的关键缺失环节。

## What Changes

- 创建独立的 **nebula-runtime** 代码库，与 nebula-platform 分离
- nebula-runtime 加载版本化的 Build Artifact → 启动 Docker 容器 → PM 浏览器访问
- 实现 Artifact Registry：管理所有历史版本的 Artifact，支持版本选择和回退
- 提供运行时 API（健康检查、Artifact 加载状态、日志查看）
- 运行时引擎中不含任何构建引擎逻辑（对话、文档生成、编码调度），保持轻量和可审计
- nebula-runtime 可独立部署，运行平台升级不影响已部署的业务代码
- Artifact 附带 Dockerfile 和 manifest.json，无需平台即可独立运行

## Capabilities

### New Capabilities

- `runtime-engine`: nebula-runtime 运行时引擎，加载 Build Artifact 并启动业务应用
- `artifact-registry`: Build Artifact 的版本化管理与存储

### Modified Capabilities

无（这是全新的运行时能力，不修改现有功能）

## Impact

- **新增代码库**：`nebula-runtime/` 独立项目，全新创建
- **新增依赖**：Docker SDK for Python、FastAPI（轻量运行时 API）
- **与 nebula-platform 的集成点**：platform 完成构建后，将 Artifact 推送到 runtime 的 Registry；runtime 向 platform 暴露状态查询接口（Artifact 是否启动、运行是否正常）
- **不影响现有 MVP 代码**：platform 侧无修改，只新增推送 Artifact 的能力
- **对用户可见的变化**：PM 在构建完成后可点击"预览"直接跳转到运行中的业务应用页面

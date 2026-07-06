## Why

MVP 阶段的构建管道是单向的：对话 → 文档 → 编码 → 构建 → 交付。PM 在构建完成后只能看到"构建成功"的状态，无法对生成的代码做任何调整。如果代码不满足预期，只能重新对话、重新生成——整个流程重来一遍。

需要提供一个**代码沙箱**，让 PM 在 nebula-platform 中直接查看和修改 Claude Code 生成的源代码，修改后触发重新构建，推送新 Artifact 版本到运行时预览。这样 PM 能快速微调，不需要重启整个对话流程。

## What Changes

- 在 nebula-platform 中集成 Monaco Editor 作为在线代码编辑器
- PM 在构建完成后可查看 Artifact 的完整源码（目录树 + 文件内容）
- PM 可直接修改源码文件，修改内容暂存到工作区
- 修改完成后点击"重新构建"，触发完整构建管道
- 构建管道从修改后的源码重新生成 Artifact（新版本号）
- 新 Artifact 推送到 nebula-runtime 重新预览
- 保留修改历史：每次构建前自动保存快照，支持对比 diff
- 修改行为**始终在 nebula-platform 上进行**，nebula-runtime 不做任何代码修改

## Capabilities

### New Capabilities

- `code-sandbox`: Monaco Editor 在线代码编辑器，支持文件树浏览、源码修改、保存快照、对比 diff
- `rebuild-pipeline`: 从沙箱修改触发重新构建，生成新的 Artifact 版本

### Modified Capabilities

无（code-sandbox 和 rebuild-pipeline 均为全新能力，不修改现有功能）

## Impact

- **新增前端页面/组件**：沙箱页面（文件树面板 + 编辑器面板）、保存/重新构建按钮
- **新增后端服务**：sandbox_service.py（工作区管理、快照管理、diff 计算）
- **修改已有服务**：build_service.py 支持从工作区目录构建（而非仅从原始 src）
- **与 nebula-runtime 的集成**：重新构建后自动推送到 runtime 预览
- **新增前端依赖**：Monaco Editor React 组件（@monaco-editor/react）
- **不影响 MVP 现有流程**：原始对话 → 文档 → 编码 → 构建链路不变，沙箱作为可选的"修改后重试"路径

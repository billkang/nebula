## 1. 后端：SandboxService 基础

- [x] 1.1 创建 `app/services/sandbox_service.py` 服务模块
- [x] 1.2 实现 `init_sandbox(project_id, version)` — 从 Artifact 复制源码到沙箱工作区
- [x] 1.3 实现 `get_sandbox_files(project_id)` — 递归扫描工作区文件树
- [x] 1.4 实现 `get_file_content(project_id, file_path)` — 读取工作区文件
- [x] 1.5 实现 `save_file(project_id, file_path, content)` — 保存文件到工作区
- [x] 1.6 编写 sandbox_service 核心方法 pytest 测试

## 2. 后端：快照管理

- [x] 2.1 实现 `create_snapshot(project_id, description)` — 完整复制工作区为快照
- [x] 2.2 实现 `get_snapshots(project_id)` — 列出所有快照（含元数据）
- [x] 2.3 实现 `restore_from_snapshot(project_id, snapshot_id)` — 从快照恢复工作区
- [x] 2.4 实现自动清理逻辑：保留最近 10 个快照
- [x] 2.5 编写快照管理相关 pytest 测试

## 3. 后端：Diff 计算

- [x] 3.1 实现 `get_diff(project_id, file_path)` — 计算文件与原始 Artifact 的 diff
- [x] 3.2 实现 diff 结果格式化（行级别的添加/删除/修改标记）
- [x] 3.3 实现 `get_original_content(project_id, file_path)` — 从原始 Artifact 读取基线版本
- [x] 3.4 编写 diff 相关 pytest 测试

## 4. 后端：Sandbox API + 重建触发

- [x] 4.1 创建 `app/api/sandbox.py` 路由模块
- [x] 4.2 实现 `POST /api/v1/projects/:id/sandbox/init` 初始化沙箱
- [x] 4.3 实现 `GET /api/v1/projects/:id/sandbox/files` 文件树
- [x] 4.4 实现 `GET /api/v1/projects/:id/sandbox/files/*` 读取文件
- [x] 4.5 实现 `PUT /api/v1/projects/:id/sandbox/files/*` 保存文件
- [x] 4.6 实现 `POST /api/v1/projects/:id/sandbox/snapshots` 创建快照
- [x] 4.7 实现 `GET /api/v1/projects/:id/sandbox/snapshots` 快照列表
- [x] 4.8 实现 `POST /api/v1/projects/:id/sandbox/restore/:sid` 从快照恢复
- [x] 4.9 实现 `GET /api/v1/projects/:id/sandbox/diff/*` diff 接口
- [x] 4.10 实现 `POST /api/v1/projects/:id/sandbox/rebuild` 触发重建（含自动快照 + 推送 runtime）
- [x] 4.11 修改 `app/api/router.py` 注册 sandbox 路由
- [x] 4.12 编写 Sandbox API 相关 pytest 测试

## 5. 后端：BuildService 适配

- [x] 5.1 修改 `BuildService.build()` 支持 `source_dir` 参数，从沙箱目录构建
- [x] 5.2 确保重建时版本号自动递增（从当前最大版本 +1）
- [x] 5.3 确保重建后自动推送到 nebula-runtime（runtime-engine 的 push API）
- [x] 5.4 编写重建相关的集成测试

## 6. 前端：Monaco Editor 集成

- [x] 6.1 安装 `@monaco-editor/react` 依赖
- [x] 6.2 创建 `src/components/SandboxMonacoEditor.tsx` — Monaco Editor 封装组件（语法高亮、只读/编辑模式切换）
- [x] 6.3 创建 `src/components/FileTreePanel.tsx` — 文件树面板（递归树、展开/折叠、文件图标、未保存标记）
- [x] 6.4 创建 `src/components/SandboxHeader.tsx` — 沙箱顶部栏（面包屑导航、已修改文件数、操作按钮组）
- [x] 6.5 创建 `src/components/SandboxDiffView.tsx` — diff 对比面板（左右分栏显示新旧版本差异）
- [x] 6.6 创建 `src/components/SandboxSnapshotPanel.tsx` — 快照历史面板（时间线列表 + 恢复按钮）

## 7. 前端：Sandbox 页面

- [x] 7.1 创建 `src/pages/Sandbox.tsx` — 沙箱主页面（Header + FileTree + Editor 三栏布局）
- [x] 7.2 实现文件选择逻辑（点击文件树 → 编辑器加载内容）
- [x] 7.3 实现文件修改跟踪（未保存标记、修改计数）
- [x] 7.4 实现 Ctrl+S / Cmd+S 快捷保存
- [x] 7.5 实现 Save All / Restore Original / View Diff 操作
- [x] 7.6 实现 Rebuild 按钮和重建过程中的进度显示
- [x] 7.7 实现重建完成后的"Preview in Runtime"跳转按钮
- [x] 7.8 在 `App.tsx` 添加路由 `/projects/:id/sandbox`
- [x] 7.9 对接后端 Sandbox API（react-query hooks）

## 8. 前端：Chat 页面集成

- [x] 8.1 在 Chat 页面的构建成功状态后增加"在沙箱中编辑"按钮
- [x] 8.2 按钮跳转到 `/projects/:id/sandbox`
- [x] 8.3 如果沙箱未初始化，先调用 init 再跳转

## 9. 端到端集成测试

- [x] 9.1 编写集成测试：构建完成 → 进入沙箱 → 编辑文件 → 保存 → 重建 → 验证新 Artifact 版本
- [x] 9.2 编写集成测试：重建后自动推送到 runtime（mock runtime API）
- [x] 9.3 编写集成测试：创建快照 → 修改文件 → 从快照恢复 → 验证文件恢复
- [x] 9.4 编写集成测试：修改后重建 → 测试运行在修改后的代码上

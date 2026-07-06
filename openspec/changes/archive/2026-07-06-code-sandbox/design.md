## Context

MVP 构建管道当前是单向的：Claude Code 生成代码 → 构建 → 打包为 Artifact。PM 无法对生成的代码做任何调整。如果代码不满足预期（例如样式不对、逻辑有偏差），只能重新开启对话流程，效率很低。

本项目与 runtime-engine 同属 Phase 1，两者协作关系：
- **code-sandbox**（本 change）：在 nebula-platform 中提供代码编辑能力，修改后触發重新构建
- **runtime-engine**（已同步进行）：接收新 Artifact 并运行预览

```
Platform 编码完成 → 构建 → Artifact v1
                           ↓
                   PM 预览（runtime-engine）
                           ↓
                  ┌─ 满意 → 交付
                  │
                  不满意
                  │
           Monaco Editor 编辑源码
                  ↓
             重新构建 → Artifact v2 → 重新预览
```

## Goals / Non-Goals

**Goals:**

- 在 nebula-platform 中集成 Monaco Editor，PM 可查看和修改 Artifact 源码
- 文件树面板展示 Artifact 的完整`src/`目录结构
- 修改后保存到隔离的工作区目录，不污染原始 Artifact
- 触发重新构建，生成新的 Artifact 版本
- 自动推送到 nebula-runtime 预览
- 提供快照管理，支持对比 diff 和回退

**Non-Goals:**

- v1 不做多人协作编辑（一次只有一人操作）
- v1 不做代码沙箱中的终端/命令行（纯文件编辑）
- v1 不做 Lint/类型检查的实时反馈（仅保存/构建时校验）
- 不在 nebula-runtime 中编辑代码（沙箱只在 platform 侧）

## Decisions

### 1. 编辑器选型：Monaco Editor

**决策：** 使用 `@monaco-editor/react` React 组件封装。

Monaco Editor（VS Code 内核）提供完整 IDE 级别的编辑体验：语法高亮、代码折叠、多光标编辑、自动缩进。相比 CodeMirror（轻量但功能少），Monaco 更符合"PM 直接改源码"的场景——界面接近 IDE，降低学习成本。

**备选方案：**
- CodeMirror → 更轻量（~100KB vs ~2MB），但缺少 VS Code 级别的功能
- Ace Editor → 维护不如 Monaco 活跃

### 2. 工作区存储：文件系统，不引入数据库

**决策：** 沙箱工作区使用文件系统存储，每个项目一个隔离目录。

```
projects/<project-id>/
  ├── src/                    ← 原始生成的源码（不可变）
  ├── sandbox/                ← 沙箱工作区（PM 修改的目标）
  │   ├── src/                ← 工作区源码副本
  │   ├── requirements.txt    ← 可修改
  │   ├── Dockerfile          ← 可修改
  │   └── sandbox.json        ← 沙箱元信息
  ├── sandbox_snapshots/      ← 快照（在 sandbox 外避免 pytest 冲突）
  │   ├── 20260706_120000/
  │   └── 20260706_123000/
  └── artifacts/
      ├── v1/                 ← 原始 Artifact
      └── v2/                 ← 沙箱重建后的 Artifact
```

工作区在首次进入沙箱时从原始 Artifact 复制创建。
快照是工作区的完整副本（含元数据）。

### 3. 重建流程复用现有构建管道

**决策：** 沙箱重建直接复用 MVP 已有的 `BuildService`，仅变更源目录路径。

```
原始构建路径：
  BuildService.build(project_id) → 从 projects/<id>/src/ 构建

沙箱重建路径：
  BuildService.build(project_id, source_dir="sandbox/src") → 从 projects/<id>/sandbox/src/ 构建
```

不创建新的构建逻辑，降低维护成本和出错风险。
构建结果用同一 Artifact Registry 管理，自动递增版本号。

### 4. 快照机制：软复制

**决策：** 快照使用文件复制（非 git），每次构建前自动创建。

不使用 git 的原因：
- 沙箱是 PM 使用，不期望 PM 理解 git 概念
- 快照是自动触发的，不需要 commit message
- 快照数量有限（保留最近 10 个），磁盘占用可控

用 `shutil.copytree` 复制工作区到快照目录，附带 `metadata.json`（时间戳、Artifact 版本、操作描述）。

### 5. 前端架构：独立页面路由

**决策：** 沙箱作为独立页面 `projects/:id/sandbox`，通过路由导航进入。

```
/projects/:id           → 对话页
/projects/:id/docs      → 文档页
/projects/:id/sandbox   → 代码沙箱（新增）
```

对话页的构建完成后增加"在沙箱中编辑"按钮，跳转到沙箱页面。
沙箱页面顶部有导航面包屑（项目名 → 文档 → 沙箱）。

## 前端组件结构

```
SandboxPage
├── HeaderBar
│   ├── Breadcrumb（项目名 / 沙箱）
│   ├── FileStatus（已修改 N 个文件）
│   └── ActionButtons
│       ├── Save All (Ctrl+S)
│       ├── View Diff
│       ├── Restore Original
│       └── Trigger Rebuild 🚀
├── FileTreePanel（左，可折叠）
│   └── FileTreeNode（递归）
└── EditorPanel（右）
    ├── MonacoEditor
    ├── TabBar（打开的文件标签）
    └── StatusBar（行号/列号/文件类型）
```

## 后端新增服务

### sandbox_service.py

```python
class SandboxService:
    @staticmethod
    def init_sandbox(project_id: str, artifact_version: str) -> dict:
        """从 Artifact 复制源码到沙箱工作区"""

    @staticmethod
    def get_sandbox_files(project_id: str) -> list[dict]:
        """获取沙箱工作区文件树"""

    @staticmethod
    def get_file_content(project_id: str, file_path: str) -> str:
        """读取工作区文件内容"""

    @staticmethod
    def save_file(project_id: str, file_path: str, content: str) -> dict:
        """保存文件到工作区"""

    @staticmethod
    def create_snapshot(project_id: str, description: str = "") -> dict:
        """创建工作区快照"""

    @staticmethod
    def get_diff(project_id: str, file_path: str) -> dict:
        """计算文件与原始 Artifact 的 diff"""

    @staticmethod
    def restore_from_snapshot(project_id: str, snapshot_id: str) -> dict:
        """从快照恢复工作区"""

    @staticmethod
    def get_snapshots(project_id: str) -> list[dict]:
        """列出所有快照"""

    @staticmethod
    def trigger_rebuild(project_id: str) -> dict:
        """创建快照 → 调用 BuildService → 推送 runtime"""
```

### Sandbox API

```
POST   /api/v1/projects/:id/sandbox/init         ← 初始化沙箱
GET    /api/v1/projects/:id/sandbox/files         ← 文件树
GET    /api/v1/projects/:id/sandbox/files/*       ← 读取文件
PUT    /api/v1/projects/:id/sandbox/files/*       ← 保存文件
POST   /api/v1/projects/:id/sandbox/snapshots     ← 创建快照
GET    /api/v1/projects/:id/sandbox/snapshots     ← 快照列表
POST   /api/v1/projects/:id/sandbox/restore/:sid  ← 从快照恢复
GET    /api/v1/projects/:id/sandbox/diff/*        ← diff 文件
POST   /api/v1/projects/:id/sandbox/rebuild       ← 触发重建
```

## 完整流程

```
构建完成（Chat 页面）
  ↓ PM 点击「在沙箱中编辑」
  ↓
SandboxService.init_sandbox()
  → 复制 artifacts/<project>/v1/ → projects/<project>/sandbox/
  → 重定向到 /projects/:id/sandbox
  ↓
PM 浏览/修改代码（FileTree + Monaco Editor）
  ↓
PM 点击「Rebuild」
  ↓
SandboxService.trigger_rebuild()
  1. create_snapshot() — 自动保存当前状态
  2. BuildService.build(project_id, source_dir="sandbox/src")
  3. 自动 push 到 runtime（POST /api/v1/runtime/push）
  4. 返回新 Artifact 版本号 + 预览 URL
  ↓
PM 点击「Preview」跳转到运行时查看效果
  ↓
┌─ 满意 → 交付
│
不满意 → 继续编辑 → 再次 Rebuild
```

## Architecture Integration

```
┌──────────────────────────────────────────────────┐
│                nebula-platform                     │
│                                                    │
│  Chat Page → Build → Artifact v1                   │
│                         ↓                          │
│  Sandbox Page ← Monaco Editor ← FileTree           │
│       ↓                                            │
│  SandboxService.trigger_rebuild()                  │
│       ↓                                            │
│  BuildService.build(source_dir="sandbox")          │
│       ↓                                            │
│  Artifact v2                                       │
│       ↓                                            │
│  push to runtime (HTTP) ──────┐                   │
└───────────────────────────────┼───────────────────┘
                                │
                ┌───────────────▼───────────────────┐
                │           nebula-runtime            │
                │                                    │
                │  Runtime starts v2 container       │
                │  PM previews in browser            │
                └────────────────────────────────────┘
```

## 前端依赖变更

```
npm install @monaco-editor/react
```

不引入其他新依赖。现有的 React、TypeScript、Tailwind、zustand、react-query 足够支撑。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|---|---|
| Monaco Editor 包体积较大（~2MB） | 按需加载（动态 import），仅在进入沙箱页面时加载 |
| 沙箱工作区文件过多（大量文件同时修改） | 限制一次最多显示 200 个文件。超出时折叠为目录摘要 |
| 快照磁盘占用膨胀（每次构建前都复制全部文件） | 保留最近 10 个快照，自动清理旧的；快照只复制 src/ 不复制 node_modules |
| PM 误删关键文件（requirements.txt / Dockerfile） | 重建时的完整性检查会报错，提示缺失文件。可一键恢复 |
| 同时编辑多人冲突 | v1 不做多人编辑。每个沙箱绑定一个 session |
| 重建过程中 PM 关闭页面 | 重建在后台进行，完成后生成 Artifact。PM 重新打开时可看到完成状态 |

## Migration Plan

1. **后端：实现 SandboxService** — 文件管理、快照、diff 计算
2. **后端：实现 Sandbox API** — 注册路由
3. **前端：安装 Monaco Editor** — `npm install @monaco-editor/react`
4. **前端：实现 SandboxPage** — FileTreePanel + EditorPanel + HeaderBar
5. **前端：嵌入 Chat 页面** — 构建完成后增加"在沙箱中编辑"按钮
6. **后端：修改 BuildService** — 支持从 sandbox 目录构建
7. **集成测试** — 端到端：编辑 → 重建 → 推送 → runtime 预览

### 回退策略

- 沙箱是增量新增，不修改 MVP 现有功能
- 如果不启用到沙箱页面，Chat 页面正常可用
- 回退只需停止沙箱 API 路由，不影响构建流程
- 工作区文件可手动清理（目录存在但无人使用无副作用）

## Open Questions

- [ ] 是否需要文件创建/删除能力？还是只允许修改现有文件？
- [ ] 快照命名策略：时间戳 vs 语义化（如"调整前"、"第二轮修改后"）？
- [ ] 是否需要在沙箱中显示构建状态（从平台 Chat 页面复用 StatusBadge）？
- [ ] Monaco Editor 主题：使用 Light 还是 Dark 主题？或者允许 PM 切换？

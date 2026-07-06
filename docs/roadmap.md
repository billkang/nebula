# 星云 · Nebula — 产品路线图

> 最后更新：2026-07-06
> 状态：Phase 1a（runtime-engine）✅, Phase 1b（code-sandbox）✅

---

## 当前状态

MVP v1（Phase 0）已全部完成。Phase 1a（runtime-engine）和 Phase 1b（code-sandbox）已实现。

| 模块 | 状态 |
|---|---|
| 后端脚手架（FastAPI + SQLAlchemy + Alembic） | ✅ |
| 用户认证（注册/登录/JWT/内置用户） | ✅ |
| 项目管理（CRUD/权限隔离） | ✅ |
| LangGraph 对话 Agent（5段式 StateGraph） | ✅ |
| 对话 API + 持久化 | ✅ |
| OpenSpec 文档生成服务 | ✅ |
| 编码执行器（subprocess Claude Code） | ✅ |
| 构建验证器（测试 + 打包 Artifact） | ✅ |
| 前端（所有页面 + 组件） | ✅ |
| 运行时引擎（nebula-runtime） | ✅ |
| 代码沙箱（Monaco Editor + 快照 + Diff + 重建） | ✅ |
| 测试 | **88/88 全过** |

---

## Openspec Changes 总览

| Phase | Change | 路径 | 状态 |
|---|---|---|---|
| 1a | `runtime-engine` | `openspec/changes/runtime-engine/` | ✅ **已实现**（28 测试通过） |
| 1b | `code-sandbox` | `openspec/changes/code-sandbox/` | ✅ **已实现**（26 测试通过） |
| 2 | `docker-executor` | `openspec/changes/docker-executor/` | ⏳ 未开始 |
| 3 | `skill-system` | `openspec/changes/skill-system/` | ⏳ 未开始 |
| 4 | `protocol-gateway` | `openspec/changes/protocol-gateway/` | ⏳ 未开始 |
| 5 | `infrastructure` | `openspec/changes/infrastructure/` | ⏳ 未开始 |

每个 change 走 SDD 流程：proposal → specs → design → tasks → 实现

---

## 路线图总览

```
Phase 1 ─→ Phase 2 ─→ Phase 3 ─→ Phase 4 ─→ Phase 5
 运行时引擎       Docker       Skill      协议网关     基础设施
 + 代码沙箱       容器化       体系       A2A/MCP     完善
                 编码执行                  Gateway
```

---

## Phase 1：运行时引擎 + 代码沙箱 ✅

**目标：让 MVP 产出的代码真正可见可跑，PM 能在浏览器预览和微调**

### 1.1 运行时引擎（nebula-runtime）✅

- **独立的轻量代码库**，可独立部署
- Artifact Registry（注册/列裴/获取/删除版本，自动递增，完整性校验）
- Docker 容器管理（构建/运行/停止/日志/状态，资源限制，健康检查）
- Runtime API（start/stop/status/logs/push/versions）
- 平台集成：构建后自动推送 Artifact，前端预览按钮
- **28 测试通过**

### 1.2 代码沙箱 ✅

- **位置：** nebula-platform，非 nebula-runtime
- Monaco Editor 集成（语法高亮、代码折叠、多语言支持）
- 文件树面板（递归展开/折叠、修改标记、文件图标）
- 工作区管理：从 Artifact 提取源码到隔离沙箱目录
- 快照管理：自动创建 + 手动快照 + 从快照恢复（保留最近 10 个）
- Diff 对比：当前工作区 vs 原始 Artifact（行级 unified diff）
- 一键重建：自动快照 → BuildService 从沙箱构建 → 推送到 runtime
- `Ctrl+S` 快捷保存、未保存标记、重建进度展示
- **26 测试通过**

### 1.3 交付验收闭环

```
PM 在浏览器中预览运行效果
  → PM 确认 ✓ / 驳回 ✗
    ├── 确认 → Artifact 标记为「可交付」，锁定设计文档版本
    └── 驳回 → 进入沙箱修改源代码 → 重建 → 重新预览
```

### 关键设计

- 修改行为**始终在开发平台**（nebula-platform），不在运行平台改代码
- 修改后**重新走构建管道**，生成新的 Artifact 版本
- 运行平台**只管加载 Artifact 运行预览**，不做修改
- Artifact Registry 保存所有历史版本，可回退

---

## Phase 2：Docker 容器化编码执行

**目标：替换本地 subprocess 调用，实现环境隔离**

- 编码容器（大镜像，含 Claude Code SDK 等开发工具）
- 构建容器（小镜像，alpine + Python，验证依赖 + 测试 + 打包）
- 两容器生命周期分离
- 抽象 CoderBackend 接口，v1 Docker → v2 可扩展 A2A

```python
class CoderBackend(ABC):
    @abstractmethod
    async def execute_development(self, spec: dict, skill: Skill, project_dir: str) -> DevelopmentResult:
        ...
```

### Openspec Change

| Change | 路径 | 内容 |
|---|---|---|
| `docker-executor` | `openspec/changes/docker-executor/` | 编码容器 + 构建容器 + CoderBackend 抽象 |

---

## Phase 3：Skill 体系

**目标：把需求翻译成精确的编码指令模板包**

### Skill 结构

```
skills/<skill-name>/
  ├── skill.yaml             → 元信息（名称、适用场景、when_to_use）
  ├── clarify.md             → 需要向 PM 问的问题
  ├── blueprint.md           → 架构蓝图（目录结构、数据模型、API）
  ├── coding-prompt.md       → 给 Claude Code 的精确编码指令
  ├── verify.md              → 验证标准（测试要求、验收条件）
  └── variants/              → 技术栈变体（Python / TypeScript 等）
```

### MVP 首批 Skill 集合

| Skill | 用途 | 优先级 |
|---|---|---|
| `style-backend` | Python 后端代码风格约束 | P0 |
| `style-frontend` | React 前端代码风格约束 | P0 |
| `gen-service` | 生成 API + 数据层 + 业务逻辑 | P0 |
| `gen-crud` | 生成 CRUD 页面（表单 + 表格 + 详情） | P1 |
| `testcase` | 生成单元测试 / E2E 测试 | P1 |
| `harden` | 安全加固 + 输入校验 | P2 |
| `commit` | commit message / changelog 生成 | P2 |

### 质量保障

```
LLM 生成 Skill
  → 自动验证：蓝图结构完整性、引用闭合
  → 自动测试：用此 Skill 跑最小示例，验证产出可用
  → 人工 review（内部团队确认后才进入生产库）
  → 版本化：上线后支持 A/B 对比、回退
```

---

## Phase 4：协议网关

**目标：标准化外部工具调用和 Agent 间通信**

| 组件 | 职责 |
|---|---|
| MCP Registry | 外部工具接入注册中心 |
| MCP Gateway | 外部工具调用代理 |
| A2A Registry | Agent 间通信注册中心 |
| A2A Gateway | Agent 间通信代理 |

---

## Phase 5：基础设施完善

**目标：生产环境就绪**

| 任务 | 说明 |
|---|---|
| SQLite → PostgreSQL | 连接串切换 + 全量功能验证 |
| 多租户 / 细粒度权限 | 从两级角色扩展到完整权限模型 |
| OAuth / SSO | 第三方登录支持 |
| 监控告警 | 平台自身 + Agent 运行时监控 |

---

## Phase 依赖关系图

```
Phase 1（运行时+沙箱）✅
  │
  ├── Phase 2（Docker 容器化）
  │     │
  │     └── Phase 3（Skill 体系）── Phase 4（协议网关）
  │                                             │
  └───────────────────────────────────────── Phase 5（基础设施）
```

- Phase 1 无前置依赖，最优先 ✅
- Phase 2 无前置依赖，可与 Phase 1 并行
- Phase 3 依赖 Phase 2（容器化后才能稳定执行 Skill 生成的编码指令）
- Phase 4 依赖 Phase 3（Skill 体系完善后才需要多 Agent 协作）
- Phase 5 独立于上层，但建议从 SQLite 切换到 PG 后做彻底验证

---

## 测试统计

| 套件 | 数量 |
|---|---|
| platform 后端（认证/项目/Agent/集成） | 34 |
| nebula-runtime（注册表/运行时 API/集成） | 28 |
| 代码沙箱（SandboxService/Sandbox API） | 26 |
| **合计** | **88** |

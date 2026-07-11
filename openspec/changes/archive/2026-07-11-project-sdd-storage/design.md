## Context

当前 `DocService` 硬编码 `CHANGE_NAME = "mvp-scope-planning"`，所有用户项目的 SDD 文档都写入后端根目录 `openspec/changes/mvp-scope-planning/`。这在 MVP 阶段可以工作，但无法支持多用户、多项目。

LLM Provider 层和 change_name 翻译已经实现（#arc llm-provider）。现在需要：
- 项目创建时自动创建文件系统目录并 `openspec init`
- DocService 使用 `{username}-{change_name}` 路径，而非硬编码
- 项目删除时清理磁盘

## Goals / Non-Goals

**Goals:**
- Project 模型：id 改为 auto-increment integer，新增 change_name 列
- 项目创建时创建 `projects/{username}-{change_name>/` 目录并运行 `openspec init --tools none`
- DocService.generate_docs 使用项目目录运行 openspec CLI
- DocService 支持多 change 列表面，读取 SDD 从项目工作区
- 项目删除时递归清理文件系统目录
- 已有的 proposal.md/spec files（specs/project-sdd-storage/ 和 specs/project-directory-lifecycle/）已是 openspec 变更内容

**Non-Goals:**
- 不修改 Session 模型
- 不涉及 Spring Boot/A2A 后端（目前只有 Python 后端）
- 不处理用户注册时创建用户目录（projects/ 目录延迟到项目创建时）

## Decisions

### Decision 1: id 改 Integer（不保留 UUID）

当前 Project 模型用 `id = Column(String(36))` 存 UUID 字符串。改为 `id = Column(Integer, primary_key=True, autoincrement=True)`。

- **Rationale**: SQLAlchemy 默认对 Integer PK 自增行为稳定，API URL `/projects/1` 更简洁。且项目是新建平台，无存量 UUID 数据需要迁移。
- **Rejected**: 保留 UUID 字符串但加自增 integer 列 — 增加复杂度，且无需兼容 legacy。

### Decision 2: 项目根目录统一管理

所有用户项目存入 `projects/`（相对于后端根目录），不分散到多处。

- **Structure**: `projects/{username}-{change_name}/`
- **优点**: 路径可预测，`ls projects/` 即知所有项目，`rm -rf projects/` 即清理所有残留
- **username + change_name 复合**: 避免不同用户的同名项目冲突

### Decision 3: openspec init 只在项目创建时执行一次

`ProjectService.create_project` 创建目录后立即运行 `openspec init --tools none`。后续文档生成只在该工作区内操作。

- **Rationale**: `openspec init` 会生成 `.openspec/` 元数据，只需一次。后续 `openspec new change` 和 `openspec instructions` 在同一工作区内运行即可。
- **Error handling**: 如果 `openspec init` 失败，回滚数据库记录，返回 500。

### Decision 4: DocService 动态获取用户名和 change_name

DocService 不再存硬编码常量，而是通过 `project_id` 查 `Project` 模型得 `change_name`，再查 `User` 模型得 `username`。

- **Path resolution**: `projects/{username}-{change_name>/` 拼出来
- **Method**: `DocService._get_project_dir(project_id)` 私有方法
- **Caching**: 不需要缓存（每次调用查 DB 即可，调用频率不高）

### Decision 5: 后续需求 change 命名规范

对于后续需求（非第一个），change 名使用 `{username}-{change_name}-{increment}`。

- **第一个需求**: `{username}-{change_name}-init`（如 `billkang-travel-assistant-init`）
- **后续需求**: `{username}-{change_name}-{seq}`（如 `billkang-travel-assistant-add-login`、`billkang-travel-assistant-payment`）
- **seq 生成**: 读取 `projects/{username}-{change_name}/openspec/changes/` 下已完成 change 列表，取最新序号+1
- **命名来源**: 未来由 LLM 从需求描述生成 change 名称（英语短词），但当前阶段使用自增序号 fallback

### Decision 6: 目录创建失败回滚 DB，目录删除失败不阻塞 DB

- **创建**: DB + 文件系统是原子操作 — 任一失败则整体回滚
- **删除**: DB 记录是 source of truth。文件系统删除失败只记日志，不阻止 DB 删除

## Risks / Trade-offs

- [文件系统与数据库一致] → 创建时使用 try/except 包裹文件系统操作，失败时 raise 触发 DB rollback。删除时文件系统失败只记 warning 日志。
- [用户名变更] → 路径中包含 username，如果用户名变更，项目路径不会自动迁移。当前平台 MVP 阶段不提供用户名变更功能，后续可考虑加软链接。
- [并发创建同名项目] → 不同用户同名项目通过 `{username}-{change_name}` 区分。同一用户同名项目应在 create 前检查 `change_name` 唯一性或目录是否存在。当前简单方案：目录已存在则报错。

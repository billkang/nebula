## Why

当前 `DocService` 硬编码 `CHANGE_NAME = "mvp-scope-planning"`，所有**用户项目**的 SDD 文档统一写入 `openspec/changes/mvp-scope-planning/` 目录。这混淆了两个概念：

| 路径 | 归属 | 示例 |
|------|------|------|
| `openspec/changes/` | **星云平台自身**的开发 SDD | 当前 `project-sdd-storage` change |
| `projects/{username}-{change_name}/openspec/` | **用户项目**的 SDD | `billkang-travel-assistant/openspec/` |

问题：
- `openspec/changes/` 被用户项目 SDD 污染
- `projects/` 目录存在但未实际使用
- 多个用户项目无法独立管理自己的 SDD
- 项目删除时残留磁盘文件
- 缺少归档机制，用户项目的新需求无法独立 create change

## What Changes

1. **Project 模型增加 `change_name` 字段** — 项目名翻译为英文 kebab-case（如 `旅游助手` → `travel-assistant`），用于目录命名和 openspec change 命名。**不使用拼音直译。**
2. **`ProjectService.create_project` 增加文件系统目录创建** — 创建 `projects/{username}-{change_name}/` 目录，执行 `openspec init` 初始化 openspec 工作区
3. **`ProjectService.delete_project` 清除文件系统目录** — 删除项目时清理 `projects/{username}-{change_name}/`
4. **`DocService` 重构** — 去掉硬编码 `CHANGE_NAME`，以项目目录为 openspec 工作区运行 CLI
5. **多需求支持** — 每个新需求创建独立 openspec change，历史归档保留
6. **`POST /projects` 自动翻译 change_name** — API 层调用 LLM 将中文项目名翻译为英文 kebab-case
7. **openspec change 名 = `{username}-{change_name}`**（如 `billkang-travel-assistant`），项目目录名同

## Capabilities

### New Capabilities
- `project-directory-lifecycle`: 项目创建/删除时文件系统目录的创建与清理（含 openspec init）
- `project-sdd-storage`: 用户项目 SDD 文档的存储与读取，支持多 change 归档

### Modified Capabilities
- **(无 — 不修改已有 spec 行为)**

## Impact

- **DB**: `projects` 表增加列：
  - `id` → auto-increment 整数（替换 UUID）
  - 新增 `change_name` 列（英文 kebab-case）
- **API**: `POST /projects` — 接收 name（中文）、自动翻译生成 change_name，返回含 change_name
- **API**: `POST /projects/{id}/docs/generate` — 在项目 openspec 工作区内创建 change 并生成 SDD
- **API**: `DELETE /projects/{id}` — 同时清理文件系统目录
- **File System**:
  - `projects/{username}-{change_name}/` — 项目根目录
  - `projects/{username}-{change_name}/openspec/` — 项目 openspec 工作区（init 初始化）
  - `projects/{username}-{change_name}/openspec/changes/{change_name}/` — 当前需求的 SDD
  - `openspec/changes/` — 仅作星云平台自身 SDD

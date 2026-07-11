# Brainstorming Session — 项目 SDD 存储架构修复

- **日期**：2026-07-07
- **参与人**：用户 + AI
- **讨论主题**：修复项目创建时 SDD 文档的存储路径

## 关键决策

1. **project_id 改为 auto-increment 整数**（替换 UUID），仅 DB 层使用
2. **项目目录名 = `{username}-{change_name}`**（如 `billkang-travel-assistant`），人类可读
3. **change_name** 为项目名翻译为英文 kebab-case（如 `旅游助手` → `travel-assistant`），**不使用拼音**。DB 仅存 change_name（不含用户名前缀）
4. **change_name 生成时机**：`POST /projects` API 层调用 LLM 翻译
5. **openspec change 名 = project 目录名** = `{username}-{change_name}`
6. **SDD 文档**直接存放在项目目录下的 openspec 工作区（`openspec/changes/{change-name}/`），不复制
7. **项目创建时 openspec init**，项目目录即为 openspec 工作区
8. **多需求支持**：每次新需求创建独立 openspec change，历史归档保留
9. **conversation_context.md** 保存在文件系统，不落库
10. **本变更范围**仅限后端架构修复（项目目录创建 + SDD 存放路径），不包含前端改动

## 需求要点

- `ProjectService.create_project` — 创建 `projects/{username}-{change_name}/`，执行 openspec init
- `ProjectService.delete_project` — 删除项目时清理文件系统目录
- `DocService.generate_docs` — 去掉硬编码，在项目 openspec 工作区创建 change 并生成 SDD
- `DocService.list_docs/get_doc` — 从项目 openspec 工作区读取文档
- `POST /projects` — 增加 LLM 翻译 change_name 逻辑
- Project 模型 — id 改为 auto-increment，新增 change_name 字段

## 边界范围

- 不做前端修改（按钮可见性、会话恢复等留待后续变更）
- 不修改数据库表结构之外的迁移逻辑

## 后续步骤

- 生成 proposal → specs → design → tasks
- 按 openspec SDD 规划实现

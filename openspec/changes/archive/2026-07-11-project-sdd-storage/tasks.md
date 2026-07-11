## 1. Project 模型改造

- [x] 1.1 修改 Project 模型：id 改为 auto-increment Integer（替换 String UUID），保留 change_name 字段
- [x] 1.2 修改 Session 模型：project_id 类型同步改为 Integer
- [x] 1.3 更新 Project schema：id 字段类型改为 int
- [x] 1.4 更新测试和 Service 中 Project 引用的类型适配

## 2. 项目目录生命周期

- [x] 2.1 `ProjectService.create_project` 创建项目目录 `projects/{username}-{change_name}/`
- [x] 2.2 `ProjectService.create_project` 在新目录中执行 `openspec init --tools none`
- [x] 2.3 `ProjectService.create_project` 目录创建失败时回滚 DB 记录
- [x] 2.4 `ProjectService.delete_project` 删除项目目录（递归清理）
- [x] 2.5 `ProjectService.delete_project` 目录删除失败只记日志不阻塞 DB

## 3. DocService 重构

- [x] 3.1 DocService 替换硬编码 CHANGE_NAME：根据 project_id 查 DB 获取 username 和 change_name
- [x] 3.2 `generate_docs` 在项目 openspec 工作区运行 CLI 生成 SDD
- [x] 3.3 `generate_docs` 将 conversation_context.md 写入项目根目录
- [x] 3.4 `list_docs` 枚举项目 openspec/changes/ 下的所有 change
- [x] 3.5 `get_doc` 从项目 openspec 工作区读取指定 artifact
- [x] 3.6 `generate_docs` 的错误处理和回滚（openspec CLI 非零退出码）

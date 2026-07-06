## 新增需求

### 需求：存在 @nebula/shared-ui 前端共享包
系统 SHALL 在 `packages/shared-ui/` 下提供一个名为 `@nebula/shared-ui` 的前端共享 UI 包。

#### 场景：包可被 workspace 解析
- **WHEN** 从项目根目录执行 `pnpm ls -r`
- **THEN** 输出中包含 `@nebula/shared-ui`

### 需求：包包含结构骨架
`@nebula/shared-ui` 包 SHALL 提供：
- `package.json`，包名为 `@nebula/shared-ui`，融入 `pnpm-workspace.yaml`
- 组件、hooks 和共享工具函数的初始目录
- README 说明使用方法

#### 场景：包结构存在
- **WHEN** 列出 `packages/shared-ui/`
- **THEN** `package.json` 和 `src/` 目录存在
- **AND** `package.json` 包含 `"name": "@nebula/shared-ui"`

### 需求：前端可引用 shared-ui
`build-engine/frontend` SHALL 通过 pnpm workspace 依赖能够导入 `@nebula/shared-ui`。

#### 场景：前端解析 shared-ui 导入
- **WHEN** 从项目根目录执行 `pnpm install`
- **THEN** `@nebula/shared-ui` 在 workspace 中被正确解析
- **AND** TypeScript 能正确解析 `@nebula/shared-ui` 的导入

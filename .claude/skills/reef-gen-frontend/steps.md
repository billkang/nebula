# React 前端编码步骤

按以下顺序逐块编写，依赖关系由前向后：

1. **类型定义** — 实体接口/类型、Props 类型、API 响应类型
2. **API Hooks** — 自定义 Hook 封装数据获取（loading / error / data 三态）
3. **组件** — Ant Design 函数组件 + Hooks 状态管理
4. **页面组装** — React Router 路由配置、Layout 页面布局

每完成一块对照 `reef:reef-style-frontend` 中对应章节检查。

## 核心约束

- 函数组件 + TypeScript（禁止 Class 组件）
- Props 使用 `interface` 定义（公共 API），联合类型使用 `type`
- 自定义 Hook 使用 `use` 前缀命名
- `useEffect` 依赖数组必须穷举闭包内所有响应值
- 数据获取层与 UI 渲染层分离（自定义 Hook 封装业务逻辑）
- Ant Design 组件按需导入（`import { Button } from 'antd'`）
- 路由组件使用 `React.lazy()` + `Suspense` 懒加载

## 构建命令

```bash
# 快速验证
npx tsc --noEmit
npx lint

# 完整检查
npx tsc --noEmit && npx lint && npx vitest run
```

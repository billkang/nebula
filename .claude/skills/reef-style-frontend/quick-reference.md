# 前端编码快速参考 (React)

按需加载。仅当你需要编写对应组件类型时阅读相关章节。

> **完整示例代码见 `examples/` 目录。** 已安装子维度的规范，通过该维度的 `{value}.md` 文件阅读。

## 速查

| 场景 | 决策 |
| --- | --- |
| 新建组件 | 函数组件 + TypeScript + `interface` Props |
| 新建表单 | Ant Design `Form` + `useState` / `useReducer` |
| 读数据 | 自定义 Hook（`useUsers`）封装 fetch/axios |
| 写数据 | 自定义 Hook + `useState` loading/error 三态 |
| Hook 职责 | 只负责业务逻辑和数据获取，不管理 UI 渲染 |
| 路由 | `React.lazy()` + `Suspense` 懒加载 |

## 新建组件

```tsx
interface UserTableProps {
  users: User[]
  loading?: boolean
  onSelect?: (user: User) => void
}

const UserTable: React.FC<UserTableProps> = ({ users, loading, onSelect }) => {
  return (
    <Table
      dataSource={users}
      loading={loading}
      rowKey="id"
      columns={columns}
      onRow={(record) => ({
        onClick: () => onSelect?.(record),
      })}
    />
  )
}
```

| 规则 | 要求 |
| --- | --- |
| 函数组件 | 禁止 Class 组件，使用 `React.FC` 或显式 Props 类型 |
| `interface` Props | 使用 `interface` 定义 Props，使用 `type` 定义联合类型 |
| 状态提升 | 组件间共享状态提升到最近公共父组件 |
| 默认导出 | 页面级组件使用 `export default`，通用组件使用具名导出 |

## Hooks 规则

- **顶层调用**：禁止在条件、循环、嵌套函数中调用 Hooks
- **依赖数组**：`useEffect` / `useCallback` / `useMemo` 的依赖数组必须穷举闭包内所有响应值
- **自定义 Hook**：以 `use` 开头命名，返回值为对象或元组

```tsx
// ✅ 正确：自定义 Hook 分离数据获取逻辑
function useUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    fetch('/api/v1/users')
      .then(res => res.json())
      .then(data => { setUsers(data); setLoading(false) })
      .catch(err => { setError(err); setLoading(false) })
  }, [])

  return { users, loading, error }
}
```

## Ant Design 组件

- **按需导入**：`import { Button, Table } from 'antd'`（Ant Design 5.x 支持 Tree Shaking，无需额外配置）
- **Form**：`Form.Item` 的 `name` 必须与数据模型字段一致
- **Table**：列定义使用 `columns` 数组，`dataSource` 需要唯一 `rowKey`
- **Modal**：关闭时通过 `afterClose` 或 `destroyOnClose` 重置内部状态
- **布局**：使用 `Row` / `Col` 栅格系统或 Flex 布局

## 错误处理

- 全局错误边界（Error Boundary）捕获组件渲染异常
- API 错误在 Hook 层捕获并暴露错误状态，UI 层通过 Ant Design 组件展示反馈
- 表单校验使用 Ant Design Form 内置校验规则，非必要不自定义 `validator`

## 路由

- 所有页面组件使用 `React.lazy()` + `Suspense` 懒加载
- 路由配置集中定义在路由文件中，不在组件内嵌路由
- 权限通过 Route 组件的 wrapper 或 middleware 模式控制

```tsx
const UserList = React.lazy(() => import('./pages/UserList'))
const UserDetail = React.lazy(() => import('./pages/UserDetail'))

const routes = [
  { path: '/users', element: <UserList /> },
  { path: '/users/:id', element: <UserDetail /> },
]
```

## 代码风格

- 控制流语句必须使用大括号，禁止无大括号的早期返回
- 代码折行规则（90 列限制）详见 `examples/code-wrapping.md`
- JSX 属性超过 3 个时换行排列
- 自闭合标签：无子元素时使用 `<Component />` 而非 `<Component></Component>`

## 常见坑

| 场景 | 问题 | 正确做法 |
|------|------|---------|
| `useEffect` 依赖遗漏 | 闭包内使用了 state 或 props 但未加入依赖数组 | 穷举所有依赖，或使用 `useCallback` 稳定引用 |
| 列表 `key` | 使用 index 作为 key 导致渲染异常 | 使用唯一 ID（`rowKey` / 数据 id） |
| 表单受控/非受控混淆 | 组件同时接收 `value` 和 `defaultValue` | 受控组件用 `value` + `onChange`，非受控用 `defaultValue` |
| 状态更新异步 | 连续 `setState` 导致只生效最后一次 | 使用函数形式 `setCount(prev => prev + 1)` |
| `useCallback` 滥用 | 对所有函数都用 `useCallback` | 仅对传给子组件或 `useEffect` 依赖的函数使用 |

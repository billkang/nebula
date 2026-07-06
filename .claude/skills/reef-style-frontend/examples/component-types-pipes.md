# React 组件模式示例

React 中 Pipe 的概念通过自定义 Hook、工具函数或组件组合实现。

## 自定义 Hook 替代 Pipe（数据转换）

Angular Pipe 在 React 中用自定义 Hook 或纯函数替代：

```tsx
// ✅ 方案1: 纯函数（无状态转换）
function formatDate(date: string | Date, format: 'short' | 'long' = 'short'): string {
  const d = typeof date === 'string' ? new Date(date) : date
  if (format === 'short') {
    return d.toLocaleDateString('zh-CN')
  }
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatCurrency(amount: number, currency = 'CNY'): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency,
  }).format(amount)
}

// 使用
const UserList: React.FC = () => {
  const { users } = useUsers()
  return (
    <Table
      dataSource={users}
      columns={[
        { title: '创建时间', dataIndex: 'createdAt', render: (v: string) => formatDate(v, 'short') },
        { title: '金额', dataIndex: 'amount', render: (v: number) => formatCurrency(v) },
      ]}
    />
  )
}

// ✅ 方案2: 自定义 Hook（有状态转换 — 如搜索/过滤）
function useUserFilter(users: User[], search: string): User[] {
  return useMemo(() => {
    if (!search.trim()) return users
    const q = search.toLowerCase()
    return users.filter(
      u => u.username.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
    )
  }, [users, search])
}
```

## 高阶组件（HOC）— 权限控制

```tsx
// hoc/withAuth.tsx
interface WithAuthProps {
  requiredRole?: UserRole
}

export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  options?: WithAuthProps
) {
  const AuthenticatedComponent: React.FC<P> = (props) => {
    const { user, loading } = useAuth()

    if (loading) return <Spin />
    if (!user) return <Navigate to="/login" replace />

    if (options?.requiredRole && user.role !== options.requiredRole) {
      return <Result status="403" title="无权限访问" />
    }

    return <Component {...props} />
  }

  AuthenticatedComponent.displayName = `withAuth(${Component.displayName || Component.name})`
  return AuthenticatedComponent
}

// 使用
const AdminDashboard = withAuth(Dashboard, { requiredRole: UserRole.Admin })
```

## 组件组合模式

```tsx
// ✅ 复合组件模式（Compound Component）
interface CardComposition {
  Header: React.FC<{ title: string }>
  Body: React.FC<{ children: React.ReactNode }>
  Footer: React.FC<{ children: React.ReactNode }>
}

const Card: React.FC<{ children: React.ReactNode }> & CardComposition = ({ children }) => (
  <Card className="rounded-lg border shadow-sm">{children}</Card>
)

Card.Header = ({ title }) => (
  <div className="border-b px-4 py-3 font-medium">{title}</div>
)
Card.Body = ({ children }) => (
  <div className="px-4 py-3">{children}</div>
)
Card.Footer = ({ children }) => (
  <div className="border-t px-4 py-3 flex justify-end gap-2">{children}</div>
)

// 使用
<Card>
  <Card.Header title="用户信息" />
  <Card.Body>
    <p>用户名: {user.username}</p>
    <p>邮箱: {user.email}</p>
  </Card.Body>
  <Card.Footer>
    <Button onClick={onCancel}>取消</Button>
    <Button type="primary" onClick={onSave}>保存</Button>
  </Card.Footer>
</Card>
```

## Render Props 模式

```tsx
// 数据获取 Render Props（复用数据加载逻辑）
interface DataLoaderProps<T> {
  fetchFn: () => Promise<T>
  children: (result: { data: T | null; loading: boolean; error: Error | null }) => React.ReactNode
}

function DataLoader<T>({ fetchFn, children }: DataLoaderProps<T>) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    fetchFn()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  return <>{children({ data, loading, error })}</>
}

// 使用
<DataLoader fetchFn={() => userService.getById(id)}>
  {({ data: user, loading, error }) => {
    if (loading) return <Skeleton active />
    if (error) return <Alert type="error" message={error.message} />
    return <UserForm user={user} />
  }}
</DataLoader>
```

## Discriminated Union 组件模式

```tsx
// 多形态组件 - 根据 type 渲染不同 UI
type NotificationCardProps =
  | { type: 'success'; message: string }
  | { type: 'error'; message: string; errorCode?: string }
  | { type: 'confirm'; message: string; onConfirm: () => void; onCancel: () => void }

const NotificationCard: React.FC<NotificationCardProps> = (props) => {
  switch (props.type) {
    case 'success':
      return <Alert type="success" message={props.message} showIcon />
    case 'error':
      return (
        <Alert
          type="error"
          message={props.message}
          description={props.errorCode ? `错误码: ${props.errorCode}` : undefined}
          showIcon
        />
      )
    case 'confirm':
      return (
        <Modal
          open
          title="确认"
          onOk={props.onConfirm}
          onCancel={props.onCancel}
        >
          <p>{props.message}</p>
        </Modal>
      )
  }
}
```

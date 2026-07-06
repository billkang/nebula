# React 数据获取层 + 路由配置示例

## 自定义 Hook（数据获取层）

```tsx
// hooks/useUsers.ts
import { useState, useEffect, useCallback } from 'react'
import type { User, PageResponse } from '../shared/types/user'

interface UseUsersOptions {
  page?: number
  size?: number
  search?: string
  role?: string
}

interface UseUsersResult {
  users: User[]
  total: number
  loading: boolean
  error: Error | null
  refresh: () => void
}

// 使用 URLSearchParams 构建查询参数
function buildQuery(params: UseUsersOptions): string {
  const searchParams = new URLSearchParams()
  if (params.page !== undefined) searchParams.set('page', String(params.page))
  if (params.size !== undefined) searchParams.set('size', String(params.size))
  if (params.search) searchParams.set('search', params.search)
  if (params.role) searchParams.set('role', params.role)
  const qs = searchParams.toString()
  return qs ? `?${qs}` : ''
}

export function useUsers(options: UseUsersOptions = {}): UseUsersResult {
  const [users, setUsers] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const refresh = useCallback(() => setRefreshKey(k => k + 1), [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    fetch(`/api/v1/users${buildQuery(options)}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json() as Promise<PageResponse<User>>
      })
      .then(data => {
        if (!cancelled) {
          setUsers(data.content)
          setTotal(data.totalElements)
          setLoading(false)
        }
      })
      .catch(err => {
        if (!cancelled) {
          setError(err)
          setLoading(false)
        }
      })

    return () => { cancelled = true }
  }, [options.page, options.size, options.search, options.role, refreshKey])

  return { users, total, loading, error, refresh }
}

// 写操作 Hook
export function useCreateUser() {
  const [loading, setLoading] = useState(false)

  const create = async (data: CreateUserRequest): Promise<User> => {
    setLoading(true)
    const res = await fetch('/api/v1/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const user = await res.json()
    setLoading(false)
    return user
  }

  return { create, loading }
}
```

## Service 层抽取（可选 — 复杂项目使用）

```tsx
// services/userService.ts
// 将 API 调用统一到 Service 层，Hook 只负责状态管理
import type { User, CreateUserRequest, UpdateUserRequest, PageResponse } from '../shared/types/user'

const BASE_URL = '/api/v1/users'

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: `HTTP ${res.status}` }))
    throw new Error(error.message)
  }
  return res.json()
}

export const userService = {
  list(params?: Record<string, string | number>): Promise<PageResponse<User>> {
    const qs = params ? '?' + new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString() : ''
    return fetch(`${BASE_URL}${qs}`).then(handleResponse)
  },

  getById(id: string): Promise<User> {
    return fetch(`${BASE_URL}/${id}`).then(handleResponse)
  },

  create(data: CreateUserRequest): Promise<User> {
    return fetch(BASE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(handleResponse)
  },

  update(id: string, data: UpdateUserRequest): Promise<User> {
    return fetch(`${BASE_URL}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(handleResponse)
  },

  delete(id: string): Promise<void> {
    return fetch(`${BASE_URL}/${id}`, { method: 'DELETE' }).then(handleResponse)
  },
}
```

## 路由配置

```tsx
// routes/index.tsx
import { createBrowserRouter, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { Spin } from 'antd'

// 懒加载页面组件
const Dashboard = lazy(() => import('../pages/Dashboard'))
const UserList = lazy(() => import('../pages/UserList'))
const UserDetail = lazy(() => import('../pages/UserDetail'))
const CreateUser = lazy(() => import('../pages/CreateUser'))
const Settings = lazy(() => import('../pages/Settings'))
const NotFound = lazy(() => import('../pages/NotFound'))

// 通用懒加载包装
const LazyLoad: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Suspense fallback={<Spin style={{ display: 'flex', justifyContent: 'center', marginTop: 120 }} />}>
    {children}
  </Suspense>
)

export const router = createBrowserRouter([
  {
    path: '/',
    element: <LazyLoad><Dashboard /></LazyLoad>,
  },
  {
    path: '/users',
    element: <LazyLoad><UserList /></LazyLoad>,
  },
  {
    path: '/users/new',
    element: <LazyLoad><CreateUser /></LazyLoad>,
  },
  {
    path: '/users/:id',
    element: <LazyLoad><UserDetail /></LazyLoad>,
  },
  {
    path: '/settings',
    element: <LazyLoad><Settings /></LazyLoad>,
  },
  {
    path: '/404',
    element: <LazyLoad><NotFound /></LazyLoad>,
  },
  {
    path: '*',
    element: <Navigate to="/404" replace />,
  },
])
```

## 主应用入口

```tsx
// App.tsx
import { RouterProvider } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import { router } from './routes'

const App: React.FC = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
      }}
    >
      <RouterProvider router={router} />
    </ConfigProvider>
  )
}

export default App
```

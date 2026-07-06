# React 组件和 Hook 测试代码示例

## 组件渲染测试

```tsx
// UserAvatar.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { UserAvatar } from './UserAvatar'

describe('UserAvatar', () => {
  const mockUser = { username: 'alice', avatar: 'https://example.com/avatar.png' }

  it('renders with avatar image', () => {
    render(<UserAvatar user={mockUser} />)
    const img = screen.getByAltText('alice')
    expect(img).toBeInTheDocument()
    expect(img).toHaveAttribute('src', mockUser.avatar)
  })

  it('renders with size classes', () => {
    const { container } = render(<UserAvatar user={mockUser} size="lg" />)
    // Ant Design Avatar 通过 size 属性控制尺寸
    expect(container.querySelector('.ant-avatar')).toBeInTheDocument()
  })

  it('is clickable when onClick provided', async () => {
    const handleClick = vi.fn()
    render(<UserAvatar user={mockUser} onClick={handleClick} />)

    await userEvent.click(screen.getByAltText('alice'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

## 表单测试

```tsx
// CreateUserForm.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { CreateUserForm } from './CreateUserForm'

// Mock message
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd')
  return { ...actual, message: { success: vi.fn(), error: vi.fn() } }
})

describe('CreateUserForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all form fields', () => {
    render(<CreateUserForm />)

    expect(screen.getByLabelText('用户名')).toBeInTheDocument()
    expect(screen.getByLabelText('邮箱')).toBeInTheDocument()
    expect(screen.getByLabelText('角色')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '创建' })).toBeInTheDocument()
  })

  it('shows validation errors on empty submit', async () => {
    render(<CreateUserForm />)

    await userEvent.click(screen.getByRole('button', { name: '创建' }))

    await waitFor(() => {
      expect(screen.getByText('请输入用户名')).toBeInTheDocument()
      expect(screen.getByText('请输入邮箱')).toBeInTheDocument()
    })
  })

  it('submits form with valid data', async () => {
    const createUser = vi.fn().mockResolvedValue({ id: '1' })
    render(<CreateUserForm onSubmit={createUser} />)

    await userEvent.type(screen.getByLabelText('用户名'), 'newuser')
    await userEvent.type(screen.getByLabelText('邮箱'), 'new@example.com')

    // Ant Design Select 需要特殊处理
    const roleSelect = screen.getByLabelText('角色')
    await userEvent.click(roleSelect)
    await userEvent.click(screen.getByText('编辑'))

    await userEvent.click(screen.getByRole('button', { name: '创建' }))

    await waitFor(() => {
      expect(createUser).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'new@example.com',
        role: 'EDITOR',
      })
    })
  })
})
```

## Hook 测试

```tsx
// useUsers.test.ts
import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useUsers } from './useUsers'

describe('useUsers', () => {
  const mockUsers = [
    { id: '1', username: 'alice', email: 'alice@example.com', role: 'ADMIN' },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns loading state initially', () => {
    global.fetch = vi.fn().mockImplementation(() => new Promise(() => {})) // 永不 resolve

    const { result } = renderHook(() => useUsers())

    expect(result.current.loading).toBe(true)
    expect(result.current.users).toEqual([])
    expect(result.current.error).toBeNull()
  })

  it('returns users on successful fetch', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ content: mockUsers, totalElements: 1 }),
    })

    const { result } = renderHook(() => useUsers())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.users).toEqual(mockUsers)
    expect(result.current.error).toBeNull()
  })

  it('returns error on fetch failure', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useUsers())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBeInstanceOf(Error)
    expect(result.current.error?.message).toBe('Network error')
    expect(result.current.users).toEqual([])
  })

  it('refresh resets loading state', async () => {
    let resolvePromise!: (value: unknown) => void
    global.fetch = vi.fn().mockImplementation(
      () => new Promise((resolve) => { resolvePromise = resolve })
    )

    const { result } = renderHook(() => useUsers())

    act(() => {
      result.current.refresh()
    })

    // refresh should trigger a new fetch, loading goes back to true
    expect(result.current.loading).toBe(true)
  })
})
```

## Ant Design 组件集成测试

```tsx
// UserTable.test.tsx
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'

interface User {
  id: string
  username: string
  email: string
  role: string
}

describe('UserTable with Ant Design', () => {
  const columns: ColumnsType<User> = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { title: '角色', dataIndex: 'role', key: 'role' },
  ]

  const mockData: User[] = [
    { id: '1', username: 'alice', email: 'alice@example.com', role: 'ADMIN' },
    { id: '2', username: 'bob', email: 'bob@example.com', role: 'EDITOR' },
  ]

  it('renders table with data', () => {
    render(
      <Table
        columns={columns}
        dataSource={mockData}
        rowKey="id"
      />
    )

    expect(screen.getByText('alice')).toBeInTheDocument()
    expect(screen.getByText('bob')).toBeInTheDocument()
  })

  it('shows empty state when no data', () => {
    render(
      <Table
        columns={columns}
        dataSource={[]}
        rowKey="id"
        locale={{ emptyText: '暂无数据' }}
      />
    )

    expect(screen.getByText('暂无数据')).toBeInTheDocument()
  })

  it('handles row click', async () => {
    const handleRow = vi.fn()
    render(
      <Table
        columns={columns}
        dataSource={mockData}
        rowKey="id"
        onRow={() => ({
          onClick: () => handleRow(),
        })}
      />
    )

    const rows = screen.getAllByRole('row')
    // 第一行是 header, 第二行是第一个数据行
    await userEvent.click(rows[1])
    expect(handleRow).toHaveBeenCalled()
  })
})
```

## 路由组件测试

```tsx
// ProtectedRoute.test.tsx
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'

// Mock auth hook
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: null, loading: false }),
}))

import { ProtectedRoute } from './ProtectedRoute'

describe('ProtectedRoute', () => {
  it('redirects to login when not authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/login" element={<div>登录页</div>} />
          <Route path="/dashboard" element={<ProtectedRoute><div>仪表盘</div></ProtectedRoute>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText('登录页')).toBeInTheDocument()
    expect(screen.queryByText('仪表盘')).not.toBeInTheDocument()
  })
})
```

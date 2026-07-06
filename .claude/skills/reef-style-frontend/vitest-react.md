# Vitest + React Testing Library 测试规范

## 测试配置

```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/**/*.d.ts', 'src/test/**'],
      thresholds: {
        branches: 80,
        functions: 80,
        lines: 80,
        statements: 80,
      },
    },
  },
})
```

```ts
// src/test/setup.ts
import '@testing-library/jest-dom'
```

## 通用原则

- 遵循 AAA 模式：Arrange（准备）→ Act（执行）→ Assert（断言）
- 测试应与实现解耦 — 通过用户可见的行为（文本、角色、aria-label）选择元素
- 测试用户交互而非组件内部状态
- 每个测试聚焦一个场景

## 组件测试

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'

// ✅ 正确：通过文本寻找元素
render(<Button>提交</Button>)
expect(screen.getByRole('button', { name: '提交' })).toBeInTheDocument()

// ✅ 正确：模拟用户交互
await userEvent.click(screen.getByRole('button'))

// ❌ 避免：通过测试 ID 或实现细节选择
// screen.getByTestId('submit-btn') // 仅在无其他方式时使用
// wrapper.find('.btn-primary') // 禁止通过 CSS 类选择
```

## Hook 测试

```tsx
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

describe('useCounter', () => {
  it('should increment count', () => {
    const { result } = renderHook(() => useCounter())

    act(() => {
      result.current.increment()
    })

    expect(result.current.count).toBe(1)
  })
})
```

## 测试文件命名与位置

- 测试文件放在被测模块旁：`UserList.tsx` → `UserList.test.tsx`
- 通用测试放在 `src/test/` 目录
- Hook 测试：`useUsers.ts` → `useUsers.test.ts`

## Mock 策略

```tsx
// 全局 mock API 调用
import { vi } from 'vitest'

// Mock fetch
global.fetch = vi.fn()

// Mock 模块
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd')
  return {
    ...actual,
    message: {
      success: vi.fn(),
      error: vi.fn(),
    },
  }
})

// Mock 自定义 Hook
vi.mock('../hooks/useUsers', () => ({
  useUsers: () => ({
    users: mockUsers,
    loading: false,
    error: null,
    refresh: vi.fn(),
  }),
}))
```

## 异步测试

```tsx
it('should load and display users', async () => {
  // Arrange
  const mockUsers = [
    { id: '1', username: 'alice', email: 'alice@example.com', role: 'ADMIN' },
    { id: '2', username: 'bob', email: 'bob@example.com', role: 'EDITOR' },
  ]

  // 模拟 API 响应
  const mockFetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ content: mockUsers, totalElements: 2 }),
  })
  global.fetch = mockFetch

  // Act
  render(<UserList />)

  // Assert — 等待异步渲染完成
  expect(await screen.findByText('alice')).toBeInTheDocument()
  expect(screen.getByText('bob')).toBeInTheDocument()
  expect(screen.getByText('ADMIN')).toBeInTheDocument()
})
```

## 覆盖率要求

- 功能性组件覆盖率达到 80%+（branches, functions, lines）
- 核心业务逻辑的 Hook 需要 100% 覆盖
- 工具函数/纯函数需要 100% 覆盖
- UI 展示组件（页面布局）可低于 80%，但至少覆盖渲染正常路径和空状态

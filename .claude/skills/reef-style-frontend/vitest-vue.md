# Vitest + Vue Test Utils 测试规范

## 测试配置

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{vue,ts}'],
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

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom'
```

## 通用原则

- 遵循 AAA 模式：Arrange（准备）→ Act（执行）→ Assert（断言）
- 测试应与实现解耦 — 通过用户可见的行为（文本、角色、aria-label）选择元素
- 测试用户交互而非组件内部状态
- 每个测试聚焦一个场景

## 组件测试（Vue Test Utils）

```typescript
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'

// ✅ 正确：通过文本寻找元素
const wrapper = mount(MyComponent)
expect(wrapper.text()).toContain('提交')

// ✅ 正确：模拟用户交互
await wrapper.find('button').trigger('click')

// ✅ 正确：通过 findComponent 查找子组件
expect(wrapper.findComponent({ name: 'AButton' }).exists()).toBe(true)

// ❌ 避免：通过 CSS 类名选择
// wrapper.find('.btn-primary') // 禁止
```

## Hook / 组合式函数测试

```typescript
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

- 测试文件放在被测模块旁：`UserList.vue` → `UserList.test.ts`
- 通用测试放在 `src/test/` 目录
- 组合式函数测试：`useUsers.ts` → `useUsers.test.ts`

## Mock 策略

```typescript
import { vi } from 'vitest'

// Mock fetch
global.fetch = vi.fn()

// Mock 模块
vi.mock('ant-design-vue', async () => {
  const actual = await vi.importActual('ant-design-vue')
  return {
    ...actual,
    message: {
      success: vi.fn(),
      error: vi.fn(),
    },
  }
})

// Mock 组合式函数
vi.mock('@/composables/useUsers', () => ({
  useUsers: () => ({
    users: mockUsers,
    loading: false,
    error: null,
    refresh: vi.fn(),
  }),
}))
```

## 异步测试

```typescript
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
  const wrapper = mount(UserList)

  // Assert — 等待异步渲染完成
  await nextTick()
  expect(wrapper.text()).toContain('alice')
})

// @testing-library/vue 方案（自动等待）
import { render, screen } from '@testing-library/vue'

it('should display users with testing-library', async () => {
  render(UserList)
  expect(await screen.findByText('alice')).toBeInTheDocument()
})
```

## Pinia 测试

```typescript
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { describe, it, expect, vi } from 'vitest'
import UserList from '@/views/UserList.vue'

describe('UserList with Pinia', () => {
  it('renders loading state', () => {
    const wrapper = mount(UserList, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              auth: { user: null, loading: true },
            },
          }),
        ],
      },
    })

    expect(wrapper.findComponent({ name: 'ASpin' }).exists()).toBe(true)
  })
})
```

## 覆盖率要求

- 功能性组件覆盖率达到 80%+（branches, functions, lines）
- 核心业务逻辑的组合式函数需要 100% 覆盖
- 工具函数/纯函数需要 100% 覆盖
- UI 展示组件（页面布局）可低于 80%，但至少覆盖渲染正常路径和空状态

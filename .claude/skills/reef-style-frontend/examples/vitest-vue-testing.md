# Vue 组件和组合式函数测试代码示例

## 组件渲染测试

```vue
<!-- UserAvatar.vue -->
<script setup lang="ts">
interface Props {
  username: string
  avatar?: string
  size?: 'sm' | 'md' | 'lg'
  onClick?: () => void
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
})
</script>

<template>
  <a-avatar
    :src="avatar"
    :alt="username"
    :size="size === 'sm' ? 24 : size === 'md' ? 32 : 48"
    :style="{ cursor: onClick ? 'pointer' : 'default' }"
    @click="onClick"
  />
</template>
```

```typescript
// UserAvatar.test.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import UserAvatar from './UserAvatar.vue'

describe('UserAvatar', () => {
  const mockUser = { username: 'alice', avatar: 'https://example.com/avatar.png' }

  it('renders with avatar image', () => {
    const wrapper = mount(UserAvatar, {
      props: {
        username: mockUser.username,
        avatar: mockUser.avatar,
      },
    })

    const img = wrapper.find('img')
    expect(img.attributes('alt')).toBe('alice')
    expect(img.attributes('src')).toBe(mockUser.avatar)
  })

  it('renders with size classes', () => {
    const wrapper = mount(UserAvatar, {
      props: {
        username: mockUser.username,
        size: 'lg',
      },
    })

    // Ant Design Vue Avatar 通过 size 属性控制尺寸
    expect(wrapper.findComponent({ name: 'AAvatar' }).exists()).toBe(true)
  })

  it('is clickable when onClick provided', async () => {
    const handleClick = vi.fn()
    const wrapper = mount(UserAvatar, {
      props: {
        username: mockUser.username,
        onClick: handleClick,
      },
    })

    await wrapper.findComponent({ name: 'AAvatar' }).trigger('click')
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

## 表单测试

```vue
<!-- CreateUserForm.vue -->
<script setup lang="ts">
import { reactive, ref } from 'vue'
import { message } from 'ant-design-vue'

interface FormState {
  username: string
  email: string
  role: string | undefined
}

const emit = defineEmits<{
  success: []
}>()

const formState = reactive<FormState>({
  username: '',
  email: '',
  role: undefined,
})

const loading = ref(false)
const formRef = ref()

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
    loading.value = true

    const res = await fetch('/api/v1/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formState),
    })

    if (!res.ok) throw new Error('创建失败')
    message.success('用户创建成功')
    emit('success')
  } catch (e) {
    if (e instanceof Error) message.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <a-form
    ref="formRef"
    :model="formState"
    :rules="rules"
    :label-col="{ span: 6 }"
    :wrapper-col="{ span: 16 }"
    @finish="handleSubmit"
  >
    <a-form-item label="用户名" name="username">
      <a-input v-model:value="formState.username" />
    </a-form-item>

    <a-form-item label="邮箱" name="email">
      <a-input v-model:value="formState.email" />
    </a-form-item>

    <a-form-item label="角色" name="role">
      <a-select v-model:value="formState.role">
        <a-select-option value="EDITOR">编辑</a-select-option>
      </a-select>
    </a-form-item>

    <a-form-item :wrapper-col="{ offset: 6, span: 16 }">
      <a-button type="primary" html-type="submit" :loading="loading">
        创建
      </a-button>
    </a-form-item>
  </a-form>
</template>
```

```typescript
// CreateUserForm.test.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import CreateUserForm from './CreateUserForm.vue'

// Mock Ant Design Vue message
vi.mock('ant-design-vue', async () => {
  const actual = await vi.importActual('ant-design-vue')
  return { ...actual, message: { success: vi.fn(), error: vi.fn() } }
})

describe('CreateUserForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all form fields', () => {
    const wrapper = mount(CreateUserForm)

    expect(wrapper.text()).toContain('用户名')
    expect(wrapper.text()).toContain('邮箱')
    expect(wrapper.text()).toContain('角色')
  })

  it('shows validation errors on empty submit', async () => {
    const wrapper = mount(CreateUserForm)

    await wrapper.find('form').trigger('submit')
    await nextTick()

    expect(wrapper.text()).toContain('请输入用户名')
    expect(wrapper.text()).toContain('请输入邮箱')
  })

  it('submits form with valid data', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: '1' }),
    })

    const wrapper = mount(CreateUserForm)

    // 填充表单
    await wrapper.find('input').setValue('newuser')
    const inputs = wrapper.findAll('input')
    await inputs[1].setValue('new@example.com')

    // 提交
    await wrapper.find('form').trigger('submit')
    await nextTick()

    expect(global.fetch).toHaveBeenCalled()
  })
})
```

## 组合式函数测试

```typescript
// useUsers.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { withSetup } from '@/test/utils'

// withSetup 辅助函数：在测试环境中执行组合式函数
function withSetup<T>(hook: () => T): T {
  let result: T
  const wrapper = defineComponent({
    setup() {
      result = hook()
      return () => null
    },
  })
  mount(wrapper)
  return result!
}

describe('useUsers', () => {
  const mockUsers = [
    { id: '1', username: 'alice', email: 'alice@example.com', role: 'ADMIN' },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns loading state initially', () => {
    global.fetch = vi.fn().mockImplementation(() => new Promise(() => {}))

    const { loading, users, error } = useUsers()

    expect(loading.value).toBe(true)
    expect(users.value).toEqual([])
    expect(error.value).toBeNull()
  })

  it('returns users on successful fetch', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ content: mockUsers, totalElements: 1 }),
    })

    // 在 setup 中调用组合式函数
    let result: ReturnType<typeof useUsers>
    mount(
      defineComponent({
        setup() {
          result = useUsers()
          return () => null
        },
      })
    )

    await vi.waitFor(() => {
      expect(result!.loading.value).toBe(false)
    })

    expect(result!.users.value).toEqual(mockUsers)
    expect(result!.error.value).toBeNull()
  })

  it('returns error on fetch failure', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    let result: ReturnType<typeof useUsers>
    mount(
      defineComponent({
        setup() {
          result = useUsers()
          return () => null
        },
      })
    )

    await vi.waitFor(() => {
      expect(result!.loading.value).toBe(false)
    })

    expect(result!.error.value).toBeInstanceOf(Error)
    expect(result!.error.value?.message).toBe('Network error')
  })

  it('refresh resets loading state', async () => {
    let resolvePromise!: (value: unknown) => void
    global.fetch = vi.fn().mockImplementation(
      () => new Promise((resolve) => { resolvePromise = resolve })
    )

    let result: ReturnType<typeof useUsers>
    mount(
      defineComponent({
        setup() {
          result = useUsers()
          return () => null
        },
      })
    )

    result!.refresh()
    expect(result!.loading.value).toBe(true)
  })
})
```

## Ant Design Vue 组件集成测试

```typescript
// UserTable.test.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import { defineComponent } from 'vue'
import { Table } from 'ant-design-vue'

interface User {
  id: string
  username: string
  email: string
  role: string
}

describe('UserTable with Ant Design Vue', () => {
  const columns = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { title: '角色', dataIndex: 'role', key: 'role' },
  ]

  const mockData: User[] = [
    { id: '1', username: 'alice', email: 'alice@example.com', role: 'ADMIN' },
    { id: '2', username: 'bob', email: 'bob@example.com', role: 'EDITOR' },
  ]

  it('renders table with data', () => {
    const wrapper = mount(
      defineComponent({
        template: `
          <a-table
            :data-source="data"
            :columns="columns"
            row-key="id"
          />
        `,
        components: { ATable: Table },
        setup: () => ({ data: mockData, columns }),
      })
    )

    expect(wrapper.text()).toContain('alice')
    expect(wrapper.text()).toContain('bob')
  })

  it('shows empty state when no data', () => {
    const wrapper = mount(
      defineComponent({
        template: `
          <a-table
            :data-source="[]"
            :columns="columns"
            row-key="id"
            :locale="{ emptyText: '暂无数据' }"
          />
        `,
        components: { ATable: Table },
        setup: () => ({ columns }),
      })
    )

    expect(wrapper.text()).toContain('暂无数据')
  })
})
```

## 路由组件测试

```vue
<!-- ProtectedRoute.vue -->
<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

if (!auth.isAuthenticated) {
  router.replace({ name: 'login' })
}
</script>

<template>
  <slot v-if="auth.isAuthenticated" />
</template>
```

```typescript
// ProtectedRoute.test.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'
import { createTestingPinia } from '@pinia/testing'
import ProtectedRoute from './ProtectedRoute.vue'

describe('ProtectedRoute', () => {
  it('redirects to login when not authenticated', () => {
    const wrapper = mount(ProtectedRoute, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              auth: { user: null, token: null },
            },
          }),
          createRouter({
            history: createWebHistory(),
            routes: [
              { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
              { path: '/login', name: 'login', component: { template: '<div>Login</div>' } },
            ],
          }),
        ],
      },
    })

    expect(wrapper.text()).not.toContain('Protected Content')
  })
})
```

# React 表单模式（Ant Design Form）

## 基础表单

```tsx
interface CreateUserFormValues {
  username: string
  email: string
  displayName: string
  role: UserRole
}

const CreateUserForm: React.FC = () => {
  const [form] = Form.useForm<CreateUserFormValues>()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (values: CreateUserFormValues) => {
    setLoading(true)
    try {
      await createUser(values)
      message.success('用户创建成功')
      form.resetFields()
    } catch (err) {
      // Ant Design Form 会自动捕获校验错误
      message.error('创建失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      autoComplete="off"
    >
      <Form.Item
        name="username"
        label="用户名"
        rules={[
          { required: true, message: '请输入用户名' },
          { min: 3, max: 32, message: '用户名长度 3-32 个字符' },
        ]}
      >
        <Input placeholder="请输入用户名" />
      </Form.Item>

      <Form.Item
        name="email"
        label="邮箱"
        rules={[
          { required: true, message: '请输入邮箱' },
          { type: 'email', message: '请输入有效的邮箱地址' },
        ]}
      >
        <Input placeholder="请输入邮箱" />
      </Form.Item>

      <Form.Item
        name="displayName"
        label="显示名称"
        rules={[{ required: true, message: '请输入显示名称' }]}
      >
        <Input placeholder="请输入显示名称" />
      </Form.Item>

      <Form.Item
        name="role"
        label="角色"
        rules={[{ required: true, message: '请选择角色' }]}
      >
        <Select placeholder="请选择角色">
          <Select.Option value="ADMIN">管理员</Select.Option>
          <Select.Option value="EDITOR">编辑</Select.Option>
          <Select.Option value="VIEWER">查看者</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading}>
          创建
        </Button>
      </Form.Item>
    </Form>
  )
}
```

## 编辑表单（初始值）

```tsx
interface EditUserFormProps {
  user: User
  onSuccess: () => void
}

const EditUserForm: React.FC<EditUserFormProps> = ({ user, onSuccess }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  // 初始值填充
  useEffect(() => {
    form.setFieldsValue({
      displayName: user.displayName,
      email: user.email,
      role: user.role,
    })
  }, [user, form])

  const handleSubmit = async (values: Partial<CreateUserRequest>) => {
    setLoading(true)
    try {
      await updateUser(user.id, values)
      message.success('用户信息已更新')
      onSuccess()
    } catch {
      message.error('更新失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
    >
      {/* 用户名只读展示 */}
      <Form.Item label="用户名">
        <Input value={user.username} disabled />
      </Form.Item>

      <Form.Item
        name="email"
        label="邮箱"
        rules={[{ type: 'email' }]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        name="displayName"
        label="显示名称"
      >
        <Input />
      </Form.Item>

      <Form.Item
        name="role"
        label="角色"
      >
        <Select>
          <Select.Option value="ADMIN">管理员</Select.Option>
          <Select.Option value="EDITOR">编辑</Select.Option>
          <Select.Option value="VIEWER">查看者</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading}>
          保存
        </Button>
      </Form.Item>
    </Form>
  )
}
```

## 搜索表单（非受控 + 联动 Table）

```tsx
const UserListPage: React.FC = () => {
  const [searchForm] = Form.useForm()
  const [query, setQuery] = useState<Record<string, string>>({})

  const handleSearch = (values: Record<string, string>) => {
    // 过滤空值
    const filtered = Object.fromEntries(
      Object.entries(values).filter(([, v]) => v !== undefined && v !== '')
    )
    setQuery(filtered)
  }

  const handleReset = () => {
    searchForm.resetFields()
    setQuery({})
  }

  return (
    <div>
      <Form
        form={searchForm}
        layout="inline"
        onFinish={handleSearch}
      >
        <Form.Item name="keyword">
          <Input.Search placeholder="搜索用户名/邮箱" onSearch={() => searchForm.submit()} />
        </Form.Item>
        <Form.Item name="role">
          <Select placeholder="角色" allowClear style={{ width: 120 }}>
            <Select.Option value="ADMIN">管理员</Select.Option>
            <Select.Option value="EDITOR">编辑</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item name="status">
          <Select placeholder="状态" allowClear style={{ width: 120 }}>
            <Select.Option value="active">活跃</Select.Option>
            <Select.Option value="inactive">停用</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">查询</Button>
          <Button onClick={handleReset} style={{ marginLeft: 8 }}>重置</Button>
        </Form.Item>
      </Form>

      <UserTable query={query} />
    </div>
  )
}
```

## 全局校验信息配置

```tsx
// 在应用入口统一配置校验信息
import { ConfigProvider } from 'antd'

const App: React.FC = () => (
  <ConfigProvider
    form={{
      validateMessages: {
        required: "'${label}' 是必填项",
        types: {
          email: "'${label}' 不是有效的邮箱地址",
          number: "'${label}' 不是有效的数字",
        },
        string: {
          min: "'${label}' 最少 ${min} 个字符",
          max: "'${label}' 最多 ${max} 个字符",
          range: "'${label}' 长度在 ${min} 到 ${max} 之间",
        },
      },
    }}
  >
    {/* Router 和页面内容 */}
  </ConfigProvider>
)
```

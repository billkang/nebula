# React/JSX 代码折行规则

遵循 90 列限制，以下是 React 专有的折行场景。

## JSX 属性换行

单个属性保持在行内；3 个及以上属性每个占一行：

```tsx
// ✅ 单属性行内
<Button type="primary">提交</Button>

// ✅ 2 个属性行内
<Button type="primary" loading={submitting}>提交</Button>

// ✅ 3+ 属性换行排列
<Table
  dataSource={users}
  columns={columns}
  rowKey="id"
  loading={loading}
  pagination={{ pageSize: 20 }}
  onChange={handlePageChange}
/>
```

## 自闭合标签

无子元素时使用自闭合标签，属性换行规则同上：

```tsx
// ✅ 无属性
<Divider />

// ✅ 多属性
<DatePicker
  value={date}
  onChange={setDate}
  format="YYYY-MM-DD"
/>
```

## 条件渲染换行

```tsx
// ✅ 简单的三元表达式保持行内
return <div>{loading ? <Spin /> : <UserTable users={users} />}</div>

// ✅ 复杂条件使用 && 或三元换行
return (
  <div>
    {error && (
      <Alert
        type="error"
        message={error.message}
        closable
        onClose={clearError}
      />
    )}
    {!loading && !error && <UserTable users={users} />}
  </div>
)
```

## Hook 声明

```tsx
// ✅ Hook 声明连续排列，按逻辑分组
const [users, setUsers] = useState<User[]>([])
const [loading, setLoading] = useState(true)
const [search, setSearch] = useState('')

// useEffect 依赖较长时换行
useEffect(() => {
  fetchUsers(search)
}, [search]) // 短依赖数组行内

// ✅ 长依赖数组换行
useEffect(() => {
  fetchFilteredUsers({ search, role, status, page, size })
}, [
  search,
  role,
  status,
  page,
  size,
])
```

## 函数 Props 换行

```tsx
// ✅ 短函数表达式行内
<Button onClick={() => setIsOpen(true)}>打开</Button>

// ✅ 多行函数体换行
<Modal
  title="确认删除"
  open={isOpen}
  onOk={async () => {
    await deleteUser(id)
    message.success('删除成功')
    setIsOpen(false)
    onDeleted?.()
  }}
  onCancel={() => setIsOpen(false)}
>
  <p>确定要删除该用户吗？</p>
</Modal>
```

## 类型定义换行

```tsx
// ✅ Props 类型每个属性一行
interface UserFormProps {
  user?: User
  onSubmit: (values: CreateUserRequest) => Promise<void>
  onCancel: () => void
}

// ✅ 联合类型换行
type UserStatus = 'active' | 'inactive' | 'locked' | 'pending'
```

# Ant Design 5.x 组件使用规范

## 通用原则

- Ant Design 5.x 使用 CSS-in-JS（`@ant-design/cssinjs`），无需额外引入 CSS 文件
- 组件使用 Tree Shaking 按需导入，`import { Button, Table } from 'antd'` 即可
- 主题定制通过 `ConfigProvider` 的 `theme` 属性配置，禁止直接覆盖 Ant Design 的 CSS 类名
- 图标使用 `@ant-design/icons` 的具名导入：`import { UserOutlined } from '@ant-design/icons'`

## 常用组件规范

### Button（按钮）
- 主要操作使用 `type="primary"`，次要操作默认
- 危险操作使用 `danger` 属性
- 异步操作必须设置 `loading` 状态防重复提交
- 纯图标按钮必须有 `aria-label` 提供无障碍说明

```tsx
<Button type="primary" loading={submitting} onClick={handleSubmit}>
  提交
</Button>
<Button danger onClick={handleDelete}>删除</Button>
<Button icon={<SearchOutlined />} aria-label="搜索" />
```

### Table（表格）
- 始终指定 `rowKey` 为唯一标识字段（如 `id`）
- 列表格使用 `pagination` 属性控制分页
- 长列表开启 `virtual` 虚拟滚动（>= 1000 行）
- 空数据使用 `locale.emptyText` 自定义空状态提示
- 后端分页使用 `onChange` 回调 + `pagination.current/pageSize` 受控

```tsx
<Table
  dataSource={users}
  columns={columns}
  rowKey="id"
  loading={loading}
  pagination={{
    current: page,
    pageSize: 20,
    total,
    showSizeChanger: true,
    showTotal: (total) => `共 ${total} 条`,
  }}
  onChange={(pagination) => {
    setPage(pagination.current)
    setPageSize(pagination.pageSize)
  }}
  locale={{ emptyText: <Empty description="暂无数据" /> }}
/>
```

### Form（表单）
- 使用 `layout="vertical"` 默认垂直布局
- 所有校验规则集中在 `rules` 中定义，避免使用自定义 `validator`（除非复杂业务）
- `Form.Item` 的 `name` 必须与提交数据结构的字段名一致
- 编辑表单用 `form.setFieldsValue()` 填充初始值，不要用 `initialValues`
- 全局校验信息通过 `ConfigProvider` 的 `form.validateMessages` 统一配置

```tsx
<Form
  form={form}
  layout="vertical"
  onFinish={handleSubmit}
  autoComplete="off"
>
  <Form.Item
    name="email"
    label="邮箱"
    rules={[
      { required: true, message: '请输入邮箱' },
      { type: 'email', message: '邮箱格式不正确' },
    ]}
  >
    <Input placeholder="请输入邮箱" />
  </Form.Item>
</Form>
```

### Modal（弹窗）
- 表单弹窗用 `destroyOnClose` 确保关闭后重置状态
- `afterClose` 用于关闭后的清理回调
- 确认弹窗用 `Modal.confirm()` 快捷方法

```tsx
<Modal
  title="编辑用户"
  open={isOpen}
  onOk={handleSave}
  onCancel={handleCancel}
  confirmLoading={saving}
  destroyOnClose
  afterClose={() => form.resetFields()}
>
  <UserForm form={form} user={editingUser} />
</Modal>

// 确认弹窗
Modal.confirm({
  title: '确认删除',
  content: '确定要删除该用户吗？此操作不可恢复。',
  okText: '确认删除',
  okType: 'danger',
  onOk: () => deleteUser(id),
})
```

### Select（选择器）
- 选项少时直接写 `<Select.Option>`；选项多时使用 `options` 数组属性
- 远程搜索使用 `showSearch` + `onSearch` + `filterOption` 自定义
- 多选用 `mode="multiple"`

### DatePicker（日期选择器）
- 使用 `format` 指定显示格式
- 表单中配合 `Form.Item` 使用，值类型为 `dayjs` 对象
- 范围选择用 `DatePicker.RangePicker`

### Space（间距）
- 组件间间距优先使用 `<Space>` 包裹，避免手动 `margin`
- 默认间距为 `size="small"`（8px），可根据上下文调整

### message / notification（消息提示）
- 操作反馈使用 `message.success()` / `message.error()` 轻量提示
- 重要通知使用 `notification.open()` / `notification.info()`
- 不要在组件中手动创建 message 实例 — 使用静态方法即可

### Spin（加载中）
- 页面级加载使用 `Spin` 包裹内容区域
- 组件级加载使用 Spin 组件的 `spinning` 属性
- 全局加载状态使用 `Spin` + Suspense（React.lazy 场景）

## 主题定制

```tsx
<ConfigProvider
  theme={{
    token: {
      colorPrimary: '#1677ff',
      borderRadius: 6,
      colorBgContainer: '#ffffff',
    },
    components: {
      Table: {
        headerBg: '#fafafa',
        rowHoverBg: '#f5f5f5',
      },
    },
  }}
>
  <App />
</ConfigProvider>
```

## Ant Design + Tailwind CSS 共存

- Ant Design 负责组件内部样式，Tailwind 负责页面/组件外部的布局和间距
- 避免在 Ant Design 组件上直接用 Tailwind 覆盖内联样式（Ant Design 的 CSS-in-JS 优先级高）
- 布局使用 Tailwind 的 `flex`/`grid` 类 + Ant Design 的 `Row`/`Col` 搭配
- 使用 Tailwind 的 `dark:` 变体时，需同时配置 Ant Design ConfigProvider 的 `theme.algorithm`（`darkAlgorithm`）

## 性能注意

- 大列表（>500 行）使用 Table 的 `virtual` 属性开启虚拟滚动
- 大数据集的选择器使用 `virtual` 属性（Select + options 数量多时）
- 避免频繁调用 `message`/`notification` — 使用 `message.destroy()` 或防抖

# Ant Design 组件代码示例

## 完整数据表格（搜索 + 分页 + 操作列）

```tsx
import { useState, useEffect } from 'react'
import { Table, Button, Space, Input, Tag, Modal, message } from 'antd'
import { SearchOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import type { User, PageResponse } from '../types/user'
import { userService } from '../services/userService'

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })
  const [search, setSearch] = useState('')

  const fetchUsers = async (page: number, size: number, keyword?: string) => {
    setLoading(true)
    try {
      const data: PageResponse<User> = await userService.list({ page, size, search: keyword })
      setUsers(data.content)
      setPagination(prev => ({ ...prev, current: data.number, total: data.totalElements }))
    } catch {
      message.error('加载用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers(pagination.current, pagination.pageSize, search)
  }, [pagination.current, pagination.pageSize])

  const handleSearch = (value: string) => {
    setSearch(value)
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  const handleDelete = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后不可恢复，确定继续？',
      okText: '删除',
      okType: 'danger',
      onOk: async () => {
        await userService.delete(id)
        message.success('删除成功')
        fetchUsers(pagination.current, pagination.pageSize, search)
      },
    })
  }

  const columns: ColumnsType<User> = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const color = role === 'ADMIN' ? 'red' : role === 'EDITOR' ? 'blue' : 'default'
        return <Tag color={color}>{role}</Tag>
      },
    },
    {
      title: '状态',
      dataIndex: 'active',
      key: 'active',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'default'}>{active ? '活跃' : '停用'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Input.Search
          placeholder="搜索用户名/邮箱"
          allowClear
          onSearch={handleSearch}
          style={{ width: 300 }}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新增用户
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={loading}
        pagination={{
          ...pagination,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
        onChange={(pag: TablePaginationConfig) => {
          setPagination(prev => ({
            ...prev,
            current: pag.current ?? 1,
            pageSize: pag.pageSize ?? 20,
          }))
        }}
      />
    </div>
  )
}
```

## 表单弹窗（创建/编辑）

```tsx
interface UserFormModalProps {
  open: boolean
  editingUser?: User | null
  onClose: () => void
  onSuccess: () => void
}

const UserFormModal: React.FC<UserFormModalProps> = ({ open, editingUser, onClose, onSuccess }) => {
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const isEditing = !!editingUser

  useEffect(() => {
    if (open) {
      if (editingUser) {
        form.setFieldsValue({
          displayName: editingUser.displayName,
          email: editingUser.email,
          role: editingUser.role,
        })
      } else {
        form.resetFields()
      }
    }
  }, [open, editingUser, form])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)
      if (isEditing) {
        await userService.update(editingUser!.id, values)
        message.success('用户信息已更新')
      } else {
        await userService.create(values)
        message.success('用户创建成功')
      }
      onSuccess()
      onClose()
    } catch (err) {
      // Form validateFields 校验失败会自动聚焦到错误字段，不需要额外处理
      if (err instanceof Error) {
        message.error(err.message)
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      title={isEditing ? '编辑用户' : '新增用户'}
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={saving}
      destroyOnClose
      okText={isEditing ? '保存' : '创建'}
    >
      <Form
        form={form}
        layout="vertical"
        autoComplete="off"
      >
        <Form.Item
          name="displayName"
          label="显示名称"
          rules={[{ required: true, message: '请输入显示名称' }]}
        >
          <Input placeholder="请输入显示名称" />
        </Form.Item>

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
      </Form>
    </Modal>
  )
}
```

## 响应式布局

```tsx
import { Row, Col, Card, Statistic } from 'antd'
import { UserOutlined, FileTextOutlined, AuditOutlined } from '@ant-design/icons'

const Dashboard: React.FC = () => {
  return (
    <div>
      {/* 统计卡片 - 响应式栅格 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="用户总数" value={1280} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="文档数" value={356} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="待审核" value={23} prefix={<AuditOutlined />} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
```

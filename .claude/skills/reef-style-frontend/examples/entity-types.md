# React 实体类型定义示例

## 基础实体层次

```tsx
// shared/types/entity.ts
export interface ImmutableEntity {
  readonly id: string
  readonly createdAt: string
  readonly updatedAt: string
}

export interface Entity extends ImmutableEntity {
  version: number
}

export interface Auditable<T> extends Entity {
  createdBy: T
  updatedBy: T
}

export interface ImmutableAuditable<T> extends ImmutableEntity {
  createdBy: T
}
```

## API 响应类型

```tsx
// shared/types/api.ts
export interface PageResponse<T> {
  content: T[]
  totalElements: number
  totalPages: number
  number: number
  size: number
  first: boolean
  last: boolean
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, string[]>
}
```

## 业务实体示例

```tsx
// shared/types/user.ts
export interface User extends Auditable<string> {
  username: string
  email: string
  displayName: string
  avatar?: string
  role: UserRole
  active: boolean
}

export enum UserRole {
  Admin = 'ADMIN',
  Editor = 'EDITOR',
  Viewer = 'VIEWER',
}

export interface CreateUserRequest {
  username: string
  email: string
  displayName: string
  role: UserRole
}

export interface UpdateUserRequest {
  email?: string
  displayName?: string
  role?: UserRole
}
```

## 组件 Props 类型

```tsx
// 通用组件：具名导出 + interface Props
export interface UserAvatarProps {
  user: Pick<User, 'username' | 'avatar'>
  size?: 'sm' | 'md' | 'lg'
  onClick?: () => void
}

export const UserAvatar: React.FC<UserAvatarProps> = ({ user, size = 'md', onClick }) => {
  return (
    <Avatar
      src={user.avatar}
      alt={user.username}
      size={size === 'sm' ? 24 : size === 'md' ? 32 : 48}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    />
  )
}

// 页面组件：默认导出 + Props 从路由参数推断
export interface UserListPageProps {
  // 可由 React Router loader 数据注入
}

const UserListPage: React.FC<UserListPageProps> = () => {
  const { users, loading } = useUsers()
  return <UserTable users={users} loading={loading} />
}
export default UserListPage
```

## Discriminated Union 类型

```tsx
// 用于多状态组件
export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface NotificationConfig {
  type: NotificationType
  title: string
  message: string
  duration?: number
}
```

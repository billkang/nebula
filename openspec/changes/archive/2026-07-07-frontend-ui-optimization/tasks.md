## 1. 依赖安装与基础设施

- [x] 1.1 安装 antd、@ant-design/icons 依赖
- [x] 1.2 创建 theme/ 目录结构（ThemeProvider、tokens、variables.css）
- [x] 1.3 定义 Design Tokens（tokens.ts — 浅色/深色双主题色值常量）
- [x] 1.4 创建 CSS Variables（variables.css — 在 :root 和 .dark 下声明）
- [x] 1.5 实现 ThemeProvider 组件（读取偏好 + 系统检测 + ConfigProvider 包裹）
- [x] 1.6 实现 useTheme hook 导出（theme、toggleTheme、setTheme、isDark）
- [x] 1.7 在 main.tsx 中包裹 ThemeProvider
- [x] 1.8 扩展 tailwind.config.js（自定义主题色引用 CSS Variables）
- [x] 1.9 重写 index.css（CSS Variables 驱动的基础样式）
- [x] 1.10 在 index.html 中添加内联 style 防 FOUC（首屏主题闪烁）

## 2. 布局重构 — 毛玻璃侧边栏 + 主题切换

- [x] 2.1 重写 Sidebar.tsx：毛玻璃效果 + 浅色/深色背景适配
- [x] 2.2 重写 Sidebar.tsx：导航项 hover/active 状态样式
- [x] 2.3 新增 ThemeToggle.tsx 组件（Sun/Moon 图标切换）
- [x] 2.4 在 Sidebar 中集成 ThemeToggle
- [x] 2.5 重写 AppLayout.tsx：main 区域 padding、内容区布局调整
- [x] 2.6 在 App.tsx 中添加页面路由过渡动画（fade）

## 3. 认证页面重写

- [x] 3.1 重写 Login.tsx（居中卡片布局、品牌色渐变背景）
- [x] 3.2 重写 Register.tsx（与 Login 风格一致）

## 4. 项目列表面页重写

- [x] 4.1 重写 Projects.tsx（卡片网格、hover 阴影效果）
- [x] 4.2 添加 skeleton 加载骨架

## 5. 对话页面重写

- [x] 5.1 重写 Chat.tsx 页面容器样式
- [x] 5.2 重写 MessageBubble.tsx（气泡样式、时间戳、入场动画）
- [x] 5.3 重写 MessageInput.tsx（浮层输入、send 按钮 hover 动画）
- [x] 5.4 重写 ConfirmCard.tsx（左侧 accent 边框、动画）
- [x] 5.5 重写 StatusBadge.tsx（语义色、pulse 动画）
- [x] 5.6 重写 DocViewer.tsx（文档卡片样式）
- [x] 5.7 重写 FileTreePanel.tsx（树形列表样式）

## 6. 沙箱页面重写

- [x] 6.1 重写 SandboxHeader.tsx（toolbar 样式）
- [x] 6.2 重写 SandboxMonacoEditor.tsx（容器样式 + 主题同步 light/dark）
- [x] 6.3 重写 SandboxDiffView.tsx（diff 行颜色）
- [x] 6.4 重写 SandboxSnapshotPanel.tsx（快照卡片、hover 效果）
- [x] 6.5 重写 Sandbox.tsx 页面容器样式

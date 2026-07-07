## Context

星云 (Nebula) 平台前端（`packages/build-engine/frontend/`）当前使用纯 Tailwind CSS 进行样式开发，未使用任何组件库。视觉上缺少统一的设计语言和品牌感，存在以下问题：

- 无设计 token 体系，所有颜色写在 Tailwind utility class 中
- 不支持暗黑模式
- 无动画/微交互
- 布局组件（侧边栏、卡片、消息气泡）视觉效果简单

本变更引入 **Ant Design v5** 组件库，基于其 Design Token 体系 + ConfigProvider 实现主题定制，参考 **Linear App** 设计语言，以浅蓝色系为品牌主色进行全面 UI 重做。

## Goals / Non-Goals

**Goals：**
- 建立统一的设计 token 体系（颜色、字体、间距、圆角、阴影），同时作用于 Ant Design 组件和 Tailwind utility
- 实现浅色/深色双主题，支持系统偏好检测 + 手动切换
- 所有页面和组件的视觉升级（登录、注册、项目列表、对话、文档、沙箱）
- 毛玻璃侧边栏效果
- 页面路由过渡、hover 微交互、加载骨架动画
- 主题切换 UI 入口

**Non-Goals：**
- 不改变现有交互逻辑、API 调用、数据流
- 不做移动端响应式适配
- 不替换现有技术栈（React Router、Zustand、React Query 维持不变）
- 不新增页面或功能
- 不涉及后端改动

## Decisions

### D1：Design Token 体系 — Ant Design ConfigProvider + Tailwind CSS Variables

| 方面 | 决策 |
|------|------|
| **方案** | 以 Ant Design `ConfigProvider` 的 `theme.token` 为单一事实源，通过 CSS Variables 同步到 Tailwind |
| **实现** | 自定义 `ThemeProvider` 组件包裹 `ConfigProvider`，在 light/dark 切换时同时更新 Ant Design token 和 CSS 自定义属性 |
| **Token 映射** | 品牌色 → `colorPrimary`, `colorInfo`；语义色 → `colorSuccess`, `colorWarning`, `colorError`；中性色 → `colorText`, `colorBgContainer` 等 |
| **Tailwind 同步** | `tailwind.config.js` 的 `theme.extend.colors` 引用 CSS Variables（`var(--color-primary)`），实现双体系颜色一致 |

**Rationale：**
- Ant Design 的 Design Token 体系是业内最完善的组件级主题方案之一
- CSS Variables 桥接方案让 Tailwind utility class 和 Ant Design 组件共享同一套色板
- v5 的 CSS-in-JS 方案无需 Less 编译，与 Vite 兼容性好

### D2：主题架构 — Context Provider + CSS Variables + localStorage

```
ThemeProvider (Context)
├── 读取系统偏好 / localStorage
├── ConfigProvider (antd theme.lightAlgorithm / darkAlgorithm)
│   └── set CSS Variables on :root / .dark
└── 提供 useTheme() hook (theme, toggleTheme, setTheme)
```

**实现方式：**
1. `packages/build-engine/frontend/src/theme/ThemeProvider.tsx` — 核心 Provider
2. `packages/build-engine/frontend/src/theme/tokens.ts` — 浅色/深色 token 定义
3. `packages/build-engine/frontend/src/theme/variables.css` — CSS 自定义属性变量
4. `packages/build-engine/frontend/src/hooks/useTheme.ts` — 主题 hook

**初始加载顺序：** `localStorage` 设置 → `prefers-color-scheme`（首次访问）→ 默认 light

### D3：Ant Design 版本选择

| 版本 | Bundle 策略 | 集成方式 |
|------|------------|---------|
| v5（选定） | Tree-shakable，CSS-in-JS | ESM import，`ConfigProvider` 包裹 |
| v4 | 需 Less 编译 | 与 Vite/Tailwind 兼容性差 |

**选择 v5**：v5 使用 CSS-in-JS 运行时方案，无需 Less 预处理，与 Tailwind 协同工作最简单。

### D4：毛玻璃效果实现

```css
.glass-sidebar {
  background: rgba(255, 255, 255, 0.7);       /* light mode */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-right: 1px solid rgba(229, 231, 235, 0.5);
}

.dark .glass-sidebar {
  background: rgba(15, 15, 30, 0.75);           /* dark mode */
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}
```

- 侧边栏使用 CSS class 直接实现，不依赖额外库
- `backdrop-filter` 需要父容器非透明背景，已经在 AppLayout 层级解决

### D5：动效实现 — Pure CSS + 少量 React 集成

| 动效类型 | 实现方式 |
|---------|---------|
| Hover/focus 过渡 | CSS `transition` + Tailwind `transition-*` `duration-*` |
| 页面路由过渡 | React Router 的 `useLocation` + CSS class 切换（fade） |
| Skeleton 加载 | Tailwind `animate-pulse` + antd `<Skeleton>` |
| 列表入场/出场 | CSS animation `fadeIn`/`fadeOut` |

**不引入 framer-motion**（根据 grill-me 确认），降低依赖成本和 bundle 大小。

### D6：安装包清单

| 包 | 版本 | 用途 |
|---|------|------|
| `antd` | ^5.x | 组件库 + Design Token 体系 |
| `@ant-design/icons` | ^5.x | Ant Design 图标集 |

无需其他新依赖。现有 `tailwindcss`、`react-router-dom`、`zustand`、`react-query` 保持不变。

### D7：@nebula/shared-ui 包策略

暂不将主题相关逻辑迁移到 shared-ui。所有主题/样式文件直接放在 `build-engine/frontend/` 下，等后续有多个前端使用时再抽取。shared-ui 包保持空壳。

### D8：页面重写范围矩阵

| 页面 | 组件 | 改动类型 | 说明 |
|------|------|---------|------|
| Login | Login.tsx | 样式重写 | 居中卡片布局，品牌色背景，渐变/毛玻璃效果 |
| Register | Register.tsx | 样式重写 | 与 Login 风格一致 |
| Projects | Projects.tsx | 样式重写 | 项目卡片网格，hover 阴影，skeleton 加载 |
| Chat | Chat.tsx | 样式重写 | 背景色、消息流、输入区 |
|  | MessageBubble.tsx | 样式重写 | 气泡样式、时间戳、动画 |
|  | MessageInput.tsx | 样式重写 | 输入框浮层、send 按钮 |
|  | ConfirmCard.tsx | 样式重写 | 左侧 accent 边框、动画 |
|  | StatusBadge.tsx | 样式重写 | 语义色、pulse 动画 |
|  | DocViewer.tsx | 样式重写 | 文档卡片、间距 |
|  | FileTreePanel.tsx | 样式重写 | 树形列表样式 |
| Sandbox | SandboxHeader.tsx | 样式重写 | Toolbar 样式 |
|  | SandboxMonacoEditor.tsx | 样式重写 | 容器样式、主题同步 |
|  | SandboxDiffView.tsx | 样式重写 | diff 行颜色、边框 |
|  | SandboxSnapshotPanel.tsx | 样式重写 | 快照卡片、hover 效果 |
| Layout | AppLayout.tsx | 结构+样式重写 | main 区域 padding、布局调整 |
|  | Sidebar.tsx | 结构+样式重写 | 毛玻璃效果、导航项、主题切换 |

## Risks / Trade-offs

| 风险 | 缓解方案 |
|------|---------|
| Ant Design v5 CSS-in-JS 在 Vite 下热更新性能 | v5 仅首屏计算样式，热更新时增量 diff，通常在可接受范围。如遇到性能问题，可用 `@ant-design/cssinjs` 的缓存优化 |
| `backdrop-filter` 在部分旧浏览器不支持 | 使用 `@supports` 做 feature query，不支持时回退到纯色半透明背景 |
| 样式覆盖冲突（Ant Design class 与 Tailwind） | Tailwind 样式写在组件 className 上，Ant Design 的 cssinjs 样式有更高特异性。如需覆盖，使用 `!important` 语义明确的位置 |
| 暗黑模式切换瞬间闪烁 | 通过 <style> 标签内联在 index.html 中设置初始主题（防止 FOUC） |
| 主题变量数量大，维护成本 | token 定义集中在 `tokens.ts` 中，与 `tailwind.config.js` 的 extend 共享同一份色值常量 |

## Change Scope Matrix

| 文件 | 操作 | 说明 |
|------|------|------|
| `package.json` | 修改 | 新增 `antd`、`@ant-design/icons` 依赖 |
| `src/main.tsx` | 修改 | 包裹 `ThemeProvider` |
| `src/index.css` | 修改 | 替换为 CSS Variables + theme 变量 |
| `src/App.tsx` | 修改 | 添加页面过渡动画 |
| `src/theme/ThemeProvider.tsx` | 新增 | 主题上下文 Provider |
| `src/theme/tokens.ts` | 新增 | 浅色/深色 token 定义 |
| `src/theme/variables.css` | 新增 | CSS 自定义属性 |
| `src/hooks/useTheme.ts` | 新增 | 主题 hook |
| `src/components/ThemeToggle.tsx` | 新增 | 主题切换按钮 |
| `src/components/AppLayout.tsx` | 修改 | 布局样式重写 |
| `src/components/Sidebar.tsx` | 修改 | 毛玻璃风格重写 |
| `src/components/MessageBubble.tsx` | 修改 | 气泡样式重写 |
| `src/components/MessageInput.tsx` | 修改 | 输入区样式重写 |
| `src/components/ConfirmCard.tsx` | 修改 | 样式重写 |
| `src/components/StatusBadge.tsx` | 修改 | 样式重写 |
| `src/components/DocViewer.tsx` | 修改 | 样式重写 |
| `src/components/FileTreePanel.tsx` | 修改 | 样式重写 |
| `src/components/SandboxHeader.tsx` | 修改 | 样式重写 |
| `src/components/SandboxMonacoEditor.tsx` | 修改 | 样式重写 + 主题同步 |
| `src/components/SandboxDiffView.tsx` | 修改 | 样式重写 |
| `src/components/SandboxSnapshotPanel.tsx` | 修改 | 样式重写 |
| `src/pages/Login.tsx` | 修改 | 样式重写 |
| `src/pages/Register.tsx` | 修改 | 样式重写 |
| `src/pages/Projects.tsx` | 修改 | 样式重写 |
| `src/pages/Chat.tsx` | 修改 | 样式重写 |
| `src/pages/Docs.tsx` | 修改 | 样式重写 |
| `src/pages/Sandbox.tsx` | 修改 | 样式重写 |
| `tailwind.config.js` | 修改 | 扩展自定义颜色主题 |

总共：新增约 5 个文件，修改约 24 个文件。

## Validation Approach

本变更为纯视觉变更，不涉及逻辑测试。验证策略：

1. **主题切换** — 手动在 light/dark 模式间切换，确认所有页面和组件正确响应
2. **视觉检查** — 逐页面遍历，确保所有 UI 元素渲染正常：Login → Register → Projects → Chat → Docs → Sandbox
3. **交互状态** — 检查按钮/卡片/链接的 hover、focus、active 状态
4. **动画效果** — 确认路由过渡、骨架屏、列表入场动画正常播放
5. **毛玻璃效果** — 确认 `backdrop-filter` 在 Chrome/Safari/Firefox 下正常工作
6. **Monaco 主题同步** — 切换整体主题时，代码编辑器正确切换 vs/vs-dark
7. **功能回归** — 核心流（登录→查看项目→发送消息→沙箱操作）在主题切换前后仍可用
8. **构建验证** — `pnpm build` 通过

## Known Limitations

1. **Ant Design 版本锁定风险** — antd v5 若未来有 breaking change 需迁移
2. **CSS Variables 桥接维护成本** — 新增颜色需同时维护 Ant Design tokens 和 CSS Variables
3. **毛玻璃滚动性能** — `backdrop-filter` 在复杂内容滚动时可能产生性能问题，实现后需实测
4. **双主题不可扩展** — 当前仅支持两套硬编码色值，自定义主题需重构
5. **无设计稿驱动** — 视觉一致性多人协作时可能退化

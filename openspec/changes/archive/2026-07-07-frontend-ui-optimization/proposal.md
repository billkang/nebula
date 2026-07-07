## Why

星云 (Nebula) 平台当前前端页面 UI 质量较低，所有样式基于纯 Tailwind CSS 默认色板，缺少统一的视觉设计语言。主要痛点：

1. **无品牌感** — 使用 Tailwind 默认蓝色系，没有品牌标识和视觉层次
2. **页面寡淡** — 大面积白色/灰色背景，卡片无质感，缺乏视觉层级
3. **无暗黑模式** — 仅支持浅色主题，夜间使用体验差
4. **缺乏微交互** — 页面切换、按钮悬浮、列表项均无过渡动画，交互生硬
5. **无组件库** — 未使用 Ant Design 等组件库，手写 UI 导致一致性差、开发效率低

本变更旨在通过引入 Linear App 风格的设计语言 + Ant Design 组件库，全面提升前端视觉品质和用户体验。

**关键决策：** 本次仅改视觉外观和布局，不涉及交互逻辑变更。

## What Changes

- 安装并接入 **Ant Design** 组件库（v5），通过 ConfigProvider 定制 Design Token
- 基于 **浅蓝色系 + Linear 风格** 重写全局样式体系（颜色、圆角、阴影、字体、间距）
- 引入 **暗黑模式**，支持浅色/深色双主题切换（含系统偏好检测 + 手动切换）
- 新增 **微交互动画体系**（页面过渡、悬浮效果、加载骨架、列表入场/出场）
- 重写 **AppLayout** 布局（毛玻璃侧边栏、呼吸感内容区）
- 重写所有页面（Login、Register、Projects、Chat、Docs、Sandbox）的视觉样式
- 重构 **Sidebar** 为毛玻璃风格导航
- 美化 **Chat / MessageBubble** 组件（气泡消息、渐变背景）
- 美化 **Sandbox** 系列组件（代码编辑器、Diff 视图、快照面板）
- 配置 Tailwind CSS 扩展主题（自定义颜色与 Ant Design tokens 对齐）
- **填充 @nebula/shared-ui 包** — 迁移共享样式变量和基础组件

## Capabilities

### New Capabilities
- `design-token-system`: Ant Design Design Token 体系 + Tailwind 主题扩展，定义品牌色板、语义色、圆角、阴影、字体、间距等设计变量
- `dark-mode`: 浅色/深色双主题切换能力，含系统偏好自动检测（prefers-color-scheme）和手动切换 UI
- `micro-interactions`: 全局微交互动画系统（页面路由过渡、hover 缩放/阴影、列表入场动画、Loading Skeleton 动画）
- `glassmorphism-sidebar`: 毛玻璃风格侧边栏导航组件
- `chat-ui-enhancement`: 优化对话界面，消息气泡、输入区、确认卡片等组件的视觉升级
- `sandbox-ui-enhancement`: 沙箱页面（Monaco Editor、Diff View、Snapshot Panel）视觉升级
- `theme-switcher`: 主题切换 UI，用户可手动在浅色/深色模式间切换

### Modified Capabilities
- （无现有 spec 变更 — 本变更不修改现有功能的行为逻辑）

## Impact

| 方面 | 影响 |
|------|------|
| **FE 依赖** | 新增 `antd` v5、`@ant-design/icons`（动效用纯 CSS 实现，不引入额外库） |
| **样式系统** | 引入 Ant Design Design Token + CSS Variables 双体系，重构 `index.css` 为设计变量驱动 |
| **布局组件** | AppLayout、Sidebar 重写为毛玻璃风格 |
| **页面代码** | 所有页面（Login/Register/Projects/Chat/Docs/Sandbox）样式层重写 |
| **Tailwind 配置** | `tailwind.config.js` 扩展自定义主题色，与 Ant Design tokens 同步 |
| **暗黑模式** | 新增 ThemeProvider 上下文 + 系统偏好检测 |
| **@nebula/shared-ui** | 暂不涉及（设计 tokens 直接放在 frontend/ 内，后续多前端时再抽取） |
| **权限系统** | 无影响 |
| **多租户** | 无影响 |
| **后端 API** | 无影响 |
| **数据库** | 无影响 |

## Out of Scope

以下内容明确不在本变更范围内（v1 不做）：

1. **交互逻辑改动** — 按钮点击、页面跳转、表单提交等交互行为保持不变，仅改视觉呈现
2. **移动端响应式适配** — 桌面端优先，移动端/平板适配推迟到后续版本
3. **组件库替换** — 不移除 Ant Design 以外的组件库，也不引入新组件库
4. **新增页面或功能** — 不添加任何新页面、路由、API 端点或功能模块
5. **后端/API 变更** — 不修改任何后端代码、API 接口、数据库结构
6. **品牌视觉全面设计系统** — 本次仅定义颜色/间距/字体 token，完整的品牌设计系统（Logo、插画风格、图标库等）推迟到 v2
7. **Figma 设计稿产出** — 无设计资源，全靠代码实现视觉效果（设计色值为草案值，实现时可调整）
8. **用户测试/可用性研究** — 不进行正式的 A/B 测试或用户调研
9. **无障碍专项审计** — 虽遵循 basic WCAG 要求（对比度 4.5:1），但不做专项无障碍合规审计

## Validation

| 验证项 | 方法 |
|--------|------|
| 主题切换功能 | 手动验证：点击主题切换按钮，页面在浅色/深色间正确切换，Ant Design 组件随主题更新 |
| 毛玻璃效果 | 手动验证：侧边栏在两种主题下均显示 backdrop-blur 效果 |
| 页面样式 | 视觉检查：逐页巡视 Login/Register/Projects/Chat/Docs/Sandbox，确认样式一致 |
| 动效 | 手动验证：hover 按钮有过渡动画、路由切换有 fade、skeleton 加载正常显示 |
| 暗黑模式 | 手动验证：设置 prefers-color-scheme: dark 访问首页，自动加载深色主题 |
| 动画时长 | 默认值 200ms/300ms 为草案值，实现后根据实测感知调整 |
| 颜色值 | 所有色值为草案值，实现时以视觉效果为准，无需严格对应 hex 值 |
| 功能回归 | 手动验证：登录、注册、项目创建、对话发送、沙箱打开等核心功能在主题切换后仍正常工作 |
| Build | `pnpm build` 无错误 |
| Bundle | `antd` 首次引入后检查构建产物增量大小 |

## Known Limitations

1. **Ant Design 版本锁定风险** — 当前选择 antd v5，若未来 v6 有 breaking change 或弃用 CSS-in-JS 方案，需要迁移计划
2. **CSS Variables 桥接维护成本** — Ant Design tokens 和 Tailwind CSS Variables 需要同步维护，新增颜色时需同时在两处添加
3. **毛玻璃滚动性能** — `backdrop-filter` 在复杂页面内容滚动时可能产生 jank，实现后需要实际测试
4. **双主题扩展性** — 当前仅支持浅色/深色两套硬编码色值，未来如需支持自定义主题/品牌色，需要重构为动态 token
5. **无设计稿驱动** — 全靠代码中"目测"的颜色值，多人协作时视觉一致性可能随人员变化而退化

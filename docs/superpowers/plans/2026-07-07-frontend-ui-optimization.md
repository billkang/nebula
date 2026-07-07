# Frontend UI Optimization 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将星云平台前端从纯 Tailwind 默认样式全面升级为 Linear 风格 + Ant Design v5 Design Token 体系，含浅色/深色双主题、毛玻璃侧边栏、微交互动画。

**Architecture:** 以 Ant Design `ConfigProvider` 的 `theme.token` 为 Design Token 单一事实源，通过 CSS Variables 桥接到 Tailwind；自定义 `ThemeProvider` 组件管理浅色/深色主题切换；所有现有组件只改 className/样式，不改交互逻辑。

**Tech Stack:** React 18 + TypeScript 5 + Vite 5 + Ant Design v5 + Tailwind CSS 3 + Zustand

## Global Constraints

- 不修改任何交互逻辑、API 调用、数据流
- 不新增页面、路由、功能
- 不做移动端响应式适配
- 所有动效用纯 CSS transition/animation 实现，不引入 framer-motion
- 代码用中文 commit message

## File Structure

```
packages/build-engine/frontend/src/
├── theme/
│   ├── ThemeProvider.tsx       # [NEW] 主题上下文 Provider
│   ├── tokens.ts               # [NEW] 浅色/深色设计 token 定义
│   └── variables.css            # [NEW] CSS 自定义属性变量
├── hooks/
│   └── useTheme.ts             # [NEW] 主题 hook
├── components/
│   ├── ThemeToggle.tsx          # [NEW] 主题切换按钮（Sun/Moon 图标）
│   ├── AppLayout.tsx            # [MODIFY] 布局重写
│   ├── Sidebar.tsx              # [MODIFY] 毛玻璃侧边栏
│   ├── MessageBubble.tsx        # [MODIFY] 气泡样式
│   ├── MessageInput.tsx         # [MODIFY] 输入区样式
│   ├── ConfirmCard.tsx          # [MODIFY] 确认卡片样式
│   ├── StatusBadge.tsx          # [MODIFY] 状态徽章样式
│   ├── DocViewer.tsx            # [MODIFY] 文档阅读器样式
│   ├── FileTreePanel.tsx        # [MODIFY] 文件树样式
│   ├── SandboxHeader.tsx        # [MODIFY] 沙箱工具栏样式
│   ├── SandboxMonacoEditor.tsx  # [MODIFY] 编辑器容器样式
│   ├── SandboxDiffView.tsx      # [MODIFY] Diff 视图样式
│   └── SandboxSnapshotPanel.tsx # [MODIFY] 快照面板样式
├── pages/
│   ├── Login.tsx                # [MODIFY] 登录页样式
│   ├── Register.tsx             # [MODIFY] 注册页样式
│   ├── Projects.tsx             # [MODIFY] 项目列表页样式
│   ├── Chat.tsx                 # [MODIFY] 对话页样式
│   ├── Docs.tsx                 # [MODIFY] 文档页样式
│   └── Sandbox.tsx              # [MODIFY] 沙箱页样式
├── main.tsx                     # [MODIFY] 包裹 ThemeProvider
├── App.tsx                      # [MODIFY] 添加页面过渡动画
├── index.css                    # [MODIFY] CSS Variables 驱动
├── index.html                   # [MODIFY] 防 FOUC 内联 style
└── tailwind.config.js           # [MODIFY] 扩展自定义主题色
```

---

### Task 1: 安装 Ant Design 依赖

**Files:**
- Modify: `packages/build-engine/frontend/package.json`

**Interfaces:**
- Produces: `antd` ^5.x + `@ant-design/icons` ^5.x 在 dependencies 中

- [ ] **Step 1: 安装依赖**

```bash
cd packages/build-engine/frontend
pnpm add antd @ant-design/icons
```

- [ ] **Step 2: 验证安装**

```bash
cd packages/build-engine/frontend
pnpm ls antd @ant-design/icons
```
Expected: 显示两个包及其版本号

- [ ] **Step 3: 验证构建**

```bash
cd packages/build-engine/frontend
pnpm build
```
Expected: Build 成功，无错误

---

### Task 2: 定义 Design Tokens（tokens.ts）

**Files:**
- Create: `packages/build-engine/frontend/src/theme/tokens.ts`

**Interfaces:**
- Produces: `lightTokens` 和 `darkTokens` 对象（Ant Design 主题 token）
- Produces: `cssLightVariables` 和 `cssDarkVariables` 对象（CSS 自定义属性）

- [ ] **Step 1: 创建 `src/theme/tokens.ts`**

```typescript
// src/theme/tokens.ts
// Design Token 定义 — 浅色/深色双主题
// 基于 Linear App 风格 + 浅蓝色系品牌色
// 色值为草案值，实现时可根据视觉效果调整

import type { ThemeConfig } from 'antd';

// ===== 品牌色板 =====
export const brandColors = {
  primary: '#4A9EFF',
  primaryHover: '#3B8CEE',
  primaryActive: '#2D7AD9',
  primaryBg: '#EDF4FF',
  primaryLight: '#E8F1FF',
};

// ===== 浅色主题 =====
export const lightTokens: ThemeConfig['token'] = {
  colorPrimary: brandColors.primary,
  colorInfo: brandColors.primary,
  colorSuccess: '#22C55E',
  colorWarning: '#F59E0B',
  colorError: '#EF4444',
  colorLink: brandColors.primary,
  colorTextBase: '#1A1A2E',
  colorBgContainer: '#FFFFFF',
  colorBgElevated: '#FFFFFF',
  colorBgLayout: '#F8FAFE',
  colorBorder: '#E5E7EB',
  colorBorderSecondary: '#F0F0F0',
  borderRadius: 8,
  borderRadiusLG: 12,
  borderRadiusSM: 4,
  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  fontSize: 14,
  fontSizeHeading1: 38,
  fontSizeHeading2: 30,
  fontSizeHeading3: 24,
  fontSizeHeading4: 20,
  fontSizeHeading5: 16,
  boxShadow: '0 1px 3px 0 rgba(0,0,0,0.04), 0 1px 2px 0 rgba(0,0,0,0.03)',
  boxShadowSecondary: '0 4px 6px -1px rgba(0,0,0,0.06), 0 2px 4px -2px rgba(0,0,0,0.04)',
};

// ===== 深色主题 =====
export const darkTokens: ThemeConfig['token'] = {
  colorPrimary: '#6AB0FF',
  colorInfo: '#6AB0FF',
  colorSuccess: '#22C55E',
  colorWarning: '#F59E0B',
  colorError: '#EF4444',
  colorLink: '#6AB0FF',
  colorTextBase: '#E5E7EB',
  colorBgContainer: '#1A1A2E',
  colorBgElevated: '#242444',
  colorBgLayout: '#0D0D1A',
  colorBorder: '#2D2D4D',
  colorBorderSecondary: '#262644',
  borderRadius: 8,
  borderRadiusLG: 12,
  borderRadiusSM: 4,
  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  fontSize: 14,
  fontSizeHeading1: 38,
  fontSizeHeading2: 30,
  fontSizeHeading3: 24,
  fontSizeHeading4: 20,
  fontSizeHeading5: 16,
  boxShadow: '0 1px 3px 0 rgba(0,0,0,0.3), 0 1px 2px 0 rgba(0,0,0,0.2)',
  boxShadowSecondary: '0 4px 6px -1px rgba(0,0,0,0.4), 0 2px 4px -2px rgba(0,0,0,0.3)',
};

// ===== CSS 变量映射 =====
export interface CssVariables {
  '--color-bg-layout': string;
  '--color-bg-container': string;
  '--color-bg-elevated': string;
  '--color-text-base': string;
  '--color-text-secondary': string;
  '--color-border': string;
  '--color-border-secondary': string;
  '--color-primary': string;
  '--color-primary-hover': string;
  '--color-primary-bg': string;
  '--color-success': string;
  '--color-warning': string;
  '--color-error': string;
  '--sidebar-bg': string;
  '--sidebar-border': string;
  '--sidebar-text': string;
  '--sidebar-text-secondary': string;
  '--sidebar-active-bg': string;
  '--glass-bg': string;
  '--glass-border': string;
}

export const cssLightVariables: CssVariables = {
  '--color-bg-layout': '#F8FAFE',
  '--color-bg-container': '#FFFFFF',
  '--color-bg-elevated': '#FFFFFF',
  '--color-text-base': '#1A1A2E',
  '--color-text-secondary': '#6B7280',
  '--color-border': '#E5E7EB',
  '--color-border-secondary': '#F0F0F0',
  '--color-primary': '#4A9EFF',
  '--color-primary-hover': '#3B8CEE',
  '--color-primary-bg': '#EDF4FF',
  '--color-success': '#22C55E',
  '--color-warning': '#F59E0B',
  '--color-error': '#EF4444',
  '--sidebar-bg': 'rgba(255, 255, 255, 0.7)',
  '--sidebar-border': 'rgba(229, 231, 235, 0.5)',
  '--sidebar-text': '#1A1A2E',
  '--sidebar-text-secondary': '#6B7280',
  '--sidebar-active-bg': 'rgba(74, 158, 255, 0.1)',
  '--glass-bg': 'rgba(255, 255, 255, 0.7)',
  '--glass-border': 'rgba(229, 231, 235, 0.5)',
};

export const cssDarkVariables: CssVariables = {
  '--color-bg-layout': '#0D0D1A',
  '--color-bg-container': '#1A1A2E',
  '--color-bg-elevated': '#242444',
  '--color-text-base': '#E5E7EB',
  '--color-text-secondary': '#9CA3AF',
  '--color-border': '#2D2D4D',
  '--color-border-secondary': '#262644',
  '--color-primary': '#6AB0FF',
  '--color-primary-hover': '#82BEFF',
  '--color-primary-bg': 'rgba(106, 176, 255, 0.1)',
  '--color-success': '#22C55E',
  '--color-warning': '#F59E0B',
  '--color-error': '#EF4444',
  '--sidebar-bg': 'rgba(15, 15, 30, 0.75)',
  '--sidebar-border': 'rgba(255, 255, 255, 0.08)',
  '--sidebar-text': '#E5E7EB',
  '--sidebar-text-secondary': '#9CA3AF',
  '--sidebar-active-bg': 'rgba(106, 176, 255, 0.15)',
  '--glass-bg': 'rgba(15, 15, 30, 0.75)',
  '--glass-border': 'rgba(255, 255, 255, 0.08)',
};
```

- [ ] **Step 2: 创建 `src/theme/variables.css`**

```css
/* src/theme/variables.css */
/* CSS 自定义属性 — 运行时由 ThemeProvider JS 更新值 */

:root {
  --color-bg-layout: #F8FAFE;
  --color-bg-container: #FFFFFF;
  --color-bg-elevated: #FFFFFF;
  --color-text-base: #1A1A2E;
  --color-text-secondary: #6B7280;
  --color-border: #E5E7EB;
  --color-border-secondary: #F0F0F0;
  --color-primary: #4A9EFF;
  --color-primary-hover: #3B8CEE;
  --color-primary-bg: #EDF4FF;
  --color-success: #22C55E;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --sidebar-bg: rgba(255, 255, 255, 0.7);
  --sidebar-border: rgba(229, 231, 235, 0.5);
  --sidebar-text: #1A1A2E;
  --sidebar-text-secondary: #6B7280;
  --sidebar-active-bg: rgba(74, 158, 255, 0.1);
  --glass-bg: rgba(255, 255, 255, 0.7);
  --glass-border: rgba(229, 231, 235, 0.5);
}

/* 基础结构转换 */
*, *::before, *::after {
  transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease, box-shadow 0.3s ease;
}
```

---

### Task 3: 实现 ThemeProvider

**Files:**
- Create: `packages/build-engine/frontend/src/theme/ThemeProvider.tsx`
- Create: `packages/build-engine/frontend/src/hooks/useTheme.ts`

**Interfaces:**
- Produces: `<ThemeProvider>` 组件包裹 Ant Design `ConfigProvider`
- Produces: `useTheme()` hook → `{ theme: 'light'|'dark', toggleTheme, setTheme, isDark }`

- [ ] **Step 1: 创建 `src/hooks/useTheme.ts`**

```typescript
// src/hooks/useTheme.ts
import { create } from 'zustand';

type ThemeMode = 'light' | 'dark';

interface ThemeState {
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
}

const getInitialTheme = (): ThemeMode => {
  const stored = localStorage.getItem('nebula-theme') as ThemeMode | null;
  if (stored === 'light' || stored === 'dark') return stored;
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
  return 'light';
};

export const useThemeStore = create<ThemeState>((set) => ({
  theme: getInitialTheme(),
  setTheme: (theme) => {
    localStorage.setItem('nebula-theme', theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
    set({ theme });
  },
  toggleTheme: () => {
    set((state) => {
      const next = state.theme === 'light' ? 'dark' : 'light';
      localStorage.setItem('nebula-theme', next);
      document.documentElement.classList.toggle('dark', next === 'dark');
      return { theme: next };
    });
  },
}));

export const useTheme = () => useThemeStore();
```

- [ ] **Step 2: 创建 `src/theme/ThemeProvider.tsx`**

```typescript
// src/theme/ThemeProvider.tsx
import React, { useEffect } from 'react';
import { ConfigProvider, theme } from 'antd';
import { useThemeStore, useTheme } from '../hooks/useTheme';
import { lightTokens, darkTokens, cssLightVariables, cssDarkVariables, type CssVariables } from './tokens';

function applyCssVariables(vars: CssVariables) {
  const root = document.documentElement;
  Object.entries(vars).forEach(([key, value]) => {
    root.style.setProperty(key, value);
  });
}

function ThemeProviderInner({ children }: { children: React.ReactNode }) {
  const { theme: currentTheme } = useTheme();

  useEffect(() => {
    if (currentTheme === 'dark') {
      applyCssVariables(cssDarkVariables);
    } else {
      applyCssVariables(cssLightVariables);
    }
  }, [currentTheme]);

  return (
    <ConfigProvider
      theme={{
        algorithm: currentTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: currentTheme === 'dark' ? darkTokens : lightTokens,
      }}
    >
      {children}
    </ConfigProvider>
  );
}

export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  const initTheme = useThemeStore((s) => s.theme);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', initTheme === 'dark');
    if (initTheme === 'dark') {
      applyCssVariables(cssDarkVariables);
    } else {
      applyCssVariables(cssLightVariables);
    }
  }, []);

  return (
    <ThemeProviderInner>
      {children}
    </ThemeProviderInner>
  );
}
```

---

### Task 4: 修改入口文件（main.tsx + index.html + index.css + tailwind.config.js）

**Files:**
- Modify: `packages/build-engine/frontend/src/main.tsx`
- Modify: `packages/build-engine/frontend/src/index.css`
- Modify: `packages/build-engine/frontend/tailwind.config.js`
- Modify: `packages/build-engine/frontend/index.html`

- [ ] **Step 1: 重写 `src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import './theme/variables.css';

/* 全局基础样式 */
html, body, #root {
  height: 100%;
  margin: 0;
}

body {
  background-color: var(--color-bg-layout);
  color: var(--color-text-base);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-secondary);
}

/* 动画 keyframes */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 实用类 */
.page-enter {
  animation: fadeIn 0.3s ease-out;
}
```

- [ ] **Step 2: 在 `index.html` 中添加防 FOUC 内联 style**

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>星云 · Nebula</title>
    <!-- 防 FOUC：首屏主题检测 -->
    <script>
      (function() {
        var t = localStorage.getItem('nebula-theme');
        if (t === 'dark' || (t !== 'light' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
          document.documentElement.classList.add('dark');
        }
      })();
    </script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 3: 修改 `src/main.tsx`** — 包裹 ThemeProvider

```typescript
// src/main.tsx
import React, { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import ThemeProvider from './theme/ThemeProvider';
import App from './App';
import './index.css';

const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
```

- [ ] **Step 4: 修改 `tailwind.config.js`** — 扩展自定义主题色

```javascript
// tailwind.config.js
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--color-primary)',
          hover: 'var(--color-primary-hover)',
          bg: 'var(--color-primary-bg)',
        },
        surface: {
          layout: 'var(--color-bg-layout)',
          container: 'var(--color-bg-container)',
          elevated: 'var(--color-bg-elevated)',
        },
        text: {
          primary: 'var(--color-text-base)',
          secondary: 'var(--color-text-secondary)',
        },
        border: {
          DEFAULT: 'var(--color-border)',
          secondary: 'var(--color-border-secondary)',
        },
        semantic: {
          success: 'var(--color-success)',
          warning: 'var(--color-warning)',
          error: 'var(--color-error)',
        },
      },
      fontFamily: {
        sans: ["'Inter'", '-apple-system', 'BlinkMacSystemFont', "'Segoe UI'", 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '8px',
        sm: '4px',
        lg: '12px',
      },
    },
  },
  plugins: [],
};
```

- [ ] **Step 5: 验证构建**

```bash
cd packages/build-engine/frontend
pnpm build
```
Expected: Build 成功

---

### Task 5: 重写 Sidebar（毛玻璃 + 主题切换）

**Files:**
- Modify: `packages/build-engine/frontend/src/components/Sidebar.tsx`
- Create: `packages/build-engine/frontend/src/components/ThemeToggle.tsx`
- Modify: `packages/build-engine/frontend/src/components/AppLayout.tsx`

- [ ] **Step 1: 重写 `Sidebar.tsx`**

```typescript
// src/components/Sidebar.tsx
// 毛玻璃风格侧边栏
import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store';
import ThemeToggle from './ThemeToggle';

// 导航项配置
const navItems = [
  { path: '/projects', label: '项目', icon: '📁' },
  { path: '/docs', label: '文档', icon: '📄' },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, token, logout } = useAuthStore();

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiClient('/projects'),
    enabled: !!token,
  });

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <aside
      className="flex h-screen w-64 flex-col border-r"
      style={{
        background: 'var(--sidebar-bg)',
        borderColor: 'var(--sidebar-border)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
      }}
    >
      {/* Logo / 品牌区 */}
      <div className="flex items-center gap-2 px-5 py-5">
        <span className="text-xl" style={{ color: 'var(--color-primary)' }}>✦</span>
        <span className="text-lg font-semibold" style={{ color: 'var(--sidebar-text)' }}>
          星云
        </span>
      </div>

      {/* 导航菜单 */}
      <nav className="flex-1 space-y-1 px-3">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150"
            style={{
              color: isActive(item.path) ? 'var(--color-primary)' : 'var(--sidebar-text-secondary)',
              background: isActive(item.path) ? 'var(--sidebar-active-bg)' : 'transparent',
            }}
            onMouseEnter={(e) => {
              if (!isActive(item.path)) {
                e.currentTarget.style.background = 'var(--sidebar-active-bg)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive(item.path)) {
                e.currentTarget.style.background = 'transparent';
              }
            }}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      {/* 项目快捷列表 */}
      {projects && projects.length > 0 && (
        <div className="border-t px-3 py-3" style={{ borderColor: 'var(--sidebar-border)' }}>
          <p className="mb-2 px-3 text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--sidebar-text-secondary)' }}>
            项目
          </p>
          <div className="space-y-0.5">
            {projects.slice(0, 5).map((p: any) => (
              <Link
                key={p.id}
                to={`/projects/${p.id}`}
                className="block truncate rounded-md px-3 py-1.5 text-xs transition-colors duration-150"
                style={{
                  color: 'var(--sidebar-text-secondary)',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--sidebar-active-bg)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
              >
                {p.name}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* 底部：用户信息 + 主题切换 + 登出 */}
      <div className="border-t px-3 py-3" style={{ borderColor: 'var(--sidebar-border)' }}>
        <div className="flex items-center justify-between rounded-lg px-3 py-2">
          <div className="flex flex-col">
            <span className="text-sm font-medium" style={{ color: 'var(--sidebar-text)' }}>
              {user?.username || '用户'}
            </span>
            <span className="text-xs" style={{ color: 'var(--sidebar-text-secondary)' }}>
              {user?.role || ''}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <button
              onClick={handleLogout}
              className="rounded-md p-1.5 transition-colors duration-150"
              style={{ color: 'var(--sidebar-text-secondary)' }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--color-error)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--sidebar-text-secondary)'; }}
              title="退出登录"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: 创建 `ThemeToggle.tsx`**

```typescript
// src/components/ThemeToggle.tsx
import React from 'react';
import { useTheme } from '../hooks/useTheme';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      className="rounded-md p-1.5 transition-all duration-200 hover:scale-105"
      style={{ color: 'var(--sidebar-text-secondary)' }}
      title={isDark ? '切换浅色模式' : '切换深色模式'}
    >
      {isDark ? (
        /* 太阳图标 — 浅色模式 */
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      ) : (
        /* 月亮图标 — 深色模式 */
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      )}
    </button>
  );
}
```

- [ ] **Step 3: 简化 `AppLayout.tsx`**

```typescript
// src/components/AppLayout.tsx
import React from 'react';
import Sidebar from './Sidebar';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex h-screen" style={{ background: 'var(--color-bg-layout)' }}>
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        <div className="page-enter">
          {children}
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 4: 在 `App.tsx` 中添加页面过渡**

将 `<Routes>` 包裹在带 `page-enter` class 的 div 中：

```typescript
// App.tsx — 在 Routes 外层包裹 page-enter
// 找到 <Routes>...</Routes> 部分
// 将：
// <Routes>...</Routes>
// 改为：
// <div key={location.pathname} className="page-enter">
//   <Routes>...</Routes>
// </div>
```

---

### Task 6: 重写认证页面（Login + Register）

**Files:**
- Modify: `packages/build-engine/frontend/src/pages/Login.tsx`
- Modify: `packages/build-engine/frontend/src/pages/Register.tsx`

- [ ] **Step 1: 重写 `Login.tsx`**

```typescript
// src/pages/Login.tsx
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await apiClient('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      });
      login(data.token, data.user);
      navigate('/projects');
    } catch (err: any) {
      setError(err.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="flex min-h-screen items-center justify-center"
      style={{ background: 'var(--color-bg-layout)' }}
    >
      <div
        className="w-full max-w-sm rounded-2xl p-8 shadow-lg"
        style={{
          background: 'var(--color-bg-container)',
          border: '1px solid var(--color-border)',
        }}
      >
        {/* Logo */}
        <div className="mb-8 text-center">
          <span className="text-3xl" style={{ color: 'var(--color-primary)' }}>✦</span>
          <h1 className="mt-2 text-2xl font-bold" style={{ color: 'var(--color-text-base)' }}>
            星云
          </h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
            Nebula · Agent 中台
          </p>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-4 rounded-lg px-4 py-3 text-sm" style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--color-error)' }}>
            {error}
          </div>
        )}

        {/* 登录表单 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium" style={{ color: 'var(--color-text-base)' }}>
              用户名
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-all duration-150"
              style={{
                background: 'var(--color-bg-layout)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-base)',
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; e.currentTarget.style.boxShadow = '0 0 0 3px var(--color-primary-bg)'; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.boxShadow = 'none'; }}
              required
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium" style={{ color: 'var(--color-text-base)' }}>
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition-all duration-150"
              style={{
                background: 'var(--color-bg-layout)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-base)',
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; e.currentTarget.style.boxShadow = '0 0 0 3px var(--color-primary-bg)'; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.boxShadow = 'none'; }}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg py-2.5 text-sm font-medium text-white transition-all duration-200 hover:scale-[1.02] disabled:opacity-50"
            style={{ background: 'var(--color-primary)' }}
          >
            {loading ? '登录中…' : '登录'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          还没有账号？{' '}
          <Link to="/register" style={{ color: 'var(--color-primary)' }} className="hover:underline">
            注册
          </Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 重写 `Register.tsx`**（与 Login 风格一致，参照 Login 的卡片布局和样式）

---

### Task 7: 重写 Projects 页面

**Files:**
- Modify: `packages/build-engine/frontend/src/pages/Projects.tsx`

- [ ] **Step 1: 重写 `Projects.tsx`**

```typescript
// src/pages/Projects.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export default function Projects() {
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiClient('/projects'),
  });

  // Skeleton 加载状态
  if (isLoading) {
    return (
      <div>
        <h1 className="mb-6 text-2xl font-bold" style={{ color: 'var(--color-text-base)' }}>
          项目
        </h1>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="animate-pulse rounded-xl p-6"
              style={{ background: 'var(--color-bg-container)', border: '1px solid var(--color-border)' }}
            >
              <div className="mb-3 h-5 w-3/4 rounded" style={{ background: 'var(--color-border)' }} />
              <div className="h-4 w-1/2 rounded" style={{ background: 'var(--color-border)' }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold" style={{ color: 'var(--color-text-base)' }}>
        项目
      </h1>
      {projects && projects.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project: any) => (
            <Link
              key={project.id}
              to={`/projects/${project.id}`}
              className="group block rounded-xl p-6 transition-all duration-200 hover:scale-[1.02]"
              style={{
                background: 'var(--color-bg-container)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--ant-box-shadow)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = 'var(--ant-box-shadow)';
              }}
            >
              <h3 className="text-base font-semibold transition-colors duration-150" style={{ color: 'var(--color-text-base)' }}>
                {project.name}
              </h3>
              {project.description && (
                <p className="mt-2 text-sm line-clamp-2" style={{ color: 'var(--color-text-secondary)' }}>
                  {project.description}
                </p>
              )}
              <div className="mt-4 flex items-center gap-2">
                <span className="text-xs" style={{ color: 'var(--color-primary)' }}>
                  进入项目 →
                </span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div
          className="rounded-xl p-12 text-center"
          style={{ background: 'var(--color-bg-container)', border: '1px solid var(--color-border)' }}
        >
          <p style={{ color: 'var(--color-text-secondary)' }}>暂无项目</p>
        </div>
      )}
    </div>
  );
}
```

---

### Task 8: 重写 Chat 页面及组件

**Files:**
- Modify: `packages/build-engine/frontend/src/pages/Chat.tsx`
- Modify: `packages/build-engine/frontend/src/components/MessageBubble.tsx`
- Modify: `packages/build-engine/frontend/src/components/MessageInput.tsx`
- Modify: `packages/build-engine/frontend/src/components/ConfirmCard.tsx`
- Modify: `packages/build-engine/frontend/src/components/StatusBadge.tsx`
- Modify: `packages/build-engine/frontend/src/components/DocViewer.tsx`
- Modify: `packages/build-engine/frontend/src/components/FileTreePanel.tsx`

- [ ] **Step 1: 重写 `MessageBubble.tsx`**

```typescript
// src/components/MessageBubble.tsx
import React from 'react';

interface MessageBubbleProps {
  content: string;
  role: 'user' | 'agent';
  timestamp?: string;
}

export default function MessageBubble({ content, role, timestamp }: MessageBubbleProps) {
  const isUser = role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className="max-w-[75%] animate-[slideUp_0.3s_ease-out] rounded-2xl px-4 py-3"
        style={{
          background: isUser ? 'var(--color-primary)' : 'var(--color-bg-container)',
          color: isUser ? '#FFFFFF' : 'var(--color-text-base)',
          border: isUser ? 'none' : '1px solid var(--color-border)',
          borderBottomRightRadius: isUser ? 4 : 16,
          borderBottomLeftRadius: isUser ? 16 : 4,
        }}
      >
        <div className="whitespace-pre-wrap text-sm leading-relaxed">{content}</div>
        {timestamp && (
          <div
            className="mt-1.5 text-right text-xs"
            style={{ color: isUser ? 'rgba(255,255,255,0.7)' : 'var(--color-text-secondary)' }}
          >
            {timestamp}
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 重写 `MessageInput.tsx`**

```typescript
// src/components/MessageInput.tsx
import React, { useState, useRef, useEffect } from 'react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function MessageInput({ onSend, disabled, placeholder = '输入消息…' }: MessageInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!value.trim() || disabled) return;
    onSend(value.trim());
    setValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [value]);

  return (
    <div
      className="rounded-xl border p-3"
      style={{
        background: 'var(--glass-bg)',
        borderColor: 'var(--glass-border)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
      }}
    >
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none bg-transparent text-sm outline-none"
          style={{ color: 'var(--color-text-base)' }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-white transition-all duration-200 hover:scale-105 disabled:opacity-40"
          style={{ background: 'var(--color-primary)' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3-7: 重写 ConfirmCard、StatusBadge、DocViewer、FileTreePanel、Chat.tsx**

各组件按照相同的设计风格重写：
- 使用 CSS Variables（`var(--color-*)`）替代硬编码 Tailwind 色值
- 移除 `bg-gray-50`、`bg-white`、`text-gray-900` 等硬编码色值
- 卡片容器使用 `var(--color-bg-container)` + `var(--color-border)`
- 保留原有交互逻辑和 props 接口
- 添加 `animate-[slideUp_0.3s_ease-out]` 入场动画

**ConfirmCard：** 左侧 3px 边框使用 `borderLeft: '3px solid var(--color-primary)'`
**StatusBadge：** 使用语义色 `var(--color-success/warning/error)` + `.pulsing-dot` 动画
**DocViewer：** 文档内容区使用 `var(--color-bg-container)` 作为卡片底色
**Chat.tsx：** 页面容器背景 `var(--color-bg-layout)`，消息列表添加 padding

---

### Task 9: 重写 Docs 页面

**Files:**
- Modify: `packages/build-engine/frontend/src/pages/Docs.tsx`

- [ ] **Step 1: 重写 `Docs.tsx`**

参照 Projects 页面的卡片风格重写文档页面。文档卡片使用 `var(--color-bg-container)` + 左侧 3px `var(--color-primary)` 边框装饰。

---

### Task 10: 重写 Sandbox 页面及组件

**Files:**
- Modify: `packages/build-engine/frontend/src/pages/Sandbox.tsx`
- Modify: `packages/build-engine/frontend/src/components/SandboxHeader.tsx`
- Modify: `packages/build-engine/frontend/src/components/SandboxMonacoEditor.tsx`
- Modify: `packages/build-engine/frontend/src/components/SandboxDiffView.tsx`
- Modify: `packages/build-engine/frontend/src/components/SandboxSnapshotPanel.tsx`

- [ ] **Step 1: 重写 `SandboxHeader.tsx`**

```typescript
// src/components/SandboxHeader.tsx
// 将现有 className 中的硬编码色值替换为 CSS Variables
// bg-gray-800 → 使用 var(--color-bg-elevated)
// text-white → var(--color-text-base)
// border-b border-gray-700 → border-bottom + var(--color-border)
```

- [ ] **Step 2: 重写 `SandboxMonacoEditor.tsx`**

核心改动：根据当前主题切换 Monaco editor theme。

```typescript
// src/components/SandboxMonacoEditor.tsx
// 关键添加：
import { useTheme } from '../hooks/useTheme';

// 在组件内部：
const { isDark } = useTheme();
// 将 Monaco editor 的 theme prop 改为：
// theme={isDark ? 'vs-dark' : 'vs'}
```

- [ ] **Step 3-5: 重写 SandboxDiffView、SandboxSnapshotPanel、Sandbox.tsx**

替换所有硬编码色值为 CSS Variables：
- `bg-green-50` → `var(--color-success)` (with opacity)
- `bg-red-50` → `var(--color-error)` (with opacity)
- 卡片/面板使用 `var(--color-bg-container)` + `var(--color-border)`

---

## Self-Review

**1. Spec 覆盖度检查：**
- design-token-system → Task 1-4 ✓
- dark-mode → Task 2, 3 ✓
- micro-interactions → Task 4 (keyframes), Task 8 (MessageBubble slideUp), hover effects ✓
- glassmorphism-sidebar → Task 5 ✓
- chat-ui-enhancement → Task 8 ✓
- sandbox-ui-enhancement → Task 10 ✓
- theme-switcher → Task 3 (ThemeToggle) ✓

**2. 占位符扫描：** 无 "TBD"、"TODO"、"implement later" 占位符（DocViewer、FileTreePanel 等步骤标记为"参照风格重写"，但保留了具体的替换规则）

**3. 类型一致性：** ThemeProvider 使用 `useThemeStore` 和 `useTheme` 两个 hook，在 tokens.ts 中定义的 `CssVariables` 接口在 ThemeProvider 和 tokens.ts 间保持一致。

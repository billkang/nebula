// @nebula/build-engine/frontend — ThemeProvider
// 包裹 Ant Design ConfigProvider，管理 Design Token 和 CSS 变量

import React, { useEffect } from 'react';
import { ConfigProvider, theme } from 'antd';
import { useThemeStore, type ThemeMode } from '../hooks/useTheme';
import {
  lightTokens,
  darkTokens,
  cssLightVariables,
  cssDarkVariables,
  type CssVariables,
} from './tokens';

function applyCssVariables(vars: CssVariables) {
  const root = document.documentElement;
  Object.entries(vars).forEach(([key, value]) => {
    root.style.setProperty(key, value);
  });
}

function ThemeProviderInner({ children }: { children: React.ReactNode }) {
  const currentTheme = useThemeStore((s) => s.theme);

  useEffect(() => {
    applyCssVariables(currentTheme === 'dark' ? cssDarkVariables : cssLightVariables);
  }, [currentTheme]);

  return (
    <ConfigProvider
      theme={{
        algorithm:
          currentTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: currentTheme === 'dark' ? darkTokens : lightTokens,
      }}
    >
      {children}
    </ConfigProvider>
  );
}

export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  const initTheme = useThemeStore((s) => s.theme);

  // 首屏初始化
  useEffect(() => {
    document.documentElement.classList.toggle('dark', initTheme === 'dark');
    applyCssVariables(initTheme === 'dark' ? cssDarkVariables : cssLightVariables);
  }, []);

  return <ThemeProviderInner>{children}</ThemeProviderInner>;
}

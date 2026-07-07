// @nebula/build-engine/frontend — Design Tokens
// 基于 Linear App 风格 + 浅蓝色系品牌色
// 色值为草案值，实现时可根据视觉效果调整

import type { ThemeConfig } from 'antd';

// ===== 品牌色板 =====
export const brandColors = {
  primary: '#4A9EFF',
  primaryHover: '#3B8CEE',
  primaryActive: '#2D7AD9',
  primaryBg: '#EDF4FF',
} as const;

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
  boxShadow:
    '0 1px 3px 0 rgba(0,0,0,0.04), 0 1px 2px 0 rgba(0,0,0,0.03)',
  boxShadowSecondary:
    '0 4px 6px -1px rgba(0,0,0,0.06), 0 2px 4px -2px rgba(0,0,0,0.04)',
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
  boxShadow:
    '0 1px 3px 0 rgba(0,0,0,0.3), 0 1px 2px 0 rgba(0,0,0,0.2)',
  boxShadowSecondary:
    '0 4px 6px -1px rgba(0,0,0,0.4), 0 2px 4px -2px rgba(0,0,0,0.3)',
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

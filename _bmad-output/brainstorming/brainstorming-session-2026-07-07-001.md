# Brainstorming Session — 前端 UI 全量优化

- **日期：** 2026-07-07
- **讨论主题：** 星云 (Nebula) 平台前端页面 UI 全量重做
- **Change：** `frontend-ui-optimization`

---

## 关键决策

| # | 决策 | 结论 |
|---|------|------|
| 1 | 变更范围 | 所有前端页面，全量调整 UI 风格 |
| 2 | 交互逻辑 | 本次不改，后续再说 |
| 3 | 移动端适配 | 不做，先只改桌面端 |
| 4 | 暗黑模式 | 一起上 |
| 5 | 动效 | 成本不高的话做复杂些（微交互动画、页面过渡、加载状态） |
| 6 | 设计稿 | 无 Figma 文件，全靠代码实现 |
| 7 | 组件库 | 继续用 Ant Design，仅调整样式和布局 |
| 8 | 风格参考 | Linear App 风格 + Ant Design token 定制 |
| 9 | 品牌色 | 浅蓝色系（待设计阶段推荐具体色值） |
| 10 | 技术栈 | React + Ant Design + Tailwind CSS |

---

## 需求要点

### 视觉风格方向

参考 **Linear App** 的设计语言：
- 极简蓝调，大面积留白
- 毛玻璃卡片（glassmorphism）效果
- 浅蓝渐变作为品牌色
- 干净锋利的排版层级
- 克制用色，强调色聚焦在操作区域

### 暗黑模式

与浅色模式同时实现，基于 Ant Design Design Token 的暗黑主题方案：
- 深色背景（#0d0d0d ~ #1a1a1a 范围）
- 浅蓝强调色在暗色背景下保持可读性
- 语义色（成功/警告/错误）同步适配

### 动效要求

在合理成本范围内尽量丰富：
- 页面切换过渡动画（fade/slide）
- 悬浮/点击微交互（scale、shadow lift）
- 加载 Skeleton 动画
- 列表项 enter/exit 动画

---

## 边界范围（不做）

- ❌ 交互流程/功能逻辑改动
- ❌ 移动端/响应式适配
- ❌ 替换 Ant Design 组件库
- ❌ 后端 API 改动
- ❌ Figma 设计稿产出
- ❌ 用户测试/可用性研究

---

## 后续步骤

1. → **阶段三：SDD 文档生成**
   - Proposal → specs → design → tasks
   - spec-hardener 校审
   - writing-plans 生成实现计划
2. → **Superpowers 门禁检查**
3. → **阶段四：TDD 实现**
4. → **Code Review & 分支结束**

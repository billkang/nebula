# Vitest 测试规范

按需加载。编写测试时阅读相关章节。

> **完整示例代码见 `examples/testing.md`**。

## 概述

使用 Vitest 作为单元测试框架，配合 Testing Library 进行组件测试。

## 文件与命名规范

- 测试文件放在 `__tests__/` 目录下，与被测文件同层级
- 测试文件后缀：`.test.ts` 优先于 `.spec.ts`
- describe/it 描述使用中文，说明被测功能
- 固定 import 写法：

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/angular';
```

## 测试类型

| 测试类型 | 范围 | 工具 | 关键关注点 |
|---------|------|------|-----------|
| 单元测试 | 单个函数/方法 | Vitest | 逻辑正确性、边界条件 |
| 组件测试 | 单个组件 | Testing Library | 渲染、交互、事件 |

## 基本模式

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/angular';
import { ButtonComponent } from './button.component';

describe('ButtonComponent', () => {
  // 初始化
  beforeEach(async () => {
    await render(ButtonComponent, {
      inputs: { label: '提交' },
    });
  });

  // 验证渲染
  it('应该渲染带 label 的按钮', () => {
    expect(screen.getByText('提交')).toBeTruthy();
  });

  // 验证交互
  it('点击按钮时应触发 click 事件', async () => {
    const onClick = vi.fn();
    await render(ButtonComponent, {
      inputs: { onClick },
    });
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
```

## 异步测试

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/angular';

describe('UserProfileComponent', () => {
  it('异步加载用户数据后应显示用户名', async () => {
    // 使用 fake timers 控制异步行为
    vi.useFakeTimers();

    await render(UserProfileComponent, {
      componentProviders: [
        {
          provide: UserService,
          useValue: {
            getUser: () => Promise.resolve({ name: 'Alice' }),
          },
        },
      ],
    });

    // 等待异步操作完成
    vi.runAllTimers();

    expect(await screen.findByText('Alice')).toBeTruthy();

    vi.useRealTimers();
  });
});
```

## Signal 组件测试

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/angular';
import { CounterComponent } from './counter.component';

describe('CounterComponent (Signal)', () => {
  it('点击按钮后计数应增加', async () => {
    await render(CounterComponent);

    const button = screen.getByRole('button', { name: /增加/i });
    expect(screen.getByText('计数: 0')).toBeTruthy();

    fireEvent.click(button);

    // Signal 是同步更新的，不需要额外等待
    expect(screen.getByText('计数: 1')).toBeTruthy();
  });
});
```

## Mock 规范

```typescript
import { vi } from 'vitest';

// 模拟服务
const mockUserService = {
  getUser: vi.fn().mockResolvedValue({ id: 1, name: 'Test' }),
};

// 模拟模块
vi.mock('./user.service', () => ({
  UserService: vi.fn().mockImplementation(() => mockUserService),
}));

// 异步 mock
const mockFetch = vi.fn().mockRejectedValue(new Error('Network error'));
vi.stubGlobal('fetch', mockFetch);
```

## 覆盖率要求

- 语句覆盖率: ≥80%
- 分支覆盖率: ≥75%
- 函数覆盖率: ≥85%
- 行覆盖率: ≥80%

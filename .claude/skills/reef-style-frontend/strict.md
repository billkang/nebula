# TypeScript 严格模式规范

## 概述

启用 TypeScript 严格模式 (`strict: true`)，提供更强的类型安全保障。

## 配置

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": false
  }
}
```

## 核心规则

### strictNullChecks

`null` 和 `undefined` 不可赋值给其他类型：

```typescript
// ❌ 错误
const name: string = null;

// ✅ 正确
const name: string | null = null;
const value = maybeUndefined(); // string | undefined
```

### noUncheckedIndexedAccess

对象索引访问返回 `T | undefined`，不可直接使用：

```typescript
interface Dict {
  [key: string]: string;
}

const dict: Dict = { a: "1" };

// ❌ 错误 — dict["b"] 可能是 undefined
console.log(dict["b"].toString());

// ✅ 正确
const b = dict["b"];
if (b) {
  console.log(b.toString());
}

// 或用可选链
console.log(dict["b"]?.toString());
```

### noImplicitOverride

重写父类方法必须显式标记 `override`：

```typescript
class Base {
  save(): void { /* ... */ }
}

class Derived extends Base {
  // ❌ 错误 — 缺少 override
  save(): void { /* ... */ }

  // ✅ 正确
  override save(): void { /* ... */ }
}
```

## 常见场景

### 数组查找

```typescript
const items: string[] = ["a", "b", "c"];

// ❌ 错误 — find 返回 T | undefined
const item = items.find(x => x === "d");
console.log(item.length);

// ✅ 正确
const item = items.find(x => x === "d");
if (item) {
  console.log(item.length);
}
```

### 对象属性访问

```typescript
interface Config {
  theme?: {
    color?: string;
  };
}

const config: Config = {};

// ❌ 错误 — 深层可选链
const color: string = config.theme.color;

// ✅ 正确
const color = config.theme?.color;
```

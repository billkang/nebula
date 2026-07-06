# 后端编码快速参考 — Python（FastAPI）

按需加载。仅当你需要编写对应组件类型时阅读相关章节。

> 已安装子维度的规范，通过该维度的 `{value}.md` 文件阅读。本页只包含 Python 语言通用的核心规范。
>
> **跨维度规范（适用所有后端代码）：**
> - [API 规范](api-spec.md) — RESTful 命名、统一响应体、OpenAPI、版本策略
> - [依赖管理规范](dependency-management.md) — pyproject.toml、版本声明、CVE
> - [异常处理深度规范](exception-handling.md) — AppError 层次、错误码、全局处理
> - [安全红线](security-redlines.md) — P0/P1 安全规则（必须遵守）

## 推荐项目结构

```
app/
├── api/v1/           # FastAPI routers（按领域分组）
├── core/             # 配置、中间件、全局依赖
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic request/response schemas
├── services/         # 业务逻辑层
├── migrations/       # Alembic migration files
├── tasks/            # 后台任务（Celery/ARQ）
└── tests/            # pytest tests
    ├── unit/         # 纯逻辑测试
    └── integration/  # 集成测试（DB/API）
```

## 速查

| 场景 | 决策 |
| --- | --- |
| 字符串格式化 | 用 f-string（`f"Hello {name}"`），不用 `％` 或 `.format()` |
| 类型分发 | 用多态 / Protocol，不用 `isinstance()` 链 |
| 类型注释 | 都标注返回类型和参数类型（mypy 检查通过） |
| 参数顺序 | 路由可见参数 → body → query → dependency |
| 模块名 | snake_case，禁止驼峰 |
| 弃用 API | mypy / ruff 警告中的废弃 API 在同一次 PR 中替换为新 API |
| 类命名 | PascalCase（如 `UserService`、`CreateUserRequest`） |
| 函数/变量命名 | snake_case（如 `get_user()`、`user_service`） |
| 常量命名 | UPPER_SNAKE_CASE（如 `MAX_RETRY_COUNT`） |

## 代码风格

### 通用约定

- 变量命名有意义，禁止单字母（循环计数器 `i`/`j`/`k` 除外）
- 优先用类型别名 / Protocol 而不是裸字典或 `Any`
- f-string 替代 `％` 格式化或 `.format()`
- 用枚举（`StrEnum`）替代魔法字符串常量
- 用 `is` / `is not` 比较 `None`，不用 `== None`
- ruff 规则 `F`(Pyflakes) + `E`(pycodestyle) + `I`(isort) + `N`(pep8-naming) 全部通过
- 100 列折行（black 默认），运算符放行首

### Capability 模式

当实体层次需要按子类暴露能力时，在基类中用 `ABC.abstractmethod` 声明，各子类按需实现：

```python
from abc import ABC, abstractmethod

class FormControl(ABC):
    @abstractmethod
    def supports_importing(self) -> bool: ...

class TextControl(FormControl):
    def supports_importing(self) -> bool: return True

class NumberControl(FormControl):
    def supports_importing(self) -> bool: return False
```

**适用场景：** 基类有多个子类，且某个操作只在部分子类上有意义。
**替代方案：** 用 `isinstance()` 判断 → ✗ 不推荐，违反开闭原则。
**优势：** 开闭原则 — 新增子类只需在自己的类中覆盖方法；新增能力只需在基类加方法 + 各子类实现。

## 类型注释规则

| 声明位置 | 需要类型注释 |
|---------|-------------|
| 函数参数 | ✓ 是 |
| 函数返回值 | ✓ 是（`-> None` 也必须标注） |
| 模块级变量 | ✓ 是 |
| 类属性 / Pydantic Field | ✓ 是 |
| 循环变量 / 列表推导 | ✗ 否 |

## 错误处理模式

```python
# ✅ 好：统一异常 + 全局 handler
from fastapi import HTTPException

class AppError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        super().__init__(status_code=status_code, detail=message)

# ✅ 好：Service 层抛自定义业务异常
class UserNotFoundError(AppError):
    def __init__(self, user_id: int):
        super().__init__(code="USER_NOT_FOUND", message=f"User {user_id} not found", status_code=404)
```

## 常见坑

| 场景 | 问题 | 正确做法 |
|------|------|---------|
| `isinstance()` 分发 | Service 层用 `isinstance()` 链判断所有子类型 | 优先在基类中用抽象方法 / Protocol |
| 裸 `async` 阻塞 | `async` 函数内调了同步 IO 操作 | 用 `httpx.AsyncClient`、`asyncio.to_thread`、异步 ORM |
| N+1 查询 | 循环内访问关联对象的属性，逐条 SELECT | 用 `selectinload()` / `joinedload()` 主动预加载 |
| 类型不兼容 | mypy strict 模式通不过 | 所有函数标注类型，`None` 必须显式声明 |

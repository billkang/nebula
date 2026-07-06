# 依赖管理规范（Python）

## 速查

| 场景 | 决策 |
| --- | --- |
| 包管理器 | `uv`（统一管理和运行） |
| 声明依赖 | `uv add {package}` 或直接在 `pyproject.toml` 中声明 |
| 版本声明 | 在 `pyproject.toml` 中指定主版本范围：`>=1.0,<2.0` |
| 禁止通配符版本 | 禁止 `*` 或 `>=0.0.0` |
| 禁止硬编码 | 禁止 `pip install package==1.0.0`（不可复现） |
| 依赖分组 | `[project.dependencies]`（运行）+ `[project.optional-dependencies]`（dev） |
| 锁定文件 | `uv.lock` — 提交到 Git |
| CVE 检查 | `uv audit` 扫描已知漏洞 |
| 版本升级 | 手动升级后运行 `uv lock` 更新锁定文件 |

## 核心规范

### pyproject.toml 结构

```toml
[project]
name = "my-app"
version = "0.1.0"
requires-python = ">=3.10"

dependencies = [
    "fastapi>=0.115.0,<1.0.0",
    "sqlalchemy>=2.0,<3.0",
    "alembic>=1.14,<2.0",
    "pydantic>=2.10,<3.0",
    "pydantic-settings>=2.7,<3.0",
    "httpx>=0.28,<1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9.0",
    "pytest-asyncio>=0.24,<1.0",
    "ruff>=0.8,<1.0",
    "mypy>=1.13,<2.0",
    "httpx>=0.28,<1.0",
]

[tool.ruff]
# ruff 配置...

[tool.mypy]
# mypy 配置...
```

**规范：**
- 运行依赖在 `[project.dependencies]` 中声明
- 开发/测试依赖在 `[project.optional-dependencies]` 中分组
- 每组使用语义化版本范围：`>=min,<max`
- 同一生态的库保持版本一致（如 FastAPI + Pydantic 需兼容）

### 禁止通配符版本

```toml
# ❌ 坏：通配符或不限版本
dependencies = [
    "fastapi=*",
    "sqlalchemy>=0.0.0",
]

# ✅ 好：限制主版本范围
dependencies = [
    "fastapi>=0.115.0,<1.0.0",
    "sqlalchemy>=2.0,<3.0",
]
```

### uv 命令速查

```bash
# 添加依赖
uv add fastapi

# 添加开发依赖
uv add --dev pytest pytest-asyncio

# 移除依赖
uv remove fastapi

# 更新锁文件（升级所有兼容版本）
uv lock

# 升级特定包
uv lock --upgrade-package fastapi

# 安全审计
uv audit

# 查看依赖树
uv tree
```

```bash
# ❌ 坏：直接 pip install（绕过 uv.lock）
pip install fastapi==0.115.0

# ✅ 好：用 uv 管理所有依赖
uv add fastapi
```

### 版本升级规则

| 升级类型 | 操作 | 验证 |
|---------|------|------|
| Major 升级 | 手动升级，独立 PR | 需检查 breaking changes + API 兼容性 |
| Minor 升级 | `uv lock --upgrade-package {pkg}` | 运行完整测试套件 |
| Patch 升级 | `uv lock --upgrade-package {pkg}` | 运行测试 + lint |

### 安全审计

```bash
# 扫描 CVE
uv audit

# 输出示例：
# Found 2 vulnerabilities:
# - urllib3<2.2.3 (CVE-2024-37891, medium)
# - requests<2.32.0 (CVE-2024-35195, medium)
```

**规范：**
- 每次 CI 中运行 `uv audit`
- 紧急 CVE（CVSS >= 7.0）：1 天内升级并验证
- 无法立即升级时，加备注和缓解措施文档

### 已知 CVE 常见的 Python 包

| 包 | 受影响版本 | 最低安全版本 |
|---|----------|------------|
| urllib3 | < 2.2.3 | >= 2.2.3 |
| requests | < 2.32.0 | >= 2.32.0 |
| Jinja2 | < 3.1.5 | >= 3.1.5 |
| cryptography | < 43.0.1 | >= 43.0.1 |

# ruff + mypy 工具链规范

## ruff 配置（pyproject.toml）

```toml
[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = [
    "F",   # Pyflakes — 检测未使用导入、未定义变量等
    "E",   # pycodestyle — PEP 8 风格错误
    "W",   # pycodestyle — 警告
    "I",   # isort — 导入排序
    "N",   # pep8-naming — 命名规范
    "UP",  # pyupgrade — 新版语法建议
    "B",   # flake8-bugbear — 常见 bug 模式
]
ignore = [
    "E501",  # 行长度交给 black，不在 ruff 中检查
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["N"]  # 测试文件放宽命名规范

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"
```

**规范：**
- ruff 负责 lint（`ruff check`）和 format（`ruff format`）双重职责
- 启用 `F` + `E` + `W` + `I` + `N` + `UP` + `B` 规则组
- 行长度检查（`E501`）交给 black / ruff format，不在 lint 中重复

## mypy 配置（pyproject.toml）

```toml
[tool.mypy]
strict = true
python_version = "3.10"
check_untyped_defs = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_return_any = true
no_implicit_optional = true
disallow_any_unimported = true
disallow_untyped_defs = true
disallow_untyped_calls = true

[[tool.mypy.overrides]]
module = [
    "tests.*",
]
ignore_missing_imports = true
disallow_untyped_defs = false
```

**规范：**
- 生产代码使用 `strict = true`
- 所有函数必须有类型注释
- 测试文件放宽类型要求

## 常用命令

```bash
# 快速 lint
ruff check .

# 自动修复
ruff check --fix .

# 格式化
ruff format

# 类型检查
mypy .

# 完整检查（推荐 CI 用）
ruff check . && ruff format --check && mypy .
```

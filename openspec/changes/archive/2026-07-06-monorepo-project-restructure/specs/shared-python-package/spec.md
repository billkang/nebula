## 新增需求

### 需求：存在 nebula-shared Python 共享包
系统 SHALL 在 `packages/shared-python/` 下提供一个名为 `nebula-shared` 的 Python 共享包（导入名为 `nebula_shared`）。

#### 场景：包可被导入
- **WHEN** 在 `packages/shared-python/` 下执行 `uv run python -c "import nebula_shared"`
- **THEN** 导入成功，无错误

### 需求：包使用 src layout
`nebula-shared` 包 SHALL 使用 src layout，初始目录结构如下：

```
packages/shared-python/
  ├── pyproject.toml
  ├── README.md
  └── src/
      └── nebula_shared/
          ├── __init__.py
          ├── models/
          │   ├── __init__.py
          │   └── common.py
          ├── config/
          │   ├── __init__.py
          │   └── base.py
          └── utils/
              ├── __init__.py
              └── helpers.py
```

#### 场景：包目录结构正确
- **WHEN** 列出 `packages/shared-python/src/nebula_shared/`
- **THEN** `__init__.py`、`models/`、`config/`、`utils/` 子目录均存在
- **AND** 所有子目录包含 `__init__.py`

### 需求：workspace 消费者可引用 nebula-shared
`build-engine/backend` 和 `runtime-engine` SHALL 通过 uv workspace 依赖能够导入 `nebula_shared`。

#### 场景：后端可导入共享包
- **WHEN** 从 `packages/build-engine/backend/` 执行 `uv run python -c "from nebula_shared.config.base import BaseConfig"`
- **THEN** 导入成功

#### 场景：运行时可导入共享包
- **WHEN** 从 `packages/runtime-engine/` 执行相同命令
- **THEN** 导入成功

### 需求：初始内容提供结构骨架
`nebula-shared` 初始版本 SHALL 包含：
- `BaseConfig` 类，展示 pydantic-settings 的配置模式
- 工具函数占位（例如类型别名、通用枚举）
- 模型基类示例

#### 场景：BaseConfig 可访问
- **WHEN** 导入 `nebula_shared.config.base.BaseConfig`
- **THEN** 它是一个 `pydantic_settings.BaseSettings` 的子类

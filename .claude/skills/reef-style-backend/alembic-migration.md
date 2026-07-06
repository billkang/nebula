# Alembic 迁移实践

## 初始化

```bash
# 初始化 Alembic
alembic init -t async migrations

# 配置 async 引擎（migrations/env.py 中）
# target_metadata = Base.metadata
```

## 创建迁移

```bash
# ✅ 自动生成迁移（推荐）
alembic revision --autogenerate -m "add user table"

# ⚠️ 检查自动生成的内容是否正确后再提交
# 自动生成不能 100% 检测到所有变更（如列重命名）

# ✅ 手动创建空迁移（特殊场景）
alembic revision -m "migrate data"
```

## 应用迁移

```bash
# 升级到最新
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 查看历史
alembic history

# 查看当前版本
alembic current
```

## 迁移文件规范

```python
"""add user table

Revision ID: abc123
Revises: 
Create Date: 2026-06-25 10:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "abc123"
down_revision = None

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

def downgrade() -> None:
    op.drop_table("users")
```

**规范：**
- 每个迁移文件只做**一件事**（一个表或一个字段变更）
- `upgrade()` 和 `downgrade()` 必须互逆
- `down_revision` 必须正确指向前一个迁移
- **禁止**在生产环境直接执行未经 review 的自动生成迁移

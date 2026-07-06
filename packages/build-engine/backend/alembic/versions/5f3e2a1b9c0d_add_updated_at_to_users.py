"""add updated_at column to users

Revision ID: 5f3e2a1b9c0d
Revises: 626483d1da5c
Create Date: 2026-07-06 14:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f3e2a1b9c0d'
down_revision: Union[str, Sequence[str], None] = '626483d1da5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'updated_at')

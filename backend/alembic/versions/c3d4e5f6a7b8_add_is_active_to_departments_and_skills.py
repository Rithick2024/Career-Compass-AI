"""add is_active and timestamps to departments and skills

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-22 22:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_active, created_at, updated_at to departments table
    op.add_column('departments', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('departments', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('departments', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))

    # Add is_active to skills table
    op.add_column('skills', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    op.drop_column('skills', 'is_active')
    op.drop_column('departments', 'updated_at')
    op.drop_column('departments', 'created_at')
    op.drop_column('departments', 'is_active')

"""add evidence fields to improvement_plan_actions table

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-10-12 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'improvement_plan_actions',
        sa.Column('evidence_source', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'improvement_plan_actions',
        sa.Column('evidence_reference', sa.String(length=500), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('improvement_plan_actions', 'evidence_reference')
    op.drop_column('improvement_plan_actions', 'evidence_source')

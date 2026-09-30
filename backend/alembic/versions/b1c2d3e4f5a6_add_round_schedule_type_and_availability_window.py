"""add round schedule_type and availability_window

Revision ID: b1c2d3e4f5a6
Revises: 9a8b7c6d5e4f
Create Date: 2026-09-30 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '9a8b7c6d5e4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create schedule_type_enum
    schedule_type_enum = postgresql.ENUM('FIXED_TIME', 'AVAILABILITY_WINDOW', name='schedule_type_enum')
    schedule_type_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add columns to application_rounds
    op.add_column(
        'application_rounds',
        sa.Column(
            'schedule_type',
            sa.Enum('FIXED_TIME', 'AVAILABILITY_WINDOW', name='schedule_type_enum'),
            nullable=False,
            server_default='FIXED_TIME',
        ),
    )
    op.add_column('application_rounds', sa.Column('available_from', sa.DateTime(timezone=True), nullable=True))
    op.add_column('application_rounds', sa.Column('available_until', sa.DateTime(timezone=True), nullable=True))

    # 3. Data migration: copy existing scheduled_at to available_from
    op.execute("UPDATE application_rounds SET available_from = scheduled_at WHERE scheduled_at IS NOT NULL")

    # 4. Drop legacy scheduled_at column
    op.drop_column('application_rounds', 'scheduled_at')


def downgrade() -> None:
    op.add_column('application_rounds', sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE application_rounds SET scheduled_at = available_from WHERE available_from IS NOT NULL")

    op.drop_column('application_rounds', 'available_until')
    op.drop_column('application_rounds', 'available_from')
    op.drop_column('application_rounds', 'schedule_type')

    op.execute("DROP TYPE IF EXISTS schedule_type_enum")

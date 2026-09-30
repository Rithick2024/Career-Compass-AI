"""create job_rounds table and update application_rounds with template fields

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-09-30 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing postgresql enum references
    round_type_enum = postgresql.ENUM(
        'ONLINE_ASSESSMENT', 'CODING_TEST', 'TECHNICAL_INTERVIEW', 'HR_INTERVIEW', 'GROUP_DISCUSSION', 'OTHER',
        name='round_type',
        create_type=False
    )
    schedule_type_enum = postgresql.ENUM(
        'FIXED_TIME', 'AVAILABILITY_WINDOW',
        name='schedule_type_enum',
        create_type=False
    )

    # 1. Create job_rounds table
    op.create_table(
        'job_rounds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('round_type', round_type_enum, nullable=False),
        sa.Column('title', sa.String(length=150), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('schedule_type', schedule_type_enum, nullable=False, server_default='FIXED_TIME'),
        sa.Column('available_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('available_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('meeting_link', sa.String(length=500), nullable=True),
        sa.Column('test_link', sa.String(length=500), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', 'round_number', name='uq_job_rounds_job_id_round_number')
    )
    op.create_index(op.f('ix_job_rounds_job_id'), 'job_rounds', ['job_id'], unique=False)

    # 2. Add columns to application_rounds
    op.add_column('application_rounds', sa.Column('job_round_id', sa.Integer(), nullable=True))
    op.add_column('application_rounds', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('application_rounds', sa.Column('meeting_link', sa.String(length=500), nullable=True))
    op.add_column('application_rounds', sa.Column('test_link', sa.String(length=500), nullable=True))
    op.add_column('application_rounds', sa.Column('instructions', sa.Text(), nullable=True))

    op.create_foreign_key(
        'fk_application_rounds_job_round_id',
        'application_rounds', 'job_rounds',
        ['job_round_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index(op.f('ix_application_rounds_job_round_id'), 'application_rounds', ['job_round_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_application_rounds_job_round_id'), table_name='application_rounds')
    op.drop_constraint('fk_application_rounds_job_round_id', 'application_rounds', type_='foreignkey')
    op.drop_column('application_rounds', 'instructions')
    op.drop_column('application_rounds', 'test_link')
    op.drop_column('application_rounds', 'meeting_link')
    op.drop_column('application_rounds', 'description')
    op.drop_column('application_rounds', 'job_round_id')

    op.drop_index(op.f('ix_job_rounds_job_id'), table_name='job_rounds')
    op.drop_table('job_rounds')

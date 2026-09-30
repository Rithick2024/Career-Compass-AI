"""enhance recruitment workflow

Revision ID: 9a8b7c6d5e4f
Revises: 81798731b236
Create Date: 2026-09-30 13:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9a8b7c6d5e4f'
down_revision: Union[str, None] = '81798731b236'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns to jobs
    op.add_column('jobs', sa.Column('application_start_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('jobs', sa.Column('work_mode', sa.String(length=50), nullable=True))
    op.add_column('jobs', sa.Column('instructions', sa.Text(), nullable=True))

    # 2. Create Enum types for PostgreSQL
    student_attendance_enum = postgresql.ENUM('NOT_REPORTED', 'ATTENDED', 'ABSENT', name='student_attendance_enum')
    student_attendance_enum.create(op.get_bind(), checkfirst=True)

    staff_verification_enum = postgresql.ENUM('PENDING', 'VERIFIED', 'REJECTED', name='staff_verification_enum')
    staff_verification_enum.create(op.get_bind(), checkfirst=True)

    # 3. Add columns to application_rounds
    op.add_column('application_rounds', sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='60'))
    op.add_column(
        'application_rounds',
        sa.Column(
            'student_attendance',
            sa.Enum('NOT_REPORTED', 'ATTENDED', 'ABSENT', name='student_attendance_enum'),
            nullable=False,
            server_default='NOT_REPORTED',
        ),
    )
    op.add_column('application_rounds', sa.Column('student_action_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        'application_rounds',
        sa.Column(
            'staff_verification',
            sa.Enum('PENDING', 'VERIFIED', 'REJECTED', name='staff_verification_enum'),
            nullable=False,
            server_default='PENDING',
        ),
    )
    op.add_column('application_rounds', sa.Column('staff_verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('application_rounds', sa.Column('staff_verified_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('application_rounds', sa.Column('rescheduled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('application_rounds', sa.Column('reschedule_reason', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('application_rounds', 'reschedule_reason')
    op.drop_column('application_rounds', 'rescheduled_at')
    op.drop_constraint('fk_application_rounds_staff_verified_by_id_users', 'application_rounds', type_='foreignkey')
    op.drop_column('application_rounds', 'staff_verified_by_id')
    op.drop_column('application_rounds', 'staff_verified_at')
    op.drop_column('application_rounds', 'staff_verification')
    op.drop_column('application_rounds', 'student_action_at')
    op.drop_column('application_rounds', 'student_attendance')
    op.drop_column('application_rounds', 'duration_minutes')

    op.execute('DROP TYPE IF EXISTS staff_verification_enum')
    op.execute('DROP TYPE IF EXISTS student_attendance_enum')

    op.drop_column('jobs', 'instructions')
    op.drop_column('jobs', 'work_mode')
    op.drop_column('jobs', 'application_start_at')

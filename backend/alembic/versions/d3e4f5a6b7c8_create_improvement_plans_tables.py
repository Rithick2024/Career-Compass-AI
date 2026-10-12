"""create improvement_plans and improvement_plan_actions tables

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-10-12 19:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create improvement_plans table
    op.create_table(
        'improvement_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'job_id', name='uq_improvement_plans_student_job')
    )
    op.create_index(op.f('ix_improvement_plans_job_id'), 'improvement_plans', ['job_id'], unique=False)
    op.create_index(op.f('ix_improvement_plans_student_id'), 'improvement_plans', ['student_id'], unique=False)

    # 2. Create improvement_plan_actions table
    op.create_table(
        'improvement_plan_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=True),
        sa.Column('skill_name', sa.String(length=100), nullable=False),
        sa.Column('current_proficiency', sa.String(length=50), nullable=True),
        sa.Column('target_proficiency', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), server_default='MEDIUM', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='PENDING', nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=False),
        sa.Column('suggested_activity', sa.Text(), nullable=False),
        sa.Column('completion_criteria', sa.String(length=500), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['improvement_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_improvement_plan_actions_plan_id'), 'improvement_plan_actions', ['plan_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_improvement_plan_actions_plan_id'), table_name='improvement_plan_actions')
    op.drop_table('improvement_plan_actions')
    op.drop_index(op.f('ix_improvement_plans_student_id'), table_name='improvement_plans')
    op.drop_index(op.f('ix_improvement_plans_job_id'), table_name='improvement_plans')
    op.drop_table('improvement_plans')

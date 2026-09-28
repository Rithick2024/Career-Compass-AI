"""create jobs, job_required_skills, and job_eligible_departments tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-28 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('role_category', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=150), nullable=True),
        sa.Column('employment_type', sa.String(length=50), server_default='Full-time', nullable=False),
        sa.Column('ctc_lpa', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('min_cgpa', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_company_id'), 'jobs', ['company_id'], unique=False)
    op.create_index(op.f('ix_jobs_deadline'), 'jobs', ['deadline'], unique=False)
    op.create_index(op.f('ix_jobs_is_active'), 'jobs', ['is_active'], unique=False)

    # 2. Create job_required_skills table
    proficiency_enum = postgresql.ENUM('beginner', 'intermediate', 'advanced', name='proficiency_level', create_type=False)

    op.create_table(
        'job_required_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('min_proficiency', proficiency_enum, nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', 'skill_id', name='uq_job_required_skills_job_id_skill_id')
    )
    op.create_index(op.f('ix_job_required_skills_job_id'), 'job_required_skills', ['job_id'], unique=False)
    op.create_index(op.f('ix_job_required_skills_skill_id'), 'job_required_skills', ['skill_id'], unique=False)

    # 3. Create job_eligible_departments table
    op.create_table(
        'job_eligible_departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', 'department_id', name='uq_job_eligible_departments_job_id_department_id')
    )
    op.create_index(op.f('ix_job_eligible_departments_department_id'), 'job_eligible_departments', ['department_id'], unique=False)
    op.create_index(op.f('ix_job_eligible_departments_job_id'), 'job_eligible_departments', ['job_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_job_eligible_departments_job_id'), table_name='job_eligible_departments')
    op.drop_index(op.f('ix_job_eligible_departments_department_id'), table_name='job_eligible_departments')
    op.drop_table('job_eligible_departments')

    op.drop_index(op.f('ix_job_required_skills_skill_id'), table_name='job_required_skills')
    op.drop_index(op.f('ix_job_required_skills_job_id'), table_name='job_required_skills')
    op.drop_table('job_required_skills')

    op.drop_index(op.f('ix_jobs_is_active'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_deadline'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_company_id'), table_name='jobs')
    op.drop_table('jobs')

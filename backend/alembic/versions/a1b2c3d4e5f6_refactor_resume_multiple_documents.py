"""refactor resume multiple documents

Revision ID: a1b2c3d4e5f6
Revises: 995c78159606
Create Date: 2026-09-22 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '995c78159606'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop old unique index on student_id and recreate as non-unique
    op.drop_index('ix_resumes_student_id', table_name='resumes')
    op.create_index('ix_resumes_student_id', 'resumes', ['student_id'], unique=False)

    # Clean up legacy rows with no uploaded file
    op.execute("DELETE FROM resumes WHERE file_name IS NULL")

    # 2. Add title, description, is_default columns
    op.add_column('resumes', sa.Column('title', sa.String(length=100), nullable=True))
    op.add_column('resumes', sa.Column('description', sa.String(length=500), nullable=True))
    op.add_column('resumes', sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False))

    # Set default title for existing rows and enforce non-nullable
    op.execute("UPDATE resumes SET title = 'General Resume' WHERE title IS NULL")
    op.alter_column('resumes', 'title', nullable=False)

    # Set existing remaining resumes to is_default = true
    op.execute("UPDATE resumes SET is_default = true")

    # Enforce non-nullable file metadata
    op.alter_column('resumes', 'file_name', nullable=False)
    op.alter_column('resumes', 'file_path', nullable=False)
    op.alter_column('resumes', 'file_type', nullable=False)
    op.alter_column('resumes', 'file_size', nullable=False)

    # Drop old professional_summary and career_objective columns
    op.drop_column('resumes', 'professional_summary')
    op.drop_column('resumes', 'career_objective')

    # Create partial unique index for default resume per student
    op.create_index(
        'idx_student_default_resume',
        'resumes',
        ['student_id'],
        unique=True,
        postgresql_where=sa.text('is_default = true')
    )


def downgrade() -> None:
    op.drop_index('idx_student_default_resume', table_name='resumes')

    op.add_column('resumes', sa.Column('professional_summary', sa.String(length=2000), nullable=True))
    op.add_column('resumes', sa.Column('career_objective', sa.String(length=1000), nullable=True))

    op.alter_column('resumes', 'file_name', nullable=True)
    op.alter_column('resumes', 'file_path', nullable=True)
    op.alter_column('resumes', 'file_type', nullable=True)
    op.alter_column('resumes', 'file_size', nullable=True)

    op.drop_column('resumes', 'is_default')
    op.drop_column('resumes', 'description')
    op.drop_column('resumes', 'title')

    op.drop_index('ix_resumes_student_id', table_name='resumes')
    op.create_index('ix_resumes_student_id', 'resumes', ['student_id'], unique=True)

"""rename admin role to staff

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-22 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely rename PostgreSQL enum value 'admin' -> 'staff'
    op.execute("ALTER TYPE user_role RENAME VALUE 'admin' TO 'staff'")


def downgrade() -> None:
    # Revert 'staff' -> 'admin'
    op.execute("ALTER TYPE user_role RENAME VALUE 'staff' TO 'admin'")

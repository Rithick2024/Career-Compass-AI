"""remove expert proficiency level

Corrective migration: the frontend contract only defines three
proficiency levels (Beginner/Intermediate/Advanced) — the `expert`
value added in `70466c0ad0bf` doesn't exist in the actual UI. Since
`70466c0ad0bf` is already applied elsewhere, it is not rewritten here;
this migration corrects the enum on top of it instead.

PostgreSQL has no `ALTER TYPE ... DROP VALUE` — an enum value can only
be removed by recreating the type without it. The standard-safe
recipe used below:

  1. Remap any existing `expert` rows to `advanced` (the closest
     remaining level) — required so the data still fits the narrower
     type in step 3. This is a one-way, lossy step: a downgrade
     recreates the four-value type, but cannot tell which `advanced`
     rows used to say `expert`. Acceptable here since this project has
     no production data yet, but called out explicitly rather than
     left implicit.
  2. Create a new enum type with only the three allowed values.
  3. Alter `student_skills.proficiency` to the new type (via a
     text cast, since PostgreSQL can't directly cast one enum type to
     another).
  4. Drop the old (four-value) enum type and rename the new one to
     the original name, so the type name `proficiency_level` and
     everything referencing it (the SQLAlchemy model, autogenerate
     metadata) is unaffected.

Revision ID: 38f0da1163aa
Revises: 70466c0ad0bf
Create Date: 2026-08-26 05:25:06.885901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38f0da1163aa'
down_revision: Union[str, None] = '70466c0ad0bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_ENUM_VALUES = ("beginner", "intermediate", "advanced", "expert")
_NEW_ENUM_VALUES = ("beginner", "intermediate", "advanced")
_ENUM_NAME = "proficiency_level"
_TEMP_ENUM_NAME = "proficiency_level_new"


def upgrade() -> None:
    # Step 1: remap any existing 'expert' rows before narrowing the
    # type — the old (four-value) type is still active here, so this
    # UPDATE is valid.
    op.execute("UPDATE student_skills SET proficiency = 'advanced' WHERE proficiency = 'expert'")

    # Step 2: create the narrower type under a temporary name.
    new_enum = sa.Enum(*_NEW_ENUM_VALUES, name=_TEMP_ENUM_NAME)
    new_enum.create(op.get_bind(), checkfirst=False)

    # Step 3: move the column to the new type via a text cast.
    op.execute(
        f"ALTER TABLE student_skills "
        f"ALTER COLUMN proficiency TYPE {_TEMP_ENUM_NAME} "
        f"USING proficiency::text::{_TEMP_ENUM_NAME}"
    )

    # Step 4: drop the old type, rename the new one into its place.
    op.execute(f"DROP TYPE {_ENUM_NAME}")
    op.execute(f"ALTER TYPE {_TEMP_ENUM_NAME} RENAME TO {_ENUM_NAME}")


def downgrade() -> None:
    # Reverse of upgrade(): recreate the four-value type, move the
    # column back to it, drop the three-value type. Note this does
    # NOT restore which rows were originally 'expert' before the
    # upgrade's remap — that information is gone (see module
    # docstring). Every row that was 'advanced' stays 'advanced'.
    old_enum = sa.Enum(*_OLD_ENUM_VALUES, name=_TEMP_ENUM_NAME)
    old_enum.create(op.get_bind(), checkfirst=False)

    op.execute(
        f"ALTER TABLE student_skills "
        f"ALTER COLUMN proficiency TYPE {_TEMP_ENUM_NAME} "
        f"USING proficiency::text::{_TEMP_ENUM_NAME}"
    )

    op.execute(f"DROP TYPE {_ENUM_NAME}")
    op.execute(f"ALTER TYPE {_TEMP_ENUM_NAME} RENAME TO {_ENUM_NAME}")

"""
Single import point for Alembic's autogenerate support.

Every feature module's ORM models are imported here so
`Base.metadata` is aware of every table and `alembic revision
--autogenerate` can detect schema changes.
"""

from app.db.database import Base  # noqa: F401
from app.modules.auth.models import User  # noqa: F401
from app.modules.resumes.models import Resume  # noqa: F401
from app.modules.skills.models import Skill, StudentSkill  # noqa: F401
from app.modules.students.models import Department, Student  # noqa: F401

# Example of the pattern to follow as further modules are added:
# from app.modules.placements.models import Placement  # noqa: F401

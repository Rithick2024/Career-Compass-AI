"""
Student service layer — business logic and orchestration only.

Raises `app.core.exceptions.AppException` subclasses; never touches
HTTP or SQLAlchemy directly (those belong to the router and
repository respectively).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.modules.students.models import Student
from app.modules.students.repository import StudentRepository
from app.modules.students.schemas import StudentProfileResponse, StudentProfileUpdateRequest

# Fields whose Pydantic type (HttpUrl) needs an explicit str() cast
# before it can be assigned to the corresponding String column.
_URL_FIELDS = {"linkedin_url", "github_url"}


class StudentService:
    """
    Owns the transaction boundary for student-profile operations, same
    pattern as `AuthService`: constructs its own `StudentRepository`
    from the injected session and is responsible for committing writes.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = StudentRepository(db)

    async def _get_or_create_profile(self, user_id: int) -> Student:
        """
        Resolve the current user's student profile, creating an empty
        one on first access.

        There is no separate "create profile" endpoint in this task's
        scope, and a user's profile is implicitly tied to their account
        rather than something they explicitly provision — so GET and
        PATCH both transparently provision an empty row (all fields
        null except the user link) the first time a student reaches
        their profile, rather than 404ing until some other action
        creates it first. See docs/student-module.md for the reasoning
        and the alternative considered (404 until first PATCH).
        """
        student = await self._repo.get_by_user_id(user_id)
        if student is None:
            student = await self._repo.create_for_user(user_id)
            await self._db.commit()
            # `department` is trivially None on a just-created row, but
            # re-fetching keeps this function's return value consistent
            # with the update path below (always a query result, never
            # a manually-assembled object).
            student = await self._repo.get_by_user_id(user_id)
        return student

    async def get_my_profile(self, user_id: int) -> StudentProfileResponse:
        student = await self._get_or_create_profile(user_id)
        return StudentProfileResponse.model_validate(student)

    async def update_my_profile(
        self, user_id: int, data: StudentProfileUpdateRequest
    ) -> StudentProfileResponse:
        student = await self._get_or_create_profile(user_id)

        # Only fields actually present in the request are applied —
        # this is what makes a PATCH partial rather than a full
        # overwrite. A field explicitly sent as null (e.g. clearing
        # `phone`) is still "set" and is applied as null.
        updates = data.model_dump(exclude_unset=True)

        if "department_id" in updates and updates["department_id"] is not None:
            department = await self._repo.get_department_by_id(updates["department_id"])
            if department is None:
                raise ValidationError(
                    "The specified department does not exist.",
                    error_code="INVALID_DEPARTMENT",
                )

        for field, value in updates.items():
            if field in _URL_FIELDS and value is not None:
                value = str(value)
            setattr(student, field, value)

        await self._db.commit()

        # Without this, re-fetching below can return the SAME Python
        # object from SQLAlchemy's identity map with its `department`
        # relationship still holding its pre-update value (e.g. None) —
        # a plain re-SELECT does not, by itself, force an already-loaded
        # relationship to reload just because its FK column changed.
        self._db.expire(student)

        student = await self._repo.get_by_user_id(user_id)
        return StudentProfileResponse.model_validate(student)

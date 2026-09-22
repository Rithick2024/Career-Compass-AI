"""
Student service layer — business logic and orchestration only.

Raises `app.core.exceptions.AppException` subclasses; never touches
HTTP or SQLAlchemy directly (those belong to the router and
repository respectively).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.modules.students.models import Student
from app.modules.students.repository import StudentRepository
from app.modules.students.schemas import (
    DepartmentCreateRequest,
    DepartmentResponse,
    DepartmentStatusUpdateRequest,
    DepartmentUpdateRequest,
    StudentProfileResponse,
    StudentProfileUpdateRequest,
)

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
        student = await self._repo.get_by_user_id(user_id)
        if student is None:
            student = await self._repo.create_for_user(user_id)
            await self._db.commit()
            student = await self._repo.get_by_user_id(user_id)
        return student

    async def get_my_profile(self, user_id: int) -> StudentProfileResponse:
        student = await self._get_or_create_profile(user_id)
        return StudentProfileResponse.model_validate(student)

    async def update_my_profile(
        self, user_id: int, data: StudentProfileUpdateRequest
    ) -> StudentProfileResponse:
        student = await self._get_or_create_profile(user_id)

        updates = data.model_dump(exclude_unset=True)

        if "department_id" in updates and updates["department_id"] is not None:
            department = await self._repo.get_department_by_id(updates["department_id"])
            if department is None or not department.is_active:
                raise ValidationError(
                    "The specified department does not exist or is inactive.",
                    error_code="INVALID_DEPARTMENT",
                )

        for field, value in updates.items():
            if field in _URL_FIELDS and value is not None:
                value = str(value)
            setattr(student, field, value)

        await self._db.commit()
        self._db.expire(student)

        student = await self._repo.get_by_user_id(user_id)
        return StudentProfileResponse.model_validate(student)

    # --- Department Management ---

    async def list_active_departments(self) -> list[DepartmentResponse]:
        departments = await self._repo.list_active_departments()
        return [DepartmentResponse.model_validate(d) for d in departments]

    async def list_all_departments(self) -> list[DepartmentResponse]:
        departments = await self._repo.list_all_departments()
        return [DepartmentResponse.model_validate(d) for d in departments]

    async def create_department(self, data: DepartmentCreateRequest) -> DepartmentResponse:
        clean_name = data.name.strip()
        existing = await self._repo.get_department_by_name(clean_name)
        if existing is not None:
            raise ConflictError(
                "A department with this name already exists.",
                error_code="DEPARTMENT_ALREADY_EXISTS",
            )
        dept = await self._repo.create_department(clean_name)
        await self._db.commit()
        return DepartmentResponse.model_validate(dept)

    async def update_department(
        self, department_id: int, data: DepartmentUpdateRequest
    ) -> DepartmentResponse:
        dept = await self._repo.get_department_by_id(department_id)
        if dept is None:
            raise NotFoundError(
                "The specified department does not exist.",
                error_code="DEPARTMENT_NOT_FOUND",
            )

        clean_name = data.name.strip()
        existing = await self._repo.get_department_by_name(clean_name)
        if existing is not None and existing.id != department_id:
            raise ConflictError(
                "A department with this name already exists.",
                error_code="DEPARTMENT_ALREADY_EXISTS",
            )

        updated_dept = await self._repo.update_department(dept, clean_name)
        await self._db.commit()
        return DepartmentResponse.model_validate(updated_dept)

    async def update_department_status(
        self, department_id: int, data: DepartmentStatusUpdateRequest
    ) -> DepartmentResponse:
        dept = await self._repo.get_department_by_id(department_id)
        if dept is None:
            raise NotFoundError(
                "The specified department does not exist.",
                error_code="DEPARTMENT_NOT_FOUND",
            )

        updated_dept = await self._repo.update_department_status(dept, data.is_active)
        await self._db.commit()
        return DepartmentResponse.model_validate(updated_dept)

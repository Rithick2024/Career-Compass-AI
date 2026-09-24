"""
Staff Student service layer — business logic for staff student directory.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.resumes import storage
from app.modules.staff_students.repository import StaffStudentRepository
from app.modules.staff_students.schemas import (
    StaffStudentDetailResponse,
    StaffStudentListItem,
    StaffStudentResumeResponse,
    StaffStudentSkillResponse,
)
from app.modules.students.schemas import DepartmentOut


class StaffStudentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = StaffStudentRepository(db)

    async def list_students(
        self,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        graduation_year: Optional[int] = None,
    ) -> List[StaffStudentListItem]:
        rows = await self._repo.list_students(
            search=search,
            department_id=department_id,
            graduation_year=graduation_year,
        )
        items = []
        for student, user, skills_count, resumes_count in rows:
            dept_out = DepartmentOut.model_validate(student.department) if student.department else None
            items.append(
                StaffStudentListItem(
                    id=student.id,
                    user_id=student.user_id,
                    email=user.email,
                    full_name=student.full_name,
                    department=dept_out,
                    graduation_year=student.graduation_year,
                    cgpa=float(student.cgpa) if student.cgpa is not None else None,
                    skills_count=skills_count,
                    resumes_count=resumes_count,
                    is_active=user.is_active,
                )
            )
        return items

    async def get_student_detail(self, student_id: int) -> StaffStudentDetailResponse:
        result = await self._repo.get_student_detail(student_id)
        if not result:
            raise NotFoundError(
                "The specified student profile does not exist.",
                error_code="STUDENT_NOT_FOUND",
            )
        student, user = result

        student_skills = await self._repo.get_student_skills(student_id)
        student_resumes = await self._repo.get_student_resumes(student_id)

        skill_responses = [
            StaffStudentSkillResponse(
                id=ss.id,
                skill_id=ss.skill_id,
                skill_name=ss.skill.name if ss.skill else "",
                category=ss.skill.category if ss.skill else None,
                proficiency=ss.proficiency,
            )
            for ss in student_skills
        ]

        resume_responses = [
            StaffStudentResumeResponse(
                id=r.id,
                title=r.title,
                description=r.description,
                file_name=r.file_name,
                file_type=r.file_type,
                file_size=r.file_size,
                is_default=r.is_default,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in student_resumes
        ]

        dept_out = DepartmentOut.model_validate(student.department) if student.department else None

        return StaffStudentDetailResponse(
            id=student.id,
            user_id=student.user_id,
            email=user.email,
            full_name=student.full_name,
            phone=student.phone,
            date_of_birth=student.date_of_birth,
            address=student.address,
            linkedin_url=student.linkedin_url,
            github_url=student.github_url,
            department=dept_out,
            graduation_year=student.graduation_year,
            cgpa=float(student.cgpa) if student.cgpa is not None else None,
            skills=skill_responses,
            resumes=resume_responses,
            is_active=user.is_active,
            created_at=student.created_at,
            updated_at=student.updated_at,
        )

    async def get_student_resume_file_location(
        self, student_id: int, resume_id: int
    ) -> Tuple[Path, str, str]:
        # Verify student exists first
        detail = await self._repo.get_student_detail(student_id)
        if not detail:
            raise NotFoundError(
                "The specified student profile does not exist.",
                error_code="STUDENT_NOT_FOUND",
            )

        resume = await self._repo.get_resume_by_id_and_student_id(resume_id, student_id)
        if not resume:
            raise NotFoundError(
                "Resume document not found for this student.",
                error_code="RESUME_NOT_FOUND",
            )

        absolute_path = storage.resolve_absolute_path(resume.file_path)
        if absolute_path is None:
            raise NotFoundError(
                "The resume file could not be found on server storage.",
                error_code="RESUME_FILE_NOT_FOUND",
            )

        media_type = resume.file_type or "application/octet-stream"
        return absolute_path, resume.file_name, media_type

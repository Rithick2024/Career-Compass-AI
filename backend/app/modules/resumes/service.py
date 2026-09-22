"""
Resume service layer — business logic and orchestration for multiple resume documents per student.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.resumes import storage
from app.modules.resumes.repository import ResumeRepository
from app.modules.resumes.schemas import ResumeCreate, ResumeResponse, ResumeUpdate
from app.modules.students.repository import StudentRepository


class ResumeService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._resumes = ResumeRepository(db)
        self._students = StudentRepository(db)

    async def _get_or_create_student_id(self, user_id: int) -> int:
        student = await self._students.get_by_user_id(user_id)
        if student is None:
            student = await self._students.create_for_user(user_id)
            await self._db.commit()
        return student.id

    async def _get_existing_resume_by_id(self, resume_id: int, student_id: int):
        resume = await self._resumes.get_by_id_and_student_id(resume_id, student_id)
        if resume is None:
            raise NotFoundError(
                "Resume document not found.",
                error_code="RESUME_NOT_FOUND",
            )
        return resume

    async def get_my_resumes(self, user_id: int) -> List[ResumeResponse]:
        student_id = await self._get_or_create_student_id(user_id)
        resumes = await self._resumes.get_all_by_student_id(student_id)
        return [ResumeResponse.model_validate(r) for r in resumes]

    async def get_my_resume_by_id(self, user_id: int, resume_id: int) -> ResumeResponse:
        student_id = await self._get_or_create_student_id(user_id)
        resume = await self._get_existing_resume_by_id(resume_id, student_id)
        return ResumeResponse.model_validate(resume)

    async def create_my_resume(
        self,
        user_id: int,
        title: str,
        description: Optional[str],
        upload: UploadFile,
    ) -> ResumeResponse:
        student_id = await self._get_or_create_student_id(user_id)

        # Validate request metadata via ResumeCreate schema
        create_data = ResumeCreate(title=title, description=description)

        # Save uploaded file to disk
        saved = await storage.save_upload(student_id, upload)

        # First resume automatically becomes default
        existing_count = await self._resumes.count_by_student_id(student_id)
        is_default = (existing_count == 0)

        try:
            resume = await self._resumes.create(
                student_id=student_id,
                title=create_data.title,
                description=create_data.description,
                file_name=saved.file_name,
                file_path=saved.file_path,
                file_type=saved.file_type,
                file_size=saved.file_size,
                is_default=is_default,
            )
            await self._db.commit()
            await self._db.refresh(resume)
        except Exception:
            await self._db.rollback()
            storage.delete_file(saved.file_path)
            raise

        return ResumeResponse.model_validate(resume)

    async def update_my_resume(
        self, user_id: int, resume_id: int, data: ResumeUpdate
    ) -> ResumeResponse:
        student_id = await self._get_or_create_student_id(user_id)
        resume = await self._get_existing_resume_by_id(resume_id, student_id)

        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(resume, field, value)

        await self._db.commit()
        await self._db.refresh(resume)
        return ResumeResponse.model_validate(resume)

    async def set_default_resume(self, user_id: int, resume_id: int) -> ResumeResponse:
        student_id = await self._get_or_create_student_id(user_id)
        resume = await self._get_existing_resume_by_id(resume_id, student_id)

        if not resume.is_default:
            await self._resumes.unset_default_for_student(student_id)
            resume.is_default = True
            await self._db.commit()
            await self._db.refresh(resume)

        return ResumeResponse.model_validate(resume)

    async def delete_my_resume(self, user_id: int, resume_id: int) -> None:
        student_id = await self._get_or_create_student_id(user_id)
        resume = await self._get_existing_resume_by_id(resume_id, student_id)

        old_file_path = resume.file_path
        was_default = resume.is_default

        await self._resumes.delete(resume)

        # If deleted resume was default, reassign default to another remaining resume
        if was_default:
            next_default = await self._resumes.get_latest_remaining_by_student_id(
                student_id, exclude_id=resume_id
            )
            if next_default:
                next_default.is_default = True

        await self._db.commit()

        # Physical file cleanup
        if old_file_path:
            storage.delete_file(old_file_path)

    async def get_my_resume_file_location(
        self, user_id: int, resume_id: int
    ) -> Tuple[Path, str, str]:
        student_id = await self._get_or_create_student_id(user_id)
        resume = await self._get_existing_resume_by_id(resume_id, student_id)

        absolute_path = storage.resolve_absolute_path(resume.file_path)
        if absolute_path is None:
            raise NotFoundError(
                "The resume file could not be found.", error_code="RESUME_FILE_NOT_FOUND"
            )

        media_type = resume.file_type or "application/octet-stream"
        return absolute_path, resume.file_name, media_type

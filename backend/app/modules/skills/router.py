"""
Skill catalog and per-student skill endpoints. Routers stay thin:
parse request -> call service -> return response. All business logic
lives in `SkillService`.

Two router objects are defined here, mirroring the two distinct
resources this module exposes:
- `router` (`/skills`) — the platform-wide skill catalog.
- `student_skills_router` (`/students/me/skills`) — the authenticated
  student's own skill assignments, nested under the existing
  `/students/me` resource for consistency with the student module.

Both are wired into `app.api.v1.api_router` separately — see
`app/api/v1/__init__.py`.
"""

from typing import List

from fastapi import APIRouter, status

from app.api.deps import RequireStudent, SkillServiceDep
from app.modules.skills.schemas import (
    AddStudentSkillRequest,
    SkillOut,
    StudentSkillResponse,
    UpdateStudentSkillProficiencyRequest,
)

router = APIRouter(prefix="/skills", tags=["Skills"])
student_skills_router = APIRouter(prefix="/students/me/skills", tags=["Student Skills"])


@router.get("", response_model=List[SkillOut], status_code=status.HTTP_200_OK)
async def list_skills(
    current_user: RequireStudent, skill_service: SkillServiceDep
) -> List[SkillOut]:
    """Return the full platform skill catalog."""
    return await skill_service.list_catalog()


@student_skills_router.get(
    "", response_model=List[StudentSkillResponse], status_code=status.HTTP_200_OK
)
async def list_my_skills(
    current_user: RequireStudent, skill_service: SkillServiceDep
) -> List[StudentSkillResponse]:
    """Return the authenticated student's own skills."""
    return await skill_service.list_my_skills(current_user.id)


@student_skills_router.post(
    "", response_model=StudentSkillResponse, status_code=status.HTTP_201_CREATED
)
async def add_my_skill(
    data: AddStudentSkillRequest,
    current_user: RequireStudent,
    skill_service: SkillServiceDep,
) -> StudentSkillResponse:
    """Add an existing catalog skill to the authenticated student's profile."""
    return await skill_service.add_skill(current_user.id, data)


@student_skills_router.patch(
    "/{skill_id}", response_model=StudentSkillResponse, status_code=status.HTTP_200_OK
)
async def update_my_skill_proficiency(
    skill_id: int,
    data: UpdateStudentSkillProficiencyRequest,
    current_user: RequireStudent,
    skill_service: SkillServiceDep,
) -> StudentSkillResponse:
    """Update the proficiency level for a skill already on the student's profile."""
    return await skill_service.update_skill_proficiency(current_user.id, skill_id, data)


@student_skills_router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_my_skill(
    skill_id: int, current_user: RequireStudent, skill_service: SkillServiceDep
) -> None:
    """Remove a skill from the authenticated student's profile."""
    await skill_service.remove_skill(current_user.id, skill_id)

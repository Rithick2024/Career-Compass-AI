"""
Shared, cross-module FastAPI dependencies.

Feature modules (added in later tasks) will import from here so every
router gets the DB session — and, later, the current-user dependency,
pagination params, etc. — the same way. Keeping this file separate
from `app/db/session.py` keeps the DB layer framework-agnostic while
this file is the explicit FastAPI wiring/DI boundary.
"""

from typing import Annotated, AsyncGenerator, Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.core.exceptions import ForbiddenError
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.service import AuthService
from app.modules.resumes.service import ResumeService
from app.modules.skills.service import SkillService
from app.modules.students.service import StudentService
from app.shared.enums import RoleEnum

# --- Database session ---
DBSession = Annotated[AsyncSession, Depends(get_db)]


# --- Settings ---
def get_app_settings() -> Settings:
    return settings


AppSettings = Annotated[Settings, Depends(get_app_settings)]


# --- Auth service ---
def get_auth_service(db: DBSession) -> AuthService:
    return AuthService(db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


# --- Current user / role-based authorization ---
# tokenUrl is only used to populate the "Authorize" button in /docs;
# the dependency itself just extracts the bearer token from the header.
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/swagger-login")


async def get_current_user(
    token: Annotated[str, Depends(_oauth2_scheme)],
    auth_service: AuthServiceDep,
) -> User:
    """Resolve the authenticated user from the request's bearer token."""
    return await auth_service.get_current_user(token)


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*allowed_roles: RoleEnum) -> Callable[[User], User]:
    """
    Dependency factory for role-based authorization.

    Usage in a router:
        @router.get("/staff-only", dependencies=[Depends(require_role(RoleEnum.STAFF))])
        # or, to also use the user object:
        async def handler(user: Annotated[User, Depends(require_role(RoleEnum.STAFF))]):
            ...
    """

    def _check_role(user: CurrentUser) -> User:
        if user.role not in allowed_roles:
            raise ForbiddenError(
                "You do not have permission to access this resource.",
                error_code="INSUFFICIENT_ROLE",
            )
        return user

    return _check_role


# --- Student service ---
def get_student_service(db: DBSession) -> StudentService:
    return StudentService(db)


StudentServiceDep = Annotated[StudentService, Depends(get_student_service)]

# Reuses the existing require_role factory rather than bare
# get_current_user: /students/me is specifically a *student's* own
# profile, so a non-student (e.g. staff) authenticated user shouldn't
# have an empty profile transparently provisioned for them just by
# hitting the endpoint.
RequireStudent = Annotated[User, Depends(require_role(RoleEnum.STUDENT))]
RequireStaff = Annotated[User, Depends(require_role(RoleEnum.STAFF))]


# --- Skill service ---
def get_skill_service(db: DBSession) -> SkillService:
    return SkillService(db)


SkillServiceDep = Annotated[SkillService, Depends(get_skill_service)]


# --- Resume service ---
def get_resume_service(db: DBSession) -> ResumeService:
    return ResumeService(db)


ResumeServiceDep = Annotated[ResumeService, Depends(get_resume_service)]


__all__ = [
    "DBSession",
    "AppSettings",
    "get_db",
    "get_app_settings",
    "AuthServiceDep",
    "get_auth_service",
    "CurrentUser",
    "get_current_user",
    "require_role",
    "StudentServiceDep",
    "get_student_service",
    "RequireStudent",
    "RequireStaff",
    "SkillServiceDep",
    "get_skill_service",
    "ResumeServiceDep",
    "get_resume_service",
]

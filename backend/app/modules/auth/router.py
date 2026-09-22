"""
Auth endpoints. Routers stay thin: parse request -> call service ->
return response. All business logic lives in `AuthService`.
"""

from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from app.api.deps import AuthServiceDep, CurrentUser
from app.modules.auth.schemas import (
    StaffRegisterRequest,
    TokenResponse,
    UserLoginRequest,
    UserPublic,
    UserRegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest, auth_service: AuthServiceDep) -> UserPublic:
    """
    Register a new account.

    Public registration always creates a `student` account — see
    docs/authentication.md for why staff accounts cannot be
    self-registered.
    """
    return await auth_service.register(data)


@router.post("/staff-register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_staff(data: StaffRegisterRequest, auth_service: AuthServiceDep) -> UserPublic:
    """
    Developer/Testing endpoint: Provision a new Staff account via Swagger UI.

    Not exposed on the frontend user-facing UI.
    """
    return await auth_service.register_staff(data)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(data: UserLoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
    """Authenticate with email + password and receive a JWT access token."""
    return await auth_service.authenticate(data.email, data.password)


@router.post("/swagger-login", response_model=TokenResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
async def swagger_login(
    data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    auth_service: AuthServiceDep
) -> TokenResponse:
    """Endpoint specifically for Swagger UI's OAuth2 authorization form."""
    return await auth_service.authenticate(data.username, data.password)


@router.get("/me", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def get_me(current_user: CurrentUser) -> UserPublic:
    """Return the currently authenticated user's profile."""
    return UserPublic.model_validate(current_user)

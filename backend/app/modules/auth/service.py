"""
Auth service layer — business logic and orchestration only.

Raises `app.core.exceptions.AppException` subclasses; never touches
HTTP or SQLAlchemy directly (those belong to the router and
repository respectively).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from app.core.jwt import create_access_token, decode_access_token, TokenError
from app.core.security import hash_password, verify_password
from app.shared.enums import RoleEnum
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import (
    StaffRegisterRequest,
    TokenResponse,
    UserPublic,
    UserRegisterRequest,
)


class AuthService:
    """
    Owns the transaction boundary for auth operations: it constructs
    its own `UserRepository` from the injected session and is
    responsible for committing writes. The repository itself never
    commits — that keeps it reusable from contexts with different
    transaction lifecycles later (e.g. a bulk-import script).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = UserRepository(db)

    async def register(self, data: UserRegisterRequest) -> UserPublic:
        existing = await self._repo.get_by_email(data.email)
        if existing is not None:
            raise ConflictError(
                "An account with this email already exists.",
                error_code="EMAIL_ALREADY_REGISTERED",
            )

        # `data.role` is already forced to RoleEnum.STUDENT by the schema's
        # validator — public registration cannot create other roles.
        user = await self._repo.create(
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
        )
        await self._db.commit()
        return UserPublic.model_validate(user)

    async def register_staff(self, data: StaffRegisterRequest) -> UserPublic:
        existing = await self._repo.get_by_email(data.email)
        if existing is not None:
            raise ConflictError(
                "An account with this email already exists.",
                error_code="EMAIL_ALREADY_REGISTERED",
            )

        user = await self._repo.create(
            email=data.email,
            password_hash=hash_password(data.password),
            role=RoleEnum.STAFF,
        )
        await self._db.commit()
        return UserPublic.model_validate(user)

    async def authenticate(self, email: str, password: str) -> TokenResponse:
        user = await self._repo.get_by_email(email)

        # Same generic message whether the email doesn't exist or the
        # password is wrong — never reveal which one it was.
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError(
                "Invalid email or password.", error_code="INVALID_CREDENTIALS"
            )

        if not user.is_active:
            # Credentials were valid, so this is an authorization/status
            # problem rather than an authentication one -> 403, not 401.
            # See docs/authentication.md for the reasoning.
            raise ForbiddenError(
                "This account has been deactivated.", error_code="ACCOUNT_INACTIVE"
            )

        token = create_access_token(user_id=user.id, role=user.role.value)
        return TokenResponse(access_token=token, user=UserPublic.model_validate(user))

    async def get_current_user(self, token: str) -> User:
        try:
            payload = decode_access_token(token)
        except TokenError as exc:
            raise UnauthorizedError(str(exc), error_code="INVALID_TOKEN") from exc

        subject = payload.get("sub")
        if subject is None:
            raise UnauthorizedError("Token is malformed.", error_code="INVALID_TOKEN")

        try:
            user_id = int(subject)
        except ValueError as exc:
            raise UnauthorizedError("Token is malformed.", error_code="INVALID_TOKEN") from exc

        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User no longer exists.", error_code="INVALID_TOKEN")

        if not user.is_active:
            raise ForbiddenError(
                "This account has been deactivated.", error_code="ACCOUNT_INACTIVE"
            )

        return user

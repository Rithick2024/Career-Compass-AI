"""
User repository — the only layer that issues SQLAlchemy queries
against the `users` table. The service layer depends on this, never
on the ORM/session directly.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.shared.enums import RoleEnum


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, *, email: str, password_hash: str, role: RoleEnum) -> User:
        user = User(email=email, password_hash=password_hash, role=role)
        self._db.add(user)
        await self._db.flush()  # assigns PK/defaults without ending the transaction
        await self._db.refresh(user)
        return user

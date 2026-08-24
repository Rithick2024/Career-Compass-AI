"""
User ORM model.

One table (`users`) per the finalized Day 2 database design — no
separate roles table; `role` is a native PostgreSQL enum backed by
`app.shared.enums.RoleEnum`.

`id` is an auto-incrementing integer primary key (project decision for
this MCA mini project — simpler to read/debug than UUIDs at this
scale). SQLAlchemy 2.x's `Mapped[int]` + `primary_key=True` is
sufficient on its own to get PostgreSQL `SERIAL`-style autoincrement;
no extra `autoincrement=` argument is needed.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.shared.enums import RoleEnum


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(
            RoleEnum,
            name="user_role",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=RoleEnum.STUDENT,
        server_default=RoleEnum.STUDENT.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r} role={self.role}>"

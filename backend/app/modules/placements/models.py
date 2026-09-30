"""
Placement ORM model.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.modules.applications.models import Application


class Placement(Base):
    __tablename__ = "placements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True
    )
    
    final_package_ctc: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    placement_date: Mapped[date] = mapped_column(Date, nullable=False)
    offer_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    application: Mapped["Application"] = relationship(back_populates="placement", lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Placement id={self.id} application_id={self.application_id} accepted={self.offer_accepted}>"

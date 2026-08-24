"""
SQLAlchemy engine and declarative base.

This module owns the single, process-wide `AsyncEngine`. Feature
modules should never construct their own engine — they get sessions
via `app.db.session`.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """
    Shared declarative base for all ORM models.

    Left deliberately empty today (no models are defined yet). Future
    feature modules will subclass this for their tables, and Alembic's
    autogenerate reads its metadata via `app.db.base`.
    """
    pass


def _build_engine() -> AsyncEngine:
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,  # guards against stale/dropped connections
        future=True,
    )


engine: AsyncEngine = _build_engine()

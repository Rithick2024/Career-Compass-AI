"""
Session factory and the `get_db` FastAPI dependency.

Repository/service layers should receive an `AsyncSession` via this
dependency rather than opening their own connections.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.database import engine

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a request-scoped `AsyncSession`.

    Commits are the caller's (service layer's) responsibility. This
    dependency guarantees the session is always closed, and rolls back
    on unhandled exceptions so a failed request never leaves a dirty
    transaction behind.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

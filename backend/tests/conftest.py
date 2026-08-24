"""
Shared pytest fixtures for the auth test suite.

Uses a dedicated `career_compass_test` database (never the dev DB) and
wraps each test in a transaction that's rolled back afterwards, so
tests don't leak state into one another and can run in any order.

Setup required once, before running tests:
    createdb career_compass_test
"""

import os

# Point at the test database BEFORE importing anything from `app` — the
# app's Settings object is built once at import time, so this must run
# first. An explicit env var here always wins over `.env`.
os.environ["POSTGRES_DB"] = "career_compass_test"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.modules.auth.repository import UserRepository

# NOTE on event loop scope: `engine` below is session-scoped (one asyncpg
# pool for the whole run), so every async fixture/test that touches it
# must run on the SAME event loop for the whole session — otherwise
# asyncpg raises opaque "another operation is in progress" /
# "attached to a different loop" errors. That's configured via
# `asyncio_default_fixture_loop_scope = "session"` in pyproject.toml
# (for fixtures) and `@pytest.mark.asyncio(loop_scope="session")` on
# each async test (in test_auth.py) — NOT by redefining the `event_loop`
# fixture here, which pytest-asyncio 0.23+ deprecates in favor of that
# marker-based approach.


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine():
    """One engine for the whole test session; creates/drops all tables."""
    test_engine = create_async_engine(settings.DATABASE_URL, future=True)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """
    A session bound to a single connection/transaction per test.

    The service layer calls `session.commit()` as part of normal
    operation (see AuthService.register) — `join_transaction_mode=
    "create_savepoint"` lets that commit happen as a SAVEPOINT instead
    of ending the outer transaction, so the whole thing still rolls
    back cleanly when the test finishes.
    """
    async with engine.connect() as conn:
        trans = await conn.begin()
        session_factory = async_sessionmaker(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        session: AsyncSession = session_factory()
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """Async HTTP client with the app's DB dependency overridden to use db_session."""
    from app.db.session import get_db

    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user_repo(db_session):
    return UserRepository(db_session)

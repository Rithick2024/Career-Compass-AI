"""
Health check endpoints.

`/health` — liveness only, no dependencies (used by orchestrators
for basic "is the process up" checks).
`/health/db` — readiness check that verifies the app can actually
reach PostgreSQL.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text

from app.api.deps import DBSession
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str


class DBHealthResponse(BaseModel):
    status: str
    database: str


@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Basic liveness probe — does not touch the database."""
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
    )


@router.get("/db", response_model=DBHealthResponse, status_code=status.HTTP_200_OK)
async def health_check_db(db: DBSession) -> DBHealthResponse:
    """Readiness probe — confirms a live connection to PostgreSQL."""
    await db.execute(text("SELECT 1"))
    return DBHealthResponse(status="ok", database="connected")

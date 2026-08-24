"""
Global exception handlers.

Registered once on the FastAPI app in `app.main`. Ensures every error
response — expected (`AppException`) or not — comes back as a
consistent JSON envelope instead of a stack trace leaking to clients.
"""

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException

logger = logging.getLogger("app")


def _error_body(error_code: str, message: str, details: Any = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {"error_code": error_code, "message": message}
    if details is not None:
        body["details"] = details
    return body


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "AppException: %s | path=%s | details=%s",
            exc.error_code, request.url.path, exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.error_code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Pydantic v2 includes a 'ctx' key on errors raised by custom
        # field_validators that can hold the raw exception object (e.g.
        # {'ctx': {'error': ValueError(...)}}). That's not JSON-serializable
        # and 'msg' already carries the human-readable text, so drop 'ctx'.
        errors = [
            {k: v for k, v in error.items() if k != "ctx"} for error in exc.errors()
        ]
        logger.info("RequestValidationError on %s: %s", request.url.path, errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(
                "VALIDATION_ERROR",
                "One or more fields failed validation.",
                errors,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("HTTP_ERROR", str(exc.detail)),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.error("Unhandled SQLAlchemyError on %s", request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_body("DATABASE_ERROR", "A database error occurred."),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception on %s", request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred."),
        )

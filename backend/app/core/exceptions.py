"""
Application-level exception hierarchy.

Feature modules (services/repositories) should raise these instead of
raising HTTPException directly — that keeps the service layer free of
any HTTP/framework concerns (Clean Architecture boundary). The
handlers registered in `app.core.error_handlers` translate these into
proper HTTP responses at the edge.
"""

from typing import Any, Optional


class AppException(Exception):
    """Base class for all application-defined exceptions."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        error_code: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "The requested resource was not found."


class ValidationError(AppException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Validation failed."


class ConflictError(AppException):
    status_code = 409
    error_code = "CONFLICT"
    message = "The request conflicts with the current state of the resource."


class UnauthorizedError(AppException):
    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Authentication is required to access this resource."


class ForbiddenError(AppException):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action."


class DatabaseError(AppException):
    status_code = 503
    error_code = "DATABASE_ERROR"
    message = "A database error occurred."

"""
JWT access-token creation and decoding.

Secret and expiration come from `app.core.config.settings` — never
hardcoded. Kept separate from `security.py` (password hashing) so
each concern can change independently.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings

TOKEN_TYPE = "bearer"


class TokenError(Exception):
    """Raised for any invalid, expired, or malformed token."""


def create_access_token(user_id: int, role: str) -> str:
    """
    Create a signed JWT access token.

    `sub` (subject) is the user's id — the only value `get_current_user`
    needs to resolve the user. `role` is embedded as a convenience claim;
    it is NOT trusted for authorization decisions on its own once the
    user is loaded from the DB (the DB row is the source of truth), but
    lets callers inspect the token without a lookup if ever needed.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT, raising `TokenError` on any problem."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except ExpiredSignatureError as exc:
        raise TokenError("Token has expired.") from exc
    except InvalidTokenError as exc:
        raise TokenError("Token is invalid.") from exc

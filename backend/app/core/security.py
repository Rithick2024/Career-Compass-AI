"""
Password hashing.

Uses `bcrypt` directly (not passlib — passlib is effectively
unmaintained and has known incompatibilities with recent bcrypt
releases). Kept in its own module with a narrow function-based
interface so the hashing algorithm can be swapped later (e.g. to
argon2) without touching any caller.
"""

import bcrypt

_BCRYPT_ROUNDS = 12


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage. Never store the raw password."""
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed hash (shouldn't happen for hashes we generated ourselves).
        return False

"""
Focused tests for the Authentication module.

Covers: registration, login, /me, password hashing, JWT validity,
and role-based authorization. Deliberately kept narrow per scope —
not a full test suite for the whole app.
"""

import pytest

from app.api.deps import require_role
from app.core.exceptions import ForbiddenError
from app.core.jwt import decode_access_token
from app.core.security import hash_password, verify_password
from app.modules.auth.models import User
from app.shared.enums import RoleEnum


# --- Password hashing (no DB needed) ---------------------------------

def test_password_hash_is_not_plaintext():
    hashed = hash_password("SecurePass123")
    assert hashed != "SecurePass123"
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_password_hash_verifies_correctly():
    hashed = hash_password("SecurePass123")
    assert verify_password("SecurePass123", hashed) is True
    assert verify_password("WrongPassword", hashed) is False


# --- Registration ------------------------------------------------------

@pytest.mark.asyncio(loop_scope="session")
async def test_register_success(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "New.User@Example.com", "password": "SecurePass123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new.user@example.com"  # normalized to lowercase
    assert body["role"] == "student"
    assert body["is_active"] is True
    assert "password_hash" not in body
    assert "password" not in body


@pytest.mark.asyncio(loop_scope="session")
async def test_register_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "SecurePass123"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["error_code"] == "EMAIL_ALREADY_REGISTERED"


@pytest.mark.asyncio(loop_scope="session")
async def test_register_weak_password_rejected(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
async def test_register_admin_role_rejected(client):
    """Public registration must never be able to create an admin account."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "wannabe-admin@example.com", "password": "SecurePass123", "role": "admin"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error_code"] == "VALIDATION_ERROR"


# --- Login ---------------------------------------------------------------

@pytest.mark.asyncio(loop_scope="session")
async def test_login_success(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login-ok@example.com", "password": "SecurePass123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login-ok@example.com", "password": "SecurePass123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "login-ok@example.com"

    # Token should decode and carry the right subject (sub is always a
    # string in the JWT, per unchanged JWT convention).
    payload = decode_access_token(body["access_token"])
    assert payload["sub"] == str(body["user"]["id"])


@pytest.mark.asyncio(loop_scope="session")
async def test_login_incorrect_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login-bad@example.com", "password": "SecurePass123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login-bad@example.com", "password": "WrongPassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio(loop_scope="session")
async def test_login_inactive_user_rejected(client, user_repo, db_session):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "inactive@example.com", "password": "SecurePass123"},
    )
    user = await user_repo.get_by_email("inactive@example.com")
    user.is_active = False
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "SecurePass123"},
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "ACCOUNT_INACTIVE"


# --- /me -------------------------------------------------------------------

@pytest.mark.asyncio(loop_scope="session")
async def test_me_with_valid_token(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "me-ok@example.com", "password": "SecurePass123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "me-ok@example.com", "password": "SecurePass123"},
    )
    token = login_resp.json()["access_token"]

    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me-ok@example.com"


@pytest.mark.asyncio(loop_scope="session")
async def test_me_with_invalid_token(client):
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.valid.token"}
    )
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "INVALID_TOKEN"


@pytest.mark.asyncio(loop_scope="session")
async def test_me_with_no_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# --- Role authorization ------------------------------------------------

def _make_user(role: RoleEnum) -> User:
    return User(id=1, email="role-test@example.com", password_hash="x", role=role)


def test_require_role_allows_matching_role():
    check = require_role(RoleEnum.ADMIN)
    admin = _make_user(RoleEnum.ADMIN)
    assert check(admin) is admin


def test_require_role_rejects_non_matching_role():
    check = require_role(RoleEnum.ADMIN)
    student = _make_user(RoleEnum.STUDENT)
    with pytest.raises(ForbiddenError) as exc_info:
        check(student)
    assert exc_info.value.status_code == 403
    assert exc_info.value.error_code == "INSUFFICIENT_ROLE"

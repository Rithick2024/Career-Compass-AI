"""
Focused tests for the Student Profile module.

Covers: profile retrieval (including auto-provisioning), partial
updates, validation, and ownership isolation. Deliberately kept
narrow per scope — not a full test suite for the whole app.
"""

import pytest

from app.modules.students.models import Department

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _register_and_login(client, email: str, password: str = "SecurePass123") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- GET /students/me ---------------------------------------------------

async def test_get_profile_authenticated(client):
    token = await _register_and_login(client, "get-profile@example.com")
    resp = await client.get("/api/v1/students/me", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] is None
    assert body["department"] is None
    assert "password_hash" not in body
    assert "email" not in body  # auth field, never duplicated onto the student resource


async def test_get_profile_unauthenticated_rejected(client):
    resp = await client.get("/api/v1/students/me")
    assert resp.status_code == 401


async def test_missing_profile_auto_provisioned(client):
    """
    A brand-new student account has no `students` row yet — GET should
    transparently create one (all fields null) rather than 404ing,
    per the documented design decision.
    """
    token = await _register_and_login(client, "fresh-profile@example.com")
    resp = await client.get("/api/v1/students/me", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] is not None
    assert body["id"] is not None
    assert all(
        body[field] is None
        for field in ("full_name", "phone", "department", "graduation_year", "cgpa")
    )


# --- PATCH /students/me -------------------------------------------------

async def test_update_profile_success(client):
    token = await _register_and_login(client, "update-profile@example.com")
    resp = await client.patch(
        "/api/v1/students/me",
        headers=_auth_headers(token),
        json={
            "full_name": "Rithee Kumar",
            "phone": "+91 98765 43210",
            "graduation_year": 2026,
            "cgpa": 8.75,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Rithee Kumar"
    assert body["phone"] == "+91 98765 43210"
    assert body["graduation_year"] == 2026
    assert body["cgpa"] == 8.75


async def test_patch_updates_only_supplied_fields(client):
    token = await _register_and_login(client, "partial-update@example.com")
    await client.patch(
        "/api/v1/students/me",
        headers=_auth_headers(token),
        json={"full_name": "Original Name", "phone": "+91 90000 00000"},
    )

    resp = await client.patch(
        "/api/v1/students/me",
        headers=_auth_headers(token),
        json={"cgpa": 9.1},
    )
    assert resp.status_code == 200
    body = resp.json()
    # The fields from the first PATCH must survive the second, unrelated one.
    assert body["full_name"] == "Original Name"
    assert body["phone"] == "+91 90000 00000"
    assert body["cgpa"] == 9.1


async def test_patch_sets_department(client, db_session):
    """Regression test: department must reflect in the SAME response
    that sets it (caught a stale-relationship bug during manual
    verification — see StudentService.update_my_profile)."""
    department = Department(name="Test Department")
    db_session.add(department)
    await db_session.commit()
    await db_session.refresh(department)

    token = await _register_and_login(client, "department-update@example.com")
    resp = await client.patch(
        "/api/v1/students/me",
        headers=_auth_headers(token),
        json={"department_id": department.id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["department"] is not None
    assert body["department"]["id"] == department.id
    assert body["department"]["name"] == "Test Department"


async def test_patch_invalid_department_rejected(client):
    token = await _register_and_login(client, "bad-department@example.com")
    resp = await client.patch(
        "/api/v1/students/me",
        headers=_auth_headers(token),
        json={"department_id": 999999},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "INVALID_DEPARTMENT"


async def test_patch_invalid_cgpa_rejected(client):
    token = await _register_and_login(client, "bad-cgpa@example.com")
    resp = await client.patch(
        "/api/v1/students/me", headers=_auth_headers(token), json={"cgpa": 15}
    )
    assert resp.status_code == 422


async def test_patch_invalid_url_rejected(client):
    token = await _register_and_login(client, "bad-url@example.com")
    resp = await client.patch(
        "/api/v1/students/me",
        headers=_auth_headers(token),
        json={"linkedin_url": "not-a-url"},
    )
    assert resp.status_code == 422


async def test_patch_rejects_auth_fields(client):
    """Can't smuggle a role/email change through the student PATCH schema."""
    token = await _register_and_login(client, "no-auth-fields@example.com")
    resp = await client.patch(
        "/api/v1/students/me", headers=_auth_headers(token), json={"role": "admin"}
    )
    assert resp.status_code == 422


# --- Ownership -----------------------------------------------------------

async def test_student_cannot_see_another_students_profile(client):
    token_a = await _register_and_login(client, "owner-a@example.com")
    await client.patch(
        "/api/v1/students/me", headers=_auth_headers(token_a), json={"full_name": "Student A"}
    )

    token_b = await _register_and_login(client, "owner-b@example.com")
    resp = await client.get("/api/v1/students/me", headers=_auth_headers(token_b))
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] is None  # B's own (empty) profile, not A's

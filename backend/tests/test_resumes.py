"""
Focused tests for the Resume module.

Covers: create/retrieve/update/delete lifecycle, the 404-until-created
design decision (see ResumeService's module docstring), validation,
duplicate detection, and ownership isolation. Deliberately kept narrow
per scope — not a full test suite for the whole app.
"""

import pytest

from app.shared.enums import RoleEnum

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _register_and_login(client, email: str, password: str = "SecurePass123") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- GET before any resume exists ------------------------------------------

async def test_get_resume_before_creation_returns_404(client):
    """
    No resume auto-provisioning (unlike the student profile) — see
    ResumeService's module docstring for why.
    """
    token = await _register_and_login(client, "no-resume-yet@example.com")
    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_NOT_FOUND"


# --- POST (create) ----------------------------------------------------------

async def test_create_resume(client):
    token = await _register_and_login(client, "create-resume@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={
            "professional_summary": "  Aspiring backend engineer.  ",
            "career_objective": "Land a great internship.",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    # Whitespace trimmed.
    assert body["professional_summary"] == "Aspiring backend engineer."
    assert body["career_objective"] == "Land a great internship."
    assert body["student_id"] is not None
    assert "password_hash" not in body
    assert "email" not in body


async def test_get_resume_after_creation(client):
    token = await _register_and_login(client, "get-after-create@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "Summary text"},
    )
    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["professional_summary"] == "Summary text"


async def test_create_duplicate_resume_rejected(client):
    token = await _register_and_login(client, "duplicate-resume@example.com")
    payload = {"professional_summary": "First"}
    first = await client.post(
        "/api/v1/students/me/resume", headers=_auth_headers(token), json=payload
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/students/me/resume", headers=_auth_headers(token), json={"professional_summary": "Second"}
    )
    assert second.status_code == 409
    assert second.json()["error_code"] == "RESUME_ALREADY_EXISTS"


async def test_create_resume_with_null_fields(client):
    """Both fields are optional/nullable — an empty resume is valid."""
    token = await _register_and_login(client, "empty-resume@example.com")
    resp = await client.post("/api/v1/students/me/resume", headers=_auth_headers(token), json={})
    assert resp.status_code == 201
    body = resp.json()
    assert body["professional_summary"] is None
    assert body["career_objective"] is None


# --- PATCH (partial update) -------------------------------------------------

async def test_patch_updates_only_supplied_fields(client):
    token = await _register_and_login(client, "partial-patch@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "Original summary", "career_objective": "Original objective"},
    )

    resp = await client.patch(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"career_objective": "Updated objective"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # The field from creation must survive the PATCH that didn't touch it.
    assert body["professional_summary"] == "Original summary"
    assert body["career_objective"] == "Updated objective"


async def test_patch_can_clear_field_with_explicit_null(client):
    token = await _register_and_login(client, "clear-field@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "Will be cleared", "career_objective": "Stays"},
    )

    resp = await client.patch(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": None},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["professional_summary"] is None
    assert body["career_objective"] == "Stays"


async def test_patch_when_no_resume_exists_returns_404(client):
    token = await _register_and_login(client, "patch-no-resume@example.com")
    resp = await client.patch(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"career_objective": "Should fail"},
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_NOT_FOUND"


# --- DELETE ------------------------------------------------------------------

async def test_delete_resume(client):
    token = await _register_and_login(client, "delete-resume@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "To be deleted"},
    )

    resp = await client.delete("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 204


async def test_get_after_delete_returns_404(client):
    token = await _register_and_login(client, "get-after-delete@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "Temporary"},
    )
    await client.delete("/api/v1/students/me/resume", headers=_auth_headers(token))

    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_NOT_FOUND"


async def test_delete_when_no_resume_exists_returns_404(client):
    token = await _register_and_login(client, "delete-no-resume@example.com")
    resp = await client.delete("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_NOT_FOUND"


async def test_create_after_delete_succeeds(client):
    """The 404-after-delete state is not permanent — a new resume can
    be created afterward, same as any other 0..1 resource."""
    token = await _register_and_login(client, "recreate-after-delete@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "First resume"},
    )
    await client.delete("/api/v1/students/me/resume", headers=_auth_headers(token))

    resp = await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "Second resume"},
    )
    assert resp.status_code == 201
    assert resp.json()["professional_summary"] == "Second resume"


# --- Validation --------------------------------------------------------------

async def test_create_rejects_extra_fields(client):
    """Cannot smuggle student_id (or any other field) through the create schema."""
    token = await _register_and_login(client, "extra-fields@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "ok", "student_id": 999999},
    )
    assert resp.status_code == 422


async def test_create_rejects_too_long_professional_summary(client):
    token = await _register_and_login(client, "too-long-summary@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "a" * 2001},
    )
    assert resp.status_code == 422


async def test_create_rejects_too_long_career_objective(client):
    token = await _register_and_login(client, "too-long-objective@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"career_objective": "a" * 1001},
    )
    assert resp.status_code == 422


# --- Authentication ------------------------------------------------------

async def test_get_resume_no_token_rejected(client):
    resp = await client.get("/api/v1/students/me/resume")
    assert resp.status_code == 401


async def test_get_resume_invalid_token_rejected(client):
    resp = await client.get(
        "/api/v1/students/me/resume", headers=_auth_headers("not.a.valid.token")
    )
    assert resp.status_code == 401


# --- Authorization (role) ---------------------------------------------------

async def test_admin_cannot_access_student_resume_endpoint(client, db_session, user_repo):
    token = await _register_and_login(client, "admin-blocked-resume@example.com")
    user = await user_repo.get_by_email("admin-blocked-resume@example.com")
    user.role = RoleEnum.ADMIN
    await db_session.commit()

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin-blocked-resume@example.com", "password": "SecurePass123"},
    )
    admin_token = admin_login.json()["access_token"]

    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(admin_token))
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "INSUFFICIENT_ROLE"


# --- Ownership ---------------------------------------------------------------

async def test_student_cannot_see_another_students_resume(client):
    token_a = await _register_and_login(client, "resume-owner-a@example.com")
    token_b = await _register_and_login(client, "resume-owner-b@example.com")

    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token_a),
        json={"professional_summary": "Student A's resume"},
    )

    # Student B's own GET must be 404 — not seeing A's resume, and
    # there is no endpoint that accepts a client-supplied student id
    # to even attempt cross-access.
    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token_b))
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_NOT_FOUND"


async def test_student_b_patch_and_delete_do_not_affect_student_a(client):
    token_a = await _register_and_login(client, "resume-isolation-a@example.com")
    token_b = await _register_and_login(client, "resume-isolation-b@example.com")

    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token_a),
        json={"professional_summary": "A's original summary"},
    )

    # B has no resume of their own — PATCH/DELETE must 404 for B,
    # never touching A's row.
    patch_resp = await client.patch(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token_b),
        json={"professional_summary": "B trying to overwrite"},
    )
    assert patch_resp.status_code == 404

    delete_resp = await client.delete(
        "/api/v1/students/me/resume", headers=_auth_headers(token_b)
    )
    assert delete_resp.status_code == 404

    # A's resume is untouched by B's failed attempts.
    a_resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token_a))
    assert a_resp.status_code == 200
    assert a_resp.json()["professional_summary"] == "A's original summary"

"""
Focused tests for the Skills module (skill catalog + student skills).

Covers: catalog retrieval, per-student skill CRUD, validation,
duplicate/missing-resource handling, and ownership isolation.
Deliberately kept narrow per scope — not a full test suite for the
whole app.
"""

import pytest

from app.modules.skills.models import Skill
from app.shared.enums import RoleEnum

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _register_and_login(client, email: str, password: str = "SecurePass123") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_skill(db_session, name: str, category: str = "Test Category") -> Skill:
    skill = Skill(name=name, category=category)
    db_session.add(skill)
    await db_session.commit()
    await db_session.refresh(skill)
    return skill


# --- GET /skills (catalog) -----------------------------------------------

async def test_get_skill_catalog(client, db_session):
    await _create_skill(db_session, "Catalog-Test-Python")
    await _create_skill(db_session, "Catalog-Test-Java")

    token = await _register_and_login(client, "catalog@example.com")
    resp = await client.get("/api/v1/skills", headers=_auth_headers(token))
    assert resp.status_code == 200
    names = [s["name"] for s in resp.json()]
    assert "Catalog-Test-Python" in names
    assert "Catalog-Test-Java" in names


async def test_get_skill_catalog_unauthenticated_rejected(client):
    resp = await client.get("/api/v1/skills")
    assert resp.status_code == 401


# --- GET /students/me/skills ----------------------------------------------

async def test_get_my_skills_authenticated_empty(client):
    token = await _register_and_login(client, "my-skills-empty@example.com")
    resp = await client.get("/api/v1/students/me/skills", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_my_skills_unauthenticated_rejected(client):
    resp = await client.get("/api/v1/students/me/skills")
    assert resp.status_code == 401


# --- POST /students/me/skills ---------------------------------------------

async def test_add_skill_to_profile(client, db_session):
    skill = await _create_skill(db_session, "Add-Test-Python")
    token = await _register_and_login(client, "add-skill@example.com")

    resp = await client.post(
        "/api/v1/students/me/skills",
        headers=_auth_headers(token),
        json={"skill_id": skill.id, "proficiency": "intermediate"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["skill"]["id"] == skill.id
    assert body["skill"]["name"] == "Add-Test-Python"
    assert body["proficiency"] == "intermediate"

    # Reflected immediately in the student's own list too.
    list_resp = await client.get("/api/v1/students/me/skills", headers=_auth_headers(token))
    assert len(list_resp.json()) == 1


async def test_add_duplicate_skill_rejected(client, db_session):
    skill = await _create_skill(db_session, "Dup-Test-Python")
    token = await _register_and_login(client, "dup-skill@example.com")

    payload = {"skill_id": skill.id, "proficiency": "beginner"}
    first = await client.post(
        "/api/v1/students/me/skills", headers=_auth_headers(token), json=payload
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/students/me/skills", headers=_auth_headers(token), json=payload
    )
    assert second.status_code == 409
    assert second.json()["error_code"] == "SKILL_ALREADY_ADDED"


async def test_add_nonexistent_skill_rejected(client):
    token = await _register_and_login(client, "bad-skill-id@example.com")
    resp = await client.post(
        "/api/v1/students/me/skills",
        headers=_auth_headers(token),
        json={"skill_id": 999999, "proficiency": "beginner"},
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "SKILL_NOT_FOUND"


async def test_add_invalid_proficiency_rejected(client, db_session):
    skill = await _create_skill(db_session, "Invalid-Prof-Python")
    token = await _register_and_login(client, "bad-proficiency@example.com")
    resp = await client.post(
        "/api/v1/students/me/skills",
        headers=_auth_headers(token),
        json={"skill_id": skill.id, "proficiency": "godlike"},
    )
    assert resp.status_code == 422


async def test_expert_proficiency_rejected(client, db_session):
    """
    Frontend contract only defines three levels — Beginner,
    Intermediate, Advanced. `expert` was removed from the backend
    enum (see the corrective migration) and must now be rejected the
    same as any other unrecognized value.
    """
    skill = await _create_skill(db_session, "Expert-Rejected-Python")
    token = await _register_and_login(client, "expert-rejected@example.com")
    resp = await client.post(
        "/api/v1/students/me/skills",
        headers=_auth_headers(token),
        json={"skill_id": skill.id, "proficiency": "expert"},
    )
    assert resp.status_code == 422


@pytest.mark.parametrize("proficiency", ["beginner", "intermediate", "advanced"])
async def test_each_valid_proficiency_accepted(client, db_session, proficiency):
    skill = await _create_skill(db_session, f"Valid-Prof-{proficiency}")
    token = await _register_and_login(client, f"valid-prof-{proficiency}@example.com")
    resp = await client.post(
        "/api/v1/students/me/skills",
        headers=_auth_headers(token),
        json={"skill_id": skill.id, "proficiency": proficiency},
    )
    assert resp.status_code == 201
    assert resp.json()["proficiency"] == proficiency


# --- PATCH /students/me/skills/{skill_id} ----------------------------------

async def test_update_skill_proficiency(client, db_session):
    skill = await _create_skill(db_session, "Update-Test-Python")
    token = await _register_and_login(client, "update-skill@example.com")
    await client.post(
        "/api/v1/students/me/skills",
        headers=_auth_headers(token),
        json={"skill_id": skill.id, "proficiency": "beginner"},
    )

    resp = await client.patch(
        f"/api/v1/students/me/skills/{skill.id}",
        headers=_auth_headers(token),
        json={"proficiency": "advanced"},
    )
    assert resp.status_code == 200
    assert resp.json()["proficiency"] == "advanced"


async def test_update_proficiency_for_skill_not_owned_rejected(client, db_session):
    skill = await _create_skill(db_session, "Not-Owned-Test-Python")
    token = await _register_and_login(client, "not-owned-patch@example.com")

    resp = await client.patch(
        f"/api/v1/students/me/skills/{skill.id}",
        headers=_auth_headers(token),
        json={"proficiency": "advanced"},
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "STUDENT_SKILL_NOT_FOUND"


# --- DELETE /students/me/skills/{skill_id} ---------------------------------

async def test_remove_skill(client, db_session):
    skill = await _create_skill(db_session, "Remove-Test-Python")
    token = await _register_and_login(client, "remove-skill@example.com")
    await client.post(
        "/api/v1/students/me/skills",
        headers=_auth_headers(token),
        json={"skill_id": skill.id, "proficiency": "beginner"},
    )

    resp = await client.delete(
        f"/api/v1/students/me/skills/{skill.id}", headers=_auth_headers(token)
    )
    assert resp.status_code == 204

    list_resp = await client.get("/api/v1/students/me/skills", headers=_auth_headers(token))
    assert list_resp.json() == []


async def test_remove_skill_not_owned_rejected(client, db_session):
    skill = await _create_skill(db_session, "Remove-Not-Owned-Test-Python")
    token = await _register_and_login(client, "remove-not-owned@example.com")

    resp = await client.delete(
        f"/api/v1/students/me/skills/{skill.id}", headers=_auth_headers(token)
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "STUDENT_SKILL_NOT_FOUND"


# --- Ownership -------------------------------------------------------------

async def test_student_cannot_see_or_modify_another_students_skills(client, db_session):
    skill = await _create_skill(db_session, "Isolation-Test-Python")

    token_a = await _register_and_login(client, "isolation-a@example.com")
    token_b = await _register_and_login(client, "isolation-b@example.com")

    # Student A adds the skill.
    await client.post(
        "/api/v1/students/me/skills",
        headers=_auth_headers(token_a),
        json={"skill_id": skill.id, "proficiency": "advanced"},
    )

    # Student B's own list must stay empty — not seeing A's skill.
    b_list = await client.get("/api/v1/students/me/skills", headers=_auth_headers(token_b))
    assert b_list.json() == []

    # Student B cannot PATCH the skill A owns (looks like "not found",
    # not another student's row — no cross-student leakage).
    patch_resp = await client.patch(
        f"/api/v1/students/me/skills/{skill.id}",
        headers=_auth_headers(token_b),
        json={"proficiency": "advanced"},
    )
    assert patch_resp.status_code == 404
    assert patch_resp.json()["error_code"] == "STUDENT_SKILL_NOT_FOUND"

    # Nor can B delete it.
    delete_resp = await client.delete(
        f"/api/v1/students/me/skills/{skill.id}", headers=_auth_headers(token_b)
    )
    assert delete_resp.status_code == 404

    # A's own skill is untouched by B's failed attempts.
    a_list = await client.get("/api/v1/students/me/skills", headers=_auth_headers(token_a))
    assert len(a_list.json()) == 1


# --- Authorization (role) ---------------------------------------------------

async def test_admin_cannot_use_student_skill_endpoints(client, db_session, user_repo):
    token = await _register_and_login(client, "admin-blocked@example.com")
    user = await user_repo.get_by_email("admin-blocked@example.com")
    user.role = RoleEnum.ADMIN
    await db_session.commit()

    # Re-login to get a fresh token (role is embedded as a convenience
    # claim at issue time in this codebase's JWT — a fresh token
    # reflects the DB update just made).
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin-blocked@example.com", "password": "SecurePass123"},
    )
    admin_token = admin_login.json()["access_token"]

    catalog_resp = await client.get("/api/v1/skills", headers=_auth_headers(admin_token))
    assert catalog_resp.status_code == 403
    assert catalog_resp.json()["error_code"] == "INSUFFICIENT_ROLE"

    my_skills_resp = await client.get(
        "/api/v1/students/me/skills", headers=_auth_headers(admin_token)
    )
    assert my_skills_resp.status_code == 403

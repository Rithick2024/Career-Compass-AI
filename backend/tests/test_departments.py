"""
Tests for Department management (Staff CRUD, status toggle, student active-only reading, and student validation).
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


async def _get_staff_headers(client, db_session, user_repo, email: str) -> dict:
    token = await _register_and_login(client, email)
    user = await user_repo.get_by_email(email)
    user.role = RoleEnum.STAFF
    await db_session.commit()

    staff_login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123"},
    )
    return _auth_headers(staff_login.json()["access_token"])


async def test_staff_department_crud(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "dept-staff-1@example.com")

    # 1. Staff list departments
    list_res = await client.get("/api/v1/staff/departments", headers=staff_headers)
    assert list_res.status_code == 200

    # 2. Staff create department
    create_res = await client.post(
        "/api/v1/staff/departments",
        headers=staff_headers,
        json={"name": " Data Science & Analytics "},
    )
    assert create_res.status_code == 201
    created_dept = create_res.json()
    assert created_dept["name"] == "Data Science & Analytics"
    assert created_dept["is_active"] is True
    dept_id = created_dept["id"]

    # 3. Staff update department name
    update_res = await client.patch(
        f"/api/v1/staff/departments/{dept_id}",
        headers=staff_headers,
        json={"name": "Data Science and AI"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Data Science and AI"

    # 4. Staff deactivate department
    deactivate_res = await client.patch(
        f"/api/v1/staff/departments/{dept_id}/status",
        headers=staff_headers,
        json={"is_active": False},
    )
    assert deactivate_res.status_code == 200
    assert deactivate_res.json()["is_active"] is False

    # 5. Staff reactivate department
    reactivate_res = await client.patch(
        f"/api/v1/staff/departments/{dept_id}/status",
        headers=staff_headers,
        json={"is_active": True},
    )
    assert reactivate_res.status_code == 200
    assert reactivate_res.json()["is_active"] is True


async def test_department_validation_rules(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "dept-staff-2@example.com")

    # Empty name rejection
    res = await client.post(
        "/api/v1/staff/departments",
        headers=staff_headers,
        json={"name": "   "},
    )
    assert res.status_code == 422

    # Create a department
    await client.post(
        "/api/v1/staff/departments",
        headers=staff_headers,
        json={"name": "Cyber Security"},
    )

    # Duplicate name rejection
    dup_res = await client.post(
        "/api/v1/staff/departments",
        headers=staff_headers,
        json={"name": "Cyber Security"},
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error_code"] == "DEPARTMENT_ALREADY_EXISTS"


async def test_student_department_access_and_active_filtering(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "dept-staff-3@example.com")
    student_token = await _register_and_login(client, "dept-student@example.com")
    student_headers = _auth_headers(student_token)

    # Create a department
    created = await client.post(
        "/api/v1/staff/departments",
        headers=staff_headers,
        json={"name": "Active Information Tech"},
    )
    assert created.status_code == 201
    active_dept_id = created.json()["id"]

    # Student reads active departments
    res = await client.get("/api/v1/departments", headers=student_headers)
    assert res.status_code == 200
    active_depts = res.json()
    assert len(active_depts) > 0
    assert any(d["id"] == active_dept_id for d in active_depts)

    # Create and deactivate another department
    created_deact = await client.post(
        "/api/v1/staff/departments",
        headers=staff_headers,
        json={"name": "Deactivated Dept"},
    )
    dept_id = created_deact.json()["id"]

    await client.patch(
        f"/api/v1/staff/departments/{dept_id}/status",
        headers=staff_headers,
        json={"is_active": False},
    )

    # Student active departments list should not contain deactivated department
    res_after = await client.get("/api/v1/departments", headers=student_headers)
    dept_ids = [d["id"] for d in res_after.json()]
    assert dept_id not in dept_ids

    # Student cannot select inactive department in profile update
    profile_update = await client.patch(
        "/api/v1/students/me",
        headers=student_headers,
        json={"department_id": dept_id},
    )
    assert profile_update.status_code == 422
    assert profile_update.json()["error_code"] == "INVALID_DEPARTMENT"

    # Student cannot create department
    create_try = await client.post(
        "/api/v1/staff/departments",
        headers=student_headers,
        json={"name": "Hacker Dept"},
    )
    assert create_try.status_code == 403

    # Student cannot update department
    update_try = await client.patch(
        f"/api/v1/staff/departments/{dept_id}",
        headers=student_headers,
        json={"name": "Hacked Name"},
    )
    assert update_try.status_code == 403

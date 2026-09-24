"""
Tests for Staff Company Management module.
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


async def test_staff_company_crud(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "comp-staff-1@example.com")

    # 1. Staff list companies (empty or initial)
    list_res = await client.get("/api/v1/staff/companies", headers=staff_headers)
    assert list_res.status_code == 200
    assert isinstance(list_res.json(), list)

    # 2. Staff create company
    create_res = await client.post(
        "/api/v1/staff/companies",
        headers=staff_headers,
        json={
            "name": " Acme Corporation ",
            "description": "Leading tech company",
            "industry": "Software Services",
            "website": "https://acme.example.com",
            "location": "Bangalore",
        },
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["name"] == "Acme Corporation"
    assert created["industry"] == "Software Services"
    assert created["website"] == "https://acme.example.com/" or created["website"] == "https://acme.example.com"
    assert created["location"] == "Bangalore"
    assert created["is_active"] is True
    company_id = created["id"]

    # 3. Staff get company by ID
    get_res = await client.get(f"/api/v1/staff/companies/{company_id}", headers=staff_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == company_id

    # 4. Staff update company
    update_res = await client.patch(
        f"/api/v1/staff/companies/{company_id}",
        headers=staff_headers,
        json={
            "name": "Acme Global Solutions",
            "location": "Bangalore / Remote",
        },
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Acme Global Solutions"
    assert update_res.json()["location"] == "Bangalore / Remote"

    # 5. Staff activate/deactivate company
    deactivate_res = await client.patch(
        f"/api/v1/staff/companies/{company_id}/status",
        headers=staff_headers,
        json={"is_active": False},
    )
    assert deactivate_res.status_code == 200
    assert deactivate_res.json()["is_active"] is False

    reactivate_res = await client.patch(
        f"/api/v1/staff/companies/{company_id}/status",
        headers=staff_headers,
        json={"is_active": True},
    )
    assert reactivate_res.status_code == 200
    assert reactivate_res.json()["is_active"] is True


async def test_duplicate_company_name_rejected(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "comp-staff-2@example.com")

    # Create company
    res = await client.post(
        "/api/v1/staff/companies",
        headers=staff_headers,
        json={"name": "Tech Corp"},
    )
    assert res.status_code == 201

    # Duplicate create rejected
    dup_res = await client.post(
        "/api/v1/staff/companies",
        headers=staff_headers,
        json={"name": "Tech Corp"},
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error_code"] == "COMPANY_ALREADY_EXISTS"


async def test_invalid_website_rejected(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "comp-staff-3@example.com")

    # Invalid URL scheme or format
    res = await client.post(
        "/api/v1/staff/companies",
        headers=staff_headers,
        json={"name": "Invalid Web Corp", "website": "not-a-valid-url"},
    )
    assert res.status_code == 422


async def test_company_search_and_status_filtering(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "comp-staff-4@example.com")

    # Create 3 distinct companies
    await client.post(
        "/api/v1/staff/companies",
        headers=staff_headers,
        json={"name": "Alpha FinTech", "industry": "Finance", "location": "Mumbai"},
    )
    beta = await client.post(
        "/api/v1/staff/companies",
        headers=staff_headers,
        json={"name": "Beta Health Tech", "industry": "Healthcare", "location": "Pune"},
    )
    beta_id = beta.json()["id"]

    # Deactivate Beta
    await client.patch(
        f"/api/v1/staff/companies/{beta_id}/status",
        headers=staff_headers,
        json={"is_active": False},
    )

    # 8. Search works
    search_res = await client.get("/api/v1/staff/companies?search=Health", headers=staff_headers)
    assert search_res.status_code == 200
    search_items = search_res.json()
    assert any(c["id"] == beta_id for c in search_items)
    assert not any(c["name"] == "Alpha FinTech" for c in search_items)

    # 9. Active/inactive filtering works
    active_res = await client.get("/api/v1/staff/companies?status=active", headers=staff_headers)
    assert active_res.status_code == 200
    assert all(c["is_active"] is True for c in active_res.json())

    inactive_res = await client.get("/api/v1/staff/companies?status=inactive", headers=staff_headers)
    assert inactive_res.status_code == 200
    assert all(c["is_active"] is False for c in inactive_res.json())
    assert any(c["id"] == beta_id for c in inactive_res.json())


async def test_student_cannot_access_staff_company_endpoints(client, db_session, user_repo):
    student_token = await _register_and_login(client, "comp-student@example.com")
    student_headers = _auth_headers(student_token)

    # 10. Student cannot access staff company endpoints
    res_list = await client.get("/api/v1/staff/companies", headers=student_headers)
    assert res_list.status_code == 403

    res_create = await client.post(
        "/api/v1/staff/companies",
        headers=student_headers,
        json={"name": "Student Hack Corp"},
    )
    assert res_create.status_code == 403


async def test_non_existent_company_returns_404(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "comp-staff-5@example.com")

    # 11. Non-existent company returns 404
    res = await client.get("/api/v1/staff/companies/99999", headers=staff_headers)
    assert res.status_code == 404
    assert res.json()["error_code"] == "COMPANY_NOT_FOUND"


async def test_no_delete_endpoint_exists(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "comp-staff-6@example.com")

    # Create company
    created = await client.post(
        "/api/v1/staff/companies",
        headers=staff_headers,
        json={"name": "Permanent Company"},
    )
    cid = created.json()["id"]

    # 12. No delete endpoint exists (returns 405 Method Not Allowed)
    del_res = await client.delete(f"/api/v1/staff/companies/{cid}", headers=staff_headers)
    assert del_res.status_code == 405

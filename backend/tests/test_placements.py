import pytest
from httpx import AsyncClient
from app.modules.applications.models import ApplicationStatus

pytestmark = pytest.mark.asyncio(loop_scope="session")

async def _register_and_login(client: AsyncClient, email: str, password: str = "SecurePass123") -> tuple[str, dict]:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return token, headers

async def _get_staff_headers(client: AsyncClient, db_session, user_repo, email: str) -> dict:
    from app.shared.enums import RoleEnum
    token, _ = await _register_and_login(client, email)
    user = await user_repo.get_by_email(email)
    user.role = RoleEnum.STAFF
    await db_session.commit()

    staff_login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123"},
    )
    return {"Authorization": f"Bearer {staff_login.json()['access_token']}"}

import uuid

async def setup_test_data(client, staff_headers, student_headers):
    uid = uuid.uuid4().hex[:6]
    # Company
    c_res = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": f"Placement Corp {uid}"})
    c_id = c_res.json()["id"]

    # Job
    j_res = await client.post("/api/v1/staff/jobs", headers=staff_headers, json={
        "company_id": c_id,
        "title": "Placement Dev"
    })
    j_id = j_res.json()["id"]

    # Resume
    res_resume = await client.post(
        "/api/v1/students/me/resumes",
        headers=student_headers,
        data={"title": "Plc Resume", "description": "Dev"},
        files={"file": ("resume.pdf", b"%PDF-1.4 sample pdf content for unit testing.", "application/pdf")}
    )
    resume_id = res_resume.json()["id"]

    # Application
    app_res = await client.post("/api/v1/student/applications", headers=student_headers, json={
        "job_id": j_id,
        "resume_id": resume_id
    })
    app_id = app_res.json()["id"]

    return app_id, j_id


async def test_placement_lifecycle_and_constraints(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-plc@example.com")
    _, student_headers = await _register_and_login(client, "student-plc@example.com")
    
    app_id, j_id = await setup_test_data(client, staff_headers, student_headers)

    # 1. Staff creates placement on PENDING application (fails)
    payload = {
        "application_id": app_id,
        "final_package_ctc": 7.5,
        "placement_date": "2026-10-15",
        "offer_accepted": True
    }
    p_fail = await client.post("/api/v1/staff/placements", headers=staff_headers, json=payload)
    assert p_fail.status_code == 400

    # Move application to Offered
    await client.patch(
        f"/api/v1/staff/applications/{app_id}/status",
        headers=staff_headers,
        json={"status": "Offered"}
    )

    # 2. Staff creates placement successfully
    p_res = await client.post("/api/v1/staff/placements", headers=staff_headers, json=payload)
    assert p_res.status_code == 200
    p_id = p_res.json()["placement"]["id"]

    # 3. Duplicate placement fails
    p_dup = await client.post("/api/v1/staff/placements", headers=staff_headers, json=payload)
    assert p_dup.status_code == 409

    # 4. Student can list own placements
    s_list = await client.get("/api/v1/student/placements", headers=student_headers)
    assert s_list.status_code == 200
    assert len(s_list.json()) == 1

    # 5. Cannot move Application backward once placement exists
    app_bwd = await client.patch(
        f"/api/v1/staff/applications/{app_id}/status",
        headers=staff_headers,
        json={"status": "Rejected"}
    )
    assert app_bwd.status_code == 400

    # 6. Student cannot have two accepted placements
    app_id2, j_id2 = await setup_test_data(client, staff_headers, student_headers)
    await client.patch(
        f"/api/v1/staff/applications/{app_id2}/status",
        headers=staff_headers,
        json={"status": "Offered"}
    )

    payload2 = {
        "application_id": app_id2,
        "final_package_ctc": 8.0,
        "placement_date": "2026-11-01",
        "offer_accepted": True
    }
    p_fail2 = await client.post("/api/v1/staff/placements", headers=staff_headers, json=payload2)
    assert p_fail2.status_code == 409

    # Update first to not accepted, then create second
    await client.patch(
        f"/api/v1/staff/placements/{p_id}",
        headers=staff_headers,
        json={"offer_accepted": False}
    )

    p_res2 = await client.post("/api/v1/staff/placements", headers=staff_headers, json=payload2)
    assert p_res2.status_code == 200

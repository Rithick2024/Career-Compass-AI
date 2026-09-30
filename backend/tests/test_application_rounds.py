import pytest
from httpx import AsyncClient
from datetime import datetime, timezone

from app.modules.applications.models import ApplicationStatus
from app.modules.application_rounds.models import RoundType, RoundStatus, RoundResult


async def _register_and_login(client: AsyncClient, email: str, role: str = "student"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password", "role": role}
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password"}
    )
    return login.json()["access_token"], {"Authorization": f"Bearer {login.json()['access_token']}"}

async def _get_staff_headers(client, db_session, user_repo, email: str) -> dict:
    from app.shared.enums import RoleEnum
    await client.post("/api/v1/auth/register", json={"email": email, "password": "password"})
    user = await user_repo.get_by_email(email)
    user.role = RoleEnum.STAFF
    await db_session.commit()

    staff_login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password"},
    )
    return {"Authorization": f"Bearer {staff_login.json()['access_token']}"}


import uuid
async def setup_test_data(client, staff_headers, student_headers):
    uid = uuid.uuid4().hex[:6]
    
    # Company
    c_res = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": f"Round Corp {uid}"})
    c_id = c_res.json()["id"]

    # Job
    j_res = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"title": "Round Engineer", "company_id": c_id}
    )
    j_id = j_res.json()["id"]

    # Resume
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
    r_res = await client.post(
        "/api/v1/students/me/resumes",
        headers=student_headers,
        data={"title": "My Resume"},
        files={"file": ("r.pdf", pdf_content, "application/pdf")}
    )
    r_id = r_res.json()["id"]

    # Application
    app_res = await client.post(
        "/api/v1/student/applications",
        headers=student_headers,
        json={"job_id": j_id, "resume_id": r_id}
    )
    return app_res.json()["id"], j_id


@pytest.mark.asyncio(loop_scope="session")
async def test_application_rounds_lifecycle(client: AsyncClient, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-rounds@example.com")
    _, student_headers = await _register_and_login(client, "student-rounds@example.com")

    app_id, _ = await setup_test_data(client, staff_headers, student_headers)

    # 1. Staff creates a round
    round_payload = {
        "round_number": 1,
        "round_type": "Online Assessment",
        "title": "Initial Screen",
        "status": "Scheduled",
        "scheduled_at": "2026-10-15T10:00:00Z",
    }
    r1_res = await client.post(f"/api/v1/staff/applications/{app_id}/rounds", headers=staff_headers, json=round_payload)
    assert r1_res.status_code == 201
    r1_id = r1_res.json()["id"]

    # 2. Staff cannot create duplicate round number
    dup_res = await client.post(f"/api/v1/staff/applications/{app_id}/rounds", headers=staff_headers, json=round_payload)
    assert dup_res.status_code == 409

    # 3. Staff updates round to completed with pass result
    upd_res = await client.patch(
        f"/api/v1/staff/applications/{app_id}/rounds/{r1_id}",
        headers=staff_headers,
        json={"status": "Completed", "result": "Passed"}
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["result"] == "Passed"
    assert upd_res.json()["completed_at"] is not None

    # 4. Student can view their rounds
    s_list_res = await client.get(f"/api/v1/student/applications/{app_id}/rounds", headers=student_headers)
    assert s_list_res.status_code == 200
    assert len(s_list_res.json()) == 1
    
    # 5. Student cannot access another student's application rounds
    _, student2_headers = await _register_and_login(client, "student2-rounds@example.com")
    s2_res = await client.get(f"/api/v1/student/applications/{app_id}/rounds", headers=student2_headers)
    assert s2_res.status_code == 404

    # 6. Sensible status validation (Cannot be Not Started and Passed)
    bad_upd_res = await client.patch(
        f"/api/v1/staff/applications/{app_id}/rounds/{r1_id}",
        headers=staff_headers,
        json={"status": "Scheduled"}
    )
    # Because result is currently "Passed", updating to "Scheduled" without resetting result should fail
    assert bad_upd_res.status_code == 400

    # 7. Staff creates a second round
    r2_payload = {
        "round_number": 2,
        "round_type": "Technical Interview",
        "available_from": "2026-10-16T10:00:00Z",
        "status": "Completed",
        "result": "Failed"
    }
    r2_res = await client.post(f"/api/v1/staff/applications/{app_id}/rounds", headers=staff_headers, json=r2_payload)
    assert r2_res.status_code == 201

    # Application status should now be Interview after round creation
    app_res = await client.get(f"/api/v1/staff/applications/{app_id}", headers=staff_headers)
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "Interview"

    # List rounds orders by round number
    list_res = await client.get(f"/api/v1/staff/applications/{app_id}/rounds", headers=staff_headers)
    rounds = list_res.json()
    assert len(rounds) == 2
    assert rounds[0]["round_number"] == 1
    assert rounds[1]["round_number"] == 2

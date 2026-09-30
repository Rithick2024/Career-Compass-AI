import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy import select

from app.modules.applications.models import Application, ApplicationStatus
from app.shared.enums import RoleEnum
from app.modules.resumes.models import Resume

pytestmark = pytest.mark.asyncio(loop_scope="session")

async def _register_and_login(client, email: str, password: str = "SecurePass123") -> tuple[str, dict]:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return token, headers

async def _get_staff_headers(client, db_session, user_repo, email: str) -> dict:
    token, _ = await _register_and_login(client, email)
    user = await user_repo.get_by_email(email)
    user.role = RoleEnum.STAFF
    await db_session.commit()

    staff_login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123"},
    )
    return {"Authorization": f"Bearer {staff_login.json()['access_token']}"}


async def test_application_lifecycle_and_constraints(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-app@example.com")
    
    # 1. Setup Student, Resume, Company, Job
    _, student_headers = await _register_and_login(client, "student-app@example.com")
    
    # Create resume
    res_resume = await client.post(
        "/api/v1/students/me/resumes",
        headers=student_headers,
        data={
            "title": "My Dev Resume",
            "description": "Dev stuff"
        },
        files={"file": ("resume.pdf", b"%PDF-1.4 sample pdf content for unit testing.", "application/pdf")}
    )
    resume_id = res_resume.json()["id"]

    # Create company
    c_res = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": "App Corp"})
    c_id = c_res.json()["id"]

    # Create job
    j_res = await client.post("/api/v1/staff/jobs", headers=staff_headers, json={
        "company_id": c_id,
        "title": "App Developer"
    })
    j_id = j_res.json()["id"]

    # 2. Student successfully applies with own resume
    app_res = await client.post("/api/v1/student/applications", headers=student_headers, json={
        "job_id": j_id,
        "resume_id": resume_id
    })
    assert app_res.status_code == 201
    app_id = app_res.json()["id"]
    assert app_res.json()["status"] == "Pending"

    # 3. Duplicate application rejected
    app_res2 = await client.post("/api/v1/student/applications", headers=student_headers, json={
        "job_id": j_id,
        "resume_id": resume_id
    })
    assert app_res2.status_code == 409
    assert app_res2.json()["error_code"] == "DUPLICATE_APPLICATION"

    # 4. Student can list own applications
    list_res = await client.get("/api/v1/student/applications", headers=student_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["id"] == app_id

    # 5. Staff can list applications
    staff_list_res = await client.get("/api/v1/staff/applications", headers=staff_headers)
    assert staff_list_res.status_code == 200
    assert any(a["id"] == app_id for a in staff_list_res.json())

    # 6. Staff can view application detail
    staff_detail = await client.get(f"/api/v1/staff/applications/{app_id}", headers=staff_headers)
    assert staff_detail.status_code == 200
    assert staff_detail.json()["job_title"] == "App Developer"

    # 7. Staff can update status
    update_res = await client.patch(
        f"/api/v1/staff/applications/{app_id}/status",
        headers=staff_headers,
        json={"status": "Reviewing"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Reviewing"

    # 8. Student can withdraw allowed application
    withdraw_res = await client.patch(
        f"/api/v1/student/applications/{app_id}/withdraw",
        headers=student_headers
    )
    assert withdraw_res.status_code == 200
    assert withdraw_res.json()["status"] == "Withdrawn"

    # 9. Withdrawn application is not deleted (still in list)
    list_res2 = await client.get("/api/v1/student/applications", headers=student_headers)
    assert list_res2.json()[0]["status"] == "Withdrawn"

    # 10. Resume referenced by application cannot be deleted
    # Wait, Resume deletion is currently not blocked at application level explicitly, but the DB ON DELETE RESTRICT will raise IntegrityError.
    # Let's check how Resume deletion handles it. It might return 500 if unhandled, or we should handle it in ResumeService.
    # Let's write the test and see if it fails.
    del_res = await client.delete(f"/api/v1/students/me/resumes/{resume_id}", headers=student_headers)
    # This might return 500 if IntegrityError is unhandled. We need to handle it.
    assert del_res.status_code == 409

    # 11. Student cannot access staff application endpoints
    s_staff_res = await client.get("/api/v1/staff/applications", headers=student_headers)
    assert s_staff_res.status_code == 403


async def test_application_eligibility_and_boundaries(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-app2@example.com")
    
    # Create company
    c_res = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": "App Corp 2"})
    c_id = c_res.json()["id"]

    # Create dept
    d_res = await client.post("/api/v1/staff/departments", headers=staff_headers, json={"name": "Science"})
    d_id = d_res.json()["id"]

    # Create restricted job
    j_res = await client.post("/api/v1/staff/jobs", headers=staff_headers, json={
        "company_id": c_id,
        "title": "Strict Job",
        "min_cgpa": 8.0,
        "eligible_department_ids": [d_id]
    })
    j_id = j_res.json()["id"]

    _, s1_headers = await _register_and_login(client, "student-fail@example.com")
    res_resume = await client.post(
        "/api/v1/students/me/resumes",
        headers=s1_headers,
        data={"title": "R1", "description": "D1"},
        files={"file": ("resume.pdf", b"%PDF-1.4 sample pdf content for unit testing.", "application/pdf")}
    )
    r1_id = res_resume.json()["id"]

    # Student without required department rejected
    app1 = await client.post("/api/v1/student/applications", headers=s1_headers, json={
        "job_id": j_id,
        "resume_id": r1_id
    })
    assert app1.status_code == 400
    assert app1.json()["error_code"] == "INELIGIBLE_DEPARTMENT"

    # Set department but insufficient CGPA
    await client.patch("/api/v1/students/me", headers=s1_headers, json={"department_id": d_id, "cgpa": 7.0})
    app2 = await client.post("/api/v1/student/applications", headers=s1_headers, json={
        "job_id": j_id,
        "resume_id": r1_id
    })
    assert app2.status_code == 400
    assert app2.json()["error_code"] == "INELIGIBLE_CGPA"

    # Inactive job rejected
    j_inactive = await client.post("/api/v1/staff/jobs", headers=staff_headers, json={
        "company_id": c_id,
        "title": "Inactive Job"
    })
    j_inactive_id = j_inactive.json()["id"]
    await client.patch(f"/api/v1/staff/jobs/{j_inactive_id}/status", headers=staff_headers, json={"is_active": False})

    app3 = await client.post("/api/v1/student/applications", headers=s1_headers, json={
        "job_id": j_inactive_id,
        "resume_id": r1_id
    })
    assert app3.status_code == 400
    assert app3.json()["error_code"] == "JOB_UNAVAILABLE"

    # Student using another student's resume rejected
    _, s2_headers = await _register_and_login(client, "student-other@example.com")
    res_resume2 = await client.post(
        "/api/v1/students/me/resumes",
        headers=s2_headers,
        data={"title": "R2", "description": "D2"},
        files={"file": ("resume.pdf", b"%PDF-1.4 sample pdf content for unit testing.", "application/pdf")}
    )
    r2_id = res_resume2.json()["id"]

    # Create job without restriction
    j_open = await client.post("/api/v1/staff/jobs", headers=staff_headers, json={
        "company_id": c_id,
        "title": "Open Job"
    })
    j_open_id = j_open.json()["id"]

    app4 = await client.post("/api/v1/student/applications", headers=s1_headers, json={
        "job_id": j_open_id,
        "resume_id": r2_id
    })
    assert app4.status_code == 404
    assert app4.json()["error_code"] == "RESUME_NOT_FOUND"

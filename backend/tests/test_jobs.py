"""
Tests for Staff Job Management module.
"""

from datetime import datetime, timedelta, timezone
import pytest

from app.shared.enums import RoleEnum

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


async def test_staff_job_crud_and_atomic_creation(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "job-staff-1@example.com")

    # 1. Create company, department, and skill
    comp_res = await client.post(
        "/api/v1/staff/companies",
        headers=staff_headers,
        json={"name": "Tech Corp One", "industry": "IT"},
    )
    assert comp_res.status_code == 201
    comp_id = comp_res.json()["id"]

    dept_res = await client.post(
        "/api/v1/staff/departments",
        headers=staff_headers,
        json={"name": "Computer Science"},
    )
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["id"]

    skill_res = await client.post(
        "/api/v1/staff/skills",
        headers=staff_headers,
        json={"name": "FastAPI", "category": "Framework"},
    )
    assert skill_res.status_code == 201
    skill_id = skill_res.json()["id"]

    # --- 1..4. Staff create a Job atomically with required skills & eligible departments ---
    future_deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    create_res = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={
            "company_id": comp_id,
            "title": " Backend Engineer ",
            "description": "Develop high scale python services",
            "role_category": "Software Engineering",
            "location": "Bangalore",
            "employment_type": "Full-time",
            "ctc_lpa": 14.50,
            "min_cgpa": 7.50,
            "deadline": future_deadline,
            "required_skills": [
                {"skill_id": skill_id, "min_proficiency": "intermediate"}
            ],
            "eligible_department_ids": [dept_id],
        },
    )
    assert create_res.status_code == 201
    created_job = create_res.json()
    assert created_job["title"] == "Backend Engineer"
    assert created_job["company_id"] == comp_id
    assert created_job["company"]["name"] == "Tech Corp One"
    assert len(created_job["required_skills"]) == 1
    assert created_job["required_skills"][0]["skill_name"] == "FastAPI"
    assert created_job["required_skills"][0]["min_proficiency"] == "intermediate"
    assert len(created_job["eligible_departments"]) == 1
    assert created_job["eligible_departments"][0]["department_name"] == "Computer Science"
    assert created_job["is_active"] is True
    assert created_job["is_expired"] is False
    job_id = created_job["id"]

    # --- 16. Staff retrieve Job detail ---
    get_res = await client.get(f"/api/v1/staff/jobs/{job_id}", headers=staff_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == job_id

    # --- 17..19. Staff update Job fields, skills, departments ---
    update_res = await client.patch(
        f"/api/v1/staff/jobs/{job_id}",
        headers=staff_headers,
        json={
            "title": "Senior Backend Engineer",
            "ctc_lpa": 18.00,
            "required_skills": [
                {"skill_id": skill_id, "min_proficiency": "advanced"}
            ],
        },
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Senior Backend Engineer"
    assert update_res.json()["ctc_lpa"] == 18.00
    assert update_res.json()["required_skills"][0]["min_proficiency"] == "advanced"

    # --- 20. Staff toggle Job status ---
    deact_res = await client.patch(
        f"/api/v1/staff/jobs/{job_id}/status",
        headers=staff_headers,
        json={"is_active": False},
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["is_active"] is False


async def test_job_validation_rules(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "job-staff-val@example.com")

    # Create active & inactive companies
    c_act = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": "Active Comp"})
    c_act_id = c_act.json()["id"]

    c_inact = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": "Inactive Comp"})
    c_inact_id = c_inact.json()["id"]
    await client.patch(f"/api/v1/staff/companies/{c_inact_id}/status", headers=staff_headers, json={"is_active": False})

    # --- 5. Inactive Company rejects new Job ---
    res_inact = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"company_id": c_inact_id, "title": "Dev"},
    )
    assert res_inact.status_code == 422
    assert res_inact.json()["error_code"] == "INVALID_COMPANY"

    # --- 6. Non-existent Company returns error ---
    res_no_comp = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"company_id": 99999, "title": "Dev"},
    )
    assert res_no_comp.status_code == 404

    # --- 23. Invalid CGPA rejected ---
    res_cgpa = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"company_id": c_act_id, "title": "Dev", "min_cgpa": 12.0},
    )
    assert res_cgpa.status_code == 422

    # --- 24. Negative CTC rejected ---
    res_ctc = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"company_id": c_act_id, "title": "Dev", "ctc_lpa": -5.0},
    )
    assert res_ctc.status_code == 422

    # --- 25. Invalid skill ID rejected ---
    res_sk = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"company_id": c_act_id, "title": "Dev", "required_skills": [{"skill_id": 99999}]},
    )
    assert res_sk.status_code == 422

    # --- 26. Invalid department ID rejected ---
    res_dept = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"company_id": c_act_id, "title": "Dev", "eligible_department_ids": [99999]},
    )
    assert res_dept.status_code == 422


async def test_job_search_filters_and_expired(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "job-staff-filter@example.com")

    comp_a = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": "Alpha Ltd"})
    comp_a_id = comp_a.json()["id"]

    comp_b = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": "Beta Inc"})
    comp_b_id = comp_b.json()["id"]

    dept = await client.post("/api/v1/staff/departments", headers=staff_headers, json={"name": "Mechanical Engineering"})
    dept_id = dept.json()["id"]

    # Active Job
    j1 = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"company_id": comp_a_id, "title": "Full Stack Lead", "location": "Chennai", "eligible_department_ids": [dept_id]},
    )
    j1_id = j1.json()["id"]

    # Deactivated Job
    j2 = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"company_id": comp_b_id, "title": "QA Engineer", "location": "Hyderabad"},
    )
    j2_id = j2.json()["id"]
    await client.patch(f"/api/v1/staff/jobs/{j2_id}/status", headers=staff_headers, json={"is_active": False})

    # --- 7. Staff list jobs ---
    list_res = await client.get("/api/v1/staff/jobs", headers=staff_headers)
    assert list_res.status_code == 200

    # --- 8..10. Search by title, company, location ---
    s_title = await client.get("/api/v1/staff/jobs?search=Full+Stack", headers=staff_headers)
    assert any(j["id"] == j1_id for j in s_title.json())

    s_comp = await client.get("/api/v1/staff/jobs?search=Alpha", headers=staff_headers)
    assert any(j["id"] == j1_id for j in s_comp.json())

    s_loc = await client.get("/api/v1/staff/jobs?search=Chennai", headers=staff_headers)
    assert any(j["id"] == j1_id for j in s_loc.json())

    # --- 11 & 12. Filter by Company and Department ---
    f_comp = await client.get(f"/api/v1/staff/jobs?company_id={comp_a_id}", headers=staff_headers)
    assert all(j["company_id"] == comp_a_id for j in f_comp.json())

    f_dept = await client.get(f"/api/v1/staff/jobs?department_id={dept_id}", headers=staff_headers)
    assert any(j["id"] == j1_id for j in f_dept.json())

    # --- 13 & 14. Active and Inactive status filters ---
    f_act = await client.get("/api/v1/staff/jobs?status=active", headers=staff_headers)
    assert any(j["id"] == j1_id for j in f_act.json())
    assert not any(j["id"] == j2_id for j in f_act.json())

    f_inact = await client.get("/api/v1/staff/jobs?status=inactive", headers=staff_headers)
    assert any(j["id"] == j2_id for j in f_inact.json())


async def test_student_blocked_and_security(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "job-staff-sec@example.com")
    _, student_headers = await _register_and_login(client, "job-student-sec@example.com")

    # --- 27. Student cannot access staff job endpoints ---
    res_list = await client.get("/api/v1/staff/jobs", headers=student_headers)
    assert res_list.status_code == 403

    res_post = await client.post("/api/v1/staff/jobs", headers=student_headers, json={"company_id": 1, "title": "Hacker Job"})
    assert res_post.status_code == 403

    # --- 28. Non-existent Job returns 404 ---
    res_404 = await client.get("/api/v1/staff/jobs/99999", headers=staff_headers)
    assert res_404.status_code == 404
    assert res_404.json()["error_code"] == "JOB_NOT_FOUND"


async def test_historical_integrity_and_company_deactivation(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "job-hist@example.com")

    # Create company & job
    comp = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": "Legacy Corp"})
    comp_id = comp.json()["id"]

    job = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"company_id": comp_id, "title": "Legacy Job Opening"},
    )
    job_id = job.json()["id"]

    # Deactivate Company
    await client.patch(f"/api/v1/staff/companies/{comp_id}/status", headers=staff_headers, json={"is_active": False})

    # --- 29 & 30. Existing Job and historical relationships remain intact ---
    get_job = await client.get(f"/api/v1/staff/jobs/{job_id}", headers=staff_headers)
    assert get_job.status_code == 200
    assert get_job.json()["id"] == job_id
    assert get_job.json()["company"]["is_active"] is False

    # --- 31. Verify sensitive fields not exposed ---
    assert "password_hash" not in get_job.json()
    assert "file_path" not in get_job.json()

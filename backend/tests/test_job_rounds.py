import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient

from app.modules.application_rounds.models import (
    RoundType,
    ScheduleType,
    RoundStatus,
    RoundResult,
    StudentAttendance,
    StaffVerification,
)


async def _register_and_login(client: AsyncClient, email: str, role: str = "student"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password", "role": role},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password"},
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


async def setup_company_and_job(client, staff_headers):
    uid = uuid.uuid4().hex[:6]
    c_res = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": f"Round Test Tech {uid}"})
    c_id = c_res.json()["id"]

    j_res = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={
            "title": "Backend Architect",
            "company_id": c_id,
            "work_mode": "Remote",
        },
    )
    j_id = j_res.json()["id"]
    return c_id, j_id


async def upload_resume(client, student_headers):
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
    r_res = await client.post(
        "/api/v1/students/me/resumes",
        headers=student_headers,
        data={"title": "Primary Resume"},
        files={"file": ("resume.pdf", pdf_content, "application/pdf")},
    )
    return r_res.json()["id"]


@pytest.mark.asyncio(loop_scope="session")
async def test_job_rounds_crud_and_validation(client, db_session, user_repo):
    uid = uuid.uuid4().hex[:6]
    _, staff_h = await _register_and_login(client, f"staff_{uid}@test.com", "student")
    staff_h = await _get_staff_headers(client, db_session, user_repo, f"staff_{uid}@test.com")
    _, student_h = await _register_and_login(client, f"student_{uid}@test.com", "student")

    _, job_id = await setup_company_and_job(client, staff_h)

    # 1. Staff can create JobRound
    now = datetime.now(timezone.utc) + timedelta(days=1)
    now_str = now.isoformat()

    res = await client.post(
        f"/api/v1/staff/jobs/{job_id}/rounds",
        headers=staff_h,
        json={
            "round_number": 1,
            "round_type": RoundType.ONLINE_ASSESSMENT.value,
            "title": "OA Round",
            "schedule_type": "FIXED_TIME",
            "available_from": now_str,
            "duration_minutes": 90,
            "test_link": "https://test.com/oa1",
        },
    )
    assert res.status_code == 201, res.text
    r1_data = res.json()
    assert r1_data["round_number"] == 1
    assert r1_data["title"] == "OA Round"
    assert r1_data["job_id"] == job_id

    # 2. Student cannot create JobRound
    res_student = await client.post(
        f"/api/v1/staff/jobs/{job_id}/rounds",
        headers=student_h,
        json={
            "round_number": 2,
            "round_type": RoundType.TECHNICAL_INTERVIEW.value,
            "available_from": now_str,
        },
    )
    assert res_student.status_code == 403

    # 3. Duplicate round number rejected
    res_dup = await client.post(
        f"/api/v1/staff/jobs/{job_id}/rounds",
        headers=staff_h,
        json={
            "round_number": 1,
            "round_type": RoundType.CODING_TEST.value,
            "available_from": now_str,
        },
    )
    assert res_dup.status_code == 409

    # 4. Fixed time validation (available_until not allowed for FIXED_TIME)
    res_invalid_fixed = await client.post(
        f"/api/v1/staff/jobs/{job_id}/rounds",
        headers=staff_h,
        json={
            "round_number": 2,
            "round_type": RoundType.CODING_TEST.value,
            "schedule_type": "FIXED_TIME",
            "available_from": now_str,
            "available_until": (now + timedelta(hours=2)).isoformat(),
        },
    )
    assert res_invalid_fixed.status_code == 400

    # 5. Availability window validation (available_until required)
    res_window = await client.post(
        f"/api/v1/staff/jobs/{job_id}/rounds",
        headers=staff_h,
        json={
            "round_number": 2,
            "round_type": RoundType.CODING_TEST.value,
            "schedule_type": "AVAILABILITY_WINDOW",
            "available_from": now_str,
            "available_until": (now + timedelta(days=2)).isoformat(),
            "duration_minutes": 120,
        },
    )
    assert res_window.status_code == 201
    assert res_window.json()["schedule_type"] == "AVAILABILITY_WINDOW"

    # 6. Staff can list JobRounds
    list_res = await client.get(f"/api/v1/staff/jobs/{job_id}/rounds", headers=staff_h)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 2

    # 7. Staff can update JobRound
    r1_id = r1_data["id"]
    update_res = await client.patch(
        f"/api/v1/staff/jobs/{job_id}/rounds/{r1_id}",
        headers=staff_h,
        json={"title": "Updated OA Round"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated OA Round"


@pytest.mark.asyncio(loop_scope="session")
async def test_application_round_snapshot_and_isolation(client, db_session, user_repo):
    uid = uuid.uuid4().hex[:6]
    staff_h = await _get_staff_headers(client, db_session, user_repo, f"staff_snap_{uid}@test.com")
    _, student_a_h = await _register_and_login(client, f"student_a_{uid}@test.com", "student")
    _, student_b_h = await _register_and_login(client, f"student_b_{uid}@test.com", "student")

    company_id, job_id = await setup_company_and_job(client, staff_h)

    # 1. Student A applies to Job with 0 rounds
    resume_a_id = await upload_resume(client, student_a_h)
    app_zero_res = await client.post(
        "/api/v1/student/applications",
        headers=student_a_h,
        json={"job_id": job_id, "resume_id": resume_a_id},
    )
    assert app_zero_res.status_code == 201
    assert app_zero_res.json()["status"] == "Pending"

    # Verify student A has 0 application rounds
    app_zero_id = app_zero_res.json()["id"]
    rounds_a_res = await client.get(f"/api/v1/student/applications/{app_zero_id}/rounds", headers=student_a_h)
    assert len(rounds_a_res.json()) == 0

    # Configure 2 JobRounds on the Job
    now = datetime.now(timezone.utc) + timedelta(days=2)
    now_str = now.isoformat()

    jr1_res = await client.post(
        f"/api/v1/staff/jobs/{job_id}/rounds",
        headers=staff_h,
        json={
            "round_number": 1,
            "round_type": RoundType.ONLINE_ASSESSMENT.value,
            "title": "Online Screening",
            "schedule_type": "AVAILABILITY_WINDOW",
            "available_from": now_str,
            "available_until": (now + timedelta(days=2)).isoformat(),
            "duration_minutes": 60,
        },
    )
    jr1_id = jr1_res.json()["id"]

    jr2_res = await client.post(
        f"/api/v1/staff/jobs/{job_id}/rounds",
        headers=staff_h,
        json={
            "round_number": 2,
            "round_type": RoundType.TECHNICAL_INTERVIEW.value,
            "title": "Tech Discussion 1",
            "schedule_type": "FIXED_TIME",
            "available_from": (now + timedelta(days=3)).isoformat(),
            "duration_minutes": 45,
        },
    )
    jr2_id = jr2_res.json()["id"]

    # 2. Student B applies after rounds configured
    resume_b_id = await upload_resume(client, student_b_h)
    app_b_res = await client.post(
        "/api/v1/student/applications",
        headers=student_b_h,
        json={"job_id": job_id, "resume_id": resume_b_id},
    )
    assert app_b_res.status_code == 201
    assert app_b_res.json()["status"] == "Interview"  # Auto-transition to Interview on round snapshot!

    app_b_id = app_b_res.json()["id"]
    rounds_b_res = await client.get(f"/api/v1/student/applications/{app_b_id}/rounds", headers=student_b_h)
    rounds_b = rounds_b_res.json()
    assert len(rounds_b) == 2
    assert rounds_b[0]["title"] == "Online Screening"
    assert rounds_b[0]["job_round_id"] == jr1_id
    assert rounds_b[0]["student_attendance"] == "NOT_REPORTED"
    assert rounds_b[0]["staff_verification"] == "PENDING"
    assert rounds_b[0]["result"] == "Pending"
    assert rounds_b[1]["title"] == "Tech Discussion 1"
    assert rounds_b[1]["job_round_id"] == jr2_id

    # 3. Snapshot Isolation: Edit JobRound template after Student B applied
    await client.patch(
        f"/api/v1/staff/jobs/{job_id}/rounds/{jr1_id}",
        headers=staff_h,
        json={"title": "MODIFIED Screening Title"},
    )

    # Verify Student B's ApplicationRound snapshot remains UNCHANGED
    rounds_b_after = (await client.get(f"/api/v1/student/applications/{app_b_id}/rounds", headers=student_b_h)).json()
    assert rounds_b_after[0]["title"] == "Online Screening"

    # 4. Student C applies afterward and receives updated template
    _, student_c_h = await _register_and_login(client, f"student_c_{uid}@test.com", "student")
    resume_c_id = await upload_resume(client, student_c_h)
    app_c_res = await client.post(
        "/api/v1/student/applications",
        headers=student_c_h,
        json={"job_id": job_id, "resume_id": resume_c_id},
    )
    app_c_id = app_c_res.json()["id"]
    rounds_c = (await client.get(f"/api/v1/student/applications/{app_c_id}/rounds", headers=student_c_h)).json()
    assert rounds_c[0]["title"] == "MODIFIED Screening Title"


@pytest.mark.asyncio(loop_scope="session")
async def test_reschedule_does_not_affect_job_round_or_other_students(client, db_session, user_repo):
    uid = uuid.uuid4().hex[:6]
    staff_h = await _get_staff_headers(client, db_session, user_repo, f"staff_resched_{uid}@test.com")
    _, student_1_h = await _register_and_login(client, f"student_1_{uid}@test.com", "student")
    _, student_2_h = await _register_and_login(client, f"student_2_{uid}@test.com", "student")

    _, job_id = await setup_company_and_job(client, staff_h)

    now = datetime.now(timezone.utc) + timedelta(days=2)
    jr_res = await client.post(
        f"/api/v1/staff/jobs/{job_id}/rounds",
        headers=staff_h,
        json={
            "round_number": 1,
            "round_type": RoundType.TECHNICAL_INTERVIEW.value,
            "title": "Tech Round",
            "schedule_type": "FIXED_TIME",
            "available_from": now.isoformat(),
            "duration_minutes": 60,
        },
    )
    jr_id = jr_res.json()["id"]

    res_1 = await upload_resume(client, student_1_h)
    app_1 = (await client.post("/api/v1/student/applications", headers=student_1_h, json={"job_id": job_id, "resume_id": res_1})).json()["id"]

    res_2 = await upload_resume(client, student_2_h)
    app_2 = (await client.post("/api/v1/student/applications", headers=student_2_h, json={"job_id": job_id, "resume_id": res_2})).json()["id"]

    rounds_1 = (await client.get(f"/api/v1/staff/applications/{app_1}/rounds", headers=staff_h)).json()
    r1_id = rounds_1[0]["id"]

    new_from = (now + timedelta(days=1)).isoformat()
    resched_res = await client.patch(
        f"/api/v1/staff/applications/{app_1}/rounds/{r1_id}/reschedule",
        headers=staff_h,
        json={
            "schedule_type": "FIXED_TIME",
            "new_available_from": new_from,
            "reason": "Interviewer unavailable",
        },
    )
    assert resched_res.status_code == 200

    # Check JobRound template remains unchanged
    jr_check = (await client.get(f"/api/v1/staff/jobs/{job_id}/rounds/{jr_id}", headers=staff_h)).json()
    assert jr_check["available_from"] == now.isoformat().replace("+00:00", "Z") or jr_check["available_from"].startswith(now.isoformat()[:16])

    # Check Student 2 application round remains unchanged
    rounds_2 = (await client.get(f"/api/v1/staff/applications/{app_2}/rounds", headers=staff_h)).json()
    assert rounds_2[0]["available_from"] != new_from


@pytest.mark.asyncio(loop_scope="session")
async def test_definitive_snapshot_isolation_and_job_round_deletion(client, db_session, user_repo):
    """
    Definitive validation test matching TASK 3 requirements:
    1. Create Job A.
    2. Add JobRound 1: Online Assessment.
    3. Add JobRound 2: Technical Interview, Schedule = Oct 5, 11:00.
    4. Student A applies.
    5. Verify Student A receives two ApplicationRounds.
    6. Modify JobRound 2: Schedule = Oct 6, 15:00.
    7. Verify Student A's ApplicationRound 2 still has Oct 5, 11:00.
    8. Student B applies.
    9. Verify Student B's ApplicationRound 2 has Oct 6, 15:00.
    10. Delete JobRound 2.
    11. Verify Student A's and Student B's ApplicationRound 2 records still exist.
    12. Verify snapshot data remains intact.
    13. Verify job_round_id becomes NULL.
    """
    uid = uuid.uuid4().hex[:6]
    staff_h = await _get_staff_headers(client, db_session, user_repo, f"staff_def_{uid}@test.com")
    _, student_a_h = await _register_and_login(client, f"student_a_def_{uid}@test.com", "student")
    _, student_b_h = await _register_and_login(client, f"student_b_def_{uid}@test.com", "student")

    # 1. Create Job A
    _, job_id = await setup_company_and_job(client, staff_h)

    # 2. Add JobRound 1: Online Assessment
    jr1_res = await client.post(
        f"/api/v1/staff/jobs/{job_id}/rounds",
        headers=staff_h,
        json={
            "round_number": 1,
            "round_type": RoundType.ONLINE_ASSESSMENT.value,
            "title": "Online Assessment",
            "schedule_type": "FIXED_TIME",
            "available_from": "2026-10-01T10:00:00Z",
            "duration_minutes": 60,
        },
    )
    assert jr1_res.status_code == 201

    # 3. Add JobRound 2: Technical Interview. Schedule = Oct 5, 11:00
    oct_5_str = "2026-10-05T11:00:00Z"
    jr2_res = await client.post(
        f"/api/v1/staff/jobs/{job_id}/rounds",
        headers=staff_h,
        json={
            "round_number": 2,
            "round_type": RoundType.TECHNICAL_INTERVIEW.value,
            "title": "Technical Interview",
            "schedule_type": "FIXED_TIME",
            "available_from": oct_5_str,
            "duration_minutes": 60,
            "instructions": "Join 10 minutes early",
        },
    )
    assert jr2_res.status_code == 201
    jr2_id = jr2_res.json()["id"]

    # 4. Student A applies
    res_a_id = await upload_resume(client, student_a_h)
    app_a_res = await client.post(
        "/api/v1/student/applications",
        headers=student_a_h,
        json={"job_id": job_id, "resume_id": res_a_id},
    )
    assert app_a_res.status_code == 201
    app_a_id = app_a_res.json()["id"]

    # 5. Verify Student A receives two ApplicationRounds
    rounds_a = (await client.get(f"/api/v1/student/applications/{app_a_id}/rounds", headers=student_a_h)).json()
    assert len(rounds_a) == 2
    assert rounds_a[0]["title"] == "Online Assessment"
    assert rounds_a[1]["title"] == "Technical Interview"
    assert rounds_a[1]["available_from"].startswith("2026-10-05T11:00")
    assert rounds_a[1]["instructions"] == "Join 10 minutes early"
    assert rounds_a[1]["job_round_id"] == jr2_id

    # 6. Modify JobRound 2: Schedule = Oct 6, 15:00
    oct_6_str = "2026-10-06T15:00:00Z"
    mod_res = await client.patch(
        f"/api/v1/staff/jobs/{job_id}/rounds/{jr2_id}",
        headers=staff_h,
        json={"available_from": oct_6_str},
    )
    assert mod_res.status_code == 200

    # 7. Verify Student A's ApplicationRound 2 still has: Oct 5, 11:00
    rounds_a_after = (await client.get(f"/api/v1/student/applications/{app_a_id}/rounds", headers=student_a_h)).json()
    assert rounds_a_after[1]["available_from"].startswith("2026-10-05T11:00")

    # 8. Student B applies
    res_b_id = await upload_resume(client, student_b_h)
    app_b_res = await client.post(
        "/api/v1/student/applications",
        headers=student_b_h,
        json={"job_id": job_id, "resume_id": res_b_id},
    )
    assert app_b_res.status_code == 201
    app_b_id = app_b_res.json()["id"]

    # 9. Verify Student B's ApplicationRound 2 has: Oct 6, 15:00
    rounds_b = (await client.get(f"/api/v1/student/applications/{app_b_id}/rounds", headers=student_b_h)).json()
    assert rounds_b[1]["available_from"].startswith("2026-10-06T15:00")
    assert rounds_b[1]["job_round_id"] == jr2_id

    # 10. Delete JobRound 2
    del_res = await client.delete(
        f"/api/v1/staff/jobs/{job_id}/rounds/{jr2_id}",
        headers=staff_h,
    )
    assert del_res.status_code == 200

    # 11. Verify Student A's and Student B's ApplicationRound 2 records still exist
    rounds_a_final = (await client.get(f"/api/v1/student/applications/{app_a_id}/rounds", headers=student_a_h)).json()
    rounds_b_final = (await client.get(f"/api/v1/student/applications/{app_b_id}/rounds", headers=student_b_h)).json()

    assert len(rounds_a_final) == 2
    assert len(rounds_b_final) == 2

    # 12. Verify snapshot data remains intact
    assert rounds_a_final[1]["title"] == "Technical Interview"
    assert rounds_a_final[1]["available_from"].startswith("2026-10-05T11:00")
    assert rounds_a_final[1]["instructions"] == "Join 10 minutes early"

    assert rounds_b_final[1]["title"] == "Technical Interview"
    assert rounds_b_final[1]["available_from"].startswith("2026-10-06T15:00")

    # 13. Verify job_round_id becomes NULL
    assert rounds_a_final[1]["job_round_id"] is None
    assert rounds_b_final[1]["job_round_id"] is None


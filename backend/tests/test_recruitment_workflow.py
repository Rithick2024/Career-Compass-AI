import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient

from app.modules.jobs.service import get_job_derived_status
from app.modules.application_rounds.utils import get_round_derived_state, get_round_derived_metadata
from app.modules.application_rounds.models import (
    ApplicationRound,
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


async def setup_base_data(client, staff_headers, student_headers):
    uid = uuid.uuid4().hex[:6]
    c_res = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": f"Workflow Tech {uid}"})
    c_id = c_res.json()["id"]

    j_res = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={
            "title": "Software Engineer",
            "company_id": c_id,
            "work_mode": "Hybrid",
            "instructions": "Bring laptop",
        },
    )
    j_id = j_res.json()["id"]

    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
    r_res = await client.post(
        "/api/v1/students/me/resumes",
        headers=student_headers,
        data={"title": "Main Resume"},
        files={"file": ("resume.pdf", pdf_content, "application/pdf")},
    )
    r_id = r_res.json()["id"]

    app_res = await client.post(
        "/api/v1/student/applications",
        headers=student_headers,
        json={"job_id": j_id, "resume_id": r_id},
    )
    return app_res.json()["id"], j_id, c_id, r_id


# ============================================================
# PHASE 18: JOB LIFECYCLE TESTS (1-9)
# ============================================================


class MockJob:
    def __init__(self, is_active=True, application_start_at=None, deadline=None, company_active=True):
        self.is_active = is_active
        self.application_start_at = application_start_at
        self.deadline = deadline
        class MockCompany:
            def __init__(self, is_active):
                self.is_active = is_active
        self.company = MockCompany(company_active)


@pytest.mark.asyncio(loop_scope="session")
async def test_job_derived_lifecycle_statuses():
    now = datetime.now(timezone.utc)

    # 1. start date future -> Upcoming
    j1 = MockJob(application_start_at=now + timedelta(hours=5))
    assert get_job_derived_status(j1, now) == "Upcoming"

    # 2. start date passed -> Open
    j2 = MockJob(application_start_at=now - timedelta(hours=5))
    assert get_job_derived_status(j2, now) == "Open"

    # 3. deadline >24h -> Open
    j3 = MockJob(deadline=now + timedelta(hours=48))
    assert get_job_derived_status(j3, now) == "Open"

    # 4. deadline <=24h -> Closing Soon
    j4 = MockJob(deadline=now + timedelta(hours=12))
    assert get_job_derived_status(j4, now) == "Closing Soon"

    # 5. deadline passed -> Closed
    j5 = MockJob(deadline=now - timedelta(hours=2))
    assert get_job_derived_status(j5, now) == "Closed"

    # 6. inactive -> Inactive
    j6 = MockJob(is_active=False)
    assert get_job_derived_status(j6, now) == "Inactive"

    # 7. company inactive -> Inactive
    j7 = MockJob(company_active=False)
    assert get_job_derived_status(j7, now) == "Inactive"


@pytest.mark.asyncio(loop_scope="session")
async def test_student_job_visibility(client: AsyncClient, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-jobvis@example.com")
    _, student_headers = await _register_and_login(client, "student-jobvis@example.com")

    uid = uuid.uuid4().hex[:6]
    c_res = await client.post("/api/v1/staff/companies", headers=staff_headers, json={"name": f"Vis Corp {uid}"})
    c_id = c_res.json()["id"]

    now = datetime.now(timezone.utc)
    # Upcoming job
    fut_res = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"title": "Future Role", "company_id": c_id, "application_start_at": (now + timedelta(days=2)).isoformat()},
    )
    fut_id = fut_res.json()["id"]

    # Closed job (created active then deadline set to past via DB or updated)
    past_res = await client.post(
        "/api/v1/staff/jobs",
        headers=staff_headers,
        json={"title": "Past Role", "company_id": c_id, "deadline": (now + timedelta(days=1)).isoformat()},
    )
    past_id = past_res.json()["id"]
    from app.modules.jobs.models import Job
    job_obj = await db_session.get(Job, past_id)
    job_obj.deadline = now - timedelta(days=1)
    await db_session.commit()

    # 8 & 9. Student cannot see Upcoming or Closed job
    s_jobs_res = await client.get("/api/v1/student/jobs", headers=student_headers)
    assert s_jobs_res.status_code == 200
    s_job_ids = [j["id"] for j in s_jobs_res.json()]
    assert fut_id not in s_job_ids
    assert past_id not in s_job_ids


# ============================================================
# PHASE 18: APPLICATION LIFECYCLE TESTS (10-20)
# ============================================================


@pytest.mark.asyncio(loop_scope="session")
async def test_application_lifecycle_rules(client: AsyncClient, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-applife@example.com")
    token, student_headers = await _register_and_login(client, "student-applife@example.com")

    app_id, j_id, c_id, r_id = await setup_base_data(client, staff_headers, student_headers)

    # 10. First round changes Pending -> Interview
    r1_res = await client.post(
        f"/api/v1/staff/applications/{app_id}/rounds",
        headers=staff_headers,
        json={"round_number": 1, "round_type": "Technical Interview", "scheduled_at": "2026-10-15T10:00:00Z"},
    )
    assert r1_res.status_code == 201
    
    app_chk = await client.get(f"/api/v1/staff/applications/{app_id}", headers=staff_headers)
    assert app_chk.json()["status"] == "Interview"

    # 15. Interview remains Interview when more rounds added
    r2_res = await client.post(
        f"/api/v1/staff/applications/{app_id}/rounds",
        headers=staff_headers,
        json={"round_number": 2, "round_type": "HR Interview", "scheduled_at": "2026-10-16T10:00:00Z"},
    )
    assert r2_res.status_code == 201
    app_chk2 = await client.get(f"/api/v1/staff/applications/{app_id}", headers=staff_headers)
    assert app_chk2.json()["status"] == "Interview"

    # 16. Student can withdraw during Interview
    w_res = await client.patch(f"/api/v1/student/applications/{app_id}/withdraw", headers=student_headers)
    assert w_res.status_code == 200
    assert w_res.json()["status"] == "Withdrawn"

    # 17. Withdrawal cancels future rounds
    rounds_res = await client.get(f"/api/v1/staff/applications/{app_id}/rounds", headers=staff_headers)
    assert all(r["status"] == "Cancelled" for r in rounds_res.json())

    # 14. Withdrawn application does not move to Interview when round added
    # (Creating round on withdrawn app fails or preserves status)
    r3_res = await client.post(
        f"/api/v1/staff/applications/{app_id}/rounds",
        headers=staff_headers,
        json={"round_number": 3, "round_type": "Other"},
    )
    app_chk3 = await client.get(f"/api/v1/staff/applications/{app_id}", headers=staff_headers)
    assert app_chk3.json()["status"] == "Withdrawn"


# ============================================================
# PHASE 18: ROUND DYNAMIC STATES & ATTENDANCE TESTS (21-40)
# ============================================================


@pytest.mark.asyncio(loop_scope="session")
async def test_round_dynamic_states_and_attendance(client: AsyncClient, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-roundst@example.com")
    _, student_headers = await _register_and_login(client, "student-roundst@example.com")

    app_id, j_id, c_id, r_id = await setup_base_data(client, staff_headers, student_headers)

    now = datetime.now(timezone.utc)
    
    # 21. Future round -> UPCOMING
    fut_time = (now + timedelta(hours=10)).isoformat()
    r1_res = await client.post(
        f"/api/v1/staff/applications/{app_id}/rounds",
        headers=staff_headers,
        json={"round_number": 1, "round_type": "Technical Interview", "scheduled_at": fut_time, "duration_minutes": 60},
    )
    r1 = r1_res.json()
    assert r1["derived_state"] == "UPCOMING"
    assert r1["is_upcoming"] is True

    # 26. Student cannot report future attendance
    att_fut = await client.post(
        f"/api/v1/student/applications/{app_id}/rounds/{r1['id']}/attendance",
        headers=student_headers,
        json={"attendance": "ATTENDED"},
    )
    assert att_fut.status_code == 400

    # Scheduled round for testing active window
    r2_res = await client.post(
        f"/api/v1/staff/applications/{app_id}/rounds",
        headers=staff_headers,
        json={"round_number": 2, "round_type": "Coding Test", "scheduled_at": (now + timedelta(minutes=5)).isoformat(), "duration_minutes": 60},
    )
    assert r2_res.status_code == 201
    r2 = r2_res.json()

    from app.modules.application_rounds.models import ApplicationRound
    r2_db = await db_session.get(ApplicationRound, r2["id"])
    r2_db.available_from = datetime.now(timezone.utc) - timedelta(minutes=5)
    await db_session.commit()

    # 24. Student reports ATTENDED
    att_res = await client.post(
        f"/api/v1/student/applications/{app_id}/rounds/{r2['id']}/attendance",
        headers=student_headers,
        json={"attendance": "ATTENDED"},
    )
    assert att_res.status_code == 200
    r2_att = att_res.json()
    assert r2_att["student_attendance"] == "ATTENDED"
    assert r2_att["derived_state"] == "AWAITING_VERIFICATION"

    # 29. Staff verifies attendance
    ver_res = await client.patch(
        f"/api/v1/staff/applications/{app_id}/rounds/{r2['id']}/verification",
        headers=staff_headers,
        json={"verification": "VERIFIED"},
    )
    assert ver_res.status_code == 200
    assert ver_res.json()["staff_verification"] == "VERIFIED"

    # 27. Student cannot modify after verification
    att_mod = await client.post(
        f"/api/v1/student/applications/{app_id}/rounds/{r2['id']}/attendance",
        headers=student_headers,
        json={"attendance": "ABSENT"},
    )
    assert att_mod.status_code == 400

    # 31. Verified attendance + PASSED
    res_pass = await client.patch(
        f"/api/v1/staff/applications/{app_id}/rounds/{r2['id']}/result",
        headers=staff_headers,
        json={"result": "Passed"},
    )
    assert res_pass.status_code == 200
    assert res_pass.json()["result"] == "Passed"
    assert res_pass.json()["derived_state"] == "PASSED"

    # 36. Passed round does not auto-offer application
    app_chk = await client.get(f"/api/v1/staff/applications/{app_id}", headers=staff_headers)
    assert app_chk.json()["status"] == "Interview"

    # 38 & 39. Rescheduling updates schedule and resets attendance/verification/result
    new_sched = (now + timedelta(days=3)).isoformat()
    resc_res = await client.patch(
        f"/api/v1/staff/applications/{app_id}/rounds/{r2['id']}/reschedule",
        headers=staff_headers,
        json={"new_scheduled_at": new_sched, "reason": "Interviewer unavailable"},
    )
    assert resc_res.status_code == 200
    r2_resc = resc_res.json()
    assert r2_resc["student_attendance"] == "NOT_REPORTED"
    assert r2_resc["staff_verification"] == "PENDING"
    assert r2_resc["result"] is None or r2_resc["result"] == "Pending"
    assert r2_resc["reschedule_reason"] == "Interviewer unavailable"

    # 40. Duplicate round number rejected
    dup_res = await client.post(
        f"/api/v1/staff/applications/{app_id}/rounds",
        headers=staff_headers,
        json={"round_number": 1, "round_type": "HR Interview", "available_from": fut_time},
    )
    assert dup_res.status_code == 409


@pytest.mark.asyncio(loop_scope="session")
async def test_availability_window_round_scheduling(client: AsyncClient, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-win@example.com")
    _, student_headers = await _register_and_login(client, "student-win@example.com")

    app_id, j_id, c_id, r_id = await setup_base_data(client, staff_headers, student_headers)

    now = datetime.now(timezone.utc)

    # 1. FIXED_TIME rejects available_until
    bad_fixed = await client.post(
        f"/api/v1/staff/applications/{app_id}/rounds",
        headers=staff_headers,
        json={
            "round_number": 1,
            "round_type": "Technical Interview",
            "schedule_type": "FIXED_TIME",
            "available_from": (now + timedelta(hours=1)).isoformat(),
            "available_until": (now + timedelta(hours=2)).isoformat(),
        },
    )
    assert bad_fixed.status_code == 400

    # 2. AVAILABILITY_WINDOW requires available_until > available_from
    bad_win = await client.post(
        f"/api/v1/staff/applications/{app_id}/rounds",
        headers=staff_headers,
        json={
            "round_number": 1,
            "round_type": "Online Assessment",
            "schedule_type": "AVAILABILITY_WINDOW",
            "available_from": (now + timedelta(hours=2)).isoformat(),
            "available_until": (now + timedelta(hours=1)).isoformat(),
        },
    )
    assert bad_win.status_code == 400

    # 3. Create valid AVAILABILITY_WINDOW round (future window)
    win_from = (now + timedelta(hours=2)).isoformat()
    win_until = (now + timedelta(hours=12)).isoformat()
    w1_res = await client.post(
        f"/api/v1/staff/applications/{app_id}/rounds",
        headers=staff_headers,
        json={
            "round_number": 1,
            "round_type": "Online Assessment",
            "schedule_type": "AVAILABILITY_WINDOW",
            "available_from": win_from,
            "available_until": win_until,
            "duration_minutes": 90,
        },
    )
    assert w1_res.status_code == 201
    w1 = w1_res.json()
    assert w1["schedule_type"] == "AVAILABILITY_WINDOW"
    assert w1["derived_state"] == "UPCOMING"
    assert w1["is_upcoming"] is True

    # 4. Student cannot attend before window opens
    att_early = await client.post(
        f"/api/v1/student/applications/{app_id}/rounds/{w1['id']}/attendance",
        headers=student_headers,
        json={"attendance": "ATTENDED"},
    )
    assert att_early.status_code == 400

    # 5. Move window to currently active via DB
    from app.modules.application_rounds.models import ApplicationRound
    w1_db = await db_session.get(ApplicationRound, w1["id"])
    w1_db.available_from = datetime.now(timezone.utc) - timedelta(hours=1)
    w1_db.available_until = datetime.now(timezone.utc) + timedelta(hours=5)
    await db_session.commit()

    # Student can report ATTENDED inside open window
    att_ok = await client.post(
        f"/api/v1/student/applications/{app_id}/rounds/{w1['id']}/attendance",
        headers=student_headers,
        json={"attendance": "ATTENDED"},
    )
    assert att_ok.status_code == 200
    assert att_ok.json()["student_attendance"] == "ATTENDED"
    assert att_ok.json()["derived_state"] == "AWAITING_VERIFICATION"

    # 6. Reschedule AVAILABILITY_WINDOW round
    new_from = (now + timedelta(days=2)).isoformat()
    new_until = (now + timedelta(days=3)).isoformat()
    resc_res = await client.patch(
        f"/api/v1/staff/applications/{app_id}/rounds/{w1['id']}/reschedule",
        headers=staff_headers,
        json={
            "schedule_type": "AVAILABILITY_WINDOW",
            "new_available_from": new_from,
            "new_available_until": new_until,
            "reason": "Extended assessment window",
        },
    )
    assert resc_res.status_code == 200
    w1_resc = resc_res.json()
    assert w1_resc["student_attendance"] == "NOT_REPORTED"
    assert w1_resc["staff_verification"] == "PENDING"
    assert w1_resc["available_until"] is not None


# ============================================================
# PHASE 18: AUTHORIZATION & PLACEMENT TESTS (41-50)
# ============================================================


@pytest.mark.asyncio(loop_scope="session")
async def test_authorization_and_placement_rules(client: AsyncClient, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-authplace@example.com")
    _, student1_headers = await _register_and_login(client, "student1-authplace@example.com")
    _, student2_headers = await _register_and_login(client, "student2-authplace@example.com")

    app_id, j_id, c_id, r_id = await setup_base_data(client, staff_headers, student1_headers)

    now = datetime.now(timezone.utc)
    r_res = await client.post(
        f"/api/v1/staff/applications/{app_id}/rounds",
        headers=staff_headers,
        json={"round_number": 1, "round_type": "Technical Interview", "available_from": (now + timedelta(hours=1)).isoformat()},
    )
    r_id_val = r_res.json()["id"]

    # 44. Student B cannot access or modify Student A round
    s2_att = await client.post(
        f"/api/v1/student/applications/{app_id}/rounds/{r_id_val}/attendance",
        headers=student2_headers,
        json={"attendance": "ATTENDED"},
    )
    assert s2_att.status_code == 404

    # 45. Student cannot modify result
    s1_res_mod = await client.patch(
        f"/api/v1/staff/applications/{app_id}/rounds/{r_id_val}/result",
        headers=student1_headers,
        json={"result": "Passed"},
    )
    assert s1_res_mod.status_code in (401, 403)

    # 46. Student cannot verify attendance
    s1_ver_mod = await client.patch(
        f"/api/v1/staff/applications/{app_id}/rounds/{r_id_val}/verification",
        headers=student1_headers,
        json={"verification": "VERIFIED"},
    )
    assert s1_ver_mod.status_code in (401, 403)

    # 47. Student cannot reschedule
    s1_resc_mod = await client.patch(
        f"/api/v1/staff/applications/{app_id}/rounds/{r_id_val}/reschedule",
        headers=student1_headers,
        json={"new_scheduled_at": "2026-12-01T10:00:00Z"},
    )
    assert s1_resc_mod.status_code in (401, 403)

    # 42. Non-Offered application cannot create placement
    place_bad = await client.post(
        "/api/v1/staff/placements",
        headers=staff_headers,
        json={"application_id": app_id, "final_package_ctc": 12.5, "placement_date": "2026-10-01"},
    )
    assert place_bad.status_code == 400

    # Move application to Offered
    off_res = await client.patch(
        f"/api/v1/staff/applications/{app_id}/status",
        headers=staff_headers,
        json={"status": "Offered"},
    )
    assert off_res.status_code == 200

    # 41. Offered allows placement
    place_ok = await client.post(
        "/api/v1/staff/placements",
        headers=staff_headers,
        json={"application_id": app_id, "final_package_ctc": 12.5, "placement_date": "2026-10-01"},
    )
    assert place_ok.status_code in (200, 201)

    # 20. Student cannot withdraw after Placement
    w_bad = await client.patch(f"/api/v1/student/applications/{app_id}/withdraw", headers=student1_headers)
    assert w_bad.status_code == 400

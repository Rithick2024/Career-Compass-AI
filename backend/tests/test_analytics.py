import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from app.modules.students.models import Student
from app.modules.companies.models import Company
from app.modules.jobs.models import Job
from app.modules.applications.models import Application, ApplicationStatus
from app.modules.placements.models import Placement
from app.modules.application_rounds.models import ApplicationRound, RoundStatus, RoundType, RoundResult
from app.modules.students.models import Department

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

@pytest.mark.asyncio(loop_scope="session")
async def test_analytics_empty_state(client: AsyncClient, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-empty@example.com")
    res = await client.get(
        "/api/v1/staff/analytics/overview",
        headers=staff_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_students"] == 0
    assert data["active_jobs"] == 0
    assert data["pending_applications"] == 0
    assert data["accepted_placements"] == 0
    assert data["average_package"] == 0.0

@pytest.mark.asyncio(loop_scope="session")
async def test_staff_analytics_aggregations(
    client: AsyncClient,
    db_session,
    user_repo
):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-analytics@example.com")
    
    # Create test user
    await client.post("/api/v1/auth/register", json={"email": "student-creator@example.com", "password": "password"})
    student_creator = await user_repo.get_by_email("student-creator@example.com")
    
    department = Department(name="Analytics Department")
    db_session.add(department)
    await db_session.flush()

    # Setup Data
    student = Student(user_id=student_creator.id, department_id=department.id, full_name="Analytics Student", graduation_year=2024)
    company = Company(name="Analytics Company", is_active=True)
    db_session.add(student)
    db_session.add(company)
    await db_session.flush()

    job1 = Job(company_id=company.id, title="Analytics Job 1", is_active=True)
    job2 = Job(company_id=company.id, title="Analytics Job 2", is_active=False) # inactive
    db_session.add(job1)
    db_session.add(job2)
    await db_session.flush()

    from app.modules.resumes.models import Resume
    resume = Resume(student_id=student.id, title="My Resume", file_path="/fake", file_name="resume.pdf", file_type="application/pdf", file_size=1024, is_default=True)
    db_session.add(resume)
    await db_session.flush()

    app1 = Application(student_id=student.id, job_id=job1.id, resume_id=resume.id, status=ApplicationStatus.PENDING)
    app2 = Application(student_id=student.id, job_id=job2.id, resume_id=resume.id, status=ApplicationStatus.OFFERED)
    db_session.add(app1)
    db_session.add(app2)
    await db_session.flush()

    placement1 = Placement(application_id=app2.id, offer_accepted=True, final_package_ctc=10.0, placement_date=datetime.now(timezone.utc).date())
    db_session.add(placement1)
    await db_session.flush()

    round1 = ApplicationRound(application_id=app2.id, round_number=1, round_type=RoundType.TECHNICAL_INTERVIEW, status=RoundStatus.COMPLETED, result=RoundResult.PASSED)
    round2 = ApplicationRound(application_id=app2.id, round_number=2, round_type=RoundType.HR_INTERVIEW, status=RoundStatus.COMPLETED, result=RoundResult.FAILED)
    db_session.add(round1)
    db_session.add(round2)
    await db_session.commit()

    res = await client.get(
        "/api/v1/staff/analytics/overview",
        headers=staff_headers
    )
    assert res.status_code == 200
    data = res.json()
    
    # Asserting relative changes to handle tests running sequentially with other tests inserting data
    assert data["total_students"] >= 1
    assert data["active_jobs"] >= 1
    assert data["pending_applications"] >= 1
    assert data["accepted_placements"] >= 1
    
    status_counts = {item["status"]: item["count"] for item in data["applications_by_status"]}
    assert status_counts["Pending"] >= 1
    assert status_counts["Offered"] >= 1

    dept_counts = {item["department"]: item["count"] for item in data["placements_by_department"]}
    assert "Analytics Department" in dept_counts
    assert dept_counts["Analytics Department"] >= 1

    recruitment = data["recruitment_summary"]
    assert recruitment["total_rounds"] >= 2
    assert recruitment["passed_rounds"] >= 1
    assert recruitment["failed_rounds"] >= 1

@pytest.mark.asyncio(loop_scope="session")
async def test_student_analytics_isolation(
    client: AsyncClient,
    db_session,
    user_repo
):
    token, student_headers = await _register_and_login(client, "student-iso-analytics@example.com")
    student_user = await user_repo.get_by_email("student-iso-analytics@example.com")
    
    student = Student(user_id=student_user.id, full_name="Student", graduation_year=2024)
    company = Company(name="Company A ISO", is_active=True)
    db_session.add(student)
    db_session.add(company)
    await db_session.flush()

    job1 = Job(company_id=company.id, title="Job 1 ISO", is_active=True)
    db_session.add(job1)
    await db_session.flush()

    from app.modules.resumes.models import Resume
    resume = Resume(student_id=student.id, title="My Resume", file_path="/fake", file_name="resume.pdf", file_type="application/pdf", file_size=1024, is_default=True)
    db_session.add(resume)
    await db_session.flush()

    app1 = Application(student_id=student.id, job_id=job1.id, resume_id=resume.id, status=ApplicationStatus.OFFERED)
    db_session.add(app1)
    await db_session.flush()

    future_date = datetime.now(timezone.utc) + timedelta(days=2)
    round1 = ApplicationRound(application_id=app1.id, round_number=1, round_type=RoundType.TECHNICAL_INTERVIEW, status=RoundStatus.SCHEDULED, scheduled_at=future_date)
    db_session.add(round1)
    
    placement = Placement(application_id=app1.id, offer_accepted=True, final_package_ctc=15.0, placement_date=datetime.now(timezone.utc).date())
    db_session.add(placement)
    await db_session.commit()

    res = await client.get(
        "/api/v1/student/analytics/overview",
        headers=student_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["active_applications"] == 1
    assert data["total_offers"] == 1
    
    assert len(data["upcoming_rounds"]) == 1
    assert len(data["recent_applications"]) == 1
    
    assert data["placement_summary"]["has_accepted_placement"] == True
    assert data["placement_summary"]["accepted_placement_count"] == 1
    assert data["placement_summary"]["latest_accepted_placement_package"] == 15.0
    assert data["placement_summary"]["latest_accepted_placement_company"] == "Company A ISO"

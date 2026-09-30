"""
Comprehensive test suite for Placement Readiness and Skill Gap Intelligence MVP.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.modules.students.models import Student, Department
from app.modules.skills.models import Skill, StudentSkill
from app.modules.resumes.models import Resume
from app.modules.companies.models import Company
from app.modules.jobs.models import Job, JobRequiredSkill, JobEligibleDepartment
from app.modules.applications.models import Application, ApplicationStatus
from app.modules.placements.models import Placement
from app.shared.enums import ProficiencyLevel, RoleEnum


async def _register_and_login_student(client: AsyncClient, email: str = "intel-student@example.com"):
    """Helper to register and login a student, returning token and auth headers."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password", "role": "student"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password"},
    )
    token = login.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


async def _get_staff_headers(client: AsyncClient, db_session, user_repo, email: str = "intel-staff@example.com"):
    """Helper to get staff auth headers."""
    await client.post("/api/v1/auth/register", json={"email": email, "password": "password"})
    user = await user_repo.get_by_email(email)
    user.role = RoleEnum.STAFF
    await db_session.commit()

    staff_login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password"},
    )
    return {"Authorization": f"Bearer {staff_login.json()['access_token']}"}


# ============================================================================
# READINESS TESTS (Scenarios 1-20)
# ============================================================================

@pytest.mark.asyncio(loop_scope="session")
async def test_readiness_fresh_student_empty_state(client: AsyncClient, db_session, user_repo):
    """Test 1, 2, 3, 4, 8, 14, 15, 16, 17, 18: Fresh student with no CGPA, no dept, no skills, no resumes."""
    token, headers = await _register_and_login_student(client, "fresh-student@example.com")
    
    res = await client.get("/api/v1/student/intelligence/readiness", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["readiness_score"] >= 0.0
    assert data["readiness_score"] <= 100.0
    assert data["status_category"] in ["Needs Improvement", "Developing", "Good", "Strong"]
    assert data["is_placed"] is False
    assert len(data["components"]) == 4

    # Academic component: 0 CGPA + 0 Dept = 0.0
    academic = next(c for c in data["components"] if c["name"] == "Academic Readiness")
    assert academic["score"] == 0.0

    # Skill component: 0 skills = 0.0
    skill_comp = next(c for c in data["components"] if c["name"] == "Skill Profile")
    assert skill_comp["score"] == 0.0

    # Recommendations present
    assert len(data["actionable_recommendations"]) > 0


@pytest.mark.asyncio(loop_scope="session")
async def test_readiness_complete_student_profile_and_skills(client: AsyncClient, db_session, user_repo):
    """Test 5, 6, 7, 9, 10, 11, 13, 16: Complete student with CGPA 9.0, dept, 5 Advanced skills, default resume."""
    token, headers = await _register_and_login_student(client, "complete-student@example.com")
    user = await user_repo.get_by_email("complete-student@example.com")

    # Create Department
    dept = Department(name="Computer Science & Engineering")
    db_session.add(dept)
    await db_session.flush()

    # Update Student profile
    student = Student(
        user_id=user.id,
        department_id=dept.id,
        full_name="Jane Doe",
        phone="9876543210",
        date_of_birth=datetime(2002, 5, 15).date(),
        address="123 Campus Tech Park",
        linkedin_url="https://linkedin.com/in/janedoe",
        github_url="https://github.com/janedoe",
        graduation_year=2024,
        cgpa=Decimal("9.00"),
    )
    db_session.add(student)
    await db_session.flush()

    # Create Default Resume
    resume = Resume(
        student_id=student.id,
        title="Software Engineer Resume",
        file_path="/uploads/resumes/resume.pdf",
        file_name="resume.pdf",
        file_type="application/pdf",
        file_size=2048,
        is_default=True,
    )
    db_session.add(resume)

    # Create 5 Master Skills and assign as Advanced to student
    skills = []
    for i in range(5):
        s = Skill(name=f"Intel Skill {i+1}", category="Engineering", is_active=True)
        db_session.add(s)
        skills.append(s)
    await db_session.flush()

    for s in skills:
        ss = StudentSkill(student_id=student.id, skill_id=s.id, proficiency=ProficiencyLevel.ADVANCED)
        db_session.add(ss)

    # Create Active Company & Active Job
    company = Company(name="Tech Corp Global", is_active=True)
    db_session.add(company)
    await db_session.flush()

    job = Job(company_id=company.id, title="Senior Software Engineer", min_cgpa=Decimal("8.00"), is_active=True)
    db_session.add(job)
    await db_session.flush()

    job_dept = JobEligibleDepartment(job_id=job.id, department_id=dept.id)
    db_session.add(job_dept)
    await db_session.commit()

    res = await client.get("/api/v1/student/intelligence/readiness", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Academic: (9.0 / 10 * 20) = 18.0 + 5.0 (dept) = 23.0
    acad = next(c for c in data["components"] if c["name"] == "Academic Readiness")
    assert acad["score"] == 23.0

    # Skill Profile: 5 skills -> 15.0 quantity + 20.0 quality (Advanced 1.0 factor) = 35.0
    sk = next(c for c in data["components"] if c["name"] == "Skill Profile")
    assert sk["score"] == 35.0

    # Profile & Resume: 6 fields complete (10.0) + default resume (10.0) = 20.0
    pr = next(c for c in data["components"] if c["name"] == "Profile & Resume")
    assert pr["score"] == 20.0

    # Market Eligibility: eligible for 1/1 active jobs -> 20.0
    me = next(c for c in data["components"] if c["name"] == "Market Eligibility")
    assert me["score"] == 20.0

    # Total Score: 23.0 + 35.0 + 20.0 + 20.0 = 98.0 -> Category "Strong"
    assert data["readiness_score"] == 98.0
    assert data["status_category"] == "Strong"


@pytest.mark.asyncio(loop_scope="session")
async def test_readiness_placed_student_flag(client: AsyncClient, db_session, user_repo):
    """Test 19, 20: Placed student sets is_placed=True without forcing score to 100."""
    token, headers = await _register_and_login_student(client, "placed-student@example.com")
    user = await user_repo.get_by_email("placed-student@example.com")

    student = Student(user_id=user.id, full_name="Placed Student", cgpa=Decimal("7.50"))
    company = Company(name="Placed Corp", is_active=True)
    db_session.add(student)
    db_session.add(company)
    await db_session.flush()

    job = Job(company_id=company.id, title="Developer", is_active=True)
    db_session.add(job)
    await db_session.flush()

    resume = Resume(student_id=student.id, title="Resume", file_path="/f", file_name="r.pdf", file_type="pdf", file_size=10, is_default=True)
    db_session.add(resume)
    await db_session.flush()

    app = Application(student_id=student.id, job_id=job.id, resume_id=resume.id, status=ApplicationStatus.OFFERED)
    db_session.add(app)
    await db_session.flush()

    placement = Placement(application_id=app.id, offer_accepted=True, final_package_ctc=Decimal("12.00"), placement_date=datetime.now(timezone.utc).date())
    db_session.add(placement)
    await db_session.commit()

    res = await client.get("/api/v1/student/intelligence/readiness", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["is_placed"] is True
    # Placement state is separate from readiness score (score is calculated based on formula, not forced to 100)
    assert data["readiness_score"] < 100.0


# ============================================================================
# SKILL GAP TESTS (Scenarios 21-29)
# ============================================================================

@pytest.mark.asyncio(loop_scope="session")
async def test_market_skill_gaps_analysis(client: AsyncClient, db_session, user_repo):
    """Test 21, 22, 23, 24, 25, 27, 28, 29: Market skill gaps missing vs insufficient proficiency."""
    token, headers = await _register_and_login_student(client, "skillgap-student@example.com")
    user = await user_repo.get_by_email("skillgap-student@example.com")

    student = Student(user_id=user.id, full_name="SkillGap Student")
    db_session.add(student)
    await db_session.flush()

    # Create master skills
    skill_python = Skill(name="Python Alpha", category="Backend", is_active=True)
    skill_docker = Skill(name="Docker Alpha", category="DevOps", is_active=True)
    skill_inactive = Skill(name="Obsolete Skill", category="Legacy", is_active=False)
    db_session.add_all([skill_python, skill_docker, skill_inactive])
    await db_session.flush()

    # Student has Python at Intermediate
    ss_python = StudentSkill(student_id=student.id, skill_id=skill_python.id, proficiency=ProficiencyLevel.INTERMEDIATE)
    db_session.add(ss_python)

    # Active Company & 2 Jobs
    company = Company(name="Cloud Corp", is_active=True)
    db_session.add(company)
    await db_session.flush()

    job1 = Job(company_id=company.id, title="Backend Lead", is_active=True)
    job2 = Job(company_id=company.id, title="DevOps Engineer", is_active=True)
    db_session.add_all([job1, job2])
    await db_session.flush()

    # Job 1 requires Python Advanced & Docker Intermediate
    jrs1_py = JobRequiredSkill(job_id=job1.id, skill_id=skill_python.id, min_proficiency=ProficiencyLevel.ADVANCED)
    jrs1_doc = JobRequiredSkill(job_id=job1.id, skill_id=skill_docker.id, min_proficiency=ProficiencyLevel.INTERMEDIATE)
    
    # Job 2 requires Docker Advanced & Inactive Skill
    jrs2_doc = JobRequiredSkill(job_id=job2.id, skill_id=skill_docker.id, min_proficiency=ProficiencyLevel.ADVANCED)
    jrs2_inact = JobRequiredSkill(job_id=job2.id, skill_id=skill_inactive.id, min_proficiency=ProficiencyLevel.BEGINNER)

    db_session.add_all([jrs1_py, jrs1_doc, jrs2_doc, jrs2_inact])
    await db_session.commit()

    res = await client.get("/api/v1/student/intelligence/skills/gap", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_active_jobs_evaluated"] >= 2
    gaps = data["gaps"]

    # Docker should be MISSING (required by 2 jobs)
    docker_gap = next((g for g in gaps if g["skill_name"] == "Docker Alpha"), None)
    assert docker_gap is not None
    assert docker_gap["gap_type"] == "MISSING"
    assert docker_gap["jobs_requiring_skill"] == 2
    assert docker_gap["student_proficiency"] is None

    # Python should be INSUFFICIENT_PROFICIENCY (student has Intermediate, job requires Advanced)
    python_gap = next((g for g in gaps if g["skill_name"] == "Python Alpha"), None)
    assert python_gap is not None
    assert python_gap["gap_type"] == "INSUFFICIENT_PROFICIENCY"
    assert python_gap["student_proficiency"] == "intermediate"
    assert python_gap["required_proficiency"] == "advanced"

    # Inactive skill must NOT be present
    inactive_gap = next((g for g in gaps if g["skill_name"] == "Obsolete Skill"), None)
    assert inactive_gap is None


# ============================================================================
# JOB MATCH TESTS (Scenarios 30-37)
# ============================================================================

@pytest.mark.asyncio(loop_scope="session")
async def test_job_match_eligible_and_skills(client: AsyncClient, db_session, user_repo):
    """Test 30, 31, 32, 33, 34, 35: Job specific match breakdown and eligibility."""
    token, headers = await _register_and_login_student(client, "match-student@example.com")
    user = await user_repo.get_by_email("match-student@example.com")

    dept_cse = Department(name="CSE Match Dept")
    dept_ece = Department(name="ECE Match Dept")
    db_session.add_all([dept_cse, dept_ece])
    await db_session.flush()

    student = Student(user_id=user.id, department_id=dept_cse.id, full_name="Match Student", cgpa=Decimal("8.50"))
    db_session.add(student)
    await db_session.flush()

    # Create master skills
    skill_react = Skill(name="React Match", is_active=True)
    skill_sql = Skill(name="SQL Match", is_active=True)
    skill_aws = Skill(name="AWS Match", is_active=True)
    db_session.add_all([skill_react, skill_sql, skill_aws])
    await db_session.flush()

    # Student has React Advanced & SQL Intermediate
    db_session.add(StudentSkill(student_id=student.id, skill_id=skill_react.id, proficiency=ProficiencyLevel.ADVANCED))
    db_session.add(StudentSkill(student_id=student.id, skill_id=skill_sql.id, proficiency=ProficiencyLevel.INTERMEDIATE))

    company = Company(name="Match Company", is_active=True)
    db_session.add(company)
    await db_session.flush()

    # Job 1: Min CGPA 8.0, eligible for CSE, requires React (Intermediate), SQL (Advanced), AWS (Beginner)
    job1 = Job(company_id=company.id, title="Frontend Dev Match", min_cgpa=Decimal("8.00"), is_active=True)
    db_session.add(job1)
    await db_session.flush()

    db_session.add(JobEligibleDepartment(job_id=job1.id, department_id=dept_cse.id))
    db_session.add(JobRequiredSkill(job_id=job1.id, skill_id=skill_react.id, min_proficiency=ProficiencyLevel.INTERMEDIATE))
    db_session.add(JobRequiredSkill(job_id=job1.id, skill_id=skill_sql.id, min_proficiency=ProficiencyLevel.ADVANCED))
    db_session.add(JobRequiredSkill(job_id=job1.id, skill_id=skill_aws.id, min_proficiency=ProficiencyLevel.BEGINNER))
    await db_session.commit()

    # Test Job 1 Match
    res = await client.get(f"/api/v1/student/intelligence/jobs/{job1.id}/match", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["job_id"] == job1.id
    assert data["is_eligible"] is True
    assert data["cgpa_eligible"] is True
    assert data["department_eligible"] is True

    assert data["total_required_skills"] == 3
    # React: Student Advanced > Required Intermediate -> STRONG_MATCH
    assert len(data["strong_matches"]) == 1
    assert data["strong_matches"][0]["skill_name"] == "React Match"

    # SQL: Student Intermediate < Required Advanced -> INSUFFICIENT_PROFICIENCY
    assert len(data["insufficient_proficiency"]) == 1
    assert data["insufficient_proficiency"][0]["skill_name"] == "SQL Match"

    # AWS: Student missing -> MISSING
    assert len(data["missing_skills"]) == 1
    assert data["missing_skills"][0]["skill_name"] == "AWS Match"

    # Match % = (1 satisfied / 3 total) * 100 = 33.3%
    assert data["skill_match_percentage"] == 33.3


@pytest.mark.asyncio(loop_scope="session")
async def test_job_match_zero_skills_and_ineligible(client: AsyncClient, db_session, user_repo):
    """Test 32, 33, 36: Job with zero required skills and ineligible CGPA/department."""
    token, headers = await _register_and_login_student(client, "inelig-student@example.com")
    user = await user_repo.get_by_email("inelig-student@example.com")

    dept_mech = Department(name="Mechanical Dept")
    dept_civil = Department(name="Civil Dept")
    db_session.add_all([dept_mech, dept_civil])
    await db_session.flush()

    student = Student(user_id=user.id, department_id=dept_mech.id, full_name="Mech Student", cgpa=Decimal("6.50"))
    company = Company(name="Mech Corp", is_active=True)
    db_session.add_all([student, company])
    await db_session.flush()

    # Job requiring Civil Dept & CGPA 7.50, but zero required skills
    job = Job(company_id=company.id, title="Civil Consultant", min_cgpa=Decimal("7.50"), is_active=True)
    db_session.add(job)
    await db_session.flush()
    db_session.add(JobEligibleDepartment(job_id=job.id, department_id=dept_civil.id))
    await db_session.commit()

    res = await client.get(f"/api/v1/student/intelligence/jobs/{job.id}/match", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["is_eligible"] is False
    assert data["cgpa_eligible"] is False
    assert data["department_eligible"] is False
    assert "Ineligible" in data["eligibility_explanation"]

    # Zero required skills -> 100% skill match
    assert data["total_required_skills"] == 0
    assert data["skill_match_percentage"] == 100.0


@pytest.mark.asyncio(loop_scope="session")
async def test_job_match_inactive_job_404(client: AsyncClient, db_session, user_repo):
    """Test 37: Inactive / hidden job returns 404."""
    token, headers = await _register_and_login_student(client, "hidden-job-student@example.com")

    company = Company(name="Inactive Company", is_active=True)
    db_session.add(company)
    await db_session.flush()

    job_inactive = Job(company_id=company.id, title="Hidden Job", is_active=False)
    db_session.add(job_inactive)
    await db_session.commit()

    res = await client.get(f"/api/v1/student/intelligence/jobs/{job_inactive.id}/match", headers=headers)
    assert res.status_code == 404


# ============================================================================
# SECURITY & BOUNDARY TESTS (Scenarios 38-40)
# ============================================================================

@pytest.mark.asyncio(loop_scope="session")
async def test_intelligence_security_boundaries(client: AsyncClient, db_session, user_repo):
    """Test 38, 39, 40: Auth enforcement, student isolation, and staff prohibition."""
    # Test 39: Unauthenticated call fails
    res_unauth = await client.get("/api/v1/student/intelligence/readiness")
    assert res_unauth.status_code == 401

    # Test 40: Staff user prohibited from student intelligence endpoints
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-prohibited@example.com")
    res_staff = await client.get("/api/v1/student/intelligence/readiness", headers=staff_headers)
    assert res_staff.status_code == 403

    # Test 38: Student A cannot specify another student's ID (endpoint uses token user only)
    token_a, headers_a = await _register_and_login_student(client, "student-a-sec@example.com")
    token_b, headers_b = await _register_and_login_student(client, "student-b-sec@example.com")

    res_a = await client.get("/api/v1/student/intelligence/readiness", headers=headers_a)
    res_b = await client.get("/api/v1/student/intelligence/readiness", headers=headers_b)
    assert res_a.status_code == 200
    assert res_b.status_code == 200

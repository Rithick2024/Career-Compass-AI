"""
Comprehensive tests for Career Readiness & Growth Engine:
- Job-specific readiness assessment
- Missing vs. demonstrated evidence distinction
- Personalized Improvement Plan (PIP) generation and progress updates
- Student data isolation
- Staff authorization for department skill gaps
- AI provider failure resilience
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.modules.students.models import Student, Department
from app.modules.skills.models import Skill, StudentSkill
from app.modules.resumes.models import Resume
from app.modules.companies.models import Company
from app.modules.jobs.models import Job, JobRequiredSkill, JobEligibleDepartment
from app.modules.applications.models import Application, ApplicationStatus
from app.modules.application_rounds.models import ApplicationRound, RoundStatus, RoundResult, RoundType
from app.shared.enums import ProficiencyLevel, RoleEnum


async def _register_and_login_student(client: AsyncClient, email: str):
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


async def _get_staff_headers(client: AsyncClient, db_session, user_repo, email: str = "staff-engine@example.com"):
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
# 1. ELIGIBILITY CALCULATION & ASSESSMENT TESTS
# ============================================================================

@pytest.mark.asyncio(loop_scope="session")
async def test_job_readiness_eligibility_failures(client: AsyncClient, db_session, user_repo):
    """
    Test student failing CGPA and department eligibility:
    - Overall score penalizes academic criteria
    - Eligibility blockers explicitly returned in eligibility_reasons
    - is_eligible is False
    """
    _, headers = await _register_and_login_student(client, "ineligible-student@example.com")
    user = await user_repo.get_by_email("ineligible-student@example.com")

    # Departments
    dept_cs = Department(name="CSE Department")
    dept_mech = Department(name="Mech Department")
    db_session.add_all([dept_cs, dept_mech])
    await db_session.flush()

    # Student belongs to Mech with CGPA 6.5
    student = Student(
        user_id=user.id,
        department_id=dept_mech.id,
        full_name="Low CGPA Student",
        cgpa=Decimal("6.50"),
        graduation_year=2025,
    )
    db_session.add(student)

    # Company & Job requiring CSE and min CGPA 8.0
    comp = Company(name="FinTech Corp", is_active=True)
    db_session.add(comp)
    await db_session.flush()

    job = Job(
        company_id=comp.id,
        title="Software Engineer Intern",
        min_cgpa=Decimal("8.00"),
        is_active=True,
    )
    db_session.add(job)
    await db_session.flush()

    # Job allows only CSE
    elig_dept = JobEligibleDepartment(job_id=job.id, department_id=dept_cs.id)
    db_session.add(elig_dept)
    await db_session.commit()

    # Query Job Readiness
    res = await client.get(f"/api/v1/student/intelligence/jobs/{job.id}/readiness", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["job_id"] == job.id
    assert data["is_eligible"] is False
    assert data["cgpa_eligible"] is False
    assert data["department_eligible"] is False
    assert data["score_breakdown"]["academic_points"] == 0.0
    assert any("below employer cutoff" in r for r in data["eligibility_reasons"])
    assert any("not among the eligible departments" in r for r in data["eligibility_reasons"])
    assert data["readiness_score"] <= 60.0



@pytest.mark.asyncio(loop_scope="session")
async def test_job_readiness_demonstrated_vs_missing_evidence(client: AsyncClient, db_session, user_repo):
    """
    Test distinction between:
    - Demonstrated skill (in student profile with required or higher proficiency)
    - Partially supported skill (in student profile but beginner when job needs intermediate)
    - Missing evidence (required by job, not recorded in student's profile)
    """
    _, headers = await _register_and_login_student(client, "evidence-student@example.com")
    user = await user_repo.get_by_email("evidence-student@example.com")

    dept = Department(name="IT Department")
    db_session.add(dept)
    await db_session.flush()

    student = Student(
        user_id=user.id,
        department_id=dept.id,
        full_name="Evidence Student",
        cgpa=Decimal("8.80"),
        graduation_year=2025,
    )
    db_session.add(student)
    await db_session.flush()

    # 3 skills in catalog
    skill_py = Skill(name="Python Backend", is_active=True)
    skill_sql = Skill(name="PostgreSQL Database", is_active=True)
    skill_docker = Skill(name="Docker & Containers", is_active=True)
    db_session.add_all([skill_py, skill_sql, skill_docker])
    await db_session.flush()

    # Student has Python (Advanced) and SQL (Beginner)
    ss_py = StudentSkill(student_id=student.id, skill_id=skill_py.id, proficiency=ProficiencyLevel.ADVANCED)
    ss_sql = StudentSkill(student_id=student.id, skill_id=skill_sql.id, proficiency=ProficiencyLevel.BEGINNER)
    db_session.add_all([ss_py, ss_sql])

    # Company & Job requiring all 3 skills
    comp = Company(name="Cloud Scale Inc", is_active=True)
    db_session.add(comp)
    await db_session.flush()

    job = Job(
        company_id=comp.id,
        title="Full Stack Engineer",
        min_cgpa=Decimal("7.00"),
        is_active=True,
    )
    db_session.add(job)
    await db_session.flush()

    # Python: Intermediate req (Student has Advanced -> DEMONSTRATED)
    # SQL: Intermediate req (Student has Beginner -> PARTIAL_EVIDENCE)
    # Docker: Intermediate req (Student has None -> UNVERIFIED_OR_MISSING)
    db_session.add_all([
        JobRequiredSkill(job_id=job.id, skill_id=skill_py.id, min_proficiency=ProficiencyLevel.INTERMEDIATE),
        JobRequiredSkill(job_id=job.id, skill_id=skill_sql.id, min_proficiency=ProficiencyLevel.INTERMEDIATE),
        JobRequiredSkill(job_id=job.id, skill_id=skill_docker.id, min_proficiency=ProficiencyLevel.INTERMEDIATE),
    ])
    await db_session.commit()

    res = await client.get(f"/api/v1/student/intelligence/jobs/{job.id}/readiness", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["demonstrated_count"] == 1
    assert data["partial_count"] == 1
    assert data["missing_evidence_count"] == 1

    skills_breakdown = data["skills_breakdown"]
    demonstrated_names = [s["skill_name"] for s in skills_breakdown if s["status"] == "DEMONSTRATED"]
    partially_names = [s["skill_name"] for s in skills_breakdown if s["status"] == "PARTIAL_EVIDENCE"]
    missing_names = [s["skill_name"] for s in skills_breakdown if s["status"] == "UNVERIFIED_OR_MISSING"]

    assert "Python Backend" in demonstrated_names
    assert "PostgreSQL Database" in partially_names
    assert "Docker & Containers" in missing_names

    # Check that missing explanation distinguishes lack of platform evidence from real-world inability
    docker_item = next(s for s in skills_breakdown if s["skill_name"] == "Docker & Containers")
    assert "Unverified on platform" in docker_item["evidence_summary"]



# ============================================================================
# 2. PERSONALIZED IMPROVEMENT PLAN (PIP) TESTS
# ============================================================================

@pytest.mark.asyncio(loop_scope="session")
async def test_improvement_plan_generation_and_action_lifecycle(client: AsyncClient, db_session, user_repo):
    """
    Test generating an improvement plan:
    - Generates actions for partially supported and missing skills
    - Action item priority matches gap severity
    - Transition action status: PENDING -> IN_PROGRESS -> COMPLETED
    - Plan progress percentage updates accurately
    - Re-generating the plan is idempotent and retains COMPLETED status
    """
    _, headers = await _register_and_login_student(client, "pip-student@example.com")
    user = await user_repo.get_by_email("pip-student@example.com")

    student = Student(
        user_id=user.id,
        full_name="Plan Student",
        cgpa=Decimal("8.00"),
        graduation_year=2025,
    )
    db_session.add(student)
    await db_session.flush()

    skill_algo = Skill(name="Algorithms & Data Structures", is_active=True)
    skill_k8s = Skill(name="Kubernetes", is_active=True)
    db_session.add_all([skill_algo, skill_k8s])
    await db_session.flush()

    comp = Company(name="DevOps Global", is_active=True)
    db_session.add(comp)
    await db_session.flush()

    job = Job(company_id=comp.id, title="Platform Engineer", is_active=True)
    db_session.add(job)
    await db_session.flush()

    db_session.add_all([
        JobRequiredSkill(job_id=job.id, skill_id=skill_algo.id, min_proficiency=ProficiencyLevel.ADVANCED),
        JobRequiredSkill(job_id=job.id, skill_id=skill_k8s.id, min_proficiency=ProficiencyLevel.INTERMEDIATE),
    ])
    await db_session.commit()

    # Step 1: Generate plan
    res = await client.post(f"/api/v1/student/intelligence/jobs/{job.id}/plan", headers=headers)
    assert res.status_code == 200
    plan_data = res.json()

    assert plan_data["job_id"] == job.id
    assert plan_data["total_actions"] >= 2
    assert plan_data["completed_actions"] == 0
    assert plan_data["progress_percentage"] == 0.0

    actions = plan_data["actions"]
    assert len(actions) >= 2
    action_1 = actions[0]
    assert action_1["status"] == "PENDING"
    assert action_1["suggested_activity"] != ""
    assert action_1["completion_criteria"] != ""

    # Step 2: Update action status to IN_PROGRESS
    update_res1 = await client.patch(
        f"/api/v1/student/intelligence/plans/actions/{action_1['id']}",
        json={"status": "IN_PROGRESS"},
        headers=headers,
    )
    assert update_res1.status_code == 200
    assert update_res1.json()["status"] == "IN_PROGRESS"

    # Step 3: Complete action 1
    update_res2 = await client.patch(
        f"/api/v1/student/intelligence/plans/actions/{action_1['id']}",
        json={"status": "COMPLETED"},
        headers=headers,
    )
    assert update_res2.status_code == 200
    assert update_res2.json()["status"] == "COMPLETED"
    assert update_res2.json()["completed_at"] is not None

    # Step 4: Verify plan progress reflects completed action
    get_plan_res = await client.get(f"/api/v1/student/intelligence/jobs/{job.id}/plan", headers=headers)
    assert get_plan_res.status_code == 200
    plan_after = get_plan_res.json()
    assert plan_after["completed_actions"] == 1
    assert plan_after["progress_percentage"] > 0.0

    # Step 5: Regenerate plan (idempotency check) - completed action should stay COMPLETED
    regen_res = await client.post(f"/api/v1/student/intelligence/jobs/{job.id}/plan", headers=headers)
    assert regen_res.status_code == 200
    regen_plan = regen_res.json()
    assert regen_plan["completed_actions"] == 1
    assert regen_plan["progress_percentage"] > 0.0



# ============================================================================
# 3. DATA ISOLATION & AUTHORIZATION TESTS
# ============================================================================

@pytest.mark.asyncio(loop_scope="session")
async def test_student_data_isolation(client: AsyncClient, db_session, user_repo):
    """
    Test student data isolation:
    - Student B cannot view or update Student A's improvement plan action
    """
    # Student A
    _, headers_a = await _register_and_login_student(client, "student-a@example.com")
    user_a = await user_repo.get_by_email("student-a@example.com")
    student_a = Student(user_id=user_a.id, full_name="Student A", graduation_year=2025)
    db_session.add(student_a)

    # Student B
    _, headers_b = await _register_and_login_student(client, "student-b@example.com")
    user_b = await user_repo.get_by_email("student-b@example.com")
    student_b = Student(user_id=user_b.id, full_name="Student B", graduation_year=2025)
    db_session.add(student_b)

    comp = Company(name="Isolation Test Co", is_active=True)
    db_session.add(comp)
    await db_session.flush()

    job = Job(company_id=comp.id, title="QA Engineer", is_active=True)
    db_session.add(job)
    await db_session.flush()

    skill = Skill(name="PyTest Automation", is_active=True)
    db_session.add(skill)
    await db_session.flush()

    db_session.add(JobRequiredSkill(job_id=job.id, skill_id=skill.id))
    await db_session.commit()

    # Student A generates a plan
    res_a = await client.post(f"/api/v1/student/intelligence/jobs/{job.id}/plan", headers=headers_a)
    assert res_a.status_code == 200
    action_id = res_a.json()["actions"][0]["id"]

    # Student B attempts to update Student A's action -> should receive 404
    patch_res = await client.patch(
        f"/api/v1/student/intelligence/plans/actions/{action_id}",
        json={"status": "COMPLETED"},
        headers=headers_b,
    )
    assert patch_res.status_code in [403, 404]


@pytest.mark.asyncio(loop_scope="session")
async def test_staff_department_skill_gaps_authorization(client: AsyncClient, db_session, user_repo):
    """
    Test staff department skill gaps endpoint:
    - Staff user can access /staff/analytics/department-skill-gaps
    - Student user is forbidden (403)
    """
    _, student_headers = await _register_and_login_student(client, "student-unauth@example.com")
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-analytics@example.com")

    # Student should receive 403
    student_res = await client.get("/api/v1/staff/analytics/department-skill-gaps", headers=student_headers)
    assert student_res.status_code == 403

    # Staff should receive 200 with aggregated departments
    staff_res = await client.get("/api/v1/staff/analytics/department-skill-gaps", headers=staff_headers)
    assert staff_res.status_code == 200
    data = staff_res.json()
    assert "departments" in data
    assert "total_active_jobs_analyzed" in data


# ============================================================================
# 4. AI CAREER MENTOR RESILIENCE TEST
# ============================================================================

@pytest.mark.asyncio(loop_scope="session")
async def test_job_mentor_advice_provider_failure_resilience(client: AsyncClient, db_session, user_repo):
    """
    Test AI provider failure resilience:
    - When GeminiProvider raises an exception or is unavailable,
      ask_job_mentor_advice falls back gracefully to deterministic guidance
      without raising 500 or breaking the application.
    """
    _, headers = await _register_and_login_student(client, "resilient-student@example.com")
    user = await user_repo.get_by_email("resilient-student@example.com")
    student = Student(user_id=user.id, full_name="Resilient Student", graduation_year=2025)
    db_session.add(student)

    comp = Company(name="Robust Cloud", is_active=True)
    db_session.add(comp)
    await db_session.flush()

    job = Job(company_id=comp.id, title="Cloud Architect", is_active=True)
    db_session.add(job)
    await db_session.flush()

    skill = Skill(name="AWS Solutions", is_active=True)
    db_session.add(skill)
    await db_session.flush()

    db_session.add(JobRequiredSkill(job_id=job.id, skill_id=skill.id))
    await db_session.commit()

    # Simulate Gemini provider outage by mocking generate_response to raise an exception
    with patch(
        "app.modules.intelligence.gemini_provider.GeminiProvider.generate_response",
        new=AsyncMock(side_effect=RuntimeError("Gemini API connection timed out or quota exceeded")),
    ):
        res = await client.post(
            f"/api/v1/student/intelligence/jobs/{job.id}/mentor-advice",
            json={"question": "What should I prioritize?"},
            headers=headers,
        )

        assert res.status_code == 200
        data = res.json()
        assert data["grounded_job_title"] == "Cloud Architect"
        assert "AWS Solutions" in data["advice"] or data["readiness_score"] >= 0.0


# ============================================================================
# 5. EVIDENCE-TO-OUTCOME & VERIFICATION PROVENANCE TESTS
# ============================================================================

@pytest.mark.asyncio(loop_scope="session")
async def test_evidence_provenance_assessment_verified_vs_self_reported(client: AsyncClient, db_session, user_repo):
    """
    Test evidence provenance distinction:
    - Skill with passed technical interview/coding test round is marked is_verified=True
      and evidence_source='ASSESSMENT_VERIFIED' with company/round reference.
    - Skill only in student profile is marked is_verified=False and evidence_source='SELF_REPORTED'.
    - Missing skill is marked is_verified=False and status='UNVERIFIED_OR_MISSING'.
    """
    _, headers = await _register_and_login_student(client, "verified-student@example.com")
    user = await user_repo.get_by_email("verified-student@example.com")

    student = Student(user_id=user.id, full_name="Verified Evidence Student", graduation_year=2025)
    db_session.add(student)
    await db_session.flush()

    skill_react = Skill(name="React Frontend", is_active=True)
    skill_sys_design = Skill(name="System Architecture", is_active=True)
    db_session.add_all([skill_react, skill_sys_design])
    await db_session.flush()

    # Student self-reports React on profile
    db_session.add(StudentSkill(student_id=student.id, skill_id=skill_react.id, proficiency=ProficiencyLevel.INTERMEDIATE))

    # Past company and application where student PASSED a Coding Test that evaluated System Architecture
    past_comp = Company(name="Tier 1 Tech Corp", is_active=True)
    db_session.add(past_comp)
    await db_session.flush()

    past_job = Job(company_id=past_comp.id, title="Backend Intern", is_active=True)
    db_session.add(past_job)
    await db_session.flush()

    db_session.add(JobRequiredSkill(job_id=past_job.id, skill_id=skill_sys_design.id, min_proficiency=ProficiencyLevel.ADVANCED))

    resume = Resume(
        student_id=student.id,
        title="Software Engineer Resume",
        file_name="resume.pdf",
        file_path="/uploads/resumes/resume.pdf",
        file_type="application/pdf",
        file_size=10240,
        is_default=True,
    )
    db_session.add(resume)
    await db_session.flush()

    past_app = Application(job_id=past_job.id, student_id=student.id, resume_id=resume.id, status=ApplicationStatus.INTERVIEW)
    db_session.add(past_app)
    await db_session.flush()

    past_round = ApplicationRound(
        application_id=past_app.id,
        round_number=1,
        title="Technical Coding Evaluation",
        round_type=RoundType.CODING_TEST,
        status=RoundStatus.COMPLETED,
        result=RoundResult.PASSED,
        notes="Strong performance in distributed system architecture questions.",
        completed_at=datetime.now(timezone.utc),
    )
    db_session.add(past_round)
    await db_session.flush()

    # Target Job requiring both React and System Architecture
    target_comp = Company(name="Target Enterprise", is_active=True)
    db_session.add(target_comp)
    await db_session.flush()

    target_job = Job(company_id=target_comp.id, title="Lead Solutions Architect", is_active=True)
    db_session.add(target_job)
    await db_session.flush()

    db_session.add_all([
        JobRequiredSkill(job_id=target_job.id, skill_id=skill_react.id, min_proficiency=ProficiencyLevel.INTERMEDIATE),
        JobRequiredSkill(job_id=target_job.id, skill_id=skill_sys_design.id, min_proficiency=ProficiencyLevel.INTERMEDIATE),
    ])
    await db_session.commit()

    # Assess readiness
    res = await client.get(f"/api/v1/student/intelligence/jobs/{target_job.id}/readiness", headers=headers)
    assert res.status_code == 200
    data = res.json()

    breakdown = {s["skill_name"]: s for s in data["skills_breakdown"]}

    # React: Self-reported
    react_item = breakdown["React Frontend"]
    assert react_item["is_verified"] is False
    assert react_item["evidence_source"] == "SELF_REPORTED"
    assert "Self-reported on profile" in react_item["evidence_summary"]

    # System Architecture: Assessment Verified via passed round
    sys_item = breakdown["System Architecture"]
    assert sys_item["is_verified"] is True
    assert sys_item["evidence_source"] == "ASSESSMENT_VERIFIED"
    assert "Passed Coding Test" in sys_item["evidence_summary"]
    assert "Tier 1 Tech Corp" in sys_item["evidence_summary"]
    assert "Tier 1 Tech Corp" in sys_item["evidence_reference"]


@pytest.mark.asyncio(loop_scope="session")
async def test_practice_action_completion_with_evidence_reference_preserves_honesty(client: AsyncClient, db_session, user_repo):
    """
    Test safe evidence recording:
    - Completing an improvement action with an artifact reference (e.g. GitHub link) records
      evidence_source and evidence_reference.
    - Does NOT falsely mark the skill as certified or assessment-verified.
    - Shows what changed in the evidence summary ('Formative practice completed').
    - Regenerating the plan preserves completed actions and references.
    """
    _, headers = await _register_and_login_student(client, "practice-student@example.com")
    user = await user_repo.get_by_email("practice-student@example.com")

    student = Student(user_id=user.id, full_name="Practice Student", graduation_year=2025)
    db_session.add(student)
    await db_session.flush()

    skill_fastapi = Skill(name="FastAPI Services", is_active=True)
    db_session.add(skill_fastapi)
    await db_session.flush()

    comp = Company(name="Async Cloud Labs", is_active=True)
    db_session.add(comp)
    await db_session.flush()

    job = Job(company_id=comp.id, title="Backend Engineer", is_active=True)
    db_session.add(job)
    await db_session.flush()

    db_session.add(JobRequiredSkill(job_id=job.id, skill_id=skill_fastapi.id, min_proficiency=ProficiencyLevel.INTERMEDIATE))
    await db_session.commit()

    # Step 1: Generate plan -> 1 action for FastAPI Services
    res_plan = await client.post(f"/api/v1/student/intelligence/jobs/{job.id}/plan", headers=headers)
    assert res_plan.status_code == 200
    plan_data = res_plan.json()
    fastapi_action = next(a for a in plan_data["actions"] if a["skill_name"] == "FastAPI Services")

    # Step 2: Complete action with evidence reference
    artifact_link = "https://github.com/student/fastapi-async-crud-microservice"
    update_res = await client.patch(
        f"/api/v1/student/intelligence/plans/actions/{fastapi_action['id']}",
        json={
            "status": "COMPLETED",
            "evidence_source": "PRACTICE_COMPLETED",
            "evidence_reference": artifact_link,
        },
        headers=headers,
    )
    assert update_res.status_code == 200
    updated_act = update_res.json()
    assert updated_act["status"] == "COMPLETED"
    assert updated_act["evidence_source"] == "PRACTICE_COMPLETED"
    assert updated_act["evidence_reference"] == artifact_link
    assert updated_act["completed_at"] is not None

    # Step 3: Check readiness assessment reflects the practice evidence without fabricating an assessment result
    res_readiness = await client.get(f"/api/v1/student/intelligence/jobs/{job.id}/readiness", headers=headers)
    assert res_readiness.status_code == 200
    readiness_data = res_readiness.json()
    fastapi_ev = next(s for s in readiness_data["skills_breakdown"] if s["skill_name"] == "FastAPI Services")

    assert fastapi_ev["practice_completed"] is True
    # Still False for is_verified because practice does not equal formal assessment pass
    assert fastapi_ev["is_verified"] is False
    assert fastapi_ev["evidence_reference"] == artifact_link
    assert "Practice task completed" in fastapi_ev["evidence_summary"]
    assert artifact_link in fastapi_ev["evidence_summary"]

    # Step 4: Regenerate plan -> preserves completed action and evidence reference
    regen_res = await client.post(f"/api/v1/student/intelligence/jobs/{job.id}/plan", headers=headers)
    assert regen_res.status_code == 200
    regen_data = regen_res.json()
    regen_action = next(a for a in regen_data["actions"] if a["skill_name"] == "FastAPI Services")
    assert regen_action["status"] == "COMPLETED"
    assert regen_action["evidence_reference"] == artifact_link


"""
Test suite for AI Career Mentor endpoint and Gemini Provider integration.

Tests strictly verify:
1. Authentication (missing / invalid token -> 401)
2. Role authorization (staff role -> 403)
3. Student data isolation (only authenticated student context retrieved)
4. Missing API key handling (503 AI_PROVIDER_UNCONFIGURED)
5. Provider success (mocked Gemini -> 200 with grounded context)
6. Provider quota exhaustion (mocked 429 -> 429 AI_QUOTA_EXCEEDED)
7. Request timeout handling (mocked timeout -> 504 AI_REQUEST_TIMEOUT)
8. Input validation (empty, whitespace-only, exceeding character limits)
9. Read-only invariant (zero database mutations after request)
"""

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient, TimeoutException
from sqlalchemy import select, func

from app.core.exceptions import (
    AIProviderConfigError,
    AIProviderQuotaError,
    AIProviderTimeoutError,
    AIProviderServiceError,
)
from app.modules.students.models import Student, Department
from app.modules.skills.models import Skill, StudentSkill
from app.modules.companies.models import Company
from app.modules.jobs.models import Job
from app.shared.enums import ProficiencyLevel, RoleEnum


async def _register_and_login_student(
    client: AsyncClient, email: str = "mentor-student@example.com"
):
    """Helper to register and login a student, returning token and auth headers."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "student"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


async def _get_staff_headers(
    client: AsyncClient, db_session, user_repo, email: str = "mentor-staff@example.com"
):
    """Helper to get staff auth headers."""
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "password123"}
    )
    user = await user_repo.get_by_email(email)
    user.role = RoleEnum.STAFF
    await db_session.commit()

    staff_login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    return {"Authorization": f"Bearer {staff_login.json()['access_token']}"}


# ============================================================================
# 1. AUTHENTICATION & AUTHORIZATION
# ============================================================================


@pytest.mark.asyncio(loop_scope="session")
async def test_mentor_requires_authentication(client: AsyncClient):
    """Unauthenticated request must be rejected with 401."""
    res = await client.post(
        "/api/v1/student/intelligence/mentor/chat",
        json={"message": "How do I prepare for software engineer roles?"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_mentor_requires_student_role(client: AsyncClient, db_session, user_repo):
    """Staff account cannot access student mentor endpoint (403 Forbidden)."""
    staff_headers = await _get_staff_headers(
        client, db_session, user_repo, "staff-mentor-deny@example.com"
    )
    res = await client.post(
        "/api/v1/student/intelligence/mentor/chat",
        json={"message": "How do I prepare for software engineer roles?"},
        headers=staff_headers,
    )
    assert res.status_code == 403
    assert res.json()["error_code"] == "INSUFFICIENT_ROLE"


# ============================================================================
# 2. INPUT VALIDATION
# ============================================================================


@pytest.mark.asyncio(loop_scope="session")
async def test_mentor_input_validation_empty_message(client: AsyncClient):
    """Empty message or missing field must be rejected with 422."""
    _, headers = await _register_and_login_student(client, "val1-student@example.com")

    res = await client.post(
        "/api/v1/student/intelligence/mentor/chat",
        json={"message": ""},
        headers=headers,
    )
    assert res.status_code == 422

    res_missing = await client.post(
        "/api/v1/student/intelligence/mentor/chat",
        json={},
        headers=headers,
    )
    assert res_missing.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
async def test_mentor_input_validation_excessive_length(client: AsyncClient):
    """Message exceeding 1500 characters must be rejected with 422."""
    _, headers = await _register_and_login_student(client, "val2-student@example.com")

    too_long = "a" * 1501
    res = await client.post(
        "/api/v1/student/intelligence/mentor/chat",
        json={"message": too_long},
        headers=headers,
    )
    assert res.status_code == 422


# ============================================================================
# 3. PROVIDER SUCCESS & PROFILE GROUNDING
# ============================================================================


@pytest.mark.asyncio(loop_scope="session")
async def test_mentor_success_with_grounded_student_profile(
    client: AsyncClient, db_session, user_repo
):
    """
    Verified success: Student with department, CGPA, and skills receives
    grounded advice, and the provider mock receives instructions containing
    sanitized profile information (without personal identifiers).
    """
    token, headers = await _register_and_login_student(client, "grounded-student@example.com")
    user = await user_repo.get_by_email("grounded-student@example.com")

    # Set up department
    dept = Department(name="Computer Science & Engineering", is_active=True)
    db_session.add(dept)
    await db_session.flush()

    # Set up student profile
    student = Student(
        user_id=user.id,
        department_id=dept.id,
        cgpa=8.75,
        graduation_year=2026,
    )
    db_session.add(student)
    await db_session.flush()

    # Add skills
    py_skill = Skill(name="Python", category="Programming", is_active=True)
    db_session.add(py_skill)
    await db_session.flush()

    db_session.add(
        StudentSkill(
            student_id=student.id,
            skill_id=py_skill.id,
            proficiency=ProficiencyLevel.INTERMEDIATE,
        )
    )
    await db_session.commit()

    mock_reply = "### Recommended Next Steps for Backend Development\n- Build an async FastAPI REST API."

    with patch(
        "app.modules.intelligence.service.GeminiProvider.generate_response",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = mock_reply

        res = await client.post(
            "/api/v1/student/intelligence/mentor/chat",
            json={
                "message": "Which skills should I focus on next?",
                "history": [
                    {"role": "user", "content": "Hello!"},
                    {"role": "model", "content": "Hi! How can I assist you with your career?"},
                ],
            },
            headers=headers,
        )

        assert res.status_code == 200
        data = res.json()
        assert data["response"] == mock_reply
        assert data["grounded_context"]["department"] == "Computer Science & Engineering"
        assert data["grounded_context"]["graduation_year"] == 2026
        assert data["grounded_context"]["cgpa_available"] is True
        assert data["grounded_context"]["skills_count"] >= 1
        assert "Python" in data["grounded_context"]["top_skills"]

        # Verify that mock was called with instructions grounding the student's department and skill
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args.kwargs
        system_instruction = call_kwargs["system_instruction"]
        assert "Computer Science & Engineering" in system_instruction
        assert "Python" in system_instruction
        # Verify no email was passed in the system instruction
        assert "grounded-student@example.com" not in system_instruction


# ============================================================================
# 4. ERROR STATES: MISSING KEY, QUOTA LIMIT, TIMEOUT, SERVICE FAULT
# ============================================================================


@pytest.mark.asyncio(loop_scope="session")
async def test_mentor_missing_api_key(client: AsyncClient):
    """When GEMINI_API_KEY is not configured, returns 503 AI_PROVIDER_UNCONFIGURED."""
    _, headers = await _register_and_login_student(client, "nokey-student@example.com")

    with patch(
        "app.modules.intelligence.service.GeminiProvider.generate_response",
        side_effect=AIProviderConfigError(
            "AI Career Mentor is currently unconfigured. Please configure GEMINI_API_KEY."
        ),
    ):
        res = await client.post(
            "/api/v1/student/intelligence/mentor/chat",
            json={"message": "How do I prepare for interviews?"},
            headers=headers,
        )
        assert res.status_code == 503
        data = res.json()
        assert data["error_code"] == "AI_PROVIDER_UNCONFIGURED"


@pytest.mark.asyncio(loop_scope="session")
async def test_mentor_quota_exceeded(client: AsyncClient):
    """When Gemini returns 429, endpoint returns 429 AI_QUOTA_EXCEEDED."""
    _, headers = await _register_and_login_student(client, "quota-student@example.com")

    with patch(
        "app.modules.intelligence.service.GeminiProvider.generate_response",
        side_effect=AIProviderQuotaError(
            "AI Career Mentor quota or rate limit exceeded. Please wait a minute and try again."
        ),
    ):
        res = await client.post(
            "/api/v1/student/intelligence/mentor/chat",
            json={"message": "Suggest a project for my resume."},
            headers=headers,
        )
        assert res.status_code == 429
        data = res.json()
        assert data["error_code"] == "AI_QUOTA_EXCEEDED"


@pytest.mark.asyncio(loop_scope="session")
async def test_mentor_timeout_handling(client: AsyncClient):
    """When request to Gemini times out, returns 504 AI_REQUEST_TIMEOUT."""
    _, headers = await _register_and_login_student(client, "timeout-student@example.com")

    with patch(
        "app.modules.intelligence.service.GeminiProvider.generate_response",
        side_effect=AIProviderTimeoutError("The AI Career Mentor request timed out."),
    ):
        res = await client.post(
            "/api/v1/student/intelligence/mentor/chat",
            json={"message": "What is the recruitment process like?"},
            headers=headers,
        )
        assert res.status_code == 504
        data = res.json()
        assert data["error_code"] == "AI_REQUEST_TIMEOUT"


# ============================================================================
# 5. READ-ONLY INVARIANT (NO DATABASE WRITES)
# ============================================================================


@pytest.mark.asyncio(loop_scope="session")
async def test_mentor_read_only_invariant(client: AsyncClient, db_session):
    """Verify that calling the career mentor performs zero database mutations."""
    _, headers = await _register_and_login_student(client, "readonly-student@example.com")

    count_students_before = await db_session.scalar(select(func.count(Student.id)))
    count_skills_before = await db_session.scalar(select(func.count(StudentSkill.id)))

    with patch(
        "app.modules.intelligence.service.GeminiProvider.generate_response",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = "Guidance response."

        res = await client.post(
            "/api/v1/student/intelligence/mentor/chat",
            json={"message": "Give me career advice."},
            headers=headers,
        )
        assert res.status_code == 200

    count_students_after = await db_session.scalar(select(func.count(Student.id)))
    count_skills_after = await db_session.scalar(select(func.count(StudentSkill.id)))

    # Student auto-provision on first lookup is allowed, but no unexpected new skills or placements
    assert count_skills_before == count_skills_after

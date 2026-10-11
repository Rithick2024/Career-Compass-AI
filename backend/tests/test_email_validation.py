"""
Comprehensive regression tests for demo login email validation.

Verifies:
1. Demo emails with RFC 2606 `.test` domains pass schema validation in local/dev/test.
2. Representative student demo emails pass schema validation.
3. Invalid email syntax (malformed strings, spaces, consecutive dots) remains strictly rejected.
4. Standard educational and commercial domains continue to pass.
5. Production mode (`APP_ENV=production`) strictly rejects `.test` domains while accepting standard domains.
6. The `ALLOW_TEST_EMAIL_DOMAINS` toggle correctly disables test domain acceptance even in non-production.
7. Login endpoint reaches authentication (returning 401 INVALID_CREDENTIALS on bad password)
   instead of failing at email syntax validation (422 VALIDATION_ERROR).
8. Full registration and login cycle works seamlessly with `.test` accounts.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.core.config import Settings, configure_email_validator, get_settings, settings
from app.core.jwt import decode_access_token
from app.modules.auth.schemas import (
    StaffRegisterRequest,
    UserLoginRequest,
    UserPublic,
    UserRegisterRequest,
)
from app.shared.enums import RoleEnum


# --- Fixtures for validator configuration cleanup ---

@pytest.fixture(autouse=True)
def ensure_default_validator_state():
    """Ensure each test starts and ends with the current environment settings active."""
    configure_email_validator(settings)
    yield
    configure_email_validator(settings)


# --- Unit Tests: Schema Validation ---

def test_staff_demo_email_passes_schema_validation():
    """staff.demo@example.test passes UserLoginRequest, StaffRegisterRequest, and UserPublic."""
    email = "staff.demo@example.test"

    # Login schema
    login_req = UserLoginRequest(email=email, password="AnyPassword123")
    assert login_req.email == email

    # Staff register schema
    staff_req = StaffRegisterRequest(email=email, password="AnyPassword123")
    assert staff_req.email == email

    # Public user response schema
    pub_user = UserPublic(
        id=1,
        email=email,
        role=RoleEnum.STAFF,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    assert pub_user.email == email


@pytest.mark.parametrize(
    "email",
    [
        "aarav.sharma@example.test",
        "rohan.verma@example.test",
        "priya.patel@example.test",
        "ananya.iyer@example.test",
        "vikram.aditya@example.test",
    ],
)
def test_representative_student_demo_emails_pass_schema_validation(email: str):
    """Synthetic student demo emails from the demo seeder pass validation."""
    login_req = UserLoginRequest(email=email, password="StudentPassword123")
    assert login_req.email == email

    reg_req = UserRegisterRequest(email=email, password="StudentPassword123")
    assert reg_req.email == email


@pytest.mark.parametrize(
    "malformed_email",
    [
        "not-an-email",
        "missing-at-sign.test",
        "@example.test",
        "user@",
        "user @example.test",
        "user..name@example.test",
        "user@.test",
        "user@example..test",
        "user@com",
        "user@-example.test",
        "user@example-.test",
        "user@example.test.",
    ],
)
def test_malformed_email_syntax_is_strictly_rejected(malformed_email: str):
    """
    Invalid email structures and syntax must fail validation even when test domains are enabled.
    Enabling test domains must NEVER disable or weaken fundamental email syntax verification.
    """
    with pytest.raises(ValidationError) as exc_info:
        UserLoginRequest(email=malformed_email, password="Password123")
    assert "value is not a valid email address" in str(exc_info.value)


@pytest.mark.parametrize(
    "valid_email",
    [
        "student@srmist.edu.in",
        "recruiter@google.com",
        "placement.officer@university.ac.in",
        "john.doe@sub.domain.co.uk",
    ],
)
def test_standard_domains_pass_validation(valid_email: str):
    """Standard internet domains continue to pass without regression."""
    req = UserLoginRequest(email=valid_email, password="Password123")
    assert req.email == valid_email


# --- Production Strictness and Configuration Tests ---

def test_production_environment_strictly_rejects_test_domains():
    """
    In production (APP_ENV=production), RFC 2606 test domains MUST be strictly rejected
    to prevent non-routable synthetic addresses in production user databases.
    """
    # Create production settings instance
    prod_settings = Settings(
        APP_ENV="production",
        POSTGRES_USER=settings.POSTGRES_USER,
        POSTGRES_PASSWORD=settings.POSTGRES_PASSWORD,
        POSTGRES_DB=settings.POSTGRES_DB,
        JWT_SECRET_KEY=settings.JWT_SECRET_KEY,
        ALLOW_TEST_EMAIL_DOMAINS=True,  # Even if True, production overrides it
    )
    assert prod_settings.is_production is True

    try:
        configure_email_validator(prod_settings)

        # In production, staff.demo@example.test MUST fail validation
        with pytest.raises(ValidationError) as exc_info:
            UserLoginRequest(email="staff.demo@example.test", password="Password123")
        assert "special-use or reserved name" in str(exc_info.value)

        # Standard real domains MUST still pass in production
        real_req = UserLoginRequest(email="placement@srmist.edu.in", password="Password123")
        assert real_req.email == "placement@srmist.edu.in"

    finally:
        # Restore normal environment
        configure_email_validator(settings)


def test_disabling_test_domains_in_development():
    """
    If an operator explicitly sets ALLOW_TEST_EMAIL_DOMAINS=False in development,
    test domains must be rejected.
    """
    dev_strict_settings = Settings(
        APP_ENV="development",
        POSTGRES_USER=settings.POSTGRES_USER,
        POSTGRES_PASSWORD=settings.POSTGRES_PASSWORD,
        POSTGRES_DB=settings.POSTGRES_DB,
        JWT_SECRET_KEY=settings.JWT_SECRET_KEY,
        ALLOW_TEST_EMAIL_DOMAINS=False,
    )

    try:
        configure_email_validator(dev_strict_settings)

        with pytest.raises(ValidationError) as exc_info:
            UserLoginRequest(email="staff.demo@example.test", password="Password123")
        assert "special-use or reserved name" in str(exc_info.value)

    finally:
        configure_email_validator(settings)


# --- Integration Tests: API Endpoints ---

@pytest.mark.asyncio(loop_scope="session")
async def test_api_login_with_demo_email_reaches_authentication(client):
    """
    POST /api/v1/auth/login with staff.demo@example.test must reach authentication logic.
    With an incorrect password, it must return 401 INVALID_CREDENTIALS, NOT 422 VALIDATION_ERROR.
    """
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "staff.demo@example.test", "password": "wrong_password_attempt"},
    )
    assert resp.status_code == 401
    data = resp.json()
    assert data["error_code"] == "INVALID_CREDENTIALS"
    assert data["message"] == "Invalid email or password."


@pytest.mark.asyncio(loop_scope="session")
async def test_api_login_with_student_demo_email_reaches_authentication(client):
    """
    POST /api/v1/auth/login with student demo email reaches authentication.
    """
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "aarav.sharma@example.test", "password": "wrong_password_attempt"},
    )
    assert resp.status_code == 401
    data = resp.json()
    assert data["error_code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio(loop_scope="session")
async def test_api_login_with_malformed_email_returns_validation_error(client):
    """
    POST /api/v1/auth/login with malformed email must continue to fail with 422 VALIDATION_ERROR.
    """
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": "AnyPassword123"},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio(loop_scope="session")
async def test_demo_user_registration_and_login_lifecycle(client):
    """
    Verifies that a student demo account with .test domain can be registered,
    rejects bad credentials on login, and successfully authenticates with correct credentials.
    """
    demo_email = "regression.student@example.test"
    password = "SecurePassword123"

    # 1. Register student
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": demo_email, "password": password},
    )
    assert reg_resp.status_code == 201
    reg_body = reg_resp.json()
    assert reg_body["email"] == demo_email
    assert reg_body["role"] == "student"

    # 2. Duplicate registration rejected
    dupe_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": demo_email, "password": password},
    )
    assert dupe_resp.status_code == 409
    assert dupe_resp.json()["error_code"] == "EMAIL_ALREADY_REGISTERED"

    # 3. Login with wrong password returns 401
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": demo_email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401
    assert bad_login.json()["error_code"] == "INVALID_CREDENTIALS"

    # 4. Login with correct password returns 200 and valid JWT
    good_login = await client.post(
        "/api/v1/auth/login",
        json={"email": demo_email, "password": password},
    )
    assert good_login.status_code == 200
    login_body = good_login.json()
    assert login_body["token_type"] == "bearer"
    assert login_body["user"]["email"] == demo_email
    assert login_body["user"]["role"] == "student"

    token = login_body["access_token"]
    payload = decode_access_token(token)
    assert payload["sub"] == str(login_body["user"]["id"])


@pytest.mark.asyncio(loop_scope="session")
async def test_staff_demo_registration_and_login_lifecycle(client):
    """
    Verifies that staff account with .test domain can be registered via dev endpoint
    and subsequently login with full staff role privileges.
    """
    staff_email = "regression.staff@example.test"
    password = "StaffPassword123"

    # Register staff
    reg_resp = await client.post(
        "/api/v1/auth/staff-register",
        json={"email": staff_email, "password": password},
    )
    assert reg_resp.status_code == 201
    assert reg_resp.json()["email"] == staff_email
    assert reg_resp.json()["role"] == "staff"

    # Login as staff
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": staff_email, "password": password},
    )
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["user"]["role"] == "staff"
    assert body["user"]["email"] == staff_email

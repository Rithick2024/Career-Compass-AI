"""
Focused tests for the Resume module.

Covers: create/retrieve/update/delete lifecycle, the 404-until-created
design decision (see ResumeService's module docstring), validation,
duplicate detection, and ownership isolation. Deliberately kept narrow
per scope — not a full test suite for the whole app.
"""

import pytest

from app.shared.enums import RoleEnum

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _register_and_login(client, email: str, password: str = "SecurePass123") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- GET before any resume exists ------------------------------------------

async def test_get_resume_before_creation_returns_404(client):
    """
    No resume auto-provisioning (unlike the student profile) — see
    ResumeService's module docstring for why.
    """
    token = await _register_and_login(client, "no-resume-yet@example.com")
    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_NOT_FOUND"


# --- POST (create) ----------------------------------------------------------

async def test_create_resume(client):
    token = await _register_and_login(client, "create-resume@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={
            "professional_summary": "  Aspiring backend engineer.  ",
            "career_objective": "Land a great internship.",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    # Whitespace trimmed.
    assert body["professional_summary"] == "Aspiring backend engineer."
    assert body["career_objective"] == "Land a great internship."
    assert body["student_id"] is not None
    assert "password_hash" not in body
    assert "email" not in body


async def test_get_resume_after_creation(client):
    token = await _register_and_login(client, "get-after-create@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "Summary text"},
    )
    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["professional_summary"] == "Summary text"


async def test_create_duplicate_resume_rejected(client):
    token = await _register_and_login(client, "duplicate-resume@example.com")
    payload = {"professional_summary": "First"}
    first = await client.post(
        "/api/v1/students/me/resume", headers=_auth_headers(token), json=payload
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/students/me/resume", headers=_auth_headers(token), json={"professional_summary": "Second"}
    )
    assert second.status_code == 409
    assert second.json()["error_code"] == "RESUME_ALREADY_EXISTS"


async def test_create_resume_with_null_fields(client):
    """Both fields are optional/nullable — an empty resume is valid."""
    token = await _register_and_login(client, "empty-resume@example.com")
    resp = await client.post("/api/v1/students/me/resume", headers=_auth_headers(token), json={})
    assert resp.status_code == 201
    body = resp.json()
    assert body["professional_summary"] is None
    assert body["career_objective"] is None


# --- PATCH (partial update) -------------------------------------------------

async def test_patch_updates_only_supplied_fields(client):
    token = await _register_and_login(client, "partial-patch@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "Original summary", "career_objective": "Original objective"},
    )

    resp = await client.patch(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"career_objective": "Updated objective"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # The field from creation must survive the PATCH that didn't touch it.
    assert body["professional_summary"] == "Original summary"
    assert body["career_objective"] == "Updated objective"


async def test_patch_can_clear_field_with_explicit_null(client):
    token = await _register_and_login(client, "clear-field@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "Will be cleared", "career_objective": "Stays"},
    )

    resp = await client.patch(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": None},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["professional_summary"] is None
    assert body["career_objective"] == "Stays"


async def test_patch_when_no_resume_exists_returns_404(client):
    token = await _register_and_login(client, "patch-no-resume@example.com")
    resp = await client.patch(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"career_objective": "Should fail"},
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_NOT_FOUND"


# --- DELETE ------------------------------------------------------------------

async def test_delete_resume(client):
    token = await _register_and_login(client, "delete-resume@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "To be deleted"},
    )

    resp = await client.delete("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 204


async def test_get_after_delete_returns_404(client):
    token = await _register_and_login(client, "get-after-delete@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "Temporary"},
    )
    await client.delete("/api/v1/students/me/resume", headers=_auth_headers(token))

    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_NOT_FOUND"


async def test_delete_when_no_resume_exists_returns_404(client):
    token = await _register_and_login(client, "delete-no-resume@example.com")
    resp = await client.delete("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_NOT_FOUND"


async def test_create_after_delete_succeeds(client):
    """The 404-after-delete state is not permanent — a new resume can
    be created afterward, same as any other 0..1 resource."""
    token = await _register_and_login(client, "recreate-after-delete@example.com")
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "First resume"},
    )
    await client.delete("/api/v1/students/me/resume", headers=_auth_headers(token))

    resp = await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "Second resume"},
    )
    assert resp.status_code == 201
    assert resp.json()["professional_summary"] == "Second resume"


# --- Validation --------------------------------------------------------------

async def test_create_rejects_extra_fields(client):
    """Cannot smuggle student_id (or any other field) through the create schema."""
    token = await _register_and_login(client, "extra-fields@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "ok", "student_id": 999999},
    )
    assert resp.status_code == 422


async def test_create_rejects_too_long_professional_summary(client):
    token = await _register_and_login(client, "too-long-summary@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "a" * 2001},
    )
    assert resp.status_code == 422


async def test_create_rejects_too_long_career_objective(client):
    token = await _register_and_login(client, "too-long-objective@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"career_objective": "a" * 1001},
    )
    assert resp.status_code == 422


# --- Authentication ------------------------------------------------------

async def test_get_resume_no_token_rejected(client):
    resp = await client.get("/api/v1/students/me/resume")
    assert resp.status_code == 401


async def test_get_resume_invalid_token_rejected(client):
    resp = await client.get(
        "/api/v1/students/me/resume", headers=_auth_headers("not.a.valid.token")
    )
    assert resp.status_code == 401


# --- Authorization (role) ---------------------------------------------------

async def test_admin_cannot_access_student_resume_endpoint(client, db_session, user_repo):
    token = await _register_and_login(client, "admin-blocked-resume@example.com")
    user = await user_repo.get_by_email("admin-blocked-resume@example.com")
    user.role = RoleEnum.ADMIN
    await db_session.commit()

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin-blocked-resume@example.com", "password": "SecurePass123"},
    )
    admin_token = admin_login.json()["access_token"]

    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(admin_token))
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "INSUFFICIENT_ROLE"


# --- Ownership ---------------------------------------------------------------

async def test_student_cannot_see_another_students_resume(client):
    token_a = await _register_and_login(client, "resume-owner-a@example.com")
    token_b = await _register_and_login(client, "resume-owner-b@example.com")

    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token_a),
        json={"professional_summary": "Student A's resume"},
    )

    # Student B's own GET must be 404 — not seeing A's resume, and
    # there is no endpoint that accepts a client-supplied student id
    # to even attempt cross-access.
    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token_b))
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_NOT_FOUND"


async def test_student_b_patch_and_delete_do_not_affect_student_a(client):
    token_a = await _register_and_login(client, "resume-isolation-a@example.com")
    token_b = await _register_and_login(client, "resume-isolation-b@example.com")

    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token_a),
        json={"professional_summary": "A's original summary"},
    )

    # B has no resume of their own — PATCH/DELETE must 404 for B,
    # never touching A's row.
    patch_resp = await client.patch(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token_b),
        json={"professional_summary": "B trying to overwrite"},
    )
    assert patch_resp.status_code == 404

    delete_resp = await client.delete(
        "/api/v1/students/me/resume", headers=_auth_headers(token_b)
    )
    assert delete_resp.status_code == 404

    # A's resume is untouched by B's failed attempts.
    a_resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token_a))
    assert a_resp.status_code == 200
    assert a_resp.json()["professional_summary"] == "A's original summary"


# ============================================================================
# File upload / download / delete-file
#
# `isolated_upload_dir` redirects storage writes to a pytest tmp_path for
# the duration of each test that needs it — file tests never touch the
# real `uploads/` directory. `settings.RESUME_UPLOAD_DIR` is read fresh on
# every call inside app.modules.resumes.storage (not cached at import
# time), specifically so this kind of monkeypatch works.
# ============================================================================

from app.core.config import settings

_VALID_PDF_BYTES = b"%PDF-1.4\n" + b"x" * 200
_VALID_DOC_BYTES = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"x" * 200
_VALID_DOCX_BYTES = b"PK\x03\x04" + b"x" * 200
_EXE_BYTES = b"MZ" + b"x" * 200


@pytest.fixture
def isolated_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "RESUME_UPLOAD_DIR", str(tmp_path))
    yield tmp_path


async def _create_resume_with_token(client, email: str) -> str:
    token = await _register_and_login(client, email)
    await client.post(
        "/api/v1/students/me/resume",
        headers=_auth_headers(token),
        json={"professional_summary": "Has a resume"},
    )
    return token


# --- Resume without a file remains valid ------------------------------------

async def test_resume_without_file_has_null_file_fields(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "no-file-resume@example.com")
    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_file"] is False
    assert body["file_name"] is None
    assert body["file_type"] is None
    assert body["file_size"] is None
    assert "file_path" not in body  # never exposed


# --- Upload: valid formats --------------------------------------------------

async def test_upload_valid_pdf(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "upload-pdf@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_file"] is True
    assert body["file_name"] == "resume.pdf"
    assert body["file_type"] == "application/pdf"
    assert body["file_size"] == len(_VALID_PDF_BYTES)


async def test_upload_valid_doc(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "upload-doc@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("resume.doc", _VALID_DOC_BYTES, "application/msword")},
    )
    assert resp.status_code == 200
    assert resp.json()["file_name"] == "resume.doc"


async def test_upload_valid_docx(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "upload-docx@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={
            "file": (
                "resume.docx",
                _VALID_DOCX_BYTES,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert resp.status_code == 200
    assert resp.json()["file_name"] == "resume.docx"


async def test_upload_file_metadata_returned_correctly(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "metadata-check@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("my_resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    body = resp.json()
    assert body["file_name"] == "my_resume.pdf"
    assert body["file_type"] == "application/pdf"
    assert body["file_size"] == len(_VALID_PDF_BYTES)
    assert body["has_file"] is True
    assert "file_path" not in body


async def test_upload_without_existing_resume_returns_404(client, isolated_upload_dir):
    token = await _register_and_login(client, "upload-no-resume@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_NOT_FOUND"


# --- Download ----------------------------------------------------------------

async def test_download_returns_correct_file(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "download-file@example.com")
    await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )

    resp = await client.get("/api/v1/students/me/resume/file", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.content == _VALID_PDF_BYTES
    assert resp.headers["content-type"] == "application/pdf"
    assert 'filename="resume.pdf"' in resp.headers["content-disposition"]


async def test_download_when_no_file_exists_returns_404(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "download-no-file@example.com")
    resp = await client.get("/api/v1/students/me/resume/file", headers=_auth_headers(token))
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_FILE_NOT_FOUND"


async def test_download_no_token_rejected(client, isolated_upload_dir):
    resp = await client.get("/api/v1/students/me/resume/file")
    assert resp.status_code == 401


# --- Replace -------------------------------------------------------------

async def test_replace_existing_file(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "replace-file@example.com")
    await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("first.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )

    resp = await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={
            "file": (
                "second.docx",
                _VALID_DOCX_BYTES,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["file_name"] == "second.docx"

    # Only one physical file should remain for this student (the old
    # one was cleaned up, not left orphaned).
    student_dirs = list(isolated_upload_dir.glob("*/*"))
    assert len(student_dirs) == 1

    # Downloading now returns the NEW file's content, not the old one.
    download = await client.get("/api/v1/students/me/resume/file", headers=_auth_headers(token))
    assert download.content == _VALID_DOCX_BYTES


# --- Delete file only vs. delete whole resume -------------------------------

async def test_delete_file_only(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "delete-file-only@example.com")
    await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )

    resp = await client.delete("/api/v1/students/me/resume/file", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_file"] is False
    assert body["file_name"] is None


async def test_resume_profile_remains_after_file_deletion(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "profile-survives-file-delete@example.com")
    await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    await client.delete("/api/v1/students/me/resume/file", headers=_auth_headers(token))

    resp = await client.get("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["professional_summary"] == "Has a resume"


async def test_delete_file_when_no_file_exists_returns_404(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "delete-no-file@example.com")
    resp = await client.delete("/api/v1/students/me/resume/file", headers=_auth_headers(token))
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "RESUME_FILE_NOT_FOUND"


async def test_delete_entire_resume_also_removes_physical_file(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "delete-resume-removes-file@example.com")
    await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    assert list(isolated_upload_dir.glob("*/*"))  # file exists on disk

    resp = await client.delete("/api/v1/students/me/resume", headers=_auth_headers(token))
    assert resp.status_code == 204

    # Physical file was cleaned up along with the DB record.
    assert not list(isolated_upload_dir.glob("*/*"))


# --- Validation ----------------------------------------------------------

async def test_upload_invalid_extension_rejected(client, isolated_upload_dir):
    token = await _create_resume_with_token(client, "invalid-extension@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("virus.exe", _EXE_BYTES, "application/x-msdownload")},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "UNSUPPORTED_FILE_TYPE"


async def test_upload_content_type_mismatch_rejected(client, isolated_upload_dir):
    """Extension says .pdf, but the declared Content-Type is something
    clearly unrelated (not just a permissive fallback)."""
    token = await _create_resume_with_token(client, "content-type-mismatch@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "image/png")},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "CONTENT_TYPE_MISMATCH"


async def test_upload_content_signature_mismatch_rejected(client, isolated_upload_dir):
    """Extension AND declared type say .pdf, but the actual file bytes
    are not a PDF — caught by the magic-byte signature check, not just
    trusting the label."""
    token = await _create_resume_with_token(client, "signature-mismatch@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("fake.pdf", _EXE_BYTES, "application/pdf")},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "FILE_CONTENT_MISMATCH"


async def test_upload_file_too_large_rejected(client, isolated_upload_dir, monkeypatch):
    # Shrink the limit for this test so we don't need a real multi-MB
    # payload to exercise the size check.
    monkeypatch.setattr(settings, "RESUME_MAX_FILE_SIZE_MB", 1)
    oversized = b"%PDF-1.4\n" + b"x" * (2 * 1024 * 1024)  # 2 MB, over the 1 MB test limit

    token = await _create_resume_with_token(client, "too-large@example.com")
    resp = await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("big.pdf", oversized, "application/pdf")},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "FILE_TOO_LARGE"

    # The oversized, rejected upload must not leave a partial file behind.
    assert not list(isolated_upload_dir.glob("*/*"))


# --- Authentication / authorization -----------------------------------------

async def test_upload_no_token_rejected(client, isolated_upload_dir):
    resp = await client.post(
        "/api/v1/students/me/resume/file",
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    assert resp.status_code == 401


async def test_upload_as_admin_rejected(client, isolated_upload_dir, db_session, user_repo):
    token = await _create_resume_with_token(client, "admin-upload-blocked@example.com")
    user = await user_repo.get_by_email("admin-upload-blocked@example.com")
    user.role = RoleEnum.ADMIN
    await db_session.commit()

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin-upload-blocked@example.com", "password": "SecurePass123"},
    )
    admin_token = admin_login.json()["access_token"]

    resp = await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(admin_token),
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "INSUFFICIENT_ROLE"


async def test_download_as_admin_rejected(client, isolated_upload_dir, db_session, user_repo):
    token = await _create_resume_with_token(client, "admin-download-blocked@example.com")
    await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token),
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )

    user = await user_repo.get_by_email("admin-download-blocked@example.com")
    user.role = RoleEnum.ADMIN
    await db_session.commit()

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin-download-blocked@example.com", "password": "SecurePass123"},
    )
    admin_token = admin_login.json()["access_token"]

    resp = await client.get(
        "/api/v1/students/me/resume/file", headers=_auth_headers(admin_token)
    )
    assert resp.status_code == 403


# --- Ownership ---------------------------------------------------------------

async def test_student_cannot_access_another_students_file(client, isolated_upload_dir):
    token_a = await _create_resume_with_token(client, "file-owner-a@example.com")
    await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token_a),
        files={"file": ("a_resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )

    token_b = await _register_and_login(client, "file-owner-b@example.com")

    # B has no resume of their own — every file endpoint 404s, never
    # returning or affecting A's file.
    download = await client.get("/api/v1/students/me/resume/file", headers=_auth_headers(token_b))
    assert download.status_code == 404

    delete_resp = await client.delete(
        "/api/v1/students/me/resume/file", headers=_auth_headers(token_b)
    )
    assert delete_resp.status_code == 404

    # A's file is untouched.
    a_download = await client.get(
        "/api/v1/students/me/resume/file", headers=_auth_headers(token_a)
    )
    assert a_download.status_code == 200
    assert a_download.content == _VALID_PDF_BYTES


async def test_student_cannot_manipulate_another_students_path(client, isolated_upload_dir):
    """
    There is no path/filename/id parameter anywhere in the file
    endpoints for a client to manipulate in the first place — the file
    is located entirely from the authenticated student's own resume
    row. Confirm a query-string injection attempt is simply ignored
    (the endpoint doesn't read any such parameter), not honored.
    """
    token_a = await _create_resume_with_token(client, "path-owner-a@example.com")
    await client.post(
        "/api/v1/students/me/resume/file",
        headers=_auth_headers(token_a),
        files={"file": ("a_resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )

    token_b = await _register_and_login(client, "path-owner-b@example.com")

    # Attempt to smuggle a path/id via query string — the endpoint has
    # no such parameter, so this must have no effect: B still gets
    # their own (nonexistent) resume's 404, never A's file.
    resp = await client.get(
        "/api/v1/students/me/resume/file?student_id=1&file_path=../../etc/passwd",
        headers=_auth_headers(token_b),
    )
    assert resp.status_code == 404

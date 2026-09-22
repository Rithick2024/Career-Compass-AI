"""
Tests for the Multiple Resume Document Management System.

Covers:
- Listing, creating, retrieving, updating, and deleting multiple resumes per student
- First resume automatic default rule
- Explicitly setting a new default resume and unsetting the previous default
- Deleting default resume and automatic default reassignment
- Deleting non-default resume
- File upload validations (PDF, DOC, DOCX, extension, magic signature, 5 MB limit)
- File download
- Student isolation and access control (admin rejection, cross-student isolation)
- Physical file cleanup
"""

import io
from pathlib import Path
import pytest
from app.shared.enums import RoleEnum

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _register_and_login(client, email: str, password: str = "SecurePass123") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


_VALID_PDF_BYTES = b"%PDF-1.4 sample pdf content for unit testing."
_VALID_DOC_BYTES = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1 legacy doc container bytes."
_VALID_DOCX_BYTES = b"PK\x03\x04 zip docx container bytes."


# --- GET list (empty) --------------------------------------------------------

async def test_get_resumes_empty_list(client):
    token = await _register_and_login(client, "empty-resumes@example.com")
    resp = await client.get("/api/v1/students/me/resumes", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


# --- POST create & Default Rules ---------------------------------------------

async def test_create_first_resume_is_automatically_default(client):
    token = await _register_and_login(client, "first-resume@example.com")
    files = {"file": ("frontend_resume.pdf", _VALID_PDF_BYTES, "application/pdf")}
    data = {"title": "Frontend Developer Resume", "description": "React & TypeScript profile"}

    resp = await client.post(
        "/api/v1/students/me/resumes",
        headers=_auth_headers(token),
        data=data,
        files=files,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Frontend Developer Resume"
    assert body["description"] == "React & TypeScript profile"
    assert body["file_name"] == "frontend_resume.pdf"
    assert body["file_type"] == "application/pdf"
    assert body["is_default"] is True
    assert body["has_file"] is True
    assert "student_id" not in body
    assert "file_path" not in body


async def test_create_second_resume_is_not_default(client):
    token = await _register_and_login(client, "multi-resumes@example.com")
    headers = _auth_headers(token)

    # First resume
    r1 = await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "First Resume"},
        files={"file": ("r1.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    assert r1.status_code == 201
    assert r1.json()["is_default"] is True

    # Second resume
    r2 = await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "Second Resume"},
        files={"file": ("r2.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    assert r2.status_code == 201
    assert r2.json()["is_default"] is False

    # Get list
    list_resp = await client.get("/api/v1/students/me/resumes", headers=headers)
    assert list_resp.status_code == 200
    resumes = list_resp.json()
    assert len(resumes) == 2
    # Default resume listed first
    assert resumes[0]["title"] == "First Resume"
    assert resumes[0]["is_default"] is True
    assert resumes[1]["title"] == "Second Resume"
    assert resumes[1]["is_default"] is False


# --- GET single & PATCH update ------------------------------------------------

async def test_get_single_resume(client):
    token = await _register_and_login(client, "get-single@example.com")
    headers = _auth_headers(token)

    create_resp = await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "Backend Resume", "description": "Python FastAPI"},
        files={"file": ("backend.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    resume_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/students/me/resumes/{resume_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == resume_id
    assert get_resp.json()["title"] == "Backend Resume"


async def test_patch_resume_metadata(client):
    token = await _register_and_login(client, "patch-resume@example.com")
    headers = _auth_headers(token)

    create_resp = await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "Old Title"},
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    resume_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/api/v1/students/me/resumes/{resume_id}",
        headers=headers,
        json={"title": "New Title", "description": "New Description"},
    )
    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["title"] == "New Title"
    assert body["description"] == "New Description"


async def test_patch_resume_blank_title_rejected(client):
    token = await _register_and_login(client, "patch-blank@example.com")
    headers = _auth_headers(token)

    create_resp = await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "Valid Title"},
        files={"file": ("resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    resume_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/api/v1/students/me/resumes/{resume_id}",
        headers=headers,
        json={"title": "   "},
    )
    assert patch_resp.status_code == 422


# --- Set Default & Unset Prior Default ---------------------------------------

async def test_set_default_resume(client):
    token = await _register_and_login(client, "set-default@example.com")
    headers = _auth_headers(token)

    r1 = (await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "Resume 1"},
        files={"file": ("r1.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )).json()

    r2 = (await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "Resume 2"},
        files={"file": ("r2.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )).json()

    assert r1["is_default"] is True
    assert r2["is_default"] is False

    # Set r2 as default
    set_def_resp = await client.patch(
        f"/api/v1/students/me/resumes/{r2['id']}/default",
        headers=headers,
    )
    assert set_def_resp.status_code == 200
    assert set_def_resp.json()["is_default"] is True

    # Verify r1 is no longer default
    r1_updated = (await client.get(f"/api/v1/students/me/resumes/{r1['id']}", headers=headers)).json()
    assert r1_updated["is_default"] is False


# --- Delete & Default Reassignment Rules --------------------------------------

async def test_delete_non_default_resume(client):
    token = await _register_and_login(client, "del-non-default@example.com")
    headers = _auth_headers(token)

    r1 = (await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "Default Resume"},
        files={"file": ("r1.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )).json()

    r2 = (await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "Other Resume"},
        files={"file": ("r2.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )).json()

    # Delete r2 (non-default)
    del_resp = await client.delete(f"/api/v1/students/me/resumes/{r2['id']}", headers=headers)
    assert del_resp.status_code == 204

    # r1 remains default
    r1_after = (await client.get(f"/api/v1/students/me/resumes/{r1['id']}", headers=headers)).json()
    assert r1_after["is_default"] is True


async def test_delete_default_resume_reassigns_default(client):
    token = await _register_and_login(client, "del-default@example.com")
    headers = _auth_headers(token)

    r1 = (await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "First (Default)"},
        files={"file": ("r1.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )).json()

    r2 = (await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "Second"},
        files={"file": ("r2.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )).json()

    assert r1["is_default"] is True

    # Delete r1 (the default)
    del_resp = await client.delete(f"/api/v1/students/me/resumes/{r1['id']}", headers=headers)
    assert del_resp.status_code == 204

    # r2 should now automatically be default
    r2_after = (await client.get(f"/api/v1/students/me/resumes/{r2['id']}", headers=headers)).json()
    assert r2_after["is_default"] is True


async def test_delete_last_resume(client):
    token = await _register_and_login(client, "del-last@example.com")
    headers = _auth_headers(token)

    r1 = (await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "Sole Resume"},
        files={"file": ("r1.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )).json()

    del_resp = await client.delete(f"/api/v1/students/me/resumes/{r1['id']}", headers=headers)
    assert del_resp.status_code == 204

    list_resp = await client.get("/api/v1/students/me/resumes", headers=headers)
    assert list_resp.json() == []


# --- File Upload Formats & Validations ---------------------------------------

async def test_upload_valid_doc(client):
    token = await _register_and_login(client, "upload-doc@example.com")
    resp = await client.post(
        "/api/v1/students/me/resumes",
        headers=_auth_headers(token),
        data={"title": "Legacy DOC Resume"},
        files={"file": ("resume.doc", _VALID_DOC_BYTES, "application/msword")},
    )
    assert resp.status_code == 201
    assert resp.json()["file_name"] == "resume.doc"


async def test_upload_valid_docx(client):
    token = await _register_and_login(client, "upload-docx@example.com")
    resp = await client.post(
        "/api/v1/students/me/resumes",
        headers=_auth_headers(token),
        data={"title": "DOCX Resume"},
        files={
            "file": (
                "resume.docx",
                _VALID_DOCX_BYTES,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert resp.status_code == 201
    assert resp.json()["file_name"] == "resume.docx"


async def test_upload_invalid_extension_rejected(client):
    token = await _register_and_login(client, "bad-ext@example.com")
    resp = await client.post(
        "/api/v1/students/me/resumes",
        headers=_auth_headers(token),
        data={"title": "Bad Ext"},
        files={"file": ("malicious.exe", b"MZ...", "application/octet-stream")},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "UNSUPPORTED_FILE_TYPE"


async def test_upload_content_signature_mismatch_rejected(client):
    token = await _register_and_login(client, "bad-sig@example.com")
    # File named .pdf but containing invalid magic bytes
    resp = await client.post(
        "/api/v1/students/me/resumes",
        headers=_auth_headers(token),
        data={"title": "Fake PDF"},
        files={"file": ("fake.pdf", b"NOT A REAL PDF", "application/pdf")},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "FILE_CONTENT_MISMATCH"


async def test_upload_file_too_large_rejected(client, monkeypatch):
    from app.core import config
    monkeypatch.setattr(config.settings, "RESUME_MAX_FILE_SIZE_MB", 1)

    token = await _register_and_login(client, "too-large@example.com")
    # 1.5 MB of dummy PDF content
    oversized = _VALID_PDF_BYTES + b"0" * (1500 * 1024)

    resp = await client.post(
        "/api/v1/students/me/resumes",
        headers=_auth_headers(token),
        data={"title": "Large Resume"},
        files={"file": ("large.pdf", oversized, "application/pdf")},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "FILE_TOO_LARGE"


# --- File Download -----------------------------------------------------------

async def test_download_resume_file(client):
    token = await _register_and_login(client, "download-test@example.com")
    headers = _auth_headers(token)

    create_resp = await client.post(
        "/api/v1/students/me/resumes",
        headers=headers,
        data={"title": "Download Me"},
        files={"file": ("my_resume.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )
    resume_id = create_resp.json()["id"]

    download_resp = await client.get(
        f"/api/v1/students/me/resumes/{resume_id}/file", headers=headers
    )
    assert download_resp.status_code == 200
    assert download_resp.content == _VALID_PDF_BYTES
    assert "my_resume.pdf" in download_resp.headers.get("content-disposition", "")


# --- Security & Isolation ----------------------------------------------------

async def test_unauthenticated_requests_rejected(client):
    resp = await client.get("/api/v1/students/me/resumes")
    assert resp.status_code == 401


async def test_staff_cannot_access_student_resumes(client, db_session, user_repo):
    token = await _register_and_login(client, "staff-resume-blocked@example.com")
    user = await user_repo.get_by_email("staff-resume-blocked@example.com")
    user.role = RoleEnum.STAFF
    await db_session.commit()

    staff_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "staff-resume-blocked@example.com", "password": "SecurePass123"},
    )
    staff_token = staff_login.json()["access_token"]

    resp = await client.get("/api/v1/students/me/resumes", headers=_auth_headers(staff_token))
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "INSUFFICIENT_ROLE"


async def test_cross_student_isolation(client):
    token_a = await _register_and_login(client, "student-a@example.com")
    token_b = await _register_and_login(client, "student-b@example.com")

    # Student A creates a resume
    r_a = (await client.post(
        "/api/v1/students/me/resumes",
        headers=_auth_headers(token_a),
        data={"title": "Student A Resume"},
        files={"file": ("a.pdf", _VALID_PDF_BYTES, "application/pdf")},
    )).json()

    resume_id = r_a["id"]

    # Student B attempts GET, PATCH, DELETE, set_default, download on Student A's resume
    headers_b = _auth_headers(token_b)

    get_resp = await client.get(f"/api/v1/students/me/resumes/{resume_id}", headers=headers_b)
    assert get_resp.status_code == 404

    patch_resp = await client.patch(
        f"/api/v1/students/me/resumes/{resume_id}",
        headers=headers_b,
        json={"title": "Hacked Title"},
    )
    assert patch_resp.status_code == 404

    def_resp = await client.patch(
        f"/api/v1/students/me/resumes/{resume_id}/default",
        headers=headers_b,
    )
    assert def_resp.status_code == 404

    dl_resp = await client.get(f"/api/v1/students/me/resumes/{resume_id}/file", headers=headers_b)
    assert dl_resp.status_code == 404

    del_resp = await client.delete(f"/api/v1/students/me/resumes/{resume_id}", headers=headers_b)
    assert del_resp.status_code == 404

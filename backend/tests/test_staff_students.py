"""
Tests for Staff Student Directory module.
"""

import io
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


async def test_staff_student_directory_flow(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-dir-1@example.com")

    # 1. Create a student with profile, department, skill, and resume
    _, student1_headers = await _register_and_login(client, "student-dir-1@example.com")

    # Create department
    dept_res = await client.post(
        "/api/v1/staff/departments",
        headers=staff_headers,
        json={"name": "Computer Science & Engineering"},
    )
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["id"]

    # Student update profile
    profile_res = await client.patch(
        "/api/v1/students/me",
        headers=student1_headers,
        json={
            "full_name": "Alice Cooper",
            "phone": "+91 9876543210",
            "department_id": dept_id,
            "graduation_year": 2026,
            "cgpa": 8.95,
        },
    )
    assert profile_res.status_code == 200
    student1_id = profile_res.json()["id"]

    # Create catalog skill & add to student
    skill_res = await client.post(
        "/api/v1/staff/skills",
        headers=staff_headers,
        json={"name": "Python 3", "category": "Programming"},
    )
    assert skill_res.status_code == 201
    skill_id = skill_res.json()["id"]

    add_skill_res = await client.post(
        "/api/v1/students/me/skills",
        headers=student1_headers,
        json={"skill_id": skill_id, "proficiency": "advanced"},
    )
    assert add_skill_res.status_code == 201

    # Upload resume for student
    pdf_bytes = b"%PDF-1.4 sample pdf content for resume test"
    file_tuple = ("test_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = await client.post(
        "/api/v1/students/me/resumes",
        headers=student1_headers,
        data={"title": "Master Resume", "description": "General Software Engineer"},
        files={"file": file_tuple},
    )
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["id"]

    # --- 1. Staff can list students ---
    list_res = await client.get("/api/v1/staff/students", headers=staff_headers)
    assert list_res.status_code == 200
    students_list = list_res.json()
    assert isinstance(students_list, list)

    s1_item = next(s for s in students_list if s["id"] == student1_id)
    assert s1_item["full_name"] == "Alice Cooper"
    assert s1_item["email"] == "student-dir-1@example.com"
    assert s1_item["department"]["id"] == dept_id
    assert s1_item["graduation_year"] == 2026
    assert s1_item["cgpa"] == 8.95
    # --- 11 & 12. Correct skills_count and resumes_count ---
    assert s1_item["skills_count"] == 1
    assert s1_item["resumes_count"] == 1
    assert s1_item["is_active"] is True

    # --- 15. Verify sensitive security fields are NOT exposed ---
    assert "password_hash" not in s1_item
    assert "access_token" not in s1_item
    assert "refresh_token" not in s1_item
    assert "file_path" not in s1_item

    # --- 3. Staff can retrieve student detail ---
    detail_res = await client.get(f"/api/v1/staff/students/{student1_id}", headers=staff_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == student1_id
    assert detail["full_name"] == "Alice Cooper"

    # --- 13 & 14. Detail includes skills and resumes ---
    assert len(detail["skills"]) == 1
    assert detail["skills"][0]["skill_name"] == "Python 3"
    assert detail["skills"][0]["proficiency"] == "advanced"

    assert len(detail["resumes"]) == 1
    assert detail["resumes"][0]["id"] == resume_id
    assert detail["resumes"][0]["title"] == "Master Resume"
    assert detail["resumes"][0]["is_default"] is True
    assert "file_path" not in detail["resumes"][0]

    # --- Staff download student resume ---
    dl_res = await client.get(
        f"/api/v1/staff/students/{student1_id}/resumes/{resume_id}/file",
        headers=staff_headers,
    )
    assert dl_res.status_code == 200
    assert dl_res.content == pdf_bytes


async def test_student_filtering_and_search(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-search@example.com")

    # Create dept
    dept1 = await client.post("/api/v1/staff/departments", headers=staff_headers, json={"name": "Information Tech"})
    dept1_id = dept1.json()["id"]

    dept2 = await client.post("/api/v1/staff/departments", headers=staff_headers, json={"name": "Data Analytics"})
    dept2_id = dept2.json()["id"]

    # Student A
    _, st_a = await _register_and_login(client, "bob.builder@example.com")
    await client.patch(
        "/api/v1/students/me",
        headers=st_a,
        json={"full_name": "Bob Builder", "department_id": dept1_id, "graduation_year": 2025},
    )

    # Student B
    _, st_b = await _register_and_login(client, "charlie.brown@example.com")
    await client.patch(
        "/api/v1/students/me",
        headers=st_b,
        json={"full_name": "Charlie Brown", "department_id": dept2_id, "graduation_year": 2026},
    )

    # 5. Search by name
    res_name = await client.get("/api/v1/staff/students?search=Charlie", headers=staff_headers)
    assert res_name.status_code == 200
    items_name = res_name.json()
    assert len(items_name) == 1
    assert items_name[0]["full_name"] == "Charlie Brown"

    # 6. Search by email
    res_email = await client.get("/api/v1/staff/students?search=bob.builder", headers=staff_headers)
    assert res_email.status_code == 200
    items_email = res_email.json()
    assert len(items_email) == 1
    assert items_email[0]["full_name"] == "Bob Builder"

    # 7. Filter by department
    res_dept = await client.get(f"/api/v1/staff/students?department_id={dept1_id}", headers=staff_headers)
    assert res_dept.status_code == 200
    assert all(s["department"]["id"] == dept1_id for s in res_dept.json())

    # 8. Filter by graduation year
    res_year = await client.get("/api/v1/staff/students?graduation_year=2026", headers=staff_headers)
    assert res_year.status_code == 200
    assert all(s["graduation_year"] == 2026 for s in res_year.json())

    # 9. Combined search/filter
    res_comb = await client.get(
        f"/api/v1/staff/students?search=Charlie&department_id={dept2_id}&graduation_year=2026",
        headers=staff_headers,
    )
    assert res_comb.status_code == 200
    assert len(res_comb.json()) == 1


async def test_student_access_forbidden(client, db_session, user_repo):
    _, student_headers = await _register_and_login(client, "forbidden-student@example.com")

    # 2. Student cannot access staff list
    res_list = await client.get("/api/v1/staff/students", headers=student_headers)
    assert res_list.status_code == 403

    # 4. Student cannot access staff student detail
    res_detail = await client.get("/api/v1/staff/students/1", headers=student_headers)
    assert res_detail.status_code == 403


async def test_non_existent_student_returns_404(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-404@example.com")

    # 10. Non-existent student returns 404
    res = await client.get("/api/v1/staff/students/99999", headers=staff_headers)
    assert res.status_code == 404
    assert res.json()["error_code"] == "STUDENT_NOT_FOUND"


async def test_resume_access_security_check(client, db_session, user_repo):
    staff_headers = await _get_staff_headers(client, db_session, user_repo, "staff-sec@example.com")

    # Student 1
    _, st1_headers = await _register_and_login(client, "sec-student1@example.com")
    st1_prof = await client.patch("/api/v1/students/me", headers=st1_headers, json={"full_name": "Student One"})
    st1_id = st1_prof.json()["id"]

    upload1 = await client.post(
        "/api/v1/students/me/resumes",
        headers=st1_headers,
        data={"title": "St1 Resume"},
        files={"file": ("st1.pdf", io.BytesIO(b"%PDF-1.4 st1"), "application/pdf")},
    )
    r1_id = upload1.json()["id"]

    # Student 2
    _, st2_headers = await _register_and_login(client, "sec-student2@example.com")
    st2_prof = await client.patch("/api/v1/students/me", headers=st2_headers, json={"full_name": "Student Two"})
    st2_id = st2_prof.json()["id"]

    # 16. Staff trying to access Student 1's resume under Student 2's ID route should fail with 404
    bad_dl = await client.get(
        f"/api/v1/staff/students/{st2_id}/resumes/{r1_id}/file",
        headers=staff_headers,
    )
    assert bad_dl.status_code == 404
    assert bad_dl.json()["error_code"] == "RESUME_NOT_FOUND"

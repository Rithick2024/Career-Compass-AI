# REST API Reference & Contract Specification

**Project:** Career Compass AI: Smart Placement Analytics & Career Intelligence Platform  
**Protocol:** HTTP/1.1 REST over JSON (Multipart for file uploads)  
**API Version:** v1 (`/api/v1`)  
**Total Documented Endpoints:** 54 Active Endpoints across 14 Routers  
**Document Status:** Source-Verified from FastAPI route definitions and Pydantic schemas  

---

## 1. Global Conventions & Authentication

- **Base URL:** `http://localhost:8000/api/v1` (Default local development)
- **Authentication Scheme:** HTTP Bearer token using JWT (`Authorization: Bearer <access_token>`)
- **Content-Type:** `application/json` (except `/api/v1/students/me/resumes` which accepts `multipart/form-data`)
- **Error Response Structure:** All non-2xx responses return a standardized payload:
  ```json
  {
    "detail": "Human-readable error explanation",
    "error_code": "MACHINE_READABLE_CODE"
  }
  ```

---

## 2. Health & System Connectivity (2 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `GET` | `/health` | Public | Basic application liveness check | None | `{"status": "ok", "app": "Career Compass AI"}` | `200 OK` |
| `GET` | `/health/db` | Public | Database connectivity check via `SELECT 1` | None | `{"status": "ok", "database": "connected"}` | `200 OK` |

---

## 3. Authentication & Account Management (5 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `POST` | `/auth/register` | Public | Register new candidate account | `UserRegister` (`email`, `password`, optional `role="student"`) | `UserResponse` (`id`, `email`, `role`, `is_active`) | `201 Created` |
| `POST` | `/auth/register-staff`| Public | Register new staff account (Dev/Admin setup) | `StaffRegister` (`email`, `password`) | `UserResponse` (`id`, `email`, `role="staff"`, `is_active`) | `201 Created` |
| `POST` | `/auth/login` | Public | Authenticate user and receive JWT | `LoginRequest` (`email`, `password`) | `TokenResponse` (`access_token`, `token_type="bearer"`) | `200 OK` |
| `POST` | `/auth/swagger-login` | Public | Swagger UI OAuth2 compatibility login | `OAuth2PasswordRequestForm` (form-data: `username`, `password`) | `TokenResponse` | `200 OK` |
| `GET` | `/auth/me` | Authenticated | Retrieve authenticated user profile | None | `UserResponse` | `200 OK` |

---

## 4. Student Profile & Department Management (8 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `GET` | `/students/me` | RequireStudent | Fetch caller's student profile | None | `StudentProfileResponse` | `200 OK` |
| `PUT` | `/students/me` | RequireStudent | Full student profile replacement | `StudentProfileUpdate` | `StudentProfileResponse` | `200 OK` |
| `PATCH`| `/students/me` | RequireStudent | Partial student profile update | `StudentProfilePatch` | `StudentProfileResponse` | `200 OK` |
| `GET` | `/departments` | Authenticated | List all active departments for dropdowns | None | `List[DepartmentResponse]` | `200 OK` |
| `POST` | `/staff/departments` | RequireStaff | Create new academic department | `DepartmentCreate` (`name`, `code`) | `DepartmentResponse` | `201 Created` |
| `GET` | `/staff/departments` | RequireStaff | List all departments (including inactive) | `skip=0`, `limit=50`, `is_active=None` | `List[DepartmentResponse]` | `200 OK` |
| `GET` | `/staff/departments/{id}` | RequireStaff | Get department by ID | Path `id: int` | `DepartmentResponse` | `200 OK` |
| `PATCH`| `/staff/departments/{id}` | RequireStaff | Update department details or toggle active | Path `id`, `DepartmentUpdate` | `DepartmentResponse` | `200 OK` |

---

## 5. Skills Management & Student Inventory (10 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `GET` | `/skills` | Authenticated | List active skills catalog | `category: Optional[str]` | `List[SkillResponse]` | `200 OK` |
| `GET` | `/student/skills` | RequireStudent | Fetch authenticated student's skill inventory | None | `List[StudentSkillResponse]` | `200 OK` |
| `POST` | `/student/skills` | RequireStudent | Add skill with proficiency to student profile | `StudentSkillCreate` (`skill_id`, `proficiency`) | `StudentSkillResponse` | `201 Created` |
| `PATCH`| `/student/skills/{id}`| RequireStudent | Update proficiency of an existing skill | Path `id: int`, `StudentSkillUpdate` (`proficiency`) | `StudentSkillResponse` | `200 OK` |
| `DELETE`| `/student/skills/{id}`| RequireStudent | Remove skill from student profile | Path `id: int` | Empty (`None`) | `204 No Content` |
| `POST` | `/staff/skills` | RequireStaff | Add new skill to master catalog | `SkillCreate` (`name`, `category`) | `SkillResponse` | `201 Created` |
| `GET` | `/staff/skills` | RequireStaff | List all master skills with active filter | `skip=0`, `limit=100`, `is_active=None` | `List[SkillResponse]` | `200 OK` |
| `GET` | `/staff/skills/{id}` | RequireStaff | Get skill by ID | Path `id: int` | `SkillResponse` | `200 OK` |
| `PUT` | `/staff/skills/{id}` | RequireStaff | Full update of master skill | Path `id: int`, `SkillUpdate` | `SkillResponse` | `200 OK` |
| `PATCH`| `/staff/skills/{id}` | RequireStaff | Partial update / toggle active state | Path `id: int`, `SkillPatch` | `SkillResponse` | `200 OK` |

---

## 6. Corporate Directory & Company Management (5 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `POST` | `/staff/companies` | RequireStaff | Register recruiting company | `CompanyCreate` (`name`, `website`, `industry`, `location`, `description`) | `CompanyResponse` | `201 Created` |
| `GET` | `/staff/companies` | RequireStaff | List companies with search & active filters | `skip=0`, `limit=50`, `search=str`, `is_active=bool` | `List[CompanyResponse]` | `200 OK` |
| `GET` | `/staff/companies/{id}` | RequireStaff | Get company by ID | Path `id: int` | `CompanyResponse` | `200 OK` |
| `PUT` | `/staff/companies/{id}` | RequireStaff | Replace company details | Path `id: int`, `CompanyUpdate` | `CompanyResponse` | `200 OK` |
| `PATCH`| `/staff/companies/{id}` | RequireStaff | Partial update / toggle active status | Path `id: int`, `CompanyPatch` | `CompanyResponse` | `200 OK` |

---

## 7. Staff Student Directory (2 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `GET` | `/staff/students` | RequireStaff | Browse student directory with filters | `department_id`, `graduation_year`, `search` | `List[StaffStudentListResponse]` | `200 OK` |
| `GET` | `/staff/students/{id}` | RequireStaff | View detailed student profile & resumes | Path `id: int` | `StaffStudentDetailResponse` | `200 OK` |

---

## 8. Job Management (Staff & Student) (7 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `POST` | `/staff/jobs` | RequireStaff | Create job with depts and skills | `JobCreate` (`title`, `company_id`, `ctc_lpa`, `min_cgpa`, `department_ids`, `skills`) | `JobDetailResponse` | `201 Created` |
| `GET` | `/staff/jobs` | RequireStaff | List all jobs for staff | `company_id`, `status`, `search` | `List[JobListResponse]` | `200 OK` |
| `GET` | `/staff/jobs/{id}` | RequireStaff | Get job details for staff | Path `id: int` | `JobDetailResponse` | `200 OK` |
| `PUT` | `/staff/jobs/{id}` | RequireStaff | Update job and criteria | Path `id: int`, `JobUpdate` | `JobDetailResponse` | `200 OK` |
| `PATCH`| `/staff/jobs/{id}` | RequireStaff | Partial job update / toggle active | Path `id: int`, `JobPatch` | `JobDetailResponse` | `200 OK` |
| `GET` | `/student/jobs` | RequireStudent | Discover active visible jobs | `department_id`, `employment_type`, `search` | `List[StudentJobListResponse]` | `200 OK` |
| `GET` | `/student/jobs/{id}` | RequireStudent | View job details with eligibility | Path `id: int` | `StudentJobDetailResponse` | `200 OK` |

---

## 9. Resume Management (7 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `GET` | `/students/me/resumes` | RequireStudent | List candidate's uploaded resumes | None | `List[ResumeResponse]` | `200 OK` |
| `POST` | `/students/me/resumes` | RequireStudent | Upload new resume file | Multipart: `title: str`, `file: UploadFile` ($\le 5$MB) | `ResumeResponse` | `201 Created` |
| `GET` | `/students/me/resumes/{id}` | RequireStudent | Get resume metadata | Path `id: int` | `ResumeResponse` | `200 OK` |
| `PATCH`| `/students/me/resumes/{id}` | RequireStudent | Edit resume title/summary/objective | Path `id: int`, `ResumePatch` | `ResumeResponse` | `200 OK` |
| `PATCH`| `/students/me/resumes/{id}/default`| RequireStudent | Designate resume as default | Path `id: int` | `ResumeResponse` | `200 OK` |
| `DELETE`| `/students/me/resumes/{id}`| RequireStudent | Delete resume (if unattached) | Path `id: int` | Empty (`None`) | `204 No Content` |
| `GET` | `/students/me/resumes/{id}/download`| RequireStudent | Download original resume file | Path `id: int` | `FileResponse` | `200 OK` |

---

## 10. Job Applications (Staff & Student) (7 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `POST` | `/student/applications` | RequireStudent | Apply for job (creates round snapshots) | `ApplicationCreate` (`job_id`, `resume_id`) | `StudentApplicationResponse` | `201 Created` |
| `GET` | `/student/applications` | RequireStudent | List candidate's applications | None | `List[StudentApplicationResponse]` | `200 OK` |
| `GET` | `/student/applications/{id}`| RequireStudent | Get application status & round info | Path `id: int` | `StudentApplicationResponse` | `200 OK` |
| `POST` | `/student/applications/{id}/withdraw`| RequireStudent | Withdraw application | Path `id: int` | `StudentApplicationResponse` | `200 OK` |
| `GET` | `/staff/applications` | RequireStaff | List applications across all jobs | `job_id`, `status`, `search` | `List[StaffApplicationListResponse]` | `200 OK` |
| `GET` | `/staff/applications/{id}` | RequireStaff | View application details & resume | Path `id: int` | `StaffApplicationDetailResponse` | `200 OK` |
| `PATCH`| `/staff/applications/{id}/status` | RequireStaff | Transition application status | Path `id: int`, `ApplicationStatusUpdate` | `StaffApplicationDetailResponse` | `200 OK` |

---

## 11. Job Rounds (Workflow Templates) (5 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `POST` | `/staff/jobs/{job_id}/rounds` | RequireStaff | Add template round to job | Path `job_id`, `JobRoundCreate` | `JobRoundResponse` | `201 Created` |
| `GET` | `/staff/jobs/{job_id}/rounds` | RequireStaff | List template rounds for job | Path `job_id` | `List[JobRoundResponse]` | `200 OK` |
| `GET` | `/staff/jobs/{job_id}/rounds/{round_id}` | RequireStaff | Get template round by ID | Path `job_id`, `round_id` | `JobRoundResponse` | `200 OK` |
| `PUT` | `/staff/jobs/{job_id}/rounds/{round_id}` | RequireStaff | Update template round details | Path `job_id`, `round_id`, `JobRoundUpdate` | `JobRoundResponse` | `200 OK` |
| `DELETE`| `/staff/jobs/{job_id}/rounds/{round_id}`| RequireStaff | Delete template round | Path `job_id`, `round_id` | Empty (`None`) | `204 No Content` |

---

## 12. Application Rounds & Candidate Tracking (11 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `GET` | `/student/applications/{app_id}/rounds` | RequireStudent | View candidate's round timeline | Path `app_id: int` | `List[ApplicationRoundResponse]` | `200 OK` |
| `GET` | `/student/applications/{app_id}/rounds/{round_id}`| RequireStudent | View candidate's single round | Path `app_id`, `round_id` | `ApplicationRoundResponse` | `200 OK` |
| `POST` | `/student/applications/{app_id}/rounds/{round_id}/attendance`| RequireStudent | Candidate marks attendance | Path `app_id`, `round_id`, `AttendanceReport` (`ATTENDED`/`ABSENT`) | `ApplicationRoundResponse` | `200 OK` |
| `POST` | `/staff/applications/{app_id}/rounds` | RequireStaff | Add ad-hoc round to application | Path `app_id`, `ApplicationRoundCreate` | `ApplicationRoundResponse` | `201 Created` |
| `GET` | `/staff/applications/{app_id}/rounds` | RequireStaff | List application rounds for staff | Path `app_id` | `List[ApplicationRoundResponse]` | `200 OK` |
| `GET` | `/staff/applications/{app_id}/rounds/{round_id}` | RequireStaff | Get application round details | Path `app_id`, `round_id` | `ApplicationRoundResponse` | `200 OK` |
| `PATCH`| `/staff/applications/{app_id}/rounds/{round_id}` | RequireStaff | Edit round schedule/links/notes | Path `app_id`, `round_id`, `ApplicationRoundPatch` | `ApplicationRoundResponse` | `200 OK` |
| `PATCH`| `/staff/applications/{app_id}/rounds/{round_id}/verification`| RequireStaff | Staff verifies attendance | Path `app_id`, `round_id`, `VerificationUpdate` (`VERIFIED`/`REJECTED`) | `ApplicationRoundResponse` | `200 OK` |
| `PATCH`| `/staff/applications/{app_id}/rounds/{round_id}/result` | RequireStaff | Record round outcome | Path `app_id`, `round_id`, `ResultUpdate` (`Passed`/`Failed`) | `ApplicationRoundResponse` | `200 OK` |
| `PATCH`| `/staff/applications/{app_id}/rounds/{round_id}/reschedule` | RequireStaff | Reschedule round with reason | Path `app_id`, `round_id`, `RescheduleRequest` (`new_scheduled_at`, `reason`) | `ApplicationRoundResponse` | `200 OK` |
| `DELETE`| `/staff/applications/{app_id}/rounds/{round_id}` | RequireStaff | Delete candidate round record | Path `app_id`, `round_id` | Empty (`None`) | `204 No Content` |

---

## 13. Placements & Offers (6 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `POST` | `/staff/placements` | RequireStaff | Create placement record | `PlacementCreate` (`student_id`, `job_id`, `package_lpa`, `designation`) | `PlacementResponse` | `201 Created` |
| `GET` | `/staff/placements` | RequireStaff | List all placements | `company_id`, `status` | `List[PlacementResponse]` | `200 OK` |
| `GET` | `/staff/placements/{id}` | RequireStaff | Get placement by ID | Path `id: int` | `PlacementResponse` | `200 OK` |
| `PATCH`| `/staff/placements/{id}` | RequireStaff | Edit placement package/notes | Path `id: int`, `PlacementPatch` | `PlacementResponse` | `200 OK` |
| `GET` | `/student/placements` | RequireStudent | View candidate's job offers | None | `List[PlacementResponse]` | `200 OK` |
| `PATCH`| `/student/placements/{id}/respond` | RequireStudent | Accept or decline placement offer | Path `id: int`, `PlacementResponseUpdate` (`Accepted`/`Declined`) | `PlacementResponse` | `200 OK` |

---

## 14. Placement Analytics (2 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `GET` | `/staff/analytics/overview` | RequireStaff | Comprehensive staff KPIs & charts | None | `StaffAnalyticsOverview` | `200 OK` |
| `GET` | `/student/analytics/overview`| RequireStudent | Candidate dashboard stats & rounds | None | `StudentAnalyticsOverview` | `200 OK` |

---

## 15. Placement Intelligence & Readiness (3 Endpoints)

| Method | Endpoint | Auth | Purpose | Request Body / Params | Response Model | Status |
|---|---|---|---|---|---|---|
| `GET` | `/student/intelligence/readiness` | RequireStudent | Calculate 100-pt 4-pillar readiness score & recommendations | None | `ReadinessResponse` | `200 OK` |
| `GET` | `/student/intelligence/skills/gap`| RequireStudent | Calculate market skill gaps against active job postings | None | `MarketSkillGapResponse` | `200 OK` |
| `GET` | `/student/intelligence/jobs/{job_id}/match`| RequireStudent | Analyze eligibility & skill match for a specific job | Path `job_id: int` | `JobMatchResponse` | `200 OK` |

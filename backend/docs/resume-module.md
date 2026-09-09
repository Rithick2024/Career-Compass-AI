# Resume Module

Covers the `resumes` table and the `/api/v1/students/me/resume` endpoints.
This is a **structured resume profile MVP** — a small set of free-text
fields a student maintains directly, feeding future modules (job matching,
placement readiness, analytics, AI/ML prediction). It explicitly does
**not** include AI resume generation, LLM integration, PDF parsing, OCR,
resume scoring, embeddings, a vector database, an external resume parser,
or file storage — those are future/final-year extensions, out of scope
here.

## Purpose

Students need somewhere to record resume-specific structured content —
starting with a professional summary and career objective — that is
distinct from their profile (name, phone, department, CGPA), their skills,
and their authentication account. Keeping it as its own table means it can
grow independently (see [Future extension](#future-extension-not-implemented))
without the Student Profile or Skills modules needing to change.

## Database design

### `resumes`

| Column                  | Type                       | Notes                                    |
|--------------------------|------------------------------|---------------------------------------------|
| `id`                     | integer, PK, auto-increment |                                              |
| `student_id`             | integer, FK → `students.id`, unique, indexed | `ON DELETE CASCADE`         |
| `professional_summary`   | `varchar(2000)`, nullable   | Trimmed; empty/whitespace-only → `NULL`    |
| `career_objective`       | `varchar(1000)`, nullable   | Trimmed; empty/whitespace-only → `NULL`    |
| `created_at`             | timestamptz                 | `server_default=now()`                     |
| `updated_at`             | timestamptz                 | `onupdate=now()`                           |

**No authentication, profile, or skills fields are duplicated here** —
`full_name`, `email`, `phone`, `department`, `graduation_year`, `cgpa`,
and skills all live on `User`/`Student`/`student_skills` respectively;
`resumes` only holds resume-specific structured content.

### Relationship

**`students` 1 ──── 0..1 `resumes`** — a student may have at most one
resume, and a resume never exists without a student (`student_id` is
`NOT NULL` and unique). Unlike `students.department_id`, this is enforced
with `ON DELETE CASCADE`, not `SET NULL`: a resume with no student would
be meaningless, whereas a student with no department is a normal,
representable state.

Since `resumes.student_id` references `students.id` (not `users.id`), and
the authenticated JWT only carries a `users.id`, `ResumeService` resolves
— and, on first access, auto-provisions if needed — the current user's
underlying `students.id` via `StudentRepository`, exactly the same
resolution step `SkillService` already performs. This is intentional reuse
of the Student module's data-access layer, not a new pattern.

## API endpoints

| Method | Path                            | Auth required | Success | Notable errors |
|--------|-----------------------------------|------------------|---------|------------------|
| GET    | `/api/v1/students/me/resume`     | Bearer JWT, student role | 200, `ResumeResponse` | 404 no resume yet |
| POST   | `/api/v1/students/me/resume`     | Bearer JWT, student role | 201, `ResumeResponse` | 409 already exists, 422 validation |
| PATCH  | `/api/v1/students/me/resume`     | Bearer JWT, student role | 200, `ResumeResponse` | 404 no resume yet, 422 validation |
| DELETE | `/api/v1/students/me/resume`     | Bearer JWT, student role | 204, empty body | 404 no resume yet |

Same project-wide error envelope as every other module:
`{ "error_code": "...", "message": "...", "details": ... }`.

**There is no `GET /students/{student_id}/resume` or any endpoint that
accepts a client-supplied student id.** All four endpoints are nested
under `/students/me/resume`, matching the Skills module's
`/students/me/skills` pattern — the student is always derived from the
authenticated JWT.

### Request/response examples

**`POST /api/v1/students/me/resume`**
```json
{"professional_summary": "Aspiring backend engineer.", "career_objective": "Land a great internship."}
```
→ `201`
```json
{
  "id": 1,
  "student_id": 7,
  "professional_summary": "Aspiring backend engineer.",
  "career_objective": "Land a great internship.",
  "created_at": "2026-09-09T04:36:48Z",
  "updated_at": "2026-09-09T04:36:48Z"
}
```

**`PATCH /api/v1/students/me/resume`** (partial update — only the supplied field changes)
```json
{"career_objective": "Updated objective"}
```
→ `200` (same shape, `professional_summary` unchanged, `career_objective` updated, `updated_at` refreshed)

**`DELETE /api/v1/students/me/resume`** → `204`, empty body

## Validation

| Case | Behavior |
|---|---|
| `professional_summary` over 2000 characters | `422` |
| `career_objective` over 1000 characters | `422` |
| Leading/trailing whitespace | Trimmed automatically; whitespace-only input becomes `NULL` |
| Extra/unknown fields (e.g. `student_id`) in request body | `422` (`extra="forbid"` on both request schemas) |
| No resume exists (`GET`/`PATCH`/`DELETE`) | `404 RESUME_NOT_FOUND` |
| Resume already exists (`POST`) | `409 RESUME_ALREADY_EXISTS` |

Length limits are enforced at both the Pydantic layer (immediate 422) and
the database column definition (`varchar(2000)`/`varchar(1000)`) as
defense in depth.

## Authentication & authorization

All four endpoints use `RequireStudent` — the **existing**
`require_role(RoleEnum.STUDENT)` dependency, unchanged from the student
and skills modules. No new authentication or authorization mechanism was
introduced.

**Ownership is structural, not just checked in code:** every operation
resolves the student via `current_user.id` from the JWT; there is no
request parameter anywhere in this module that identifies a student.
Attempting to `PATCH`/`DELETE` when the authenticated student has no
resume of their own returns the same `404 RESUME_NOT_FOUND` regardless of
whether some *other* student has one — it never confirms or denies another
student's resume exists.

## Duplicate handling

A resume is created only via explicit `POST`. If one already exists for
the authenticated student, `POST` returns `409 RESUME_ALREADY_EXISTS`
rather than silently overwriting it — the database's unique constraint on
`student_id` backs this up at the storage layer too, so a duplicate can't
slip through even under a race condition. To change an existing resume,
use `PATCH`; to start over, `DELETE` then `POST` again.

## Design decision: 404 rather than auto-provisioning

**This is the one place Resume's behavior deliberately differs from the
Student Profile module's pattern, and is flagged here for your review, as
requested.**

`StudentService._get_or_create_profile` auto-creates an empty student
profile on first access, because a profile is implicitly tied to the
account and the Student module has no separate "create" endpoint at all —
auto-provisioning is the only way `GET`/`PATCH` are ever usable there.

Resume was given its own explicit `POST` (with duplicate detection) and
its own explicit `DELETE`, and the task's database design names it a
"Student 1 ── 0..1 Resume" relationship — a resume genuinely may or may
not exist, and that absence is a meaningful, testable state rather than a
startup formality. Auto-provisioning here would undermine both:

- A "duplicate POST → 409" check is much less meaningful if a resume
  always already exists by the time `POST` ever runs.
- `DELETE` would have nothing distinct to test against — `GET` right
  after `DELETE` would just silently recreate an empty resume, masking
  whether delete actually worked.

So: `GET`, `PATCH`, and `DELETE` all return `404 RESUME_NOT_FOUND` when no
resume row exists; a resume is only ever created via `POST`. This mirrors
how the Skills module's `PATCH`/`DELETE` on a skill the student doesn't
have already return `404 STUDENT_SKILL_NOT_FOUND` — Resume follows that
precedent rather than the Student Profile's auto-provisioning one, since
its lifecycle (explicit create, explicit delete, meaningful absence) is
much closer to a `student_skill` row than to the always-present student
profile.

## Migration

`alembic/versions/04b4acaa5c64_create_resumes_table.py`, depends on
`38f0da1163aa` (the proficiency-correction migration — the current head
at the time this module was built). Creates `resumes` with the
PK/unique-FK/timestamps described above. No enum types are involved, so
no orphaned-type cleanup is needed on downgrade (unlike the `users` and
`skills` migrations). Verified: upgrade → downgrade → upgrade round-trip
is clean, `alembic check` reports "No new upgrade operations detected"
(zero drift), and no existing migration was edited.

## Future extension (not implemented)

The task brief explicitly asks that this MVP stay simple and normalized,
while allowing later growth without breaking this API. The natural path:

```
resumes                  (this module — summary/objective only)
resume_education          (one-to-many: degree, institution, year, ...)
resume_experience          (one-to-many: role, company, dates, description, ...)
resume_projects            (one-to-many: title, description, tech stack, link, ...)
resume_certifications      (one-to-many: name, issuer, date, credential URL, ...)
resume_achievements        (one-to-many: title, description, date, ...)
```

Each would be its own table with a `resume_id` foreign key (`ON DELETE
CASCADE`), following the exact same model/schema/repository/service/router
layering used throughout this project. None of this is implemented now —
noted here only so the current `resumes` table's simplicity is understood
as deliberate, not incomplete.

## Test coverage

`tests/test_resumes.py` — 20 tests, using the same real-PostgreSQL,
transaction-per-test infrastructure as the other test modules (no SQLite,
no mocked repositories):

- `GET` before any resume exists → 404
- Create (success, whitespace trimmed, duplicate → 409, both fields
  nullable/omittable)
- `GET` after creation returns the created data
- `PATCH` updates only the supplied field, preserves the other; explicit
  `null` clears a field; `PATCH` with no resume → 404
- `DELETE` succeeds; `GET`/`DELETE` after delete → 404; a new resume can
  be created again after deletion
- Validation: extra fields rejected, both length limits enforced
- Authentication: no token / invalid token → 401
- Authorization: admin role rejected (403) from the student-only endpoint
- Ownership: one student's resume never appears for another; a student
  with no resume of their own cannot `PATCH`/`DELETE` — every attempt
  cleanly 404s without touching another student's data

Combined with the existing 43 (14 auth + 11 student + 18 skills), the full
suite is **63 tests, all passing** (run multiple times for stability).

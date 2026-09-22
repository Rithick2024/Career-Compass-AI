# Resume Module

Covers the `resumes` table and the `/api/v1/students/me/resume` endpoints,
including uploaded **resume file** storage (PDF/DOC/DOCX, ≤5 MB). This is a
**structured resume profile + file MVP** — structured fields plus a single
uploaded file per student, feeding future modules (job matching, placement
readiness, analytics, AI/ML prediction). It explicitly does **not**
include AI resume generation, LLM integration, PDF parsing, OCR, resume
scoring, embeddings, a vector database, an external resume parser, or
cloud storage — those are future/final-year extensions, out of scope
here (see [Future extensions](#future-extensions-not-implemented)).

## Purpose

Students need somewhere to record resume-specific structured content — a
professional summary, a career objective, and (as of this extension) an
actual resume file — that is distinct from their profile (name, phone,
department, CGPA), their skills, and their authentication account. Keeping
it as its own table means it can grow independently without the Student
Profile or Skills modules needing to change.

## Database design

### `resumes`

| Column                  | Type                       | Notes                                    |
|--------------------------|------------------------------|---------------------------------------------|
| `id`                     | integer, PK, auto-increment |                                              |
| `student_id`             | integer, FK → `students.id`, unique, indexed | `ON DELETE CASCADE`         |
| `professional_summary`   | `varchar(2000)`, nullable   | Trimmed; empty/whitespace-only → `NULL`    |
| `career_objective`       | `varchar(1000)`, nullable   | Trimmed; empty/whitespace-only → `NULL`    |
| `file_name`              | `varchar(255)`, nullable    | Original filename, as uploaded — display/download only |
| `file_path`              | `varchar(500)`, nullable    | Path relative to the upload root — **internal only, never returned by the API** |
| `file_type`              | `varchar(100)`, nullable    | Declared content type at upload time       |
| `file_size`              | `bigint`, nullable          | Bytes actually written to disk             |
| `created_at`             | timestamptz                 | `server_default=now()`                     |
| `updated_at`             | timestamptz                 | `onupdate=now()`                           |

**No authentication, profile, or skills fields are duplicated here** —
`full_name`, `email`, `phone`, `department`, `graduation_year`, `cgpa`,
and skills all live on `User`/`Student`/`student_skills` respectively;
`resumes` only holds resume-specific structured content.

**The actual file content is never stored in PostgreSQL** — only these
four metadata columns. The file itself lives on the backend filesystem
(see [File storage](#file-storage)). All four file columns are nullable:
a resume may exist with no file uploaded, and every resume created before
this extension has none.

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
| POST   | `/api/v1/students/me/resume/file` | Bearer JWT, student role | 200, `ResumeResponse` | 404 no resume yet, 422 invalid file |
| GET    | `/api/v1/students/me/resume/file` | Bearer JWT, student role | 200, file bytes (`Content-Disposition: attachment`) | 404 no resume/no file/file missing on disk |
| DELETE | `/api/v1/students/me/resume/file` | Bearer JWT, student role | 200, `ResumeResponse` | 404 no resume/no file |

Same project-wide error envelope as every other module:
`{ "error_code": "...", "message": "...", "details": ... }` — except the
download endpoint, whose successful response is the raw file, not JSON.

**There is no `GET /students/{student_id}/resume` (or `.../resume/file`)
or any endpoint that accepts a client-supplied student id.** All seven
endpoints are nested under `/students/me/resume`, matching the Skills
module's `/students/me/skills` pattern — the student is always derived
from the authenticated JWT.

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
  "file_name": null,
  "file_type": null,
  "file_size": null,
  "has_file": false,
  "created_at": "2026-09-09T04:36:48Z",
  "updated_at": "2026-09-09T04:36:48Z"
}
```

**`PATCH /api/v1/students/me/resume`** (partial update — only the supplied field changes)
```json
{"career_objective": "Updated objective"}
```
→ `200` (same shape, `professional_summary` unchanged, `career_objective` updated, `updated_at` refreshed)

**`DELETE /api/v1/students/me/resume`** → `204`, empty body (also deletes the uploaded file, if any — see [File lifecycle](#file-lifecycle))

**`POST /api/v1/students/me/resume/file`** — `multipart/form-data`, field name `file`
```
POST /api/v1/students/me/resume/file
Content-Type: multipart/form-data; boundary=...

file: (binary PDF/DOC/DOCX content, ≤5 MB)
```
→ `200`
```json
{
  "id": 1,
  "student_id": 7,
  "professional_summary": "Aspiring backend engineer.",
  "career_objective": "Updated objective",
  "file_name": "Rithee_Resume.pdf",
  "file_type": "application/pdf",
  "file_size": 182734,
  "has_file": true,
  "created_at": "2026-09-09T04:36:48Z",
  "updated_at": "2026-09-22T02:39:20Z"
}
```
Note `file_path` is never in the response — see [Security design](#security--ownership).

**`GET /api/v1/students/me/resume/file`** → `200`, the raw file bytes, with:
- `Content-Type` set to the stored `file_type`
- `Content-Disposition: attachment; filename="Rithee_Resume.pdf"` (the original filename, not the generated on-disk name)

**`DELETE /api/v1/students/me/resume/file`** → `200`, the same `ResumeResponse` shape with `file_name`/`file_type`/`file_size` now `null` and `has_file: false` — the resume profile itself (`professional_summary`/`career_objective`) is untouched.

## Validation

| Case | Behavior |
|---|---|
| `professional_summary` over 2000 characters | `422` |
| `career_objective` over 1000 characters | `422` |
| Leading/trailing whitespace | Trimmed automatically; whitespace-only input becomes `NULL` |
| Extra/unknown fields (e.g. `student_id`) in request body | `422` (`extra="forbid"` on both request schemas) |
| No resume exists (`GET`/`PATCH`/`DELETE`/any file endpoint) | `404 RESUME_NOT_FOUND` |
| Resume already exists (`POST`) | `409 RESUME_ALREADY_EXISTS` |
| Unsupported file extension | `422 UNSUPPORTED_FILE_TYPE` |
| Declared `Content-Type` doesn't match the extension | `422 CONTENT_TYPE_MISMATCH` |
| File's actual content (magic bytes) doesn't match its extension | `422 FILE_CONTENT_MISMATCH` |
| File exceeds 5 MB | `422 FILE_TOO_LARGE` |
| Empty file upload | `422 EMPTY_FILE` |
| No file exists on the resume (download / delete-file) | `404 RESUME_FILE_NOT_FOUND` |

Length limits are enforced at both the Pydantic layer (immediate 422) and
the database column definition (`varchar(2000)`/`varchar(1000)`) as
defense in depth. File validation is covered in detail in
[File validation](#file-validation) below.

## Authentication & authorization

All seven endpoints use `RequireStudent` — the **existing**
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

## File storage

Local filesystem for this MVP — see [Future extensions](#future-extensions-not-implemented)
for the planned cloud-storage migration. Implemented in
`app/modules/resumes/storage.py`, kept deliberately as a handful of
functions rather than a storage-abstraction class hierarchy: "keep it
simple but clean enough to replace later," not an abstraction built ahead
of actual need. A future cloud-storage swap replaces the bodies of
`save_upload`/`delete_file`/`resolve_absolute_path` without touching their
signatures or any caller.

**Layout:**
```
<project root>/
  uploads/
    resumes/
      {student_id}/
        {generated-uuid}.{ext}
```
Root directory configurable via `RESUME_UPLOAD_DIR` (default
`uploads/resumes`, relative to the project root); max size via
`RESUME_MAX_FILE_SIZE_MB` (default `5`) — both in `.env`/`app/core/config.py`,
consistent with every other environment-driven setting in this project.
`uploads/` is git-ignored.

**The original filename is never trusted as a physical path component.**
A fresh, unguessable filename is generated (`uuid4().hex` + the validated
extension) for every upload; the original name is preserved only as the
`file_name` metadata column, used for display and as the download
filename — never for locating the file on disk.

```
Client sends:  Rithee_Resume.pdf
Stored as:     uploads/resumes/7/8f2c1a9b3e4d4f5a9c6b1e2d3f4a5b6c.pdf
DB record:     file_name = "Rithee_Resume.pdf"
               file_path = "7/8f2c1a9b3e4d4f5a9c6b1e2d3f4a5b6c.pdf"  (internal only)
               file_type = "application/pdf"
               file_size = 182734
```

## File validation

Three independent checks, **all required to pass** — no single one is
trusted alone:

1. **Extension** — must be `.pdf`, `.doc`, or `.docx` (case-insensitive).
   Anything else (`.exe`, `.js`, `.html`, `.png`, `.zip`, ...) →
   `422 UNSUPPORTED_FILE_TYPE`.
2. **Declared `Content-Type`** — must match the extension's expected MIME
   type, or be a permissive fallback (`application/octet-stream` or
   empty — common client quirks, not a security signal by themselves).
   A clearly mismatched declared type (e.g. `.pdf` declared as
   `image/png`) → `422 CONTENT_TYPE_MISMATCH`.
3. **Magic-byte signature** — the file's actual leading bytes are checked
   against the expected signature for its extension (`%PDF-` for PDF, the
   OLE/CFBF header for legacy DOC, the ZIP header `PK\x03\x04` for DOCX,
   since DOCX is a ZIP archive). A renamed `.exe` claiming to be a `.pdf`
   passes checks 1–2 (right extension, plausible declared type) but fails
   this one → `422 FILE_CONTENT_MISMATCH`. **No new dependency** (e.g.
   `python-magic`/libmagic) was introduced for this — the three MVP
   formats have short, well-known signatures, so a hand-rolled check
   keeps this genuinely simple rather than pulling in a system-level
   library for three constants.

**Size is never trusted from the client.** The upload is read and written
to disk in 1 MB chunks, with the running total checked against the 5 MB
limit as it goes — so an oversized file is rejected mid-stream, before
it's ever fully written, regardless of what `Content-Length` or any
client-reported size claimed. A rejected upload's partial file is deleted
immediately, never left behind.

## File lifecycle

**Upload (`POST .../resume/file`) — create or replace:**
1. Validate (extension → declared type → streamed signature+size). Any
   failure here happens *before* the new file touches disk at all,
   except the signature/size checks, which necessarily need some file
   bytes to check — a failure there deletes the partial write
   immediately.
2. Save the new file under a freshly generated name.
3. Commit the DB update pointing the resume at the new file.
   - If this commit fails, the just-saved new file is deleted before the
     error propagates — never left orphaned.
4. **Only after that commit succeeds**, delete the *previous* file (if
   one existed). This ordering means a mid-operation failure never
   leaves a student with neither an old nor a new file.

**Delete file only (`DELETE .../resume/file`):** commit the DB change
(clear `file_name`/`file_path`/`file_type`/`file_size`) first, then delete
the physical file. The resume record itself — `professional_summary`,
`career_objective` — is untouched.

**Delete the whole resume (`DELETE .../resume`):** unchanged endpoint,
extended behavior — the DB record is deleted first (as before), then its
physical file (if any) is deleted afterward. This is the one place this
extension modifies previously-existing Resume behavior; the endpoint's
request/response contract (204, empty body, same 404-if-missing case) is
identical to before — only an internal side effect (file cleanup) was
added.

**Missing physical files are handled gracefully, not as errors.** If DB
metadata says a file exists but it's actually gone from disk (e.g.
manual intervention, a prior partial failure), `storage.delete_file`
silently no-ops and `storage.resolve_absolute_path` returns `None` —
which the service turns into a clean `404 RESUME_FILE_NOT_FOUND` for
download, rather than a crash.

## Security & ownership

Every file endpoint resolves the student via `current_user.id` from the
JWT — exactly like the existing JSON endpoints — and **no endpoint,
request body, or query parameter anywhere in this module accepts a
student id, a filename, or a path.** The file to serve/replace/delete is
located entirely from the authenticated student's own `resumes` row; there
is no `/students/{student_id}/resume/file` and no way to address another
student's file by manipulating any client-supplied value, because none
exists to manipulate.

`resolve_absolute_path` additionally verifies the resolved path stays
within the configured upload root before returning it — defense in depth
only, since the path it resolves is always one `storage` generated itself
(a UUID-based filename under `{student_id}/`), never client input, but the
check costs nothing and protects against any future code path that might
not hold that invariant.

**`file_path` (the internal storage path) is never included in any API
response.** `ResumeResponse` exposes `file_name`, `file_type`, `file_size`,
and a derived `has_file` boolean instead — `has_file` is a Pydantic
`@computed_field`, not a real column, so it can never drift out of sync
with the actual presence of a file.

The download endpoint returns the file via FastAPI's `FileResponse` with
the *original* filename (from `file_name`) as the `Content-Disposition`
filename — the server's generated on-disk filename is never exposed to
the client at any point.

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

Two migrations:

1. **`04b4acaa5c64_create_resumes_table.py`**, depends on `38f0da1163aa`
   (the proficiency-correction migration). Creates `resumes` with the
   PK/unique-FK/timestamps described above. No enum types are involved, so
   no orphaned-type cleanup is needed on downgrade.
2. **`995c78159606_add_resume_file_metadata_columns.py`**, depends on
   `04b4acaa5c64` (confirmed as head before creating it — not rewritten).
   Adds the four nullable file-metadata columns (`file_name`, `file_path`,
   `file_type`, `file_size`) via plain `add_column`/`drop_column` — no
   data migration needed since every column is nullable and no existing
   row needs backfilling.

Both verified: upgrade → downgrade → upgrade round-trips are clean,
`alembic check` reports "No new upgrade operations detected" (zero
drift), and no existing migration was edited for either.

## Future extensions (not implemented)

**Structured sections** — the task brief explicitly asks that this MVP
stay simple and normalized, while allowing later growth without breaking
this API. The natural path:

```
resumes                  (this module — summary/objective/file only)
resume_education          (one-to-many: degree, institution, year, ...)
resume_experience          (one-to-many: role, company, dates, description, ...)
resume_projects            (one-to-many: title, description, tech stack, link, ...)
resume_certifications      (one-to-many: name, issuer, date, credential URL, ...)
resume_achievements        (one-to-many: title, description, date, ...)
```

Each would be its own table with a `resume_id` foreign key (`ON DELETE
CASCADE`), following the exact same model/schema/repository/service/router
layering used throughout this project.

**Cloud storage** — `app/modules/resumes/storage.py` was written so this
swap only touches that one file's function bodies, not their signatures
or any caller: `save_upload` would upload to S3/Azure Blob instead of
writing to a local path (returning the same `SavedFile` shape, with
`file_path` becoming an object key/blob name instead of a filesystem
path), `resolve_absolute_path`/download would generate a signed URL or
proxy the stream instead of returning a local `Path`, and `delete_file`
would issue a delete API call instead of `unlink()`. `ResumeService` and
the router would need no changes at all.

**AI parsing / resume scoring** — explicitly **not implemented in this
MVP**. No OCR, no LLM-based extraction of structured data from the
uploaded file, no resume scoring, no embeddings, no vector database. The
uploaded file today is stored and served back byte-for-byte — nothing
reads its content. A future module could parse the stored file to
populate the structured resume fields (or the planned
education/experience/etc. tables above) automatically, but that is a
distinct future capability, not a hidden dependency of anything built
here.

## Test coverage

`tests/test_resumes.py` — 43 tests, using the same real-PostgreSQL,
transaction-per-test infrastructure as the other test modules (no SQLite,
no mocked repositories). File-upload tests use a `isolated_upload_dir`
pytest fixture that monkeypatches `settings.RESUME_UPLOAD_DIR` to a
per-test `tmp_path` — file tests never write into the real `uploads/`
directory.

**Profile lifecycle (20 tests, unchanged from before this extension):**
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

**File upload/download/delete (23 new tests):**
- Resume without a file has `has_file: false` and null file fields
- Upload PDF, DOC, and DOCX individually; file metadata returned
  correctly; upload without an existing resume → 404
- Download returns the exact original bytes, correct `Content-Type`, and
  `Content-Disposition` with the original filename; download with no
  file → 404; download without a token → 401
- Replace: uploading a second file removes the first — exactly one
  physical file remains per student, and downloading returns the new
  file's content
- Delete-file-only clears metadata but the resume profile survives;
  delete-file when none exists → 404
- Deleting the whole resume also removes its physical file from disk
- Validation: wrong extension, declared-Content-Type mismatch, magic-byte
  signature mismatch, and oversized upload are each rejected with the
  correct `error_code`; an oversized upload leaves no partial file behind
- Authorization: admin rejected (403) from both upload and download
- Ownership: a student with no resume of their own gets 404 from
  download/delete-file, never another student's file or content; a
  query-string injection attempt (`?student_id=...&file_path=...`) has
  no effect, since neither endpoint reads any such parameter

Combined with the existing 63 (14 auth + 11 student + 18 skills + 20
resume-profile), the full suite is **86 tests, all passing** (run
multiple times for stability, including the exact command
`pytest tests/test_auth.py tests/test_students.py tests/test_skills.py
tests/test_resumes.py`).

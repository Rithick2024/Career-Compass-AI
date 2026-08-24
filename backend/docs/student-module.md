# Student Profile Module

Covers the `students` and `departments` tables and the `/api/v1/students/*`
endpoints: retrieving and updating a student's own profile. Admin student
management, skills, resumes, and everything downstream of a profile are out
of scope — this is profile data only.

## Module layout

```
app/modules/students/
├── models.py      # Student and Department ORM models
├── schemas.py     # Pydantic request/response contracts
├── repository.py   # StudentRepository — only place that queries students/departments
├── service.py       # StudentService — business logic, owns the DB transaction
└── router.py         # Thin FastAPI routes; no logic beyond calling the service
```

Same layering as the auth module: **router** parses the request and calls
the **service**; the **service** holds business rules and is the only thing
that commits a transaction; the **repository** is the only thing that
issues SQLAlchemy queries. The service raises `app.core.exceptions`
subclasses only, never `HTTPException`.

## Entities

### `students`

One row per student profile, extending a `users` row 1:1.

| Column             | Type                         | Notes                                    |
|---------------------|-------------------------------|--------------------------------------------|
| `id`                | integer, PK, auto-increment  | Same convention as `users.id`             |
| `user_id`           | integer, FK → `users.id`, unique | 1:1 with users; `ON DELETE CASCADE`   |
| `department_id`     | integer, FK → `departments.id`, nullable | `ON DELETE SET NULL`         |
| `full_name`         | `varchar(150)`, nullable     |                                             |
| `phone`             | `varchar(20)`, nullable      |                                             |
| `graduation_year`   | integer, nullable            |                                             |
| `cgpa`              | `numeric(4,2)`, nullable     | 0–10 scale                                 |
| `date_of_birth`     | date, nullable                |                                             |
| `address`           | `varchar(500)`, nullable     |                                             |
| `linkedin_url`      | `varchar(500)`, nullable     |                                             |
| `github_url`        | `varchar(500)`, nullable     |                                             |
| `created_at`        | timestamptz                   | `server_default=now()`                    |
| `updated_at`        | timestamptz                   | `onupdate=now()`                          |

**No authentication fields are duplicated here.** `email`, `password_hash`,
`role`, and `is_active` live on `users` only — `students` has no columns for
any of them, so there is structurally nothing to leak even by accident.

Every profile field except the `user_id` link is nullable — see
[design decisions](#design-decisions) for why.

### `departments`

A small lookup table: `id`, `name` (unique). Students reference an
**existing** department by id rather than entering free-text department
names. Seeded with six starter departments in the migration (Computer
Applications, Computer Science and Engineering, Information Technology,
Electronics and Communication Engineering, Mechanical Engineering, Business
Administration) — more can be added later via a normal data migration or a
future admin endpoint (not implemented here).

### Relationship with `users`

`students.user_id` is a unique foreign key to `users.id` — a genuine 1:1
relationship, not 1:many. Authorization is structural, not just checked in
code: every query in `StudentRepository` and every call from
`StudentService` is scoped by `current_user.id` pulled from the JWT, and no
endpoint accepts a client-supplied student or user id — so there is no
request shape that could address another student's row.

### Relationship with `departments`

`students.department_id` is a nullable foreign key to `departments.id`
(many students → one department). The ORM relationship uses
`lazy="selectin"` so `department` is always eager-loaded alongside a
student row — see [the eager-loading note](#why-lazyselectin) below for why
that matters with async SQLAlchemy specifically.

## `GET /api/v1/students/me`

Returns the authenticated student's profile, auto-provisioning an empty one
on first access (see [design decisions](#design-decisions)). Requires a
valid JWT for a **student**-role account — see
[authorization](#authorization).

Response: `StudentProfileResponse` — profile fields plus a nested
`department: { id, name } | null`.

## `PATCH /api/v1/students/me`

Partial update of the authenticated student's own profile.

- Every field is optional; **only fields present in the request body are
  changed** (`model_dump(exclude_unset=True)` in the service — a field
  omitted from the JSON body is left untouched, but a field explicitly sent
  as `null` **is** applied as null, so a student can deliberately clear a
  field like `phone`).
- `extra="forbid"` on the request schema rejects any field not in the
  schema — there is no `email`, `role`, `is_active`, etc. field on this
  schema at all, so there is no way to smuggle an auth-field change through
  this endpoint; such a request fails with **422** before it ever reaches
  the service.
- `department_id`, if supplied and non-null, must reference an existing
  department — otherwise **422 `INVALID_DEPARTMENT`**.

Response: same `StudentProfileResponse` as `GET`, reflecting the
now-updated state.

## Validation rules

| Field              | Rule                                                                 |
|---------------------|------------------------------------------------------------------------|
| `full_name`         | 1–150 chars if provided; whitespace-only is rejected                 |
| `phone`             | `^\+?[0-9\s\-\(\)]{7,20}$` — optional leading `+`, digits/spaces/hyphens/parentheses, 7–20 chars. Deliberately loose: accepts `+91 98765 43210`, `(044) 1234-5678`, `9876543210`, etc. without pinning to one country's format |
| `department_id`     | Must reference an existing `departments` row                         |
| `graduation_year`   | 1950 – (current year + 10)                                            |
| `cgpa`               | 0–10 (inclusive)                                                       |
| `date_of_birth`     | Cannot be in the future                                                |
| `address`           | Up to 500 chars                                                        |
| `linkedin_url` / `github_url` | Must be a well-formed absolute URL (Pydantic `HttpUrl`). Domain is **not** restricted to `linkedin.com`/`github.com` specifically — see note below |

**Note on URL validation:** only general URL well-formedness is enforced,
not that the domain is actually LinkedIn or GitHub. Restricting to a
specific domain risks rejecting legitimate variants (country subdomains,
short-link redirects a student might paste) for marginal benefit at this
stage. Flagged here in case product wants stricter domain checking later.

## Authorization

Both endpoints require a valid JWT, resolved through the **existing**
`get_current_user` machinery (same JWT decode → active-status check → user
load used everywhere else). Specifically, the router depends on
`RequireStudent = Depends(require_role(RoleEnum.STUDENT))` — the same
`require_role` factory the auth module already exposes for role-gating, not
a new authorization mechanism.

**Why `require_role(STUDENT)` and not bare `get_current_user`:** the task
brief names `get_current_user` as the dependency to reuse, and
`require_role` is built directly on top of it (it resolves the current user
via `get_current_user` and then adds one role check) — so using it is still
"reusing `get_current_user`," just with the additional guarantee that only
student accounts can trigger profile auto-provisioning. Without this, an
authenticated **admin** hitting `/students/me` would silently get an empty
student profile row created for their own `user_id`, which doesn't make
sense for an admin account and would pollute the `students` table. This is
a design decision, called out here in case it should be revisited once the
admin module exists.

A student can only ever reach their **own** profile: the service always
resolves the profile via `current_user.id` from the token, never from a
client-supplied id, and no route in this module accepts one.

## Design decisions

### Profile auto-provisioning (no separate "create" step)

This task's scope defines only `GET` and `PATCH` — there is no `POST
/students` to explicitly create a profile. Since a fresh student account
has no `students` row yet, both `GET` and `PATCH` transparently create an
empty one (all fields null except `user_id`) the first time the account
reaches its profile, via `StudentService._get_or_create_profile`.

**Alternative considered:** have `GET` return **404** until some other
action first creates the row. Rejected because, with only `GET`/`PATCH` in
scope, nothing else *could* create that row — a strict 404-until-created
design would leave every new student permanently locked out of an endpoint
they're clearly meant to use. Auto-provisioning was the only option that
makes the two given endpoints actually usable end-to-end within this task's
boundaries. Flagged here as a decision worth confirming — if a future
`POST /students` or student-onboarding step is added, this lazy-create
behavior may want to be reconsidered (e.g. so `GET` before onboarding
really does 404).

### Why `lazy="selectin"`

Async SQLAlchemy cannot lazily fetch a relationship attribute (e.g.
`student.department`) outside an active `await` — attempting it after the
session's async context has moved on raises `MissingGreenlet`. Setting
`lazy="selectin"` on the `Student.department` relationship means it's
always eagerly loaded as part of the normal query, so `StudentProfileResponse
.model_validate(student)` can safely read `student.department` during
response serialization without a separate loader call the repository would
otherwise have to remember on every query.

**A related bug this caught:** immediately after `PATCH` sets
`department_id`, re-fetching the student via a fresh `SELECT` was — before
a fix — still returning the *same* Python object from SQLAlchemy's
identity map, with `department` still holding its pre-update value (since
an already-loaded relationship isn't automatically refreshed by a later
`SELECT` just because the underlying FK column changed). Fixed by calling
`session.expire(student)` before the post-commit re-fetch in
`StudentService.update_my_profile`, forcing a genuine reload. Caught via
manual end-to-end testing before the automated suite was written; now
covered by `test_patch_sets_department` as a regression test.

### Every profile field is nullable

Since a profile starts empty and is filled in progressively via `PATCH`,
there is no "required at creation" set of fields to enforce — nothing is
required until the student chooses to supply it. `user_id` is the only
non-nullable link.

## Alembic

Migration: `alembic/versions/2ebd1e570480_create_departments_and_students_tables.py`,
depends on the auth module's `c227557a7841` (the integer-PK `users` table).
Creates `departments` and `students` with the PKs/FKs/unique constraints/
indexes described above, and seeds the six starter departments as data (not
hardcoded anywhere in application code — `department_id` values are looked
up, never assumed).

## Endpoints summary

| Method | Path                    | Auth required      | Success | Notable errors |
|--------|--------------------------|----------------------|---------|------------------|
| GET    | `/api/v1/students/me`   | Bearer JWT, student role | 200 | 401 missing/invalid token, 403 non-student role |
| PATCH  | `/api/v1/students/me`   | Bearer JWT, student role | 200 | 401/403 as above, 422 validation (incl. unknown department, forbidden extra fields) |

Same project-wide error envelope as every other module:
`{ "error_code": "...", "message": "...", "details": ... }`.

## Known gaps for future review

- No admin student-management endpoints yet (explicitly out of scope for
  this task) — `departments` currently has no create/update API either;
  new departments require a manual migration.
- The auto-provisioning behavior (see above) is a scope-driven design
  choice, not an explicit product requirement — worth confirming once a
  proper onboarding flow exists.
- `linkedin_url`/`github_url` accept any well-formed URL, not specifically
  LinkedIn/GitHub domains.

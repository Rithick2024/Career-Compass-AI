# Skills Module

Covers the `skills` (catalog) and `student_skills` (assignment) tables and
the `/api/v1/skills` + `/api/v1/students/me/skills` endpoints. Resume,
Companies, Jobs, Applications, Placements, and anything ML/analytics-related
are out of scope — this is the skill catalog and per-student skill
assignment only.

## Purpose

Students need to record which skills they have and at what level, drawn
from a shared, platform-wide catalog rather than free-text entry — so a
"Python" skill means the same thing across every student's profile and can
later be matched against job requirements (a future module).

## Module layout

```
app/modules/skills/
├── models.py      # Skill and StudentSkill ORM models
├── schemas.py      # Pydantic request/response contracts
├── repository.py   # SkillRepository + StudentSkillRepository
├── service.py       # SkillService — business logic, owns the DB transaction
└── router.py         # Two thin routers: catalog + per-student skills
```

Same layering as the auth and student modules: **router** parses the
request and calls the **service**; the **service** holds business rules and
is the only thing that commits a transaction; the **repositories** are the
only things that issue SQLAlchemy queries.

## Database entities

### `skills` (catalog)

| Column       | Type                      | Notes                          |
|---------------|----------------------------|----------------------------------|
| `id`          | integer, PK, auto-increment |                                |
| `name`        | `varchar(100)`, unique, indexed | e.g. "Python", "React"    |
| `category`    | `varchar(100)`, nullable   | Free-text grouping, e.g. "Programming Language", "Framework" |
| `created_at`  | timestamptz                | `server_default=now()`         |
| `updated_at`  | timestamptz                | `onupdate=now()`               |

A small lookup/catalog table — same pattern as `departments` in the student
module. Students pick from an **existing** skill rather than each creating
arbitrary duplicate entries; there is deliberately no student-facing
"create a skill" endpoint (see [Duplicate handling](#duplicate-handling)).

### `student_skills` (assignment)

| Column         | Type                          | Notes                                     |
|-----------------|---------------------------------|---------------------------------------------|
| `id`            | integer, PK, auto-increment    |                                              |
| `student_id`    | integer, FK → `students.id`, indexed | `ON DELETE CASCADE`                  |
| `skill_id`      | integer, FK → `skills.id`      | `ON DELETE CASCADE`                        |
| `proficiency`   | native enum `proficiency_level` | `beginner` \| `intermediate` \| `advanced` |
| `created_at`    | timestamptz                    | `server_default=now()`                    |
| `updated_at`    | timestamptz                    | `onupdate=now()`                          |

**Unique constraint on `(student_id, skill_id)`** — a student can have at
most one row per skill; adding an already-present skill is a **409**, not a
second row (see [Duplicate handling](#duplicate-handling)).

**`ON DELETE CASCADE` on both foreign keys:** if a student's profile is
deleted, their skill assignments go with it (same reasoning as
`students.user_id`'s cascade). If a catalog skill is ever removed (no
admin/delete API exists for skills yet), any student assignment of it is
removed too — `skill_id` is `NOT NULL`, so the `SET NULL` pattern used for
`students.department_id` isn't available here.

## Relationships

- **`students` 1 ─── N `student_skills` N ─── 1 `skills`** — a standard
  many-to-many between students and skills, with `student_skills` as the
  association table carrying the extra `proficiency` attribute.
- Every `student_skills` row's `skill` relationship uses `lazy="selectin"`
  (same reasoning as `Student.department`): async SQLAlchemy can't lazily
  fetch a relationship outside an active `await`, so eager-loading here is
  what lets response serialization safely read `student_skill.skill`
  without a separate loader call every repository query would otherwise
  have to remember.
- **`student_skills.student_id` references `students.id`, not `users.id`.**
  Since the authenticated JWT only carries a `users.id`, `SkillService`
  resolves (and, on first access, auto-provisions — reusing
  `StudentRepository` directly, the same get-or-create logic
  `StudentService` already uses) the current user's `students.id` before
  any skill operation. This is intentional reuse of the Student module's
  data-access layer, not a new auth mechanism — see
  [Authorization](#authorization).

## API endpoints

| Method | Path                              | Auth required | Success | Notable errors |
|--------|-------------------------------------|------------------|---------|------------------|
| GET    | `/api/v1/skills`                   | Bearer JWT, student role | 200, `SkillOut[]` | 401/403 |
| GET    | `/api/v1/students/me/skills`       | Bearer JWT, student role | 200, `StudentSkillResponse[]` | 401/403 |
| POST   | `/api/v1/students/me/skills`       | Bearer JWT, student role | 201, `StudentSkillResponse` | 404 unknown skill, 409 duplicate, 422 validation |
| PATCH  | `/api/v1/students/me/skills/{skill_id}` | Bearer JWT, student role | 200, `StudentSkillResponse` | 404 not on profile, 422 validation |
| DELETE | `/api/v1/students/me/skills/{skill_id}` | Bearer JWT, student role | 204, empty body | 404 not on profile |

Same project-wide error envelope as every other module:
`{ "error_code": "...", "message": "...", "details": ... }`.

### Why this contract (and not something else)

The task's suggested structure was used essentially as-is — it already
matches REST conventions well and nests naturally under the existing
`/students/me` resource, which makes ownership explicit in the URL shape
itself. Two separate `APIRouter` objects are defined in `router.py` (one
for `/skills`, one for `/students/me/skills`) to keep the two distinct
resources — a flat platform catalog vs. a nested per-student collection —
visibly separate in the code, even though both live in the same module.

### Request/response examples

**`GET /api/v1/skills`** → `200`
```json
[
  {"id": 1, "name": "Python", "category": "Programming Language"},
  {"id": 6, "name": "React", "category": "Framework"}
]
```

**`POST /api/v1/students/me/skills`**
```json
{"skill_id": 1, "proficiency": "intermediate"}
```
→ `201`
```json
{
  "id": 42,
  "student_id": 7,
  "skill": {"id": 1, "name": "Python", "category": "Programming Language"},
  "proficiency": "intermediate",
  "created_at": "2026-08-25T02:40:12Z",
  "updated_at": "2026-08-25T02:40:12Z"
}
```

**`PATCH /api/v1/students/me/skills/1`**
```json
{"proficiency": "advanced"}
```
→ `200` (same shape as above, `proficiency` updated)

**`DELETE /api/v1/students/me/skills/1`** → `204`, empty body

## Validation

| Case | Behavior |
|---|---|
| `skill_id` doesn't exist (POST) | `404 SKILL_NOT_FOUND` |
| Duplicate `(student, skill)` (POST) | `409 SKILL_ALREADY_ADDED` |
| Invalid `proficiency` value | `422` (Pydantic enum validation — not one of `beginner`/`intermediate`/`advanced`) |
| Malformed `skill_id` (non-integer path segment or body field) | `422` (FastAPI/Pydantic type coercion) |
| PATCH/DELETE on a skill the student doesn't have | `404 STUDENT_SKILL_NOT_FOUND` |
| Extra/unknown fields in request body | `422` (`extra="forbid"` on both request schemas) |

## Authorization

All five endpoints use `RequireStudent` — the **existing**
`require_role(RoleEnum.STUDENT)` dependency, unchanged from the student
module. No new authentication or authorization mechanism was introduced.

**Ownership is structural, not just checked in code:** every skill
operation resolves the student via `current_user.id` from the JWT, and
`skill_id` in the URL only identifies *which catalog skill*, not whose
assignment row. A `student_skills` row is only ever found by the compound
lookup `(current student's student_id, skill_id)` — so there is no request
shape that lets one student address another's `student_skills` row by
guessing an ID. Attempting to `PATCH`/`DELETE` a skill assignment that
belongs to a different student returns the same `404
STUDENT_SKILL_NOT_FOUND` as a skill the student genuinely never added —
it's indistinguishable from "not found," which is itself a deliberate
choice: it never confirms or denies that *some other student* has that
skill.

**Why `/skills` (the catalog) also requires student role, not just any
authenticated user:** there's no ownership concept on the flat catalog
list, so gating it with a bare "any authenticated user" dependency would
have been defensible too. `RequireStudent` was used instead purely for
consistency — every existing feature endpoint (as opposed to `/auth/*`)
already uses `RequireStudent` uniformly, and introducing a second
"authenticated, any role" tier for just this one endpoint would be a new
pattern for no real benefit yet, since no other role currently exists with
its own endpoints to justify it. Flagged here for reconsideration once an
admin or recruiter role needs catalog access.

## Duplicate handling

Skills are a **reusable, platform-level catalog** — there is no student-
facing "create a skill" endpoint, by design (per the task brief and
consistent with the `departments` pattern already established). A student
"adding a skill" always means *creating a `student_skills` row pointing at
an existing `skills` row*, never inserting a new catalog entry. The unique
constraint on `(student_id, skill_id)` enforces this at the database level
in addition to the application-level check in `SkillService.add_skill`, so
a duplicate can't slip through even under a race condition.

## Proficiency representation

**Confirmed against the actual frontend contract: exactly three levels —
`beginner`, `intermediate`, `advanced`.** An earlier version of this module
included a fourth `expert` value, added before the frontend was available
for inspection (see the module's original design-decision note in an
earlier revision of this doc). Once the frontend contract was inspected,
`expert` was found not to exist in the UI and was removed:

- `app.shared.enums.ProficiencyLevel` now defines only the three values.
- The native PostgreSQL enum type `proficiency_level` was narrowed via a
  **corrective migration** (`38f0da1163aa`) rather than editing the
  migration that originally created it — see [Migration](#migration) below.
- The API's machine-readable values stay lowercase
  (`"beginner"`/`"intermediate"`/`"advanced"`); the frontend maps these to
  its own title-case display labels (Beginner/Intermediate/Advanced). No
  casing or serialization behavior changed — only the set of valid values
  shrank from four to three.

If the level names or scale ever need to change again, the same pattern
applies: update `ProficiencyLevel`, then write a new corrective migration
using PostgreSQL's recreate-the-enum-type recipe (see the migration file's
docstring) — never edit an already-applied migration in place.

## Migration

Two migrations are involved:

1. **`70466c0ad0bf_create_skills_and_student_skills_tables.py`** — depends
   on `2ebd1e570480` (the student-profile migration). Creates `skills` and
   `student_skills` with the PKs/FKs/unique constraint/indexes described
   above, originally with a four-value `proficiency_level` enum.
   `downgrade()` explicitly drops the enum type after dropping the tables
   (same fix already applied to `user_role` in the users migration —
   `DROP TABLE` alone leaves a PostgreSQL enum type orphaned).

2. **`38f0da1163aa_remove_expert_proficiency_level.py`** — depends on
   `70466c0ad0bf`. A **corrective** migration, not a rewrite: since
   `70466c0ad0bf` was already applied, its `expert` value is removed on
   top of it rather than by editing that file's history. PostgreSQL has no
   `ALTER TYPE ... DROP VALUE`, so the migration uses the standard-safe
   recreate-the-type recipe: remap any existing `expert` rows to
   `advanced` first (a one-way step — see the migration's docstring for
   why a downgrade can't perfectly reverse it), create a new three-value
   type, move the column to it via a text cast, drop the old type, and
   rename the new one into its place. **Verified against real data**, not
   just an empty table: a row was manually set to `expert`, the migration
   re-run, and confirmed to correctly convert it to `advanced` before
   narrowing the type.

Both verified: upgrade → downgrade → upgrade round-trips cleanly for each,
and `alembic revision --autogenerate` produces an empty diff against the
final models (zero drift) after both are applied.

### Seed data

19 starter skills seeded via the `70466c0ad0bf` migration (Python, Java,
JavaScript, TypeScript, SQL, React, Node.js, FastAPI, Django, PostgreSQL,
MongoDB, Git, Docker, AWS, Azure, Machine Learning, Data Analysis, Power
BI, Excel) — the same list suggested in the task brief, lightly grouped
into categories. Reversible: downgrading `70466c0ad0bf` removes the tables
entirely, taking the seed rows with them. Unaffected by the proficiency
correction, which only touches the `proficiency` column/type.


## Test coverage

`tests/test_skills.py` — 18 tests, using the same real-PostgreSQL,
transaction-per-test infrastructure as `test_auth.py`/`test_students.py`
(no SQLite, no mocked repositories):

- Catalog retrieval (authenticated / unauthenticated)
- Student's own skill list (authenticated, empty-by-default / unauthenticated)
- Add skill (success, duplicate → 409, unknown skill → 404, invalid proficiency → 422)
- Each of the three valid proficiency values (`beginner`/`intermediate`/`advanced`) individually confirmed accepted (parametrized test)
- `expert` explicitly confirmed rejected (422) now that it's no longer a valid value
- Update proficiency (success, not-owned → 404)
- Remove skill (success, not-owned → 404)
- Cross-student ownership isolation (one student's add doesn't leak into another's list; PATCH/DELETE on another student's assignment returns 404, not another student's data)
- Admin role rejected from every student-only skills endpoint (403)

Combined with the existing 25 (14 auth + 11 student), the full suite is
**43 tests, all passing** (run twice for stability, plus a third run after
the migration was cycled downgrade→upgrade again).

## Known gaps for future review

- No admin skill-management API (create/edit/delete catalog skills) —
  adding a new skill currently requires a manual migration, same as
  departments.
- No bulk "add several skills at once" endpoint — each skill is added with
  its own `POST` call.

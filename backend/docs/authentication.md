# Authentication

Covers the `users` table and the `/api/v1/auth/*` endpoints: registration,
login, current-user resolution, and role-based authorization. This module
does not implement refresh tokens, password reset, or email verification —
those are out of scope for now.

## Module layout

```
app/modules/auth/
├── models.py      # User ORM model
├── schemas.py      # Pydantic request/response contracts
├── repository.py   # UserRepository — only place that queries `users`
├── service.py       # AuthService — business logic, owns the DB transaction
└── router.py         # Thin FastAPI routes; no logic beyond calling the service

app/core/
├── security.py    # Password hashing (bcrypt), isolated behind hash_password/verify_password
├── jwt.py          # JWT create/decode, isolated behind create_access_token/decode_access_token
└── config.py       # JWT_SECRET_KEY / JWT_ALGORITHM / JWT_ACCESS_TOKEN_EXPIRE_MINUTES (from env)

app/api/deps.py     # get_current_user, CurrentUser, require_role(...) — reusable by any future module
app/shared/enums.py  # RoleEnum(student, admin) — the shared enum strategy
```

Standard flow through the layers for every endpoint: **router** parses the
request and calls the **service**; the **service** holds business rules and
is the only thing that commits a transaction; the **repository** is the only
thing that issues SQLAlchemy queries. The service never raises
`HTTPException` — only `app.core.exceptions.AppException` subclasses, which
`app.core.error_handlers` translates into HTTP responses at the edge.

## Database: `users` table

| Column          | Type                        | Notes                                   |
|-----------------|-----------------------------|------------------------------------------|
| `id`            | `integer`, PK, auto-increment | DB-generated (PostgreSQL `SERIAL`, via `users_id_seq`) on insert |
| `email`         | `varchar(255)`, unique, indexed | Stored lowercase (see normalization)  |
| `password_hash` | `varchar(255)`              | bcrypt hash — never the plaintext         |
| `role`          | native enum `user_role`     | `student` \| `admin`; defaults to `student` |
| `is_active`     | boolean                     | Defaults to `true`                       |
| `created_at`    | timestamptz                 | Set by the DB (`server_default=now()`)   |
| `updated_at`    | timestamptz                 | Auto-updated on row change (`onupdate=now()`) |

No separate roles table — `role` is a native PostgreSQL enum, per the shared
enum strategy in `app.shared.enums.RoleEnum` (a `str, Enum` used directly as
both the Pydantic field type and the SQLAlchemy column type, so the value
list is defined once).

Migration: `alembic/versions/c227557a7841_create_users_table.py`.
`downgrade()` explicitly drops the `user_role` enum type after dropping the
table — `DROP TABLE` alone leaves a PostgreSQL enum type orphaned, since the
type isn't owned by the table.

> **Note:** this migration was regenerated in place (same "create users
> table" migration, new revision id) when `users.id` was changed from UUID
> to an auto-incrementing integer, since no data existed yet at that point
> in development. See the migration's docstring for details.

## Registration flow

`POST /api/v1/auth/register`

1. `UserRegisterRequest` validates the payload: `email` (RFC-validated),
   `password` (8–72 chars — see [password hashing](#password-hashing) for
   why 72 is a hard ceiling, not just a nice round number), and an
   **optional** `role`.
2. Email is normalized (`strip().lower()`) before it ever reaches the
   service or the DB, so `Foo@Bar.com` and `foo@bar.com` are the same
   account and collide correctly on the unique index.
3. The service checks for an existing user with that email; if found, it
   raises `ConflictError` → **409 `EMAIL_ALREADY_REGISTERED`**.
4. The password is hashed (never stored in plaintext) and a new row is
   inserted with `role=student`, `is_active=true`.
5. Response: **201**, the created user via `UserPublic` (id, email, role,
   is_active, created_at — `password_hash` is never part of any response
   schema, so there's no field to accidentally leak).

### Public registration policy (security decision)

**Public registration can only ever create a `student` account.** The
`role` field is accepted in the request but validated in
`UserRegisterRequest.validate_role`: if present and not `"student"`, the
request is rejected outright with **422**, not silently downgraded to
`student`. Silently downgrading was ruled out — a caller who explicitly
asked for `admin` and got `student` back with a 201 could easily miss that
they didn't get what they asked for; failing loudly is safer and more
honest about what happened.

There is currently no endpoint to create an admin account. Provisioning the
first admin(s) is a deliberate manual step (e.g. a direct DB insert or a
future admin-only "invite" endpoint) — intentionally left out of this task's
scope. This is flagged in the final report as something to revisit before
any real admin workflow is needed.

## Password hashing

`app/core/security.py` wraps `bcrypt` directly (not `passlib` — passlib is
effectively unmaintained and has known incompatibilities with bcrypt ≥4.1).
The interface is two functions, `hash_password` / `verify_password`, kept
deliberately narrow so the algorithm can be swapped later (e.g. to argon2)
without touching any caller.

- Bcrypt work factor: 12 rounds.
- Bcrypt only uses the first 72 bytes of the input and silently ignores the
  rest — so `UserRegisterRequest.password` caps input at 72 characters.
  Without that cap, two different long passwords sharing the same first 72
  bytes would hash identically, which would be a silent, confusing
  correctness bug rather than a loud one.
- Passwords are never logged. The only place a plaintext password exists in
  memory is inside the request body and the call into `hash_password` /
  `verify_password`.

## Login flow

`POST /api/v1/auth/login`

1. `UserLoginRequest` validates and normalizes `email` the same way as
   registration.
2. The service looks up the user by email and verifies the password with
   `verify_password`.
3. **If the user doesn't exist, or the password is wrong, the response is
   identical either way**: 401, `INVALID_CREDENTIALS`, "Invalid email or
   password." This is deliberate — returning a different message for
   "no such user" vs. "wrong password" would let an attacker enumerate
   which emails are registered.
4. If credentials are valid but `is_active` is `false`, the service raises
   `ForbiddenError` → **403 `ACCOUNT_INACTIVE`**, not 401. See
   [status code for inactive accounts](#why-403-for-inactive-accounts-not-401)
   below for the reasoning.
5. On success: a JWT is issued and returned alongside the user's public
   profile: `{ access_token, token_type: "bearer", user: {...} }`.

### Why 403 for inactive accounts, not 401

The task brief's status-code list only explicitly assigns 401 to "invalid
credentials / invalid token" and 403 to "insufficient role." Inactive-account
handling isn't explicitly assigned either code, so this was a judgment call,
documented here for review: **401 means "I don't know who you are"; 403
means "I know who you are, and the answer is no."** An inactive account has
*correct* credentials — the server successfully authenticated the request —
it's just not allowed to proceed. That's an authorization outcome, not an
authentication failure, so 403 fits better than 401. The same reasoning
applies to `get_current_user`: a syntactically valid, unexpired JWT for a
now-deactivated user also returns 403, not 401.

## JWT flow

`app/core/jwt.py`, config-driven via `settings.JWT_SECRET_KEY`,
`JWT_ALGORITHM` (default `HS256`), `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
(default 60). The secret is never hardcoded — it's required in `Settings`
(no default), so the app fails to start without one configured.

**Claims:** `sub` (the user's integer id, encoded as a string — this is the only claim
`get_current_user` actually relies on), `role` (a convenience claim for
callers who want to inspect the token without a DB round-trip — **not**
trusted for authorization decisions; the DB row is always the source of
truth for role and active-status checks), `iat`, `exp`.

**Decoding** (`decode_access_token`) wraps `PyJWT` and raises a single
`TokenError` for every failure mode — expired signature, bad signature,
malformed token — so callers don't need to know PyJWT's specific exception
hierarchy. `AuthService.get_current_user` catches `TokenError` and converts
it to `UnauthorizedError` → **401 `INVALID_TOKEN`**.

No refresh tokens are implemented (out of scope for this task, per the
brief) — when the 60-minute access token expires, the client must log in
again.

## `/me` flow

`GET /api/v1/auth/me`, protected by the `CurrentUser` dependency
(`app.api.deps.get_current_user`, built on FastAPI's `OAuth2PasswordBearer`
so the bearer token is extracted from the `Authorization` header and the
`/docs` "Authorize" button works out of the box).

Every call re-derives the user from the token and a fresh DB lookup — it
does **not** trust anything about the user's current state from the token
itself beyond `sub`. Concretely: `get_current_user`

1. Decodes the token (`TokenError` → 401).
2. Extracts and parses `sub` as an integer (malformed → 401).
3. Loads the user by id (not found → 401 — e.g. an account deleted after
   the token was issued).
4. Checks `is_active` (false → 403 `ACCOUNT_INACTIVE`).

This means deactivating a user takes effect on their very next request,
even with an otherwise still-valid, unexpired token — verified in
`test_login_inactive_user_rejected` and manually against a live token (see
final report).

Response is `UserPublic` — the same safe representation used everywhere
else; `password_hash` is structurally impossible to return since it isn't a
field on the schema.

## Role-based authorization

`app.api.deps.require_role(*allowed_roles)` is a dependency **factory** —
call it with one or more `RoleEnum` values to get a dependency that first
resolves the current user (reusing `get_current_user`), then checks
`user.role in allowed_roles`. On failure: `ForbiddenError` → **403
`INSUFFICIENT_ROLE`**.

```python
from app.api.deps import require_role
from app.shared.enums import RoleEnum

# Gate a whole route:
@router.get("/admin-only", dependencies=[Depends(require_role(RoleEnum.ADMIN))])
async def admin_report(): ...

# Or gate it and use the resolved user:
@router.get("/admin-only")
async def admin_report(user: Annotated[User, Depends(require_role(RoleEnum.ADMIN))]):
    ...
```

This lives in the shared `app/api/deps.py` (not inside the auth module)
specifically so every future feature module can import and reuse it without
depending on `app.modules.auth` internals. Student-specific authorization
(e.g. "can this student only see their own profile") is explicitly out of
scope here — that belongs to the Student module, per the task brief.

## Endpoints summary

| Method | Path                     | Auth required | Success | Notable errors |
|--------|--------------------------|----------------|---------|-----------------|
| POST   | `/api/v1/auth/register`  | No             | 201     | 409 duplicate email, 422 validation (incl. non-student role) |
| POST   | `/api/v1/auth/login`     | No             | 200     | 401 invalid credentials, 403 inactive account |
| GET    | `/api/v1/auth/me`        | Bearer JWT     | 200     | 401 missing/invalid/expired token, 403 inactive account |

All error responses use the project-wide envelope:
`{ "error_code": "...", "message": "...", "details": ... }` — no separate
format was introduced for this module.

## Security decisions checklist

- ✅ `password_hash` never appears in any response schema or log line.
- ✅ Passwords are never logged (not even at DEBUG — the request body isn't
  logged anywhere in the stack).
- ✅ `JWT_SECRET_KEY` has no default; the app won't start without one set in
  the environment.
- ✅ Public registration cannot create non-`student` accounts.
- ✅ Token expiration is enforced (`exp` claim, checked by PyJWT on decode).
- ✅ Active status is re-checked from the DB on every authenticated request,
  not cached in the token.
- ✅ Login failure messages don't distinguish "no such user" from "wrong
  password."

## Known gap for future review

There is no way to create the first admin account through the API by
design (see [public registration policy](#public-registration-policy-security-decision)).
Until an admin-provisioning path exists (manual DB insert, seed script, or a
future admin-invite endpoint), `require_role(RoleEnum.ADMIN)` has nothing to
authorize against in a fresh environment. This is intentional for this task
but should be revisited before any admin-facing module ships.

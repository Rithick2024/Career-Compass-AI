# Career Compass AI — Backend

Smart Placement Analytics Platform.

Implemented so far: project foundation (config, DB, logging, exceptions,
DI, health checks) and the **Authentication module** (registration, login,
JWT, `/me`, role-based authorization). Student, Skills, Resume, Company,
Job, Application, Dashboard, and Placement modules are not yet built.

## Stack

FastAPI · SQLAlchemy 2.x (async) · PostgreSQL · Alembic · Pydantic v2 · JWT · bcrypt

## Architecture

Feature-based modules, Repository Pattern, Service Layer, Clean Architecture.
Each feature module lives under `app/modules/<feature>/` as
`{models,schemas,repository,service,router}.py` — see `app/modules/auth/`
for the reference implementation every future module should follow.

```
app/
├── main.py                 # FastAPI app factory, lifespan, middleware
├── core/
│   ├── config.py           # Pydantic-settings, env-driven, DATABASE_URL, JWT settings
│   ├── logging_config.py   # dictConfig-based logging setup
│   ├── exceptions.py       # AppException hierarchy (framework-agnostic)
│   ├── error_handlers.py   # Global FastAPI exception handlers
│   ├── security.py         # Password hashing (bcrypt), isolated/swappable
│   └── jwt.py               # JWT create/decode
├── db/
│   ├── database.py         # Async engine + declarative Base
│   ├── base.py              # Metadata import hub for Alembic autogenerate
│   └── session.py          # AsyncSessionLocal + get_db dependency
├── api/
│   ├── deps.py              # Shared DI: DBSession, AppSettings, CurrentUser, require_role(...)
│   └── v1/
│       ├── health.py        # /health, /health/db
│       ├── __init__.py      # api_router aggregator
├── modules/
│   └── auth/                # Registration, login, /me — see docs/authentication.md
└── shared/
    └── enums.py             # RoleEnum — shared enum strategy for all modules

alembic/                     # Async migration environment, wired to app settings
docs/
└── authentication.md        # Full auth module documentation
tests/
└── test_auth.py             # Automated tests for the auth module
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt   # includes requirements.txt + test tooling

cp .env.example .env             # then edit DB credentials and JWT_SECRET_KEY
```

Generate a real JWT secret (never use the example placeholder outside local dev):

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Ensure PostgreSQL is running and the databases exist:

```bash
createdb career_compass         # dev database
createdb career_compass_test    # test database (used by the automated tests)
```

## Run

```bash
uvicorn app.main:app --reload
```

- Health check: `GET http://localhost:8000/api/v1/health`
- DB connectivity check: `GET http://localhost:8000/api/v1/health/db`
- Interactive docs: `http://localhost:8000/docs`
- Auth endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`,
  `GET /api/v1/auth/me` — see `docs/authentication.md` for full details.

## Migrations (Alembic)

`alembic/env.py` pulls the connection string from `app.core.config.settings`
(not from `alembic.ini`), so `.env` is the single source of truth. It also
imports `app.db.base.Base.metadata` for `--autogenerate` support.

```bash
alembic upgrade head                              # apply migrations
alembic revision --autogenerate -m "add students"  # once new models are added
```

## Tests

```bash
pytest tests/ -v
```

Runs against the dedicated `career_compass_test` database (never the dev
DB), with each test wrapped in a rolled-back transaction for isolation.

## Conventions for feature modules

- Routers stay thin: parse request → call service → return response.
- Services hold business logic, raise `app.core.exceptions.AppException`
  subclasses (never `HTTPException`), and own the transaction boundary
  (they call `commit()`; repositories don't).
- Repositories are the only layer that talks to SQLAlchemy directly.
- Get a DB session in a router via `app.api.deps.DBSession`; get the
  authenticated user via `app.api.deps.CurrentUser`; gate an endpoint by
  role via `app.api.deps.require_role(RoleEnum.ADMIN)`.
- Shared enums go in `app.shared.enums` (subclass `str, Enum` so they work
  as both a Pydantic field type and a native PostgreSQL enum column).


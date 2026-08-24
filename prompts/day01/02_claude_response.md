Day 1 design document is ready — covers all 13 sections with the reasoning behind each architectural choice (feature-based folders, Clean Architecture layering, Repository Pattern, why the Prediction module is isolated behind interfaces, branch strategy, and the final-year extension path).
A couple of things worth flagging since this feeds into your MCA project:

The folder structures for both frontend and backend mirror each other module-for-module (auth, students, skills, resumes, companies, jobs, dashboard, prediction) — this is intentional so you can trace any feature end-to-end during your viva.
The Prediction module is the one place I enforced a strict interface boundary, since that's almost certainly what you'll swap for real ML in your final year.

Want me to move on to Day 2 — e.g., detailed ER diagram / entity design (without actual DB tables/code, just the conceptual model), or start drafting the actual database schema and Alembic migration plan next?

----------

# Career Compass AI – Smart Placement Analytics Platform
### Day 1 – Project Foundation & Architecture Document

---

## 1. Project Overview

Career Compass AI is a full-stack web platform designed to digitize and streamline the campus placement process for an academic institution. Students use the platform to build and maintain their professional profile — skills, resumes, and preferences — while administrators (placement cell staff) use it to manage companies, job postings, and to view analytics on placement performance across batches, departments, and skill sets.

The system is built as a **modular monolith** for the mini project phase: a single deployable FastAPI backend and a single React frontend, but internally organized so that each module (Authentication, Students, Skills, Resumes, Companies, Jobs, Dashboard, Prediction) is isolated enough to later be extracted into a microservice or extended with more advanced AI capability, without a rewrite.

The "AI" in the current phase is intentionally simple — a rule-based or lightweight statistical placement-probability score — because the mini project's grading emphasis is on **architecture, correctness, and engineering discipline**, not model sophistication. The architecture is deliberately over-provisioned for this, so that in the final year expansion, real ML/NLP components (resume parsing, JD-matching, recommendation engines) can be plugged in without disturbing the rest of the system.

---

## 2. Problem Statement

Most college placement cells today rely on a combination of spreadsheets, email threads, WhatsApp groups, and static PDF resumes to run placement drives. This creates several recurring problems:

- **No single source of truth** for student skills, resume versions, or eligibility status.
- **Manual matching** of students to job openings, which doesn't scale as company/job volume increases.
- **No visibility** for administrators into aggregate trends — which skills are in demand, which departments are underperforming, which students are at risk of not being placed.
- **No predictive insight** — students don't know where they stand or what to improve; admins can't proactively intervene.
- **Fragmented resume management** — students maintain resumes outside any central, structured system, making it impossible to search/filter candidates by structured attributes (skills, CGPA, projects).

Career Compass AI addresses this by centralizing student data, company/job data, and providing structured analytics and a lightweight predictive signal, all behind a single authenticated platform with role-based access.

---

## 3. Objectives

1. Provide a **single authenticated platform** for students and placement administrators with role-based access control.
2. Allow students to **maintain a structured profile**: personal details, academic details, skills (with proficiency levels), and multiple resume versions.
3. Allow administrators to **manage companies and job listings**, and map eligibility criteria against student profiles.
4. Provide a **Placement Dashboard** with aggregate, filterable analytics (by department, batch, skill, company).
5. Provide a **simple, explainable placement-prediction score** per student based on transparent rule-based/statistical scoring — not a black box — so it can be explained in a viva/demo.
6. Build the system using **Clean Architecture and Repository Pattern** so that business logic is decoupled from frameworks (FastAPI, SQLAlchemy) and can be tested and extended independently.
7. Ensure the codebase is **production-grade and scalable**, so it can be directly extended in the final year project rather than rebuilt.

---

## 4. Functional Requirements

### 4.1 Authentication
- Users register/login as either Student or Admin.
- JWT-based access + refresh token flow.
- Password hashing, token expiry, and role claims embedded in the JWT.
- Protected routes on both frontend (route guards) and backend (dependency-based auth checks).

### 4.2 Student Management
- Students can create/update their profile (name, department, batch, CGPA, contact info).
- Admins can view/search/filter all student profiles.
- Soft-delete / deactivate student accounts (no hard deletes, to preserve historical placement data).

### 4.3 Skills Management
- Students can add/remove skills from a structured skill list, each with a proficiency level (Beginner/Intermediate/Advanced).
- Admins can view aggregate skill distribution across the student pool.
- Skills are stored as a normalized master list (not free text) so analytics remain queryable.

### 4.4 Resume Management
- Students can upload multiple resume versions (PDF).
- One resume can be marked "active/default" for job applications.
- Admins can view/download resumes for eligible students per job listing.

### 4.5 Company Management
- Admins can create/update/deactivate company records (name, industry, description, eligibility norms).
- Companies are linked to Job Listings (1-to-many).

### 4.6 Job Listings
- Admins create job postings under a company: role, package (CTC), eligibility criteria (min CGPA, allowed departments, required skills).
- Students can view jobs they are eligible for.
- Students can apply; applications are tracked with status (Applied / Shortlisted / Selected / Rejected).

### 4.7 Placement Dashboard
- Admin-facing analytics: placement % by department/batch, average package, top recruiting companies, skill-demand trends.
- Filterable by date range, department, batch, company.

### 4.8 Simple Placement Prediction
- Rule-based / statistical scoring engine that computes a "Placement Readiness Score" per student using explainable factors: CGPA, skill count/relevance, resume completeness, prior application outcomes.
- Score and its contributing factors are shown transparently to the student (explainability is a requirement, not an afterthought — this is a design decision to keep trust and to make the module viva-defensible).

### 4.9 Admin Dashboard
- Central admin view combining student management, company/job management, and placement analytics summaries.

---

## 5. Non-Functional Requirements

| Category | Requirement | Rationale |
|---|---|---|
| **Security** | JWT auth, hashed passwords (bcrypt/argon2), role-based authorization on every endpoint | Non-negotiable for any system handling student PII |
| **Scalability** | Modular monolith with clear module boundaries; stateless backend | Allows horizontal scaling and future service extraction |
| **Maintainability** | Clean Architecture, Repository Pattern, Service Layer | Business logic isolated from FastAPI/SQLAlchemy specifics; easy to test and extend |
| **Performance** | Paginated list endpoints, indexed DB columns on frequently filtered fields | Placement/student lists can grow into thousands of rows |
| **Type Safety** | TypeScript on frontend, Pydantic schemas + SQLAlchemy models on backend | Reduces runtime errors, improves refactor safety |
| **Testability** | Service layer and repositories independently unit-testable via dependency injection | Grading rubrics for MCA projects typically expect demonstrable testing |
| **Usability** | Consistent UI via shadcn/ui component library, responsive layout | Small team, no dedicated designer — a component system enforces consistency |
| **Auditability** | Soft deletes, created_at/updated_at timestamps on all entities | Placement data has institutional/historical value; nothing should be truly lost |
| **Portability** | Dockerizable backend, environment-based config (.env) | Enables consistent deployment across dev/staging/demo environments |

---

## 6. User Roles

| Role | Description | Key Permissions |
|---|---|---|
| **Student** | Primary end user maintaining their own profile | CRUD own profile, skills, resumes; view eligible jobs; apply; view own prediction score |
| **Admin (Placement Cell Staff)** | Manages the placement process | CRUD companies/jobs; view/search all students; view dashboard analytics; manage applications |
| **(Future) Super Admin** | Reserved role, not implemented in mini project | System configuration, user role management — noted here so the `role` field is designed as an extensible enum, not a boolean `is_admin` flag |

**Architectural decision:** Roles are modeled as a string/enum field on the User entity rather than separate tables per role, and authorization is done via a single reusable `require_role()` dependency in FastAPI. This keeps the auth system trivially extensible when a third or fourth role is introduced later (e.g., Recruiter role in the final year expansion) without a schema migration to restructure roles.

---

## 7. Module Breakdown

1. **Authentication Module** — registration, login, JWT issuance/refresh, password hashing, current-user resolution.
2. **Student Management Module** — student profile CRUD, search/filter for admins.
3. **Skills Management Module** — master skill list, student-skill mapping with proficiency.
4. **Resume Management Module** — file upload/storage reference, versioning, active-resume flag.
5. **Company Management Module** — company CRUD, deactivation instead of deletion.
6. **Job Listings Module** — job CRUD under a company, eligibility rule storage, application tracking.
7. **Placement Dashboard Module** — read-only aggregation queries surfaced as analytics endpoints.
8. **Placement Prediction Module** — isolated scoring service consuming data from Student/Skills/Resume/Jobs modules via defined interfaces (not direct DB reads) — this isolation is intentional so the scoring logic can later be swapped for a real ML model without touching other modules.
9. **Admin Dashboard Module** — composition layer on the frontend that aggregates Student, Company, Job, and Dashboard modules into a single operational view; not a distinct backend module.

**Why modules are structured this way:** Each module maps 1:1 to a bounded context with its own repository, service, and schema layer. The Prediction module is deliberately dependent only on *service interfaces* of other modules (not their repositories/DB tables directly) — this is the one place in the mini project where an interface boundary is enforced strictly, because it is the module most likely to be replaced wholesale in the final year (rule-based → ML-based).

---

## 8. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT (Browser)                       │
│   React + TypeScript + Vite + Tailwind + shadcn/ui               │
│   React Router (routing) · React Query (server state/cache)      │
│   Axios (HTTP client, interceptors for JWT attach/refresh)        │
└───────────────────────────────┬───────────────────────────────────┘
                                │ REST (JSON over HTTPS)
┌───────────────────────────────▼───────────────────────────────────┐
│                         API LAYER (FastAPI)                       │
│  Routers (per module) → thin, no business logic                   │
│  ── validates request via Pydantic schemas                        │
│  ── delegates to Service Layer                                     │
│  ── translates domain exceptions → HTTP responses                 │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                        SERVICE LAYER (Business Logic)              │
│  Pure Python, framework-agnostic                                   │
│  Orchestrates use-cases (e.g. "apply to job", "compute score")     │
│  Talks to Repositories via interfaces, not concrete DB session      │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                     REPOSITORY LAYER (Data Access)                 │
│  SQLAlchemy models + query logic, isolated per module               │
│  Only place in the codebase aware of SQL/ORM specifics              │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                    PostgreSQL (via Alembic migrations)              │
└─────────────────────────────────────────────────────────────────────┘
```

**Key architectural decisions and why:**

- **Routers stay thin.** FastAPI route handlers only parse/validate input and call a service method. This keeps business logic testable without spinning up HTTP — a service method can be unit tested by calling it directly with a mocked repository.
- **Service Layer is framework-agnostic.** It does not import `fastapi` or `Depends` internals. This is what makes "Clean Architecture" real rather than cosmetic: if the framework changed from FastAPI to Django tomorrow, the service layer would not need to change.
- **Repository Pattern isolates SQLAlchemy.** Services depend on repository *interfaces* (abstract base classes / Protocols), not on `Session` objects directly. This allows repositories to be swapped with in-memory fakes during testing, and is the seam where the Prediction module can later pull from an external ML service instead of Postgres.
- **Dependency Injection via FastAPI's `Depends`.** Used only at the API boundary to construct services with their repository dependencies — keeping the wiring in one place (composition root) rather than scattered.
- **REST over GraphQL:** chosen for simplicity and because the mini project's data access patterns are shallow (no deep nested graphs), so REST's simplicity outweighs GraphQL's flexibility benefits here.

---

## 9. Complete Folder Structure

### 9.1 Frontend (`/frontend`)

```
frontend/
├── public/
├── src/
│   ├── app/
│   │   ├── App.tsx                     # Root component, providers composition
│   │   ├── routes.tsx                  # Central route definitions (React Router)
│   │   └── providers/
│   │       ├── QueryProvider.tsx       # React Query client setup
│   │       └── AuthProvider.tsx        # Auth context (current user, token)
│   │
│   ├── features/                       # FEATURE-BASED structure (core requirement)
│   │   ├── auth/
│   │   │   ├── api/                    # Axios calls specific to auth
│   │   │   ├── components/             # LoginForm, RegisterForm
│   │   │   ├── hooks/                  # useLogin, useCurrentUser (React Query hooks)
│   │   │   ├── types/                  # AuthUser, LoginRequest, etc.
│   │   │   └── index.ts                # Public exports of this feature
│   │   │
│   │   ├── students/
│   │   │   ├── api/
│   │   │   ├── components/             # StudentProfileForm, StudentList, StudentCard
│   │   │   ├── hooks/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   ├── skills/
│   │   │   ├── api/
│   │   │   ├── components/             # SkillPicker, SkillBadgeList
│   │   │   ├── hooks/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   ├── resumes/
│   │   │   ├── api/
│   │   │   ├── components/             # ResumeUploader, ResumeVersionList
│   │   │   ├── hooks/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   ├── companies/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   ├── jobs/
│   │   │   ├── api/
│   │   │   ├── components/             # JobList, JobDetail, ApplyButton
│   │   │   ├── hooks/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   ├── dashboard/
│   │   │   ├── api/
│   │   │   ├── components/             # ChartCards (Recharts-based), Filters
│   │   │   ├── hooks/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   └── prediction/
│   │       ├── api/
│   │       ├── components/             # ScoreCard, FactorBreakdown
│   │       ├── hooks/
│   │       ├── types/
│   │       └── index.ts
│   │
│   ├── shared/                         # Cross-feature reusable code
│   │   ├── components/
│   │   │   ├── ui/                     # shadcn/ui generated components (button, card, dialog...)
│   │   │   └── layout/                 # AppShell, Sidebar, Navbar, ProtectedRoute
│   │   ├── hooks/                      # useDebounce, usePagination, etc.
│   │   ├── lib/
│   │   │   ├── axios.ts                # Axios instance, interceptors (JWT attach + refresh)
│   │   │   └── queryClient.ts
│   │   ├── types/                      # Global/shared TS types (ApiResponse<T>, Paginated<T>)
│   │   └── utils/                      # formatDate, cn(), validators
│   │
│   ├── config/
│   │   ├── env.ts                      # Typed access to Vite env vars
│   │   └── constants.ts
│   │
│   ├── styles/
│   │   └── globals.css                 # Tailwind base + custom tokens
│   │
│   ├── main.tsx
│   └── vite-env.d.ts
│
├── .env.example
├── index.html
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts
```

**Why feature-based, not type-based (no global `components/`, `pages/`, `hooks/` at root):** In a type-based structure, working on "Skills" means touching four different top-level folders. In a feature-based structure, everything related to Skills lives in one folder — easier to reason about, easier to delete/replace a whole feature (e.g., swapping the Prediction feature for an ML-backed version later), and it scales better as more modules are added in the final year.

The `shared/` folder is intentionally kept small and only holds things genuinely used by 2+ features, to prevent it from becoming a dumping ground.

### 9.2 Backend (`/backend`)

```
backend/
├── app/
│   ├── main.py                         # FastAPI app instantiation, middleware, router registration
│   │
│   ├── core/                           # Cross-cutting concerns
│   │   ├── config.py                   # Settings via pydantic-settings (.env driven)
│   │   ├── security.py                 # Password hashing, JWT encode/decode
│   │   ├── dependencies.py             # get_current_user, require_role(), get_db
│   │   ├── exceptions.py               # Domain exception classes + FastAPI exception handlers
│   │   └── logging.py
│   │
│   ├── db/
│   │   ├── base.py                     # Declarative Base, import hub for Alembic autogenerate
│   │   ├── session.py                  # Engine + SessionLocal factory
│   │   └── migrations/                 # Alembic env.py + versions/
│   │
│   ├── modules/                        # FEATURE-BASED, mirrors frontend features
│   │   ├── auth/
│   │   │   ├── router.py               # /api/auth/* endpoints (thin)
│   │   │   ├── schemas.py              # Pydantic request/response models
│   │   │   ├── service.py              # AuthService — business logic, framework-agnostic
│   │   │   ├── repository.py           # UserRepository — SQLAlchemy queries
│   │   │   ├── models.py               # User ORM model
│   │   │   └── interfaces.py           # Abstract repository interface (Protocol/ABC)
│   │   │
│   │   ├── students/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   └── interfaces.py
│   │   │
│   │   ├── skills/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   └── interfaces.py
│   │   │
│   │   ├── resumes/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   ├── storage.py              # File storage abstraction (local disk now, S3-ready later)
│   │   │   └── interfaces.py
│   │   │
│   │   ├── companies/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   └── interfaces.py
│   │   │
│   │   ├── jobs/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py               # Job, Application ORM models
│   │   │   └── interfaces.py
│   │   │
│   │   ├── dashboard/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   └── service.py              # Aggregation queries; read-only, no repository needed if simple
│   │   │
│   │   └── prediction/
│   │       ├── router.py
│   │       ├── schemas.py
│   │       ├── service.py              # Scoring engine, consumes other modules' service interfaces
│   │       └── interfaces.py           # Defines what data it needs from Student/Skills/Resume/Jobs
│   │
│   ├── shared/                         # Cross-module reusable backend code
│   │   ├── schemas.py                  # PaginatedResponse[T], ApiError, etc.
│   │   ├── pagination.py
│   │   └── enums.py                    # RoleEnum, ApplicationStatusEnum, ProficiencyEnum
│   │
│   └── tests/
│       ├── unit/                       # Service-layer tests with mocked repositories
│       └── integration/                # Router-level tests with test DB
│
├── alembic.ini
├── requirements.txt
├── .env.example
└── pyproject.toml
```

**Why `modules/` mirrors the frontend `features/`:** Keeping frontend and backend module names identical (auth, students, skills, resumes, companies, jobs, dashboard, prediction) means any developer — or the project viva panel — can trace a feature vertically from UI to database without a mental mapping table. This symmetry is a deliberate architectural choice, not a coincidence.

**Why `interfaces.py` per module:** Each module defines an abstract interface for its repository (and, for Prediction, for what it needs from *other* services). Concrete implementations depend on these abstractions (Dependency Inversion Principle) — this is what makes the "Clean Architecture" label accurate rather than just organizational.

---

## 10. Coding Standards

**Backend (Python/FastAPI):**
- Follow PEP 8; enforce via `black` (formatting) and `ruff` (linting) in pre-commit hooks.
- Every function/method has type hints; `mypy` run in CI for static type checking.
- No business logic in routers — routers only validate input, call a service method, and return output.
- Services never import `fastapi`; they raise domain-specific exceptions (e.g., `StudentNotFoundError`), which a centralized exception handler in `core/exceptions.py` maps to HTTP status codes. This keeps HTTP concerns out of business logic entirely.
- All DB access goes through a repository; no raw SQLAlchemy queries inside services or routers.
- Pydantic schemas separate `Create`, `Update`, and `Read`/`Response` models per entity — never reuse one schema for all operations, since input and output shapes legitimately differ (e.g., `Read` includes `id`/timestamps, `Create` doesn't).
- Environment configuration only via `pydantic-settings`, never hardcoded values or scattered `os.getenv()` calls.

**Frontend (React/TypeScript):**
- Strict TypeScript mode enabled (`strict: true` in tsconfig) — no `any` except in tightly justified, commented cases.
- Functional components only, with Hooks; no class components.
- Server state (data from the API) is managed exclusively through React Query; component-local UI state (form inputs, toggles) through `useState`/`useReducer`. This separation avoids the common anti-pattern of duplicating server data into local state.
- All API calls go through a typed Axios client + feature-specific `api/` functions — components never call `axios` directly.
- Every feature exposes a single `index.ts` as its public interface; other features must import only from that barrel file, never reach into a feature's internal folders. This enforces module boundaries at the TypeScript/import level, mirroring the backend's Clean Architecture boundaries.
- ESLint (with `typescript-eslint`) + Prettier enforced via pre-commit and CI.

**General:**
- Every module ships with at least basic unit tests for its service layer before being considered "done" — enforced as a Definition of Done for the mini project, not left implicit.
- No commented-out dead code committed; use Git history instead.

---

## 11. Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Python files/modules | `snake_case` | `student_service.py` |
| Python classes | `PascalCase` | `StudentService`, `StudentRepository` |
| Python functions/variables | `snake_case` | `get_student_by_id()` |
| SQLAlchemy models | Singular noun, `PascalCase` | `Student`, `JobApplication` |
| Database tables | Plural, `snake_case` (via `__tablename__`) | `students`, `job_applications` |
| Pydantic schemas | `PascalCase` + suffix by purpose | `StudentCreate`, `StudentUpdate`, `StudentRead` |
| FastAPI route paths | Plural, kebab/lowercase, versioned | `/api/v1/students`, `/api/v1/job-applications` |
| React components | `PascalCase`, one component per file matching filename | `StudentProfileForm.tsx` |
| React hooks | `camelCase`, prefixed `use` | `useStudentProfile.ts` |
| TypeScript types/interfaces | `PascalCase`, no Hungarian `I` prefix | `Student`, `JobListing` (not `IStudent`) |
| TS files (non-component) | `camelCase` | `axiosClient.ts`, `formatDate.ts` |
| CSS/Tailwind custom tokens | `kebab-case` | `--color-brand-primary` |
| Environment variables | `UPPER_SNAKE_CASE` | `DATABASE_URL`, `JWT_SECRET_KEY` |
| Git branches | See Section 12 | — |

**Rationale:** Consistent, predictable naming means anyone (teammate, evaluator, future-year student extending this project) can guess a file's location and purpose without searching. The `Create/Update/Read` schema suffix convention specifically prevents the common mistake of one bloated schema serving all CRUD operations, which tends to leak internal fields (like password hashes) into API responses.

---

## 12. Git Branch Strategy

A simplified **GitHub Flow** variant is used — full Git Flow (with `release/` and `hotfix/` branches) is unnecessary overhead for a mini project team, but a plain single-branch model would make evaluation of individual module work impossible.

```
main                      # Always deployable/demo-ready; protected branch
 └── develop               # Integration branch; all feature branches merge here first
      ├── feature/auth-module
      ├── feature/student-management
      ├── feature/skills-management
      ├── feature/resume-management
      ├── feature/company-management
      ├── feature/job-listings
      ├── feature/placement-dashboard
      ├── feature/placement-prediction
      ├── feature/admin-dashboard
      ├── fix/<short-description>
      └── chore/<short-description>       # tooling, config, non-feature work
```

**Rules:**
- Branch naming: `feature/<module-name>`, `fix/<bug-description>`, `chore/<task>` — all lowercase, hyphen-separated.
- No direct commits to `main` or `develop`; all changes via Pull Request.
- PRs require at least a self-review checklist (tests pass, lint clean, no console logs / print debugging left in).
- `main` is merged into only from `develop`, at milestone checkpoints (e.g., after each module review), so it always reflects a demoable state — important given periodic faculty/guide reviews.
- Commit messages follow **Conventional Commits** (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`) to keep history readable and to make it trivial to generate a changelog for the final report.

---

## 13. Future Scope (Final Year Expansion)

The current architecture is deliberately shaped so the following extensions require **addition, not rewriting**:

1. **Real AI-based Placement Prediction** — replace the rule-based scoring in the `prediction` module's service with a trained ML model (e.g., logistic regression / gradient boosting on historical placement outcomes), served either in-process or via a separate microservice. Because the Prediction module already consumes other modules through interfaces rather than direct DB access, this swap is isolated to one module.
2. **Resume Parsing & NLP Matching** — extend the `resumes` module with an NLP pipeline (spaCy/transformer-based) to auto-extract skills from uploaded resumes and auto-suggest job matches, feeding structured data into the existing `skills` module rather than bypassing it.
3. **Recommendation Engine** — a new `recommendations` module suggesting jobs to students or candidates to admins based on skill-vector similarity, layered on top of existing Skills/Jobs data.
4. **Notification System** — a new module for email/SMS/push notifications on application status changes, deadlines, and interview schedules — cleanly addable as a new feature folder on both frontend and backend without touching existing modules.
5. **Interview Scheduling Module** — calendar-based scheduling between companies and shortlisted students.
6. **Recruiter Role & Portal** — since roles are already an extensible enum, adding a `Recruiter` role who can log in and view/manage applications for their own company's job postings is a low-friction extension.
7. **Microservice Extraction** — if load grows, the Prediction module (likely the most compute-heavy, especially once ML-based) is the natural first candidate to extract into its own service, since its interface boundary is already enforced.
8. **Analytics Expansion** — richer dashboards (predictive trends year-over-year, department benchmarking) building on the existing Dashboard module's aggregation patterns.
9. **Containerization & CI/CD** — Docker Compose for local dev (already implied by the `.env`-driven config), and a CI pipeline (GitHub Actions) running lint/type-check/tests on every PR — natural extension of the coding standards already in place.

The guiding principle behind every decision in this document — feature-based structure, Clean Architecture, Repository Pattern, interface-driven module boundaries — is to make sure the final-year project is an **extension of Career Compass AI**, not a restart.

---

*End of Day 1 Design Document.*
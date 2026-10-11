# System Architecture & Component Verification

**Project:** Career Compass AI: Smart Placement Analytics & Career Intelligence Platform  
**Component Scope:** Frontend, Backend, Database, Storage, and Security Boundaries  
**Document Status:** Source-Verified from Repository Code  

---

## 1. High-Level System Architecture

Career Compass AI follows a **decoupled, multi-tier client-server architecture** designed around clean boundaries, explicit dependency injection, and asynchronous I/O.

```mermaid
graph TB
    subgraph Client Tier ["Client Tier (Browser)"]
        UI["React 18 SPA (Vite + TypeScript)"]
        Router["React Router v7 (Role-Gated Routes)"]
        State["Auth Context & Local State"]
        AxiosClient["Axios HTTP Client + Interceptor"]
        UI --> Router
        Router --> State
        State --> AxiosClient
    end

    subgraph Gateway Tier ["API Gateway & Middleware"]
        FastAPIApp["FastAPI 0.115 Application"]
        CORS["CORS Middleware"]
        ErrHandlers["Global Exception Handlers"]
        FastAPIApp --> CORS
        FastAPIApp --> ErrHandlers
    end

    subgraph Service Tier ["Service & Domain Logic Tier"]
        AuthModule["Auth & Security (JWT / Bcrypt)"]
        StudentModule["Student Profile & Department"]
        SkillsModule["Skills Catalog & Inventory"]
        JobsModule["Job Posting & Workflow Template"]
        AppsModule["Applications & Round Snapshot Engine"]
        PlacementsModule["Placement Records & Decision"]
        AnalyticsModule["Descriptive Analytics Aggregator"]
        IntelModule["Placement Readiness Engine"]
    end

    subgraph Data Tier ["Persistence & Storage Tier"]
        AsyncEngine["SQLAlchemy 2.0 Async Engine (asyncpg)"]
        PostgresDB[("PostgreSQL 14+ Relational Database")]
        FileStorage[("Local Filesystem (uploads/resumes/)")]
    end

    AxiosClient -->|"HTTP / REST (Bearer JWT)"| FastAPIApp
    FastAPIApp --> AuthModule
    FastAPIApp --> StudentModule
    FastAPIApp --> SkillsModule
    FastAPIApp --> JobsModule
    FastAPIApp --> AppsModule
    FastAPIApp --> PlacementsModule
    FastAPIApp --> AnalyticsModule
    FastAPIApp --> IntelModule

    AuthModule --> AsyncEngine
    StudentModule --> AsyncEngine
    SkillsModule --> AsyncEngine
    JobsModule --> AsyncEngine
    AppsModule --> AsyncEngine
    PlacementsModule --> AsyncEngine
    AnalyticsModule --> AsyncEngine
    IntelModule --> AsyncEngine
    AppsModule --> FileStorage

    AsyncEngine --> PostgresDB
```

---

## 2. Backend Layered Architecture (Clean Architecture)

The backend follows the **Repository Pattern and Service Layer pattern** across all 13 feature modules. Each module maintains strict isolation between transport concerns, business logic, and database access.

```mermaid
graph TD
    subgraph Transport ["1. Transport Layer (Router)"]
        R["FastAPI APIRouter (/api/v1/*)"]
        Dep["FastAPI Dependency Injection (Depends)"]
        R --> Dep
    end

    subgraph Business ["2. Service Layer (Business Logic)"]
        S["Module Service (e.g., ApplicationService)"]
        Tx["Transaction Boundary (commit / rollback)"]
        AppEx["AppException Hierarchy (Domain Errors)"]
        S --> Tx
        S --> AppEx
    end

    subgraph DataAccess ["3. Data Access Layer (Repository)"]
        Repo["Module Repository (e.g., ApplicationRepository)"]
        SQLAlchemyStmt["SQLAlchemy select() / insert() / update()"]
        Repo --> SQLAlchemyStmt
    end

    subgraph Models ["4. Domain & Persistence Models"]
        ORM["SQLAlchemy Declarative Models (Base)"]
        Pydantic["Pydantic v2 Schemas (Request / Response)"]
    end

    R -->|"Accepts Pydantic DTO"| S
    S -->|"Queries & Modifies"| Repo
    Repo -->|"Maps ORM Objects"| ORM
    S -->|"Returns Pydantic DTO"| R
```

### Layer Responsibilities & Rules
1. **Routers (`router.py`):**
   - Parse HTTP requests, path parameters, query parameters, and JSON payloads.
   - Inject dependencies (`CurrentUser`, `RequireStaff`, `RequireStudent`, `DBSession`).
   - Call the service layer; routers **never** write directly to the database or call `commit()`.
2. **Services (`service.py`):**
   - Contain business rules, eligibility validations, and snapshot creation logic.
   - Own transaction boundaries: services invoke `await session.commit()` or `await session.rollback()`.
   - Raise custom exceptions subclassing `AppException` (e.g., `NotFoundError`, `BadRequestError`, `ConflictError`, `ForbiddenError`), never raw `HTTPException`.
3. **Repositories (`repository.py`):**
   - Encapsulate all database queries using SQLAlchemy `select()`, joins, and filters.
   - Do not call `commit()`; repositories perform queries and return ORM objects or scalars.
4. **Error Handling (`app/core/error_handlers.py`):**
   - Global exception handlers catch domain `AppException` subclasses and translate them into standardized JSON error responses with appropriate HTTP status codes (400, 401, 403, 404, 409, 500).

---

## 3. Frontend Architecture & State Management

The frontend is a single-page application built on **React 18** and bundled with **Vite 5**.

```mermaid
graph LR
    subgraph Routing ["Routing Architecture"]
        BRouter["BrowserRouter"]
        AppRoutes["AppRoutes"]
        PR["ProtectedRoute"]
        BRouter --> AppRoutes
        AppRoutes --> PR
    end

    subgraph AuthLayer ["Authentication Context"]
        AuthProvider["AuthProvider (AuthContext)"]
        TokenUtil["Token Storage (localStorage: access_token)"]
        AuthProvider --> TokenUtil
    end

    subgraph RolePages ["Role-Based Page Modules"]
        PR -->|"role: student"| StudentPages["Student Pages (Dashboard, Readiness, Profile, Jobs, Apps)"]
        PR -->|"role: staff"| StaffPages["Staff Pages (Dashboard, Jobs Wizard, Applications, Placements)"]
    end

    subgraph Network ["API Client"]
        Axios["Axios Instance (api/axios.ts)"]
        ReqInterceptor["Request Interceptor (Attach Bearer Token)"]
        RespInterceptor["Response Interceptor (401 Redirect to /login)"]
        Axios --> ReqInterceptor
        Axios --> RespInterceptor
    end

    StudentPages --> Axios
    StaffPages --> Axios
```

### Route Protection Flow
1. User logs in at `/login` via `authService.login()`.
2. Access token is saved to `localStorage` under key `access_token`.
3. `AuthProvider` mounts, fetches `/api/v1/auth/me`, and populates `user` state.
4. `ProtectedRoute` checks:
   - If `loading`, displays full-screen loading spinner.
   - If not authenticated, redirects to `/login`.
   - If `user.role` does not match `allowedRoles`, redirects to user's assigned dashboard (`/student/dashboard` or `/staff/dashboard`).

---

## 4. End-to-End Recruitment Workflow Sequence

The recruitment cycle integrates job posting, template definition, candidate snapshotting, attendance self-reporting, staff verification, and placement creation.

```mermaid
sequenceDiagram
    autonumber
    actor Staff as Placement Staff
    actor Student as Student Candidate
    participant API as FastAPI Backend
    participant Snap as Snapshot Engine
    participant DB as PostgreSQL Database

    Note over Staff,DB: 1. Job Creation & Round Template Setup
    Staff->>API: POST /api/v1/staff/jobs (Job Details, Min CGPA, Eligible Depts)
    API->>DB: INSERT into jobs
    Staff->>API: POST /api/v1/staff/jobs/{id}/rounds (Round 1: Aptitude Test)
    API->>DB: INSERT into job_rounds (Template)
    Staff->>API: POST /api/v1/staff/jobs/{id}/rounds (Round 2: Technical Interview)
    API->>DB: INSERT into job_rounds (Template)

    Note over Student,DB: 2. Job Discovery & Eligibility Check
    Student->>API: GET /api/v1/student/jobs
    API->>DB: SELECT active jobs + check student CGPA & Department
    API-->>Student: Return jobs with eligibility flags

    Note over Student,DB: 3. Application Submission & Round Snapshotting
    Student->>API: POST /api/v1/student/applications (job_id, resume_id)
    API->>DB: Verify active status, deadline, department & CGPA eligibility
    API->>Snap: Clone all active JobRound templates
    Snap->>DB: INSERT into applications (status = 'Interview')
    Snap->>DB: INSERT into application_rounds (Snapshot copies with job_round_id FK)
    API-->>Student: 201 Created (Application + Snapshotted Rounds)

    Note over Staff,DB: 4. Round Execution & Attendance Reporting
    Staff->>API: PATCH /api/v1/staff/applications/{id}/rounds/{r_id} (Set available_from)
    Student->>API: POST /api/v1/student/applications/{id}/rounds/{r_id}/attendance (ATTENDED)
    API->>DB: UPDATE student_attendance = 'ATTENDED', staff_verification = 'PENDING'
    Staff->>API: PATCH /api/v1/staff/applications/{id}/rounds/{r_id}/verification (VERIFIED)
    API->>DB: UPDATE staff_verification = 'VERIFIED'
    Staff->>API: PATCH /api/v1/staff/applications/{id}/rounds/{r_id}/result (Passed)
    API->>DB: UPDATE result = 'Passed'

    Note over Staff,Student: 5. Job Round Template Deletion (Snapshot Isolation Proof)
    Staff->>API: DELETE /api/v1/staff/jobs/{id}/rounds/{r_id}
    API->>DB: DELETE FROM job_rounds (Parent Template)
    DB-->>DB: ON DELETE SET NULL triggers: ApplicationRound.job_round_id = NULL
    Note over DB: Candidate's ApplicationRound preserves all round data intact!

    Note over Staff,DB: 6. Placement Issuance & Acceptance
    Staff->>API: POST /api/v1/staff/placements (student_id, job_id, package_lpa)
    API->>DB: INSERT into placements (status = 'Offered')
    Student->>API: PATCH /api/v1/student/placements/{id}/respond (status = 'Accepted')
    API->>DB: UPDATE placements SET status = 'Accepted'
    API-->>Student: 200 OK (Offer Accepted)
```

---

## 5. Placement Readiness Scoring Pipeline Flowchart

The scoring engine executes a deterministic arithmetic pipeline calculating weighted readiness pillars without machine learning dependencies.

```mermaid
flowchart TD
    Start([Student Requests /student/intelligence/readiness]) --> FetchData[Fetch Student Profile, Active Skills, Resumes, and Active Jobs]
    
    subgraph Pillar1 ["Pillar 1: Academic Readiness (25 Pts)"]
        CGPA{"CGPA Present?"}
        CGPA -->|Yes| CGPACalc["CGPA Score = min(20.0, (CGPA / 10.0) * 20.0)"]
        CGPA -->|No| CGPAZero["CGPA Score = 0.0"]
        Dept{"Dept Assigned?"}
        Dept -->|Yes| DeptScore["Dept Score = 5.0"]
        Dept -->|No| DeptZero["Dept Score = 0.0"]
        CGPACalc & CGPAZero & DeptScore & DeptZero --> AcadTotal["Academic Total = round(CGPA Score + Dept Score, 1)"]
    end

    subgraph Pillar2 ["Pillar 2: Skill Profile (35 Pts)"]
        SkillQty["Quantity = min(Active Skills / 5.0, 1.0) * 15.0"]
        SkillQual["Proficiency Weights: Beginner=0.4, Intermediate=0.7, Advanced=1.0<br/>Quality = Average(Weights) * 20.0"]
        SkillQty & SkillQual --> SkillTotal["Skill Total = round(Quantity + Quality, 1)"]
    end

    subgraph Pillar3 ["Pillar 3: Profile & Resume (20 Pts)"]
        FieldCheck["Count 6 Optional Fields (Phone, DOB, Address, LinkedIn, GitHub, GradYear)<br/>Profile Score = (Count / 6.0) * 10.0"]
        ResumeCheck{"Default Resume Uploaded?"}
        ResumeCheck -->|Yes| ResScore["Resume Score = 10.0"]
        ResumeCheck -->|No| ResZero["Resume Score = 0.0"]
        FieldCheck & ResScore & ResZero --> ProfResTotal["Profile & Resume Total = round(Profile Score + Resume Score, 1)"]
    end

    subgraph Pillar4 ["Pillar 4: Market Eligibility (20 Pts)"]
        JobCheck{"Active Jobs Exist?"}
        JobCheck -->|Yes| MatchJobs["Calculate Eligible Jobs / Total Active Jobs * 20.0"]
        JobCheck -->|No| MarketZero["Market Score = 0.0"]
        MatchJobs & MarketZero --> MarketTotal["Market Total = round(Score, 1)"]
    end

    AcadTotal & SkillTotal & ProfResTotal & MarketTotal --> SumTotal["Raw Total = Sum of 4 Pillars (Clamped 0.0 - 100.0)"]

    subgraph Categorization ["Readiness Status Categorization"]
        SumTotal --> CatCheck{"Score Range"}
        CatCheck -->|< 40.0| NeedsImp["'Needs Improvement'"]
        CatCheck -->|40.0 - 59.9| Dev["'Developing'"]
        CatCheck -->|60.0 - 79.9| Good["'Good'"]
        CatCheck -->|>= 80.0| Strong["'Strong'"]
    end

    subgraph Recommendations ["Heuristic Recommendation Selector"]
        NeedsImp & Dev & Good & Strong --> Heuristics["Evaluate Missing Pillars<br/>(Resume missing? Skills < 5? CGPA missing? Dept missing?)<br/>Deduplicate & pick top 3"]
    end

    Recommendations --> Response([Return ReadinessResponse DTO])
```

---

## 6. Security & Authentication Architecture

1. **Password Hashing:**
   - Implemented in [app/core/security.py](file:///d:/Project%20X/CareerCompassAI/backend/app/core/security.py) using `bcrypt` (version 4.2.1) with automatically generated random salts.
   - Plaintext passwords are never logged or stored.
2. **Stateless JWT Tokens:**
   - Implemented in [app/core/jwt.py](file:///d:/Project%20X/CareerCompassAI/backend/app/core/jwt.py) using `PyJWT` (version 2.10.1).
   - Algorithm: `HS256`. Default token expiry: 60 minutes (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`).
   - Payload contains `sub` (user email string) and `role` (`student` or `staff`).
3. **Role-Based Dependency Injection:**
   - [app/api/deps.py](file:///d:/Project%20X/CareerCompassAI/backend/app/api/deps.py) provides reusable FastAPI dependency guards:
     - `CurrentUser`: Validates token and returns active database `User` instance.
     - `RequireStudent`: Gated by `require_role(RoleEnum.STUDENT)`.
     - `RequireStaff`: Gated by `require_role(RoleEnum.STAFF)`.

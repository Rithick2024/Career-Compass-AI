# Career Compass AI — Technical Evidence Report

**Project Title:** Career Compass AI: Smart Placement Analytics & Career Intelligence Platform  
**Academic Context:** SRM Institute of Science and Technology — Master of Computer Applications (MCA) Individual Mini Project  
**Audit Date:** 2026-10-11  
**Audit Status:** Source-Verified & Empirically Validated  

---

## 1. Executive Summary

This document provides a factual, source-verified technical evidence pack for the **Career Compass AI** project. All findings are derived directly from static source analysis, schema validation, and real test/build executions inside the active repository. No synthetic data, unverified metrics, or hypothetical components have been included.

### Key Audit Findings
1. **Core Platform Architecture:** The application is a fully integrated, modern full-stack web application featuring a **FastAPI** (Python 3.13) asynchronous backend and a **React 18 / TypeScript / Vite** frontend styled with **Tailwind CSS** and **Radix UI** primitives.
2. **Database & Schema:** Relational storage is powered by **PostgreSQL** using **SQLAlchemy 2.0 (async)** and tracked through **17 sequential Alembic migrations**. The primary key strategy across all entities uses integer auto-incrementing serials (`Integer`), a deliberate architecture decision documented from initial design.
3. **Recruitment Workflow & Snapshot Isolation:** The system implements a robust two-tier recruitment pipeline separating job template definitions (`JobRound`) from candidate application records (`ApplicationRound`). Upon candidate application, active rounds are snapshotted into `application_rounds`. The foreign key constraint `ApplicationRound.job_round_id` utilizes `ON DELETE SET NULL`, ensuring candidate progression history is permanently isolated from subsequent template modifications or deletions.
4. **Placement Readiness & Intelligence:** The analytical "Placement Readiness Score" (0–100) and "Skill Gap Analysis" are implemented as **deterministic, rule-based algorithmic scoring engines** with four weighted pillars (Academic Readiness: 25%, Skill Profile: 35%, Profile & Resume: 20%, Market Eligibility: 20%).
5. **Machine Learning Reality Check:** There is **no trained machine learning model, statistical inference pipeline, serialized model artifact (`.pkl`, `.joblib`, `.onnx`), or training dataset** in the repository. Predictive placement modelling, automated NLP resume parsing, and AI chatbots are strictly future/final-year scope.
6. **Empirical Test Verification:**
   - **Backend Test Suite:** **114 out of 114 tests passed** (100% pass rate) in **91.48s** against an isolated PostgreSQL test database (`career_compass_test`), surpassing the earlier milestone count of 85 tests.
   - **Frontend Type Checking:** `tsc --noEmit` passed with **0 errors**.
   - **Frontend Production Build:** Vite v5.4.8 transformed 2,926 modules and compiled a production bundle in **9.44s**.
   - **Frontend ESLint:** Reported 28 errors and 10 warnings solely related to unused variable declarations and explicit `any` types; application logic remains functional.

---

## 2. Project Identity & Runtime Inventory

### 2.1 Directory Structure & Module Responsibilities

```
CareerCompassAI/
├── backend/
│   ├── alembic/              # Alembic async migration environment (17 migration versions)
│   ├── app/
│   │   ├── api/              # API router aggregator (v1) and shared dependencies (deps.py)
│   │   ├── core/             # Configuration, logging, exception hierarchy, JWT, security
│   │   ├── db/               # Async engine, declarative Base, and session factories
│   │   ├── modules/          # 13 domain feature modules (Clean Architecture)
│   │   │   ├── analytics/            # Staff & student placement dashboard aggregations
│   │   │   ├── application_rounds/   # Per-candidate round lifecycle, attendance, verification
│   │   │   ├── applications/         # Job applications, eligibility gating, duplicate checks
│   │   │   ├── auth/                 # User authentication, registration, JWT issuance
│   │   │   ├── companies/            # Company catalog and profile management
│   │   │   ├── intelligence/         # 4-pillar readiness engine, skill gap, job match
│   │   │   ├── job_rounds/           # Job recruitment round templates/workflow definitions
│   │   │   ├── jobs/                 # Job postings, department & skill criteria
│   │   │   ├── placements/           # Offer tracking, acceptance/decline workflow
│   │   │   ├── resumes/              # Resume metadata & local file upload (PDF/DOC/DOCX)
│   │   │   ├── skills/               # Skill catalog & student skill proficiency tracking
│   │   │   ├── staff_students/       # Staff-facing student directory & profile review
│   │   │   └── students/             # Student profile CRUD & department associations
│   │   └── shared/           # Common enumeration definitions (RoleEnum, ProficiencyLevel)
│   ├── docs/                 # Technical documentation for auth, resume, skills, student
│   ├── scripts/              # Administrative utility scripts (create_staff_user.py)
│   ├── tests/                # 16 pytest test suites covering all modules (114 tests)
│   ├── uploads/resumes/      # Local filesystem resume storage directory
│   ├── requirements.txt      # Production Python dependencies
│   ├── requirements-dev.txt  # Development and test dependencies
│   └── pyproject.toml        # Black, isort, and pytest configuration
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios HTTP client with JWT interceptor and error handler
│   │   ├── components/       # Common UI elements, layouts, and Radix UI primitives
│   │   ├── features/
│   │   │   ├── analytics/    # Analytics API services and TypeScript interfaces
│   │   │   ├── auth/         # Login, Register, AuthContext, ProtectedRoute
│   │   │   ├── staff/        # Staff pages (Dashboard, Jobs Wizard, Applications, Placements)
│   │   │   └── student/      # Student pages (Dashboard, Readiness, Jobs, Applications)
│   │   ├── hooks/            # Custom React hooks (useToast, etc.)
│   │   ├── lib/              # Utility helpers (cn class merger)
│   │   ├── App.tsx           # Route tree with role-based route gating
│   │   ├── main.tsx          # React application root mount
│   │   └── index.css         # Tailwind CSS styling and theme custom properties
│   ├── package.json          # Frontend dependencies and npm scripts
│   ├── tsconfig.json         # TypeScript configuration
│   └── vite.config.ts        # Vite build tool configuration
└── docs/                     # Project report evidence documentation
```

### 2.2 Technology Stack & Exact Versions

| Component | Technology | Manifest / Lockfile Version | Active Runtime Version |
|---|---|---|---|
| **Backend Framework** | FastAPI | `0.115.6` (`requirements.txt`) | `0.115.6` |
| **ASGI Server** | Uvicorn | `0.34.0` (`requirements.txt`) | `0.34.0` |
| **Backend Runtime** | Python | `>=3.11` (`pyproject.toml`) | `3.13.14` |
| **Database ORM** | SQLAlchemy | `2.0.36` (`requirements.txt`) | `2.0.36` (asyncio) |
| **Database Driver** | asyncpg | `0.30.0` (`requirements.txt`) | `0.30.0` |
| **Schema Migrations** | Alembic | `1.14.0` (`requirements.txt`) | `1.14.0` |
| **Data Validation** | Pydantic v2 | `2.10.4` (`requirements.txt`) | `2.10.4` |
| **Settings Parsing** | pydantic-settings | `2.7.1` (`requirements.txt`) | `2.7.1` |
| **Password Hashing** | bcrypt | `4.2.1` (`requirements.txt`) | `4.2.1` |
| **Token Handling** | PyJWT | `2.10.1` (`requirements.txt`) | `2.10.1` (HS256) |
| **HTTP Test Client** | HTTPX | `0.28.1` (`requirements-dev.txt`)| `0.28.1` |
| **Backend Test Runner**| pytest | `8.3.4` (`requirements-dev.txt`)| `9.1.1` (in active venv) |
| **Async Test Plugin** | pytest-asyncio | `0.25.2` (`requirements-dev.txt`)| `1.4.0` (in active venv) |
| **Frontend Framework**| React | `^18.3.1` (`package.json`) | `18.3.1` |
| **Frontend Runtime**  | Node.js / Browser | Standard ES Modules | Active Node.js |
| **Build Tool & Bundler**| Vite | `^5.4.8` (`package.json`) | `5.4.8` |
| **Type System**       | TypeScript | `^5.5.3` (`package.json`) | `5.5.3` |
| **Routing**           | React Router DOM | `^7.18.2` (`package.json`) | `7.18.2` |
| **Styling**           | Tailwind CSS | `^3.4.13` (`package.json`) | `3.4.13` |
| **UI Components**     | Radix UI primitives | Multiple (`^1.1.0` - `^2.1.1`)| Radix UI / shadcn style |
| **Data Visualization**| Recharts | `^2.12.7` (`package.json`) | `2.12.7` |
| **HTTP Client**       | Axios | `^1.19.0` (`package.json`) | `1.19.0` |
| **Form Handling**     | React Hook Form + Zod | `^7.53.0` / `^3.23.8` | RHF 7.53.0 / Zod 3.23.8 |

---

## 3. Placement Readiness Engine Formulation

The platform's analytical cornerstone is the **Placement Readiness Engine**, located in [service.py](file:///d:/Project%20X/CareerCompassAI/backend/app/modules/intelligence/service.py). It evaluates a student across four objective pillars, generating a transparent score from 0.0 to 100.0 without black-box ML inference.

### 3.1 Mathematical Formulation of the Four Pillars

$$\text{Readiness Score} = \min\left(100.0, \, S_{\text{academic}} + S_{\text{skills}} + S_{\text{profile\_resume}} + S_{\text{market}}\right)$$

#### 1. Academic Readiness Pillar ($S_{\text{academic}}$, Max: 25.0 points)
$$\text{CGPA Component} = \max\left(0.0, \, \min\left(20.0, \, \frac{\text{CGPA}}{10.0} \times 20.0\right)\right)$$
$$\text{Department Component} = \begin{cases} 5.0 & \text{if department is assigned} \\ 0.0 & \text{otherwise} \end{cases}$$
$$S_{\text{academic}} = \text{round}(\text{CGPA Component} + \text{Department Component}, 1)$$

#### 2. Skill Profile Pillar ($S_{\text{skills}}$, Max: 35.0 points)
- **Quantity Score (15.0 points max):**
  $$\text{Quantity} = \min\left(\frac{N_{\text{active\_skills}}}{5.0}, \, 1.0\right) \times 15.0$$
- **Quality / Proficiency Score (20.0 points max):**
  Each skill is weighted by proficiency:
  $$\text{Weight}(p) = \begin{cases} 1.0 & \text{if Advanced} \\ 0.7 & \text{if Intermediate} \\ 0.4 & \text{if Beginner} \end{cases}$$
  $$\text{Proficiency Factor} = \frac{1}{N_{\text{active\_skills}}} \sum_{i=1}^{N_{\text{active\_skills}}} \text{Weight}(p_i)$$
  $$\text{Quality} = \text{Proficiency Factor} \times 20.0$$
$$S_{\text{skills}} = \text{round}(\text{Quantity} + \text{Quality}, 1)$$

#### 3. Profile & Resume Pillar ($S_{\text{profile\_resume}}$, Max: 20.0 points)
- **Profile Completeness (10.0 points max):** Evaluates 6 optional student attributes (phone, date of birth, address, LinkedIn URL, GitHub URL, graduation year):
  $$\text{Profile Score} = \left(\frac{N_{\text{completed\_fields}}}{6.0}\right) \times 10.0$$
- **Default Resume Presence (10.0 points max):**
  $$\text{Resume Score} = \begin{cases} 10.0 & \text{if default resume exists} \\ 0.0 & \text{otherwise} \end{cases}$$
$$S_{\text{profile\_resume}} = \text{round}(\text{Profile Score} + \text{Resume Score}, 1)$$

#### 4. Market Eligibility Pillar ($S_{\text{market}}$, Max: 20.0 points)
Evaluates alignment against all currently active, visible jobs ($J_{\text{active}}$):
$$\text{Eligible Jobs } (J_{\text{eligible}}) = \{ j \in J_{\text{active}} \mid \text{CGPA} \ge j.\text{min\_cgpa} \land (\text{dept} \in j.\text{eligible\_depts} \lor j.\text{eligible\_depts} = \emptyset) \}$$
$$S_{\text{market}} = \text{round}\left(\frac{|J_{\text{eligible}}|}{|J_{\text{active}}|} \times 20.0, 1\right) \quad (\text{if } |J_{\text{active}}| = 0, \, S_{\text{market}} = 0.0)$$

### 3.2 Readiness Categorization Thresholds

| Score Range | Status Category | Academic Meaning |
|---|---|---|
| **0.0 – 39.9** | `Needs Improvement` | Foundational data missing (no resume, low skills, or missing CGPA) |
| **40.0 – 59.9** | `Developing` | Profile partially filled; baseline technical skills present |
| **60.0 – 79.9** | `Good` | Strong candidate ready for campus drives with minor gaps |
| **80.0 – 100.0** | `Strong` | Full profile, default resume uploaded, $\ge 5$ advanced skills, high market alignment |

### 3.3 Actionable Recommendation Heuristics
The engine executes deterministic checks and returns up to 3 prioritized recommendations:
1. `Upload a default resume.` (Triggered if default resume missing)
2. `Add X more active skills to reach the platform readiness baseline of 5 skills.` (Triggered if active skills < 5)
3. `Add your CGPA to evaluate academic eligibility.` (Triggered if CGPA is null)
4. `Select your department to evaluate job eligibility.` (Triggered if department is null)
5. `Complete missing profile details (such as LinkedIn URL or GitHub URL).` (Triggered if optional fields < 6)
6. `Improve your eligibility for more active jobs by reviewing their CGPA and department requirements.` (Triggered if market eligibility < 50%)

---

## 4. Recruitment Workflow & Snapshot Isolation

### 4.1 JobRound vs ApplicationRound Architecture

A critical feature of the system is the separation between recruitment workflow templates and candidate application execution records:

```
[Staff Job Creation]
        │
        ▼
   JobRound (Template)
   ├── id, job_id, round_number
   ├── round_type, title, schedule_type
   ├── available_from, available_until, duration_minutes
   └── meeting_link, test_link, instructions
        │
        │ Candidate applies to job
        ▼ (Deep Snapshot Copy)
ApplicationRound (Candidate Instance)
   ├── id, application_id, round_number
   ├── round_type, title, schedule_type
   ├── available_from, available_until, duration_minutes
   ├── meeting_link, test_link, instructions
   ├── student_attendance: NOT_REPORTED | ATTENDED | ABSENT
   ├── staff_verification: PENDING | VERIFIED | REJECTED
   ├── result: PENDING | PASSED | FAILED | NOT_ATTENDED
   └── job_round_id ───(FK with ON DELETE SET NULL)───► JobRound.id
```

### 4.2 Verified Snapshot Properties
1. **Template Gating:** When an application is created, `ApplicationRound` records are created for each active `JobRound` belonging to the job.
2. **Initial Status Determination:** If active rounds exist, the initial application status is set to `Interview`; if no rounds exist, it defaults to `Pending`.
3. **Data Immutability:** Candidate rounds retain their copied instructions, meeting links, schedule dates, and titles even if staff later edits or deletes the parent `JobRound`.
4. **Foreign Key Safety:** `ApplicationRound.job_round_id` has foreign key constraint `ondelete="SET NULL"`. Verified in [test_job_rounds.py](file:///d:/Project%20X/CareerCompassAI/backend/tests/test_job_rounds.py#L300-L360): deleting a `JobRound` sets `job_round_id` to `NULL` on the candidate's round without removing or mutating the round itself.
5. **Two-Party Round Progression:**
   - **Student action:** Candidate marks attendance (`ATTENDED` or `ABSENT`).
   - **Staff verification:** Staff verifies or rejects reported attendance (`VERIFIED` or `REJECTED`).
   - **Staff outcome:** Staff marks result (`Passed` or `Failed`).
   - **Rescheduling:** Staff can reschedule a round, which resets attendance to `NOT_REPORTED`, verification to `PENDING`, and result to `Pending`.

---

## 5. Machine Learning Reality Check

In accordance with strict safety constraints, the repository was audited for data science and AI artifacts.

| Claimed Feature | Actual Repository State | Implementation Evidence | Report Classification |
|---|---|---|---|
| **Descriptive Placement Analytics** | **Fully Implemented** | SQL aggregate queries in `AnalyticsRepository` returning counts, rates, and distributions | **Implemented** |
| **Job Eligibility Checking** | **Fully Implemented** | Deterministic SQL joins verifying department, CGPA, and job status in `applications/service.py` | **Implemented** |
| **Placement Readiness Scoring** | **Fully Implemented** | 100-point 4-pillar deterministic arithmetic algorithm in `intelligence/service.py` | **Implemented (Rule-Based)** |
| **Market Skill Gap Analysis** | **Fully Implemented** | Frequency aggregation of active job skills minus student skills in `intelligence/service.py` | **Implemented (Algorithmic)** |
| **Resume Storage & Management** | **Implemented (MVP)** | Multi-file local upload (PDF/DOC/DOCX $\le 5$MB), MIME detection, default selection | **Implemented (File Storage)** |
| **Resume NLP / Parsing / OCR** | **Not Implemented** | Documented explicitly in `docs/resume-module.md` as out of scope; no PDF/text parser present | **Future Scope** |
| **Predictive ML Placement Model** | **Not Implemented** | No dataset (`.csv`), no model training script, no model weights (`.pkl`), no ML imports | **Future Scope** |
| **AI Career Chatbot** | **Not Implemented** | No LLM integration, prompt templates, or conversational UI | **Future Scope** |

> [!IMPORTANT]
> **Academic Integrity Statement:** In the project report, the "Placement Readiness Score" must be described as a **deterministic, multi-pillar analytical scoring engine**. The student must **not** claim a trained machine learning model, nor report fabricated accuracy/F1 metrics. Predictive modeling should be formally presented under **Future Work / Phase 2**.

---

## 6. Empirical Verification & Test Results

### 6.1 Backend Test Execution Evidence

- **Execution Command:** `.\venv\Scripts\pytest.exe tests/ -v`
- **Execution Timestamp:** 2026-10-11T22:50:04+05:30 to 2026-10-11T22:51:50+05:30
- **Total Tests Collected:** 114
- **Total Tests Passed:** 114
- **Total Tests Failed / Skipped:** 0 / 0
- **Pass Rate:** **100.0%**
- **Execution Time:** 91.48 seconds
- **Exit Code:** `0`

#### Module-by-Module Breakdown
1. `test_analytics.py`: 3 passed (empty state, staff aggregations, student isolation)
2. `test_application_rounds.py`: 1 passed (full round lifecycle)
3. `test_applications.py`: 2 passed (lifecycle constraints, eligibility gating)
4. `test_auth.py`: 15 passed (password hashing, registration, login, JWT validation, roles)
5. `test_companies.py`: 7 passed (company CRUD, search, status filtering, access controls)
6. `test_departments.py`: 3 passed (department CRUD, validation, active filtering)
7. `test_intelligence.py`: 8 passed (readiness calculation, gap analysis, job match, boundaries)
8. `test_job_rounds.py`: 4 passed (round CRUD, snapshot isolation, round deletion)
9. `test_jobs.py`: 5 passed (job creation, validation, search, security)
10. `test_placements.py`: 1 passed (placement lifecycle and constraints)
11. `test_recruitment_workflow.py`: 6 passed (derived status, visibility, round attendance, scheduling)
12. `test_resumes.py`: 19 passed (multi-resume CRUD, upload validation, download, isolation)
13. `test_skills.py`: 20 passed (catalog, student skills, proficiencies, staff CRUD)
14. `test_staff_students.py`: 5 passed (student directory, filtering, resume access security)
15. `test_student_jobs.py`: 4 passed (job discovery, eligibility gating, search filters)
16. `test_students.py`: 11 passed (profile auto-provisioning, updates, field restrictions)

### 6.2 Frontend Build & Quality Verification

1. **TypeScript Type Checking:**
   - **Command:** `cmd.exe /c "npm run typecheck"` (`tsc --noEmit -p tsconfig.app.json`)
   - **Exit Code:** `0`
   - **Result:** Passed cleanly with 0 type errors.
2. **Production Bundle Compilation:**
   - **Command:** `cmd.exe /c "npm run build"` (`tsc -b && vite build`)
   - **Exit Code:** `0`
   - **Result:** Successfully compiled in **9.44s**, transforming 2,926 modules and outputting optimized bundles to `dist/`.
3. **Frontend Linting:**
   - **Command:** `cmd.exe /c "npm run lint"` (`eslint .`)
   - **Exit Code:** `1`
   - **Result:** 38 problems reported (28 errors for unused variables / explicit `any`, 10 warnings for Fast Refresh / hook dependencies).
   - **Safety Assessment:** In adherence to safety guidelines, code was not modified to suppress linting warnings.

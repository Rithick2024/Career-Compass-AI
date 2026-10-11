# Career Compass AI

**Smart Placement Analytics & Career Intelligence Platform**  
*SRM Institute of Science and Technology — MCA Project*

Career Compass AI is an integrated, full-stack placement intelligence platform designed to streamline campus recruitment, candidate eligibility verification, recruitment round workflows, and placement analytics.

---

## 🛠️ Verified Technology Stack

### Frontend
- **Framework:** React 18 (`18.3.1`) with TypeScript (`5.5.3`)
- **Build Tool:** Vite (`5.4.8`)
- **Styling:** Tailwind CSS (`3.4.13`) & Radix UI primitives
- **Routing:** React Router DOM (`7.18.2`) with role-based route gating
- **Visualizations:** Recharts (`2.12.7`)
- **HTTP Client:** Axios (`1.19.0`) with JWT bearer interceptors

### Backend
- **Framework:** FastAPI (`0.115.6`) running on Uvicorn (`0.34.0`)
- **Runtime:** Python `>= 3.11` (Active runtime: `3.13.14`)
- **Database ORM:** SQLAlchemy 2.0 (`2.0.36`, asyncio) with asyncpg driver (`0.30.0`)
- **RDBMS:** PostgreSQL 14+
- **Migrations:** Alembic (`1.14.0`) — 17 migrations
- **Validation & Settings:** Pydantic v2 (`2.10.4`), pydantic-settings (`2.7.1`)
- **Security:** Bcrypt (`4.2.1`) password hashing & PyJWT (`2.10.1`) stateless tokens

---

## 📦 Implemented Domain Modules

The platform is structured into 13 Clean Architecture feature modules under `backend/app/modules/`:

1. **Authentication & RBAC:** Student and Staff registration, login, JWT token issuance, and route gating.
2. **Student Profiles:** Student profile auto-provisioning, CGPA, department assignment, and graduation details.
3. **Department Management:** Department catalog, codes, and active status filtering.
4. **Skills Inventory:** Master skill catalog and student inventory with 3 standardized proficiency tiers (*beginner*, *intermediate*, *advanced*).
5. **Resume Management:** Multi-document storage (PDF/DOC/DOCX $\le 5$ MB), MIME type validation, and default selection.
6. **Company Directory:** Recruiting partner profiles, industry classifications, and status toggles.
7. **Job Postings & Wizard:** Multi-criteria job wizard with salary, CGPA cutoffs, eligible departments, and required skills.
8. **Job Recruitment Rounds:** Sequential workflow templates (`JobRound`) with fixed-time or availability window scheduling.
9. **Applications & Snapshotting:** Candidate application submission with deep snapshotting into `ApplicationRound` instances (`ON DELETE SET NULL` isolation).
10. **Recruitment Round Tracking:** Two-party round lifecycle: candidate attendance self-reporting, staff verification, outcome evaluation (*Passed*/*Failed*), and justified rescheduling.
11. **Placement Tracking:** Formal placement offer issuance and candidate acceptance/decline tracking.
12. **Descriptive Analytics:** Staff KPIs (application funnels, department placement distributions, average packages) and student status overviews.
13. **Placement Intelligence:** 100-point transparent 4-pillar placement readiness scoring engine and market skill gap analysis.

---

## 🚀 Quick Setup & Execution

### 1. Database Setup
Ensure PostgreSQL is running locally and create the development and testing databases:
```bash
createdb CareerCompassAI
createdb career_compass_test
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env
# Edit .env with your local PostgreSQL credentials and generate JWT_SECRET_KEY:
# python -c "import secrets; print(secrets.token_urlsafe(64))"

alembic upgrade head
```

Run the backend development server:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### 3. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
- Access the web interface at `http://localhost:5173`

### 4. Seed Synthetic Demo Data (For Demos & Screenshots)
A safe, idempotent script is provided to populate realistic, 100% fictional data (`@example.test`) for UI demonstrations without exposing real data:
```bash
cd backend
# Dry-run simulation (verifies safety, rolls back all changes):
python scripts/seed_demo_data.py --dry-run

# Seed local development database (prompts securely for demo password):
python scripts/seed_demo_data.py --confirm-local-demo-db
```
*(See [DEMO_DATA_GUIDE.md](docs/demo-data/DEMO_DATA_GUIDE.md) for full persona breakdowns, readiness scores, and screenshot walkthroughs).*

---

## 🧪 Testing & Verification

- **Backend Automated Test Suite (114 Tests):**
  ```bash
  cd backend
  pytest tests/ -v
  ```
  *(114 passed out of 114 tests in 91.48s with transaction savepoint rollbacks against `career_compass_test`)*.

- **Frontend Static Typecheck:**
  ```bash
  cd frontend
  npm run typecheck
  ```
  *(Zero TypeScript compilation errors)*.

- **Frontend Production Build:**
  ```bash
  cd frontend
  npm run build
  ```
  *(2,926 modules transformed, built cleanly in ~9.44s)*.

---

## 📑 Project Report Evidence Pack

Comprehensive technical documentation and academic verification records are available in `docs/project-report-evidence/`:

- [REPORT_EVIDENCE.md](docs/project-report-evidence/REPORT_EVIDENCE.md) — Comprehensive technical findings and readiness formulations.
- [ARCHITECTURE.md](docs/project-report-evidence/ARCHITECTURE.md) — System architecture, layered patterns, and Mermaid sequence diagrams.
- [DATABASE_SCHEMA.md](docs/project-report-evidence/DATABASE_SCHEMA.md) — Complete database schema, relationships, and Mermaid ER diagram.
- [API_REFERENCE.md](docs/project-report-evidence/API_REFERENCE.md) — Specification for all 54 REST API endpoints.
- [TEST_RESULTS.md](docs/project-report-evidence/TEST_RESULTS.md) — Verified test execution logs and reproducibility audit.
- [FEATURE_TRACEABILITY.md](docs/project-report-evidence/FEATURE_TRACEABILITY.md) — End-to-end traceability matrix.
- [ENVIRONMENT_AND_SETUP.md](docs/project-report-evidence/ENVIRONMENT_AND_SETUP.md) — Prerequisites, environment variables, and run guide.
- [REPORT_EVIDENCE_MANIFEST.md](docs/project-report-evidence/REPORT_EVIDENCE_MANIFEST.md) — Academic claims checklist and confirmation items.


# Project Report Evidence Manifest & Academic Verification Checklist

**Project:** Career Compass AI: Smart Placement Analytics & Career Intelligence Platform  
**Purpose:** Comprehensive checklist categorizing all technical claims to ensure academic accuracy in the SRM MCA mini project report.  
**Audit Date:** 2026-10-11  

---

## 1. Verified Claims (Backed by Real Executable Code & Tests)

These items are 100% verified by static code analysis and empirical test execution. They can be safely stated as implemented facts in the project report.

- [x] **Full-Stack Integration:** FastAPI asynchronous backend paired with React 18 / TypeScript / Vite frontend.
- [x] **Relational Persistence:** PostgreSQL with SQLAlchemy 2.0 (asyncio) and asyncpg driver.
- [x] **Database Migration Lifecycle:** 17 sequential Alembic migrations managing all schema states.
- [x] **Primary Key Strategy:** Auto-incrementing Integer Primary Keys (`SERIAL`) across all tables.
- [x] **Authentication & Role Authorization:** Bcrypt password hashing, HS256 JWT tokens, and role-based guards (`student` and `staff`).
- [x] **Student Profile & Department Management:** Auto-provisioning of student profiles upon registration, CGPA tracking, and department assignments.
- [x] **Skill Inventory:** Master skill catalog and student skill inventory with 3 proficiency levels (`beginner`, `intermediate`, `advanced`).
- [x] **Corporate & Job Directory:** Company profiles, multi-step job creation wizard, department eligibility gating, and minimum CGPA criteria.
- [x] **Recruitment Round Template vs Snapshot Architecture:** Clear separation between `JobRound` (job templates) and `ApplicationRound` (candidate snapshots).
- [x] **Snapshot Data Isolation:** `ApplicationRound.job_round_id` uses `ON DELETE SET NULL`. Candidate rounds preserve meeting links, test links, schedule dates, and titles even if parent templates are modified or deleted.
- [x] **Two-Party Recruitment Flow:** Candidate self-reports attendance (`ATTENDED`/`ABSENT`); staff verifies attendance (`VERIFIED`/`REJECTED`); staff records evaluation (`Passed`/`Failed`); rescheduling requires a justification reason.
- [x] **Application Duplicate Prevention:** Database-level unique constraint `(student_id, job_id)` prevents duplicate applications.
- [x] **Placement Tracking:** Formal placement offer issuance by staff and candidate acceptance/decline workflow.
- [x] **Placement Readiness Engine:** Deterministic 100-point analytical engine combining 4 weighted pillars:
  - Academic Readiness (25 points)
  - Skill Profile (35 points)
  - Profile & Resume Completeness (20 points)
  - Market Eligibility (20 points)
  Categorized into: *Needs Improvement* (<40), *Developing* (40–59.9), *Good* (60–79.9), and *Strong* ($\ge 80$).
- [x] **Descriptive Placement Analytics:** Staff KPIs (total students, active jobs, pending applications, accepted placements, average package LPA, funnel pass rates) and candidate dashboard statistics.
- [x] **Empirical Backend Test Suite:** **114 out of 114 tests passing** with 0 failures across 16 test files in 91.48 seconds.
- [x] **Frontend TypeScript Typecheck:** `tsc --noEmit` compiles cleanly with **0 errors**.
- [x] **Frontend Production Build:** Vite bundle compiles cleanly in 9.44 seconds transforming 2,926 modules.

---

## 2. Historical vs Current Discrepancies

These items reflect differences between earlier milestone notes and the actual state of the repository:

| Feature / Metric | Historical Milestone Claim | Verified Current Reality | Recommendation for Project Report |
|---|---|---|---|
| **Backend Test Count** | Recorded as **85 tests** | Active suite collects and passes **114 tests** | Report **114 automated tests** as the verified metric. |
| **Authentication Tests** | Recorded as **14 tests** | `test_auth.py` contains **15 test cases** (all passing) | Report **15 authentication tests**. |
| **User Role Enum** | Historically had `'admin'` role | Migration `b2c3d4e5f6a7` renamed `'admin'` to `'staff'` | Document role as `'staff'` and explain the migration. |
| **Skill Proficiency Levels** | Historically included `'expert'` | Migration `38f0da1163aa` removed `'expert'` | Document the 3 standardized tiers: Beginner, Intermediate, Advanced. |

---

## 3. Partially Supported Claims (Boundary Clarifications)

These features are functional but have strict scope boundaries that must be stated clearly to avoid misrepresentation:

- [x] **Resume Module:**
  - *Implemented:* Multi-document file storage (PDF/DOC/DOCX $\le 5$ MB) with MIME validation, metadata storage, download, and default selection.
  - *Boundary:* Local filesystem storage only (`uploads/resumes/`). **Does not include OCR, NLP text extraction, or cloud storage (S3).**
- [x] **Job Matching & Skill Gap Analysis:**
  - *Implemented:* Deterministic set-difference calculation matching student skills against active job requirements.
  - *Boundary:* **Algorithmic rule matching only.** Does not use vector embeddings, TF-IDF, cosine similarity, or collaborative filtering.
- [x] **Frontend Code Quality:**
  - *Implemented:* Application compiles and builds cleanly for production.
  - *Boundary:* ESLint reports 28 unused variable/explicit-any errors and 10 hook warnings. Application logic was preserved rather than edited.

---

## 4. Unsupported Claims / Future Scope (Must Not Be Claimed as Implemented)

These features do not exist in the codebase and must be placed under **Future Scope / Phase 2**:

- [ ] **Predictive Machine Learning Placement Model:**
  - *Status:* **NOT IMPLEMENTED.** No datasets, scikit-learn models, weights (`.pkl`), or training scripts exist.
  - *Academic Guidance:* Do not fabricate accuracy, precision, recall, or F1 metrics. Frame predictive modeling as future work.
- [ ] **AI Career Guidance Chatbot:**
  - *Status:* **NOT IMPLEMENTED.** No LLM integration, OpenAI/Gemini API calls, or conversational UI exists.
- [ ] **AI-Powered Resume Builder / Generator:**
  - *Status:* **NOT IMPLEMENTED.** No resume generation logic exists.
- [ ] **Automated Candidate Selection / Auto-Offer:**
  - *Status:* **NOT IMPLEMENTED.** Passing an interview round does not automatically issue an offer; staff retains explicit decision-making authority.

---

## 5. Unresolved Questions & Items Needing Confirmation from Student

The following items should be reviewed and confirmed by the student before final submission of the academic report:

1. **Hardware / Deployment Specifications:** What target deployment environment (e.g., local laptop vs AWS EC2 / Render / Supabase) should be documented in the report's hardware and environment sections?
2. **Future Work Timeline:** Is the predictive ML model planned as a Final Semester MCA Major Project extension?
3. **ESLint Cleanup:** Would the student prefer to clean up the 28 non-fatal TypeScript/ESLint warnings (removing unused icon imports and typing explicit `any`s) in a future maintenance pass?
4. **Seed Account Credentials:** The administrative creation script (`scripts/create_staff_user.py`) requires manual terminal input. Should default demonstration credentials be specified in a private appendix?

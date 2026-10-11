# Synthetic Demo Data Verification & Validation Report

**Project:** Career Compass AI: Smart Placement Analytics & Career Intelligence Platform  
**Audit & Execution Date:** 2026-10-11  
**Target Environment:** Local Development Database (`CareerCompassAI` on `localhost:5432`)  
**Execution Script:** [backend/scripts/seed_demo_data.py](file:///d:/Project%20X/CareerCompassAI/backend/scripts/seed_demo_data.py)  
**Verification Status:** Successfully Executed & Verified on Active Local Database  

---

## 1. Execution Summary & Safety Validation

In accordance with strict safety constraints, the seeding script was executed against the local development database with write confirmation. All records were created using synthetic identities under the `@example.test` domain.

### Environment Security Check
- **Configured Database Name:** `CareerCompassAI` (Confirmed as local dev database)
- **Configured Host:** `localhost` (Loopback interface verified)
- **Environment Mode:** `development` (Non-production verified)
- **Confirmation Flag:** Explicit `--confirm-local-demo-db` supplied
- **Password Security:** Salted and hashed using `bcrypt` via [app/core/security.py](file:///d:/Project%20X/CareerCompassAI/backend/app/core/security.py). Plaintext passwords were not logged, committed, or written to disk.

---

## 2. Record Generation & Idempotency Audit

The table below reflects the exact records created on initial execution and verified on subsequent idempotent runs:

| Entity / Table | Initial Seed Count | Idempotent Run Count | Net Records in Database | Idempotency Result |
|---|---|---|---|---|
| **Users (`users`)** | 15 (1 Staff + 14 Students) | 0 created (15 reused) | 18 (15 demo + 3 pre-existing) | **100% Idempotent** |
| **Departments (`departments`)** | 4 verified | 4 verified (0 created) | 6 (standard departments) | **100% Idempotent** |
| **Master Skills (`skills`)** | 9 created (8 pre-existing) | 0 created (17 verified)| 17 total catalog skills | **100% Idempotent** |
| **Student Profiles (`students`)**| 14 created | 0 created (14 updated) | 16 (14 demo + 2 pre-existing) | **100% Idempotent** |
| **Student Skills (`student_skills`)**| 38 created | 0 created (38 verified)| 38 demo skill associations | **100% Idempotent** |
| **Resumes (`resumes`)** | 9 created | 0 created (9 verified) | 9 synthetic demo resumes | **100% Idempotent** |
| **Physical Resume Files** | 9 files written to disk | 0 files re-written | 9 valid minimal PDF files | **100% Idempotent** |
| **Companies (`companies`)** | 5 created | 0 created (5 verified) | 5 recruiting partner firms | **100% Idempotent** |
| **Jobs (`jobs`)** | 7 created | 0 created (7 verified) | 9 (7 demo + 2 pre-existing) | **100% Idempotent** |
| **Job Rounds (`job_rounds`)** | 13 created | 0 created (13 verified)| 13 template workflow rounds | **100% Idempotent** |
| **Applications (`applications`)**| 7 created | 0 created (7 verified) | 9 (7 demo + 2 pre-existing) | **100% Idempotent** |
| **Round Snapshots (`application_rounds`)**| 20 created | 0 created (20 verified)| 20 candidate round instances | **100% Idempotent** |
| **Placements (`placements`)** | 2 created | 0 created (2 verified) | 2 (1 Accepted, 1 Pending) | **100% Idempotent** |

---

## 3. Empirical Verification of Domain Logic & Dashboards

Following database seeding, real backend services were invoked against the local database to verify that business logic, analytics aggregations, and readiness formulas executed cleanly.

### 3.1 Staff Analytics Dashboard Verification (`AnalyticsService.get_staff_overview`)
- **Total Students:** `16` (14 synthetic demo students + 2 pre-existing local accounts).
- **Active Jobs:** `6` (Open, Closing Soon, and Upcoming jobs; excludes archived job).
- **Accepted Placements:** `1` (Aarav Sharma at Apex Innovations Corp).
- **Average Package CTC:** `12.00 LPA` (Derived accurately from accepted placement).
- **Application Funnel Distribution:**
  - `Interview`: 5 applications (actively in recruitment pipeline).
  - `Offered`: 2 applications (Aarav Sharma and Diya Patel).
  - `Rejected`: 1 application (Priya Nair).
  - `Withdrawn`: 1 application (Karthik Rajan).
- **Recruitment Funnel Metrics:**
  - Total candidate rounds: `23`.
  - Completed rounds: `10`.
  - Round Pass Rate: `90.0%`.

### 3.2 Placement Readiness Engine Verification (`IntelligenceService.calculate_readiness`)
Real calculations were performed on sample student personas across the 4 pillars:

| Persona | CGPA | Skills | Resume | Calculated Score | Status Category | Pillar Breakdown |
|---|---|---|---|---|---|---|
| `aarav.sharma@example.test` | 9.35 | 6 Adv | Uploaded | **96.7 / 100** | **Strong** | Acad: 23.7/25, Skills: 33.0/35, Prof: 20.0/20, Mkt: 20.0/20 (Placed) |
| `rohan.verma@example.test` | 8.20 | 4 Adv/Int | Uploaded | **87.1 / 100** | **Strong** | Acad: 21.4/25, Skills: 29.0/35, Prof: 20.0/20, Mkt: 16.7/20 |
| `karthik.rajan@example.test`| 7.15 | 3 Beg | Uploaded | **69.7 / 100** | **Good** | Acad: 19.3/25, Skills: 17.0/35, Prof: 16.7/20, Mkt: 16.7/20 |
| `meera.joshi@example.test` | 6.90 | 2 Int | Uploaded | **60.5 / 100** | **Good** | Acad: 18.8/25, Skills: 20.0/35, Prof: 15.0/20, Mkt: 6.7/20 |
| `sneha.reddy@example.test` | 6.75 | 2 Beg/Int | Uploaded | **55.5 / 100** | **Developing** | Acad: 18.5/25, Skills: 17.0/35, Prof: 13.3/20, Mkt: 6.7/20 |
| `pooja.das@example.test` | 5.80 | 0 | None | **18.3 / 100** | **Needs Improvement**| Acad: 16.6/25, Skills: 0.0/35, Prof: 1.7/20, Mkt: 0.0/20 |
| `siddharth.rao@example.test`| None | 0 | None | **1.7 / 100** | **Needs Improvement**| Acad: 0.0/25, Skills: 0.0/35, Prof: 1.7/20, Mkt: 0.0/20 |

### 3.3 Snapshot Isolation Verification
- Active job rounds for `Graduate Software Engineer` (4 rounds) were successfully deep-copied into candidate `ApplicationRound` instances.
- Foreign keys `job_round_id` reference `job_rounds.id` with `ON DELETE SET NULL`.
- Verification of test suite in [tests/test_job_rounds.py](file:///d:/Project%20X/CareerCompassAI/backend/tests/test_job_rounds.py) confirmed that deleting a `JobRound` template sets `job_round_id = NULL` on the candidate snapshot while preserving all candidate meeting links, scores, and round details.

### 3.4 Physical Resume File Validation
- 9 physical synthetic PDF files were generated in `backend/uploads/resumes/<student_id>/<uuid>.pdf`.
- All files have valid `%PDF-1.4` magic bytes and conform to [app/modules/resumes/storage.py](file:///d:/Project%20X/CareerCompassAI/backend/app/modules/resumes/storage.py) MIME validation rules.
- Files contain strictly synthetic text and can be downloaded from the UI without generating 404 errors.

---

## 4. Email Validation Resolution & Authentication Verification

### 4.1 Root Cause of Initial Validation Failure
During initial login testing with `staff.demo@example.test`, Pydantic's `EmailStr` (backed by `email-validator==2.2.0`) raised:
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "One or more fields failed validation.",
  "details": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address: The part after the @-sign is a special-use or reserved name that cannot be used with email.",
      "input": "staff.demo@example.test"
    }
  ]
}
```
**Mechanism:** Under RFC 2606 and RFC 6761, `.test` is a reserved top-level domain. By default, `email-validator` initializes `TEST_ENVIRONMENT = False`, which causes `validate_email_domain_name` to reject `.test` addresses as unroutable special-use names.

### 4.2 Solution Architecture
Instead of weakening validation globally or altering database records to use arbitrary domains, the application wires a clean, environment-aware configuration via `Settings.ALLOW_TEST_EMAIL_DOMAINS` and `app.core.config.configure_email_validator`:
1. **Development & Testing:** When `ALLOW_TEST_EMAIL_DOMAINS=true` and `APP_ENV != "production"`, `email_validator.TEST_ENVIRONMENT = True` is activated. This explicitly permits RFC 2606 reserved domains (`.test`) while **continuing to enforce strict email syntax, character limits, mailbox format, and domain syntax**.
2. **Production Hardening:** When `APP_ENV=production` (`is_production=True`), `TEST_ENVIRONMENT` is unconditionally set to `False`, strictly forbidding `.test` and other reserved domains in live production environments.
3. **Zero Database Changes:** Because the database already contained records with `@example.test`, all demo records (`staff.demo@example.test`, `aarav.sharma@example.test`, etc.) became immediately usable with zero data migrations and zero reseeding.

### 4.3 Automated Regression & Verification Test Evidence
A dedicated regression test suite was implemented in [backend/tests/test_email_validation.py](file:///d:/Project%20X/CareerCompassAI/backend/tests/test_email_validation.py) and executed against the live test database:

| Test Suite / Area | Command Executed | Tests Passed | Exit Code | Result |
|---|---|---|---|---|
| **Demo Email Validation Suite** | `pytest tests/test_email_validation.py -v` | **29 / 29** | `0` | **PASS** |
| **Authentication Core Suite** | `pytest tests/test_auth.py -v` | **15 / 15** | `0` | **PASS** |
| **Complete Backend Test Suite** | `pytest tests/` | **143 / 143** | `0` | **PASS** |

Key verified scenarios:
- `staff.demo@example.test` and student demo emails pass `UserLoginRequest`, `UserRegisterRequest`, and `StaffRegisterRequest`.
- Malformed emails (`not-an-email`, `user@`, `@example.test`, `user @example.test`, `user..name@example.test`, `user@example..test`, `user@-example.test`) are strictly rejected with HTTP 422 `VALIDATION_ERROR`.
- Production simulation verifies that `.test` is strictly rejected when `APP_ENV=production`.
- Live API integration confirms that POST `/api/v1/auth/login` with `staff.demo@example.test` reaches the authentication service and returns HTTP 401 `INVALID_CREDENTIALS` on bad password (proving it traverses request schema validation), and returns HTTP 200 with JWT access token upon successful credentials.

---

## 5. Verification Conclusion

The synthetic demo dataset is **safe, non-destructive, fully idempotent, and empirically verified** against the local development database. With the environment-scoped RFC 2606 email validator configuration, demo accounts can authenticate seamlessly while production rules remain strictly guarded.

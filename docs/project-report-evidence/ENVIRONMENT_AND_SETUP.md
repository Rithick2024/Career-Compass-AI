# Environment Configuration & Setup Guide

**Project:** Career Compass AI: Smart Placement Analytics & Career Intelligence Platform  
**Target Environment:** Local Development & Academic Demonstration  
**Safety Notice:** In accordance with project security constraints, this document specifies environment variable names, types, and defaults without exposing real credentials, secret keys, or private student data.  

---

## 1. Prerequisites & System Requirements

| Prerequisite | Minimum Required | Verified in Repository |
|---|---|---|
| **Operating System** | Windows 10/11, macOS, or Linux | Windows 11 |
| **Python** | `>= 3.11` | `3.13.14` |
| **Database** | PostgreSQL 14+ | PostgreSQL 14+ |
| **Node.js** | `>= 18.0.0` | Node.js (Active Windows environment) |
| **Package Managers** | `pip` (Python) and `npm` (Node) | pip 26.1.2 / npm |

---

## 2. Backend Environment Variables Reference

Backend configuration is loaded from `.env` via `pydantic-settings` in [app/core/config.py](file:///d:/Project%20X/CareerCompassAI/backend/app/core/config.py). A template is provided in `backend/.env.example`.

| Variable Name | Type | Required | Default Value | Description |
|---|---|---|---|---|
| `APP_NAME` | String | No | `"Career Compass AI"` | Application title displayed in OpenAPI docs |
| `APP_ENV` | String | No | `"development"` | Environment mode (`development` or `production`) |
| `DEBUG` | Boolean | No | `true` | FastAPI debug mode flag |
| `API_V1_PREFIX` | String | No | `"/api/v1"` | URL routing prefix for v1 endpoints |
| `HOST` | String | No | `"0.0.0.0"` | Local server bind host |
| `PORT` | Integer | No | `8000` | Local server bind port |
| `POSTGRES_USER` | String | **Yes** | — | PostgreSQL database username |
| `POSTGRES_PASSWORD` | String | **Yes** | — | PostgreSQL database user password |
| `POSTGRES_HOST` | String | No | `"localhost"` | PostgreSQL server hostname |
| `POSTGRES_PORT` | Integer | No | `5432` | PostgreSQL server port |
| `POSTGRES_DB` | String | **Yes** | `"CareerCompassAI"` | Primary application database name |
| `DB_ECHO` | Boolean | No | `false` | Echo raw SQL queries to console |
| `DB_POOL_SIZE` | Integer | No | `5` | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | Integer | No | `10` | SQLAlchemy maximum overflow connections |
| `DB_POOL_TIMEOUT` | Integer | No | `30` | Connection pool checkout timeout (seconds) |
| `CORS_ORIGINS` | String | No | `"http://localhost:5173,http://localhost:3000"` | Comma-separated list of allowed CORS origins |
| `LOG_LEVEL` | String | No | `"INFO"` | Console logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `JWT_SECRET_KEY` | String | **Yes** | — | High-entropy secret key for HS256 JWT signing |
| `JWT_ALGORITHM` | String | No | `"HS256"` | JWT cryptographic signature algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | No | `60` | JWT token validity window in minutes |
| `RESUME_UPLOAD_DIR` | String | No | `"uploads/resumes"` | Local filesystem directory for uploaded resumes |
| `RESUME_MAX_FILE_SIZE_MB` | Integer | No | `5` | Maximum allowed resume file size in megabytes |

---

## 3. Frontend Environment Variables Reference

Frontend configuration is loaded from `frontend/.env` via Vite environment variables:

| Variable Name | Type | Required | Default Value | Description |
|---|---|---|---|---|
| `VITE_API_BASE_URL` | String | No | `"http://localhost:8000/api/v1"` | Base URL pointing to the FastAPI backend API |

---

## 4. Step-by-Step Installation & Setup

### 4.1 Step 1 — Database Initialization
Ensure PostgreSQL is running locally and create the development and testing databases:
```bash
createdb CareerCompassAI
createdb career_compass_test
```

### 4.2 Step 2 — Backend Virtual Environment & Dependencies
Navigate to the `backend/` directory:
```bash
cd backend
python -m venv venv

# Activate virtual environment:
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install development and production requirements:
pip install -r requirements-dev.txt
```

### 4.3 Step 3 — Backend Configuration & JWT Secret Generation
Create the `.env` configuration file:
```bash
cp .env.example .env
```
Generate a secure random secret key for `JWT_SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
Populate `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `JWT_SECRET_KEY` inside `.env`.

### 4.4 Step 4 — Run Database Migrations
Apply all 17 Alembic migrations to build the schema:
```bash
alembic upgrade head
```

### 4.5 Step 5 — (Optional) Seed Administrative Staff Account
To create an initial staff account for administrative access:
```bash
python scripts/create_staff_user.py
```
*(Prompts for email and password securely without displaying plaintext).*

### 4.6 Step 6 — Frontend Dependencies & Configuration
Navigate to the `frontend/` directory in a new terminal:
```bash
cd frontend
npm install
cp .env.example .env
```

---

## 5. Verified Run & Test Commands

### Running Locally for Development

- **Run Backend API Server (FastAPI + Uvicorn with auto-reload):**
  ```bash
  cd backend
  .\venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
  ```
  - Interactive OpenAPI Docs: `http://localhost:8000/docs`
  - ReDoc Documentation: `http://localhost:8000/redoc`
  - Health Check: `http://localhost:8000/api/v1/health`

- **Run Frontend Dev Server (Vite):**
  ```bash
  cd frontend
  npm run dev
  ```
  - Web Interface: `http://localhost:5173`

### Executing Automated Tests & Validations

- **Execute Backend Automated Test Suite (114 Tests):**
  ```bash
  cd backend
  .\venv\Scripts\pytest.exe tests/ -v
  ```
  *(Tests execute against `career_compass_test` with transaction savepoint rollbacks).*

- **Execute Frontend TypeScript Typecheck:**
  ```bash
  cd frontend
  npm run typecheck
  ```

- **Compile Frontend Production Bundle:**
  ```bash
  cd frontend
  npm run build
  ```

- **Run Frontend Lint Check:**
  ```bash
  cd frontend
  npm run lint
  ```

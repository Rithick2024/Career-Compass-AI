"""
Safe, Repeatable Synthetic Demo Data Generator for Career Compass AI.

Purpose:
    Seeds a portable, local development database with realistic, entirely fictional
    records to support UI demos, screenshots, and evaluation of all platform modules.

Safety Invariants:
    1. NEVER uses production or real personal/company data (uses @example.test domains).
    2. NEVER hardcodes plaintext passwords into source control. Prompts or generates securely.
    3. Hashes passwords using project's existing bcrypt utility (app.core.security.hash_password).
    4. Refuses to run if configured database is production or remote.
    5. Requires explicit `--confirm-local-demo-db` flag for database writes.
    6. Fully idempotent: does not duplicate records or overwrite non-demo data.
    7. Supports `--dry-run` to inspect planned changes without persisting.

Usage:
    # Dry run (simulation only, rolls back transaction):
    python scripts/seed_demo_data.py --dry-run

    # Execute seeding against local development database:
    python scripts/seed_demo_data.py --confirm-local-demo-db
"""

import argparse
import asyncio
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import getpass
import os
from pathlib import Path
import secrets
import sys
from typing import Dict, List, Optional, Tuple
import uuid

# Ensure backend root is on Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure all ORM models are registered in SQLAlchemy registry
import app.db.base  # noqa: F401
import app.modules.job_rounds.models  # noqa: F401

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.modules.application_rounds.models import (
    ApplicationRound,
    RoundResult,
    RoundStatus,
    RoundType,
    ScheduleType,
    StaffVerification,
    StudentAttendance,
)
from app.modules.applications.models import Application, ApplicationStatus
from app.modules.auth.models import User
from app.modules.companies.models import Company
from app.modules.job_rounds.models import JobRound
from app.modules.jobs.models import Job, JobEligibleDepartment, JobRequiredSkill
from app.modules.placements.models import Placement
from app.modules.resumes.models import Resume
from app.modules.skills.models import Skill, StudentSkill
from app.modules.students.models import Department, Student
from app.shared.enums import ProficiencyLevel, RoleEnum

# Fictional domain enforced for all synthetic identities
SYNTHETIC_DOMAIN = "example.test"

# Minimal synthetic PDF bytes (valid magic bytes %PDF-1.4)
SYNTHETIC_PDF_BYTES = b"""%PDF-1.4
% Fictional Synthetic Resume for Career Compass AI Local Demonstration
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000080 00000 n 
0000000133 00000 n 
0000000192 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
265
%%EOF
"""


def verify_database_safety(dry_run: bool, confirmed: bool) -> None:
    """Verifies that the target database is strictly a local development database."""
    db_name = settings.POSTGRES_DB
    host = settings.POSTGRES_HOST.lower()
    app_env = settings.APP_ENV.lower()

    print("\n" + "=" * 70)
    print(" CAREER COMPASS AI — SAFE SYNTHETIC DEMO SEEDER")
    print("=" * 70)
    print(f" Target Database Name: {db_name}")
    print(f" Target Host:          {host}")
    print(f" Environment Mode:     {app_env}")
    print("=" * 70)

    # 1. Reject production environments
    if settings.is_production or app_env == "production":
        print("\n[SECURITY REFUSAL] Cannot run seed script in production environment.")
        sys.exit(1)

    # 2. Reject remote database hosts
    allowed_hosts = {"localhost", "127.0.0.1", "::1"}
    if host not in allowed_hosts:
        print(f"\n[SECURITY REFUSAL] Host '{host}' is not a local loopback address.")
        print("Demo seeding is strictly forbidden on remote database hosts.")
        sys.exit(1)

    # 3. Reject unknown or production-sounding DB names
    disallowed_keywords = ["prod", "production", "live", "customer", "srm_real"]
    if any(k in db_name.lower() for k in disallowed_keywords):
        print(f"\n[SECURITY REFUSAL] Database name '{db_name}' contains restricted keywords.")
        sys.exit(1)

    # 4. Require explicit confirmation if not dry-run
    if not dry_run and not confirmed:
        print("\n[CONFIRMATION REQUIRED] To write synthetic demo data to the local database,")
        print("you must supply the '--confirm-local-demo-db' flag.")
        print("Example: python scripts/seed_demo_data.py --confirm-local-demo-db\n")
        print("Alternatively, execute a simulation using '--dry-run'.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Fictional Dataset Definitions
# ---------------------------------------------------------------------------

DEMO_DEPARTMENTS = [
    "Computer Applications",
    "Computer Science and Engineering",
    "Information Technology",
    "Electronics and Communication Engineering",
]

DEMO_SKILLS = [
    ("Python", "Programming Languages"),
    ("TypeScript", "Programming Languages"),
    ("JavaScript", "Programming Languages"),
    ("Java", "Programming Languages"),
    ("FastAPI", "Backend Frameworks"),
    ("React", "Frontend Development"),
    ("Tailwind CSS", "Frontend Development"),
    ("PostgreSQL", "Databases"),
    ("Redis", "Databases"),
    ("Docker", "DevOps & Cloud"),
    ("AWS Fundamentals", "DevOps & Cloud"),
    ("Linux / Shell", "Operating Systems"),
    ("Git / Version Control", "Tools"),
    ("Unit Testing", "Software Engineering"),
    ("Data Structures & Algorithms", "Core Computer Science"),
    ("REST API Design", "Software Engineering"),
    ("HTML/CSS", "Frontend Development"),
]

DEMO_COMPANIES = [
    {
        "name": "Apex Innovations Corp",
        "industry": "Information Technology",
        "location": "Bangalore",
        "website": "https://apex-innovations.example.test",
        "description": "Fictional cloud solutions and enterprise digital transformation consultancy.",
    },
    {
        "name": "BlueWave Cloud Systems",
        "industry": "Cloud Infrastructure",
        "location": "Hyderabad",
        "website": "https://bluewave-cloud.example.test",
        "description": "Fictional distributed cloud computing and scalable storage provider.",
    },
    {
        "name": "CyberShield Security Labs",
        "industry": "Cybersecurity",
        "location": "Chennai",
        "website": "https://cybershield-labs.example.test",
        "description": "Fictional application vulnerability assessments and threat detection platform.",
    },
    {
        "name": "DataPulse Analytics",
        "industry": "Data & AI",
        "location": "Pune",
        "website": "https://datapulse-analytics.example.test",
        "description": "Fictional modern data intelligence and real-time business telemetry.",
    },
    {
        "name": "NextGen FinTech Solutions",
        "industry": "Financial Technology",
        "location": "Mumbai",
        "website": "https://nextgen-fintech.example.test",
        "description": "Fictional digital payments gateway and programmable financial infrastructure.",
    },
]

# 14 Fictional Students targeting all 4 readiness categories:
# Strong (>=80), Good (60-79.9), Developing (40-59.9), Needs Improvement (<40)
DEMO_STUDENTS = [
    # --- Category: STRONG (>=80) ---
    {
        "email": f"aarav.sharma@{SYNTHETIC_DOMAIN}",
        "full_name": "Aarav Sharma",
        "dept": "Computer Applications",
        "cgpa": Decimal("9.35"),
        "phone": "+91-9123456780",
        "grad_year": 2026,
        "dob": date(2002, 5, 14),
        "address": "Fictional Flat 402, Green Avenue, Chennai",
        "linkedin": "https://linkedin.com/in/fictional-aarav-sharma",
        "github": "https://github.com/fictional-aarav-sharma",
        "skills": [
            ("Python", ProficiencyLevel.ADVANCED),
            ("FastAPI", ProficiencyLevel.ADVANCED),
            ("PostgreSQL", ProficiencyLevel.ADVANCED),
            ("Docker", ProficiencyLevel.INTERMEDIATE),
            ("TypeScript", ProficiencyLevel.ADVANCED),
            ("React", ProficiencyLevel.INTERMEDIATE),
        ],
        "has_resume": True,
        "resume_title": "Full Stack Engineer Resume",
    },
    {
        "email": f"diya.patel@{SYNTHETIC_DOMAIN}",
        "full_name": "Diya Patel",
        "dept": "Computer Science and Engineering",
        "cgpa": Decimal("8.90"),
        "phone": "+91-9123456781",
        "grad_year": 2026,
        "dob": date(2003, 3, 22),
        "address": "Fictional Block B, Residency Heights, Chennai",
        "linkedin": "https://linkedin.com/in/fictional-diya-patel",
        "github": "https://github.com/fictional-diya-patel",
        "skills": [
            ("Python", ProficiencyLevel.ADVANCED),
            ("PostgreSQL", ProficiencyLevel.ADVANCED),
            ("Docker", ProficiencyLevel.ADVANCED),
            ("Linux / Shell", ProficiencyLevel.ADVANCED),
            ("AWS Fundamentals", ProficiencyLevel.INTERMEDIATE),
            ("FastAPI", ProficiencyLevel.INTERMEDIATE),
        ],
        "has_resume": True,
        "resume_title": "Cloud Backend Resume",
    },
    # --- Category: GOOD (60 - 79.9) ---
    {
        "email": f"rohan.verma@{SYNTHETIC_DOMAIN}",
        "full_name": "Rohan Verma",
        "dept": "Information Technology",
        "cgpa": Decimal("8.20"),
        "phone": "+91-9123456782",
        "grad_year": 2026,
        "dob": date(2002, 11, 8),
        "address": "Fictional 14, River View Road, Chennai",
        "linkedin": "https://linkedin.com/in/fictional-rohan-verma",
        "github": "https://github.com/fictional-rohan-verma",
        "skills": [
            ("React", ProficiencyLevel.ADVANCED),
            ("TypeScript", ProficiencyLevel.INTERMEDIATE),
            ("Tailwind CSS", ProficiencyLevel.ADVANCED),
            ("JavaScript", ProficiencyLevel.INTERMEDIATE),
        ],
        "has_resume": True,
        "resume_title": "Frontend Specialist Resume",
    },
    {
        "email": f"priya.nair@{SYNTHETIC_DOMAIN}",
        "full_name": "Priya Nair",
        "dept": "Computer Applications",
        "cgpa": Decimal("7.85"),
        "phone": "+91-9123456783",
        "grad_year": 2026,
        "dob": date(2003, 7, 19),
        "address": "Fictional 55, Lotus Gardens, Chennai",
        "linkedin": "https://linkedin.com/in/fictional-priya-nair",
        "github": None,
        "skills": [
            ("Java", ProficiencyLevel.ADVANCED),
            ("PostgreSQL", ProficiencyLevel.INTERMEDIATE),
            ("Data Structures & Algorithms", ProficiencyLevel.INTERMEDIATE),
            ("REST API Design", ProficiencyLevel.INTERMEDIATE),
        ],
        "has_resume": True,
        "resume_title": "Backend Software Resume",
    },
    {
        "email": f"vikram.singh@{SYNTHETIC_DOMAIN}",
        "full_name": "Vikram Singh",
        "dept": "Electronics and Communication Engineering",
        "cgpa": Decimal("7.60"),
        "phone": "+91-9123456784",
        "grad_year": 2026,
        "dob": date(2002, 9, 30),
        "address": "Fictional 88, Anna Nagar, Chennai",
        "linkedin": "https://linkedin.com/in/fictional-vikram-singh",
        "github": "https://github.com/fictional-vikram-singh",
        "skills": [
            ("Python", ProficiencyLevel.INTERMEDIATE),
            ("Linux / Shell", ProficiencyLevel.ADVANCED),
            ("Git / Version Control", ProficiencyLevel.INTERMEDIATE),
            ("Unit Testing", ProficiencyLevel.INTERMEDIATE),
        ],
        "has_resume": True,
        "resume_title": "Systems & QA Resume",
    },
    {
        "email": f"ananya.iyer@{SYNTHETIC_DOMAIN}",
        "full_name": "Ananya Iyer",
        "dept": "Computer Science and Engineering",
        "cgpa": Decimal("8.45"),
        "phone": "+91-9123456785",
        "grad_year": 2026,
        "dob": date(2003, 1, 15),
        "address": "Fictional 21, Temple Street, Chennai",
        "linkedin": None,
        "github": "https://github.com/fictional-ananya-iyer",
        "skills": [
            ("Python", ProficiencyLevel.INTERMEDIATE),
            ("Data Structures & Algorithms", ProficiencyLevel.ADVANCED),
            ("PostgreSQL", ProficiencyLevel.BEGINNER),
        ],
        "has_resume": True,
        "resume_title": "CS Core Profile",
    },
    # --- Category: DEVELOPING (40 - 59.9) ---
    {
        "email": f"karthik.rajan@{SYNTHETIC_DOMAIN}",
        "full_name": "Karthik Rajan",
        "dept": "Computer Applications",
        "cgpa": Decimal("7.15"),
        "phone": "+91-9123456786",
        "grad_year": 2026,
        "dob": date(2002, 4, 12),
        "address": "Fictional 7, Beach Road, Chennai",
        "linkedin": None,
        "github": None,
        "skills": [
            ("Python", ProficiencyLevel.BEGINNER),
            ("PostgreSQL", ProficiencyLevel.BEGINNER),
            ("Git / Version Control", ProficiencyLevel.BEGINNER),
        ],
        "has_resume": True,
        "resume_title": "Junior Developer Resume",
    },
    {
        "email": f"meera.joshi@{SYNTHETIC_DOMAIN}",
        "full_name": "Meera Joshi",
        "dept": "Information Technology",
        "cgpa": Decimal("6.90"),
        "phone": "+91-9123456787",
        "grad_year": 2026,
        "dob": None,
        "address": None,
        "linkedin": "https://linkedin.com/in/fictional-meera-joshi",
        "github": None,
        "skills": [
            ("JavaScript", ProficiencyLevel.INTERMEDIATE),
            ("HTML/CSS", ProficiencyLevel.INTERMEDIATE),
        ],
        "has_resume": True,
        "resume_title": "Web Foundations Resume",
    },
    {
        "email": f"aditya.kumar@{SYNTHETIC_DOMAIN}",
        "full_name": "Aditya Kumar",
        "dept": "Computer Science and Engineering",
        "cgpa": Decimal("7.40"),
        "phone": "+91-9123456788",
        "grad_year": 2026,
        "dob": date(2003, 8, 25),
        "address": None,
        "linkedin": None,
        "github": "https://github.com/fictional-aditya-kumar",
        "skills": [
            ("Java", ProficiencyLevel.INTERMEDIATE),
            ("Data Structures & Algorithms", ProficiencyLevel.BEGINNER),
        ],
        "has_resume": False,  # Missing default resume pulls score down into Developing
        "resume_title": None,
    },
    {
        "email": f"sneha.reddy@{SYNTHETIC_DOMAIN}",
        "full_name": "Sneha Reddy",
        "dept": "Electronics and Communication Engineering",
        "cgpa": Decimal("6.75"),
        "phone": "+91-9123456789",
        "grad_year": 2026,
        "dob": None,
        "address": None,
        "linkedin": None,
        "github": None,
        "skills": [
            ("Linux / Shell", ProficiencyLevel.INTERMEDIATE),
            ("Python", ProficiencyLevel.BEGINNER),
        ],
        "has_resume": True,
        "resume_title": "Technical Resume",
    },
    # --- Category: NEEDS IMPROVEMENT (< 40) ---
    {
        "email": f"rahul.menon@{SYNTHETIC_DOMAIN}",
        "full_name": "Rahul Menon",
        "dept": "Information Technology",
        "cgpa": Decimal("6.10"),
        "phone": None,
        "grad_year": 2026,
        "dob": None,
        "address": None,
        "linkedin": None,
        "github": None,
        "skills": [
            ("Git / Version Control", ProficiencyLevel.BEGINNER),
        ],
        "has_resume": False,
        "resume_title": None,
    },
    {
        "email": f"pooja.das@{SYNTHETIC_DOMAIN}",
        "full_name": "Pooja Das",
        "dept": "Computer Applications",
        "cgpa": Decimal("5.80"),
        "phone": None,
        "grad_year": 2026,
        "dob": None,
        "address": None,
        "linkedin": None,
        "github": None,
        "skills": [],
        "has_resume": False,
        "resume_title": None,
    },
    {
        "email": f"siddharth.rao@{SYNTHETIC_DOMAIN}",
        "full_name": "Siddharth Rao",
        "dept": None,  # No department assigned
        "cgpa": None,  # No CGPA assigned
        "phone": None,
        "grad_year": 2026,
        "dob": None,
        "address": None,
        "linkedin": None,
        "github": None,
        "skills": [],
        "has_resume": False,
        "resume_title": None,
    },
    {
        "email": f"tanvi.deshmukh@{SYNTHETIC_DOMAIN}",
        "full_name": "Tanvi Deshmukh",
        "dept": "Computer Applications",
        "cgpa": Decimal("6.40"),
        "phone": "+91-9123456790",
        "grad_year": 2026,
        "dob": None,
        "address": None,
        "linkedin": None,
        "github": None,
        "skills": [
            ("HTML/CSS", ProficiencyLevel.BEGINNER),
        ],
        "has_resume": False,
        "resume_title": None,
    },
]


def build_job_definitions(base_time: datetime, dept_map: Dict[str, int], skill_map: Dict[str, int]) -> List[dict]:
    """Builds realistic synthetic job definitions with deterministic dates."""
    return [
        {
            "company_name": "Apex Innovations Corp",
            "title": "Graduate Software Engineer",
            "role_category": "Software Development",
            "location": "Bangalore",
            "employment_type": "Full-time",
            "work_mode": "Hybrid",
            "ctc_lpa": Decimal("12.00"),
            "min_cgpa": Decimal("7.50"),
            "start": base_time - timedelta(days=5),
            "deadline": base_time + timedelta(days=15),  # OPEN
            "is_active": True,
            "description": "Fictional full-stack software development role working on microservices.",
            "instructions": "Bring laptop for coding round. Review core algorithms.",
            "departments": ["Computer Applications", "Computer Science and Engineering", "Information Technology"],
            "skills": [("Python", ProficiencyLevel.INTERMEDIATE), ("PostgreSQL", ProficiencyLevel.INTERMEDIATE), ("React", ProficiencyLevel.BEGINNER)],
            "rounds": [
                (1, RoundType.ONLINE_ASSESSMENT, "Online Aptitude & Logic Assessment", ScheduleType.AVAILABILITY_WINDOW, base_time - timedelta(days=2), base_time + timedelta(days=1), 60, "https://eval.example.test/apex-apt-101", None),
                (2, RoundType.CODING_TEST, "Hands-On Coding Test", ScheduleType.FIXED_TIME, base_time + timedelta(days=4), None, 90, "https://eval.example.test/apex-code-102", None),
                (3, RoundType.TECHNICAL_INTERVIEW, "Technical Architecture Interview", ScheduleType.FIXED_TIME, base_time + timedelta(days=7), None, 45, None, "https://meet.example.test/apex-tech-room"),
                (4, RoundType.HR_INTERVIEW, "HR & Culture Alignment Interview", ScheduleType.FIXED_TIME, base_time + timedelta(days=10), None, 30, None, "https://meet.example.test/apex-hr-room"),
            ],
        },
        {
            "company_name": "BlueWave Cloud Systems",
            "title": "Cloud Backend Developer",
            "role_category": "Cloud & Distributed Systems",
            "location": "Hyderabad",
            "employment_type": "Full-time",
            "work_mode": "Remote",
            "ctc_lpa": Decimal("10.50"),
            "min_cgpa": Decimal("7.00"),
            "start": base_time - timedelta(days=8),
            "deadline": base_time + timedelta(days=10),  # OPEN
            "is_active": True,
            "description": "Fictional backend engineering role building asynchronous microservices with FastAPI and asyncpg.",
            "instructions": "Candidate must have stable broadband for live video coding.",
            "departments": ["Computer Applications", "Computer Science and Engineering", "Information Technology"],
            "skills": [("Python", ProficiencyLevel.ADVANCED), ("FastAPI", ProficiencyLevel.INTERMEDIATE), ("Docker", ProficiencyLevel.BEGINNER)],
            "rounds": [
                (1, RoundType.CODING_TEST, "Async Python & Database Problem Solving", ScheduleType.FIXED_TIME, base_time - timedelta(days=3), None, 60, "https://eval.example.test/bw-code-201", None),
                (2, RoundType.TECHNICAL_INTERVIEW, "Systems & Concurrency Deep Dive", ScheduleType.FIXED_TIME, base_time + timedelta(days=3), None, 45, None, "https://meet.example.test/bw-tech-room"),
                (3, RoundType.HR_INTERVIEW, "HR Discussion", ScheduleType.FIXED_TIME, base_time + timedelta(days=6), None, 30, None, "https://meet.example.test/bw-hr-room"),
            ],
        },
        {
            "company_name": "NextGen FinTech Solutions",
            "title": "Frontend Engineer (React / TypeScript)",
            "role_category": "Frontend Engineering",
            "location": "Mumbai",
            "employment_type": "Full-time",
            "work_mode": "Hybrid",
            "ctc_lpa": Decimal("9.00"),
            "min_cgpa": Decimal("6.50"),
            "start": base_time - timedelta(days=12),
            "deadline": base_time + timedelta(hours=18),  # CLOSING SOON (within 24h)
            "is_active": True,
            "description": "Fictional frontend role developing transactional fintech UI dashboards with React and Tailwind CSS.",
            "instructions": "Applications closing within 24 hours. Ensure resume is up to date.",
            "departments": ["Computer Applications", "Computer Science and Engineering", "Information Technology", "Electronics and Communication Engineering"],
            "skills": [("React", ProficiencyLevel.INTERMEDIATE), ("TypeScript", ProficiencyLevel.INTERMEDIATE), ("Tailwind CSS", ProficiencyLevel.BEGINNER)],
            "rounds": [
                (1, RoundType.ONLINE_ASSESSMENT, "Modern JavaScript & React Concept Test", ScheduleType.AVAILABILITY_WINDOW, base_time - timedelta(days=5), base_time + timedelta(hours=12), 45, "https://eval.example.test/nextgen-fe-301", None),
                (2, RoundType.TECHNICAL_INTERVIEW, "Component Architecture & State Interview", ScheduleType.FIXED_TIME, base_time + timedelta(days=2), None, 45, None, "https://meet.example.test/nextgen-tech-room"),
            ],
        },
        {
            "company_name": "CyberShield Security Labs",
            "title": "Associate QA & Security Test Engineer",
            "role_category": "Quality Engineering",
            "location": "Chennai",
            "employment_type": "Full-time",
            "work_mode": "On-site",
            "ctc_lpa": Decimal("6.50"),
            "min_cgpa": Decimal("6.00"),
            "start": base_time - timedelta(days=3),
            "deadline": base_time + timedelta(days=8),  # OPEN
            "is_active": True,
            "description": "Fictional automated testing and test verification position.",
            "instructions": "Familiarity with pytest and shell scripting preferred.",
            "departments": ["Computer Applications", "Information Technology", "Electronics and Communication Engineering"],
            "skills": [("Unit Testing", ProficiencyLevel.INTERMEDIATE), ("Python", ProficiencyLevel.BEGINNER), ("Linux / Shell", ProficiencyLevel.BEGINNER)],
            "rounds": [
                (1, RoundType.ONLINE_ASSESSMENT, "QA Fundamentals & Logic Test", ScheduleType.AVAILABILITY_WINDOW, base_time - timedelta(days=1), base_time + timedelta(days=2), 60, "https://eval.example.test/cs-qa-401", None),
                (2, RoundType.TECHNICAL_INTERVIEW, "Test Automation & Tooling Discussion", ScheduleType.FIXED_TIME, base_time + timedelta(days=5), None, 45, None, "https://meet.example.test/cs-tech-room"),
            ],
        },
        {
            "company_name": "DataPulse Analytics",
            "title": "Junior Data Analyst",
            "role_category": "Analytics",
            "location": "Pune",
            "employment_type": "Full-time",
            "work_mode": "Hybrid",
            "ctc_lpa": Decimal("8.00"),
            "min_cgpa": Decimal("7.00"),
            "start": base_time + timedelta(days=3),  # UPCOMING (start in future)
            "deadline": base_time + timedelta(days=20),
            "is_active": True,
            "description": "Fictional entry-level business analytics position working with SQL and analytical dashboards.",
            "instructions": "Applications open next week.",
            "departments": ["Computer Applications", "Computer Science and Engineering", "Information Technology"],
            "skills": [("PostgreSQL", ProficiencyLevel.INTERMEDIATE), ("Python", ProficiencyLevel.BEGINNER)],
            "rounds": [
                (1, RoundType.ONLINE_ASSESSMENT, "SQL & Analytics Screening", ScheduleType.AVAILABILITY_WINDOW, base_time + timedelta(days=4), base_time + timedelta(days=7), 60, "https://eval.example.test/dp-sql-501", None),
            ],
        },
        {
            "company_name": "BlueWave Cloud Systems",
            "title": "Cloud Infrastructure Associate",
            "role_category": "DevOps",
            "location": "Hyderabad",
            "employment_type": "Full-time",
            "work_mode": "On-site",
            "ctc_lpa": Decimal("7.50"),
            "min_cgpa": Decimal("6.50"),
            "start": base_time - timedelta(days=30),
            "deadline": base_time - timedelta(days=3),  # CLOSED (past deadline)
            "is_active": True,
            "description": "Fictional past recruitment drive for cloud support engineers.",
            "instructions": "Drive completed.",
            "departments": ["Computer Science and Engineering", "Information Technology", "Electronics and Communication Engineering"],
            "skills": [("Linux / Shell", ProficiencyLevel.INTERMEDIATE), ("Docker", ProficiencyLevel.BEGINNER)],
            "rounds": [
                (1, RoundType.ONLINE_ASSESSMENT, "Linux & Cloud Screening", ScheduleType.FIXED_TIME, base_time - timedelta(days=20), None, 60, "https://eval.example.test/bw-closed-601", None),
            ],
        },
        {
            "company_name": "Apex Innovations Corp",
            "title": "Junior Mobile Developer (Archived)",
            "role_category": "Mobile Development",
            "location": "Bangalore",
            "employment_type": "Full-time",
            "work_mode": "On-site",
            "ctc_lpa": Decimal("6.00"),
            "min_cgpa": Decimal("6.00"),
            "start": base_time - timedelta(days=10),
            "deadline": base_time + timedelta(days=10),
            "is_active": False,  # INACTIVE (soft-disabled by staff)
            "description": "Fictional deactivated job posting to demonstrate staff archive visibility.",
            "instructions": "Position on hold.",
            "departments": ["Computer Applications"],
            "skills": [("JavaScript", ProficiencyLevel.BEGINNER)],
            "rounds": [],
        },
    ]


# ---------------------------------------------------------------------------
# Seeding Orchestration
# ---------------------------------------------------------------------------


class DemoDataSeeder:
    def __init__(self, session: AsyncSession, demo_password: str, base_time: datetime, dry_run: bool):
        self.db = session
        self.demo_password = demo_password
        self.password_hash = hash_password(demo_password)
        self.base_time = base_time
        self.dry_run = dry_run

        self.stats = {
            "staff_created": 0,
            "departments_verified": 0,
            "skills_created": 0,
            "students_created": 0,
            "student_skills_created": 0,
            "resumes_created": 0,
            "companies_created": 0,
            "jobs_created": 0,
            "job_rounds_created": 0,
            "applications_created": 0,
            "application_rounds_created": 0,
            "placements_created": 0,
        }

        self.dept_cache: Dict[str, Department] = {}
        self.skill_cache: Dict[str, Skill] = {}
        self.company_cache: Dict[str, Company] = {}
        self.job_cache: Dict[str, Job] = {}
        self.student_cache: Dict[str, Student] = {}
        self.user_cache: Dict[str, User] = {}
        self.resume_cache: Dict[int, Resume] = {}  # student_id -> default Resume

    async def seed_staff(self) -> User:
        """Seeds or updates the primary demo staff user."""
        staff_email = f"staff.demo@{SYNTHETIC_DOMAIN}"
        stmt = select(User).where(User.email == staff_email)
        user = (await self.db.scalars(stmt)).first()

        if user is None:
            user = User(
                email=staff_email,
                password_hash=self.password_hash,
                role=RoleEnum.STAFF,
                is_active=True,
            )
            self.db.add(user)
            await self.db.flush()
            self.stats["staff_created"] += 1
            print(f" [+] Created Staff User: {staff_email}")
        else:
            user.role = RoleEnum.STAFF
            user.password_hash = self.password_hash
            user.is_active = True
            print(f" [=] Reusing existing Staff User: {staff_email}")

        self.user_cache[staff_email] = user
        return user

    async def seed_departments(self) -> None:
        """Ensures all standard academic departments exist and are active."""
        for name in DEMO_DEPARTMENTS:
            stmt = select(Department).where(Department.name == name)
            dept = (await self.db.scalars(stmt)).first()
            if dept is None:
                dept = Department(name=name, is_active=True)
                self.db.add(dept)
                await self.db.flush()
                print(f" [+] Created Department: {name}")
            else:
                dept.is_active = True
            self.dept_cache[name] = dept
            self.stats["departments_verified"] += 1

    async def seed_skills(self) -> None:
        """Seeds standard catalog skills idempotently."""
        for name, category in DEMO_SKILLS:
            stmt = select(Skill).where(Skill.name == name)
            skill = (await self.db.scalars(stmt)).first()
            if skill is None:
                skill = Skill(name=name, category=category, is_active=True)
                self.db.add(skill)
                await self.db.flush()
                self.stats["skills_created"] += 1
            else:
                skill.is_active = True
            self.skill_cache[name] = skill

    async def seed_students(self) -> None:
        """Seeds fictional student accounts, profiles, skill inventories, and resumes."""
        upload_root = PROJECT_ROOT / settings.RESUME_UPLOAD_DIR
        upload_root.mkdir(parents=True, exist_ok=True)

        for s_data in DEMO_STUDENTS:
            email = s_data["email"]

            # 1. User Account
            user_stmt = select(User).where(User.email == email)
            user = (await self.db.scalars(user_stmt)).first()
            if user is None:
                user = User(
                    email=email,
                    password_hash=self.password_hash,
                    role=RoleEnum.STUDENT,
                    is_active=True,
                )
                self.db.add(user)
                await self.db.flush()
            else:
                user.password_hash = self.password_hash
            self.user_cache[email] = user

            # 2. Student Profile
            student_stmt = select(Student).where(Student.user_id == user.id)
            student = (await self.db.scalars(student_stmt)).first()
            dept_id = self.dept_cache[s_data["dept"]].id if s_data["dept"] else None

            if student is None:
                student = Student(
                    user_id=user.id,
                    department_id=dept_id,
                    full_name=s_data["full_name"],
                    phone=s_data["phone"],
                    graduation_year=s_data["grad_year"],
                    cgpa=s_data["cgpa"],
                    date_of_birth=s_data["dob"],
                    address=s_data["address"],
                    linkedin_url=s_data["linkedin"],
                    github_url=s_data["github"],
                )
                self.db.add(student)
                await self.db.flush()
                self.stats["students_created"] += 1
            else:
                student.full_name = s_data["full_name"]
                student.department_id = dept_id
                student.cgpa = s_data["cgpa"]
                student.phone = s_data["phone"]
                student.graduation_year = s_data["grad_year"]
                student.date_of_birth = s_data["dob"]
                student.address = s_data["address"]
                student.linkedin_url = s_data["linkedin"]
                student.github_url = s_data["github"]

            self.student_cache[email] = student

            # 3. Student Skills
            for skill_name, proficiency in s_data["skills"]:
                skill_obj = self.skill_cache[skill_name]
                ss_stmt = select(StudentSkill).where(
                    StudentSkill.student_id == student.id,
                    StudentSkill.skill_id == skill_obj.id,
                )
                existing_ss = (await self.db.scalars(ss_stmt)).first()
                if existing_ss is None:
                    ss = StudentSkill(
                        student_id=student.id,
                        skill_id=skill_obj.id,
                        proficiency=proficiency,
                    )
                    self.db.add(ss)
                    self.stats["student_skills_created"] += 1
                else:
                    existing_ss.proficiency = proficiency

            # 4. Resume & Physical File
            if s_data["has_resume"]:
                res_stmt = select(Resume).where(
                    Resume.student_id == student.id,
                    Resume.is_default == True,
                )
                resume = (await self.db.scalars(res_stmt)).first()

                if resume is None:
                    # Write physical synthetic resume file on disk
                    student_dir = upload_root / str(student.id)
                    student_dir.mkdir(parents=True, exist_ok=True)
                    generated_filename = f"{uuid.uuid4().hex}.pdf"
                    physical_file_path = student_dir / generated_filename

                    if not self.dry_run:
                        with open(physical_file_path, "wb") as f:
                            f.write(SYNTHETIC_PDF_BYTES)

                    relative_path = str(physical_file_path.relative_to(upload_root))
                    resume = Resume(
                        student_id=student.id,
                        title=s_data["resume_title"] or "Default Professional Resume",
                        description="Synthetic document created for local platform testing.",
                        file_name=f"{s_data['full_name'].replace(' ', '_')}_Resume.pdf",
                        file_path=relative_path,
                        file_type="application/pdf",
                        file_size=len(SYNTHETIC_PDF_BYTES),
                        is_default=True,
                    )
                    self.db.add(resume)
                    await self.db.flush()
                    self.stats["resumes_created"] += 1

                self.resume_cache[student.id] = resume

    async def seed_companies(self) -> None:
        """Seeds corporate recruiting partners."""
        for c in DEMO_COMPANIES:
            stmt = select(Company).where(Company.name == c["name"])
            comp = (await self.db.scalars(stmt)).first()
            if comp is None:
                comp = Company(
                    name=c["name"],
                    industry=c["industry"],
                    location=c["location"],
                    website=c["website"],
                    description=c["description"],
                    is_active=True,
                )
                self.db.add(comp)
                await self.db.flush()
                self.stats["companies_created"] += 1
            else:
                comp.is_active = True
            self.company_cache[c["name"]] = comp

    async def seed_jobs_and_rounds(self) -> None:
        """Seeds job postings, eligibility criteria, and JobRound templates."""
        job_defs = build_job_definitions(
            self.base_time,
            {k: v.id for k, v in self.dept_cache.items()},
            {k: v.id for k, v in self.skill_cache.items()},
        )

        for jd in job_defs:
            company = self.company_cache[jd["company_name"]]
            stmt = select(Job).where(Job.company_id == company.id, Job.title == jd["title"])
            job = (await self.db.scalars(stmt)).first()

            if job is None:
                job = Job(
                    company_id=company.id,
                    title=jd["title"],
                    role_category=jd["role_category"],
                    location=jd["location"],
                    employment_type=jd["employment_type"],
                    work_mode=jd["work_mode"],
                    ctc_lpa=jd["ctc_lpa"],
                    min_cgpa=jd["min_cgpa"],
                    application_start_at=jd["start"],
                    deadline=jd["deadline"],
                    is_active=jd["is_active"],
                    description=jd["description"],
                    instructions=jd["instructions"],
                )
                self.db.add(job)
                await self.db.flush()
                self.stats["jobs_created"] += 1

                # Eligible Departments
                for dept_name in jd["departments"]:
                    d_obj = self.dept_cache[dept_name]
                    self.db.add(JobEligibleDepartment(job_id=job.id, department_id=d_obj.id))

                # Required Skills
                for skill_name, min_prof in jd["skills"]:
                    s_obj = self.skill_cache[skill_name]
                    self.db.add(JobRequiredSkill(job_id=job.id, skill_id=s_obj.id, min_proficiency=min_prof))

                # Job Round Templates
                for r_num, r_type, r_title, s_type, av_from, av_until, dur, t_link, m_link in jd["rounds"]:
                    jr = JobRound(
                        job_id=job.id,
                        round_number=r_num,
                        round_type=r_type,
                        title=r_title,
                        schedule_type=s_type,
                        available_from=av_from,
                        available_until=av_until,
                        duration_minutes=dur,
                        test_link=t_link,
                        meeting_link=m_link,
                        instructions="Synthetic round instructions for demonstration.",
                        is_required=True,
                        is_active=True,
                    )
                    self.db.add(jr)
                    self.stats["job_rounds_created"] += 1

                await self.db.flush()

            self.job_cache[jd["title"]] = job

    async def seed_applications_and_workflows(self, staff_user: User) -> None:
        """
        Seeds candidate applications, round snapshots, attendance, evaluations,
        and placement records covering varied workflow states.
        """
        job_apex = self.job_cache["Graduate Software Engineer"]
        job_cloud = self.job_cache["Cloud Backend Developer"]
        job_fe = self.job_cache["Frontend Engineer (React / TypeScript)"]
        job_qa = self.job_cache["Associate QA & Security Test Engineer"]

        # Fetch active templates for snapshotting
        apex_rounds = (await self.db.scalars(
            select(JobRound).where(JobRound.job_id == job_apex.id).order_by(JobRound.round_number.asc())
        )).all()

        cloud_rounds = (await self.db.scalars(
            select(JobRound).where(JobRound.job_id == job_cloud.id).order_by(JobRound.round_number.asc())
        )).all()

        fe_rounds = (await self.db.scalars(
            select(JobRound).where(JobRound.job_id == job_fe.id).order_by(JobRound.round_number.asc())
        )).all()

        qa_rounds = (await self.db.scalars(
            select(JobRound).where(JobRound.job_id == job_qa.id).order_by(JobRound.round_number.asc())
        )).all()

        # Application scenarios table:
        # (student_email, job, resume_student_email, target_status, round_plan)
        scenarios = [
            # 1. Aarav Sharma -> Apex Software Engineer -> OFFERED & PLACED (Accepted)
            (
                f"aarav.sharma@{SYNTHETIC_DOMAIN}",
                job_apex,
                apex_rounds,
                ApplicationStatus.OFFERED,
                [
                    (1, StudentAttendance.ATTENDED, StaffVerification.VERIFIED, RoundResult.PASSED),
                    (2, StudentAttendance.ATTENDED, StaffVerification.VERIFIED, RoundResult.PASSED),
                    (3, StudentAttendance.ATTENDED, StaffVerification.VERIFIED, RoundResult.PASSED),
                    (4, StudentAttendance.ATTENDED, StaffVerification.VERIFIED, RoundResult.PASSED),
                ],
                Decimal("12.00"),
                True,  # Placement offer accepted
            ),
            # 2. Diya Patel -> BlueWave Cloud -> OFFERED (Pending / Not yet accepted)
            (
                f"diya.patel@{SYNTHETIC_DOMAIN}",
                job_cloud,
                cloud_rounds,
                ApplicationStatus.OFFERED,
                [
                    (1, StudentAttendance.ATTENDED, StaffVerification.VERIFIED, RoundResult.PASSED),
                    (2, StudentAttendance.ATTENDED, StaffVerification.VERIFIED, RoundResult.PASSED),
                    (3, StudentAttendance.ATTENDED, StaffVerification.VERIFIED, RoundResult.PASSED),
                ],
                Decimal("10.50"),
                False,  # Offer not yet accepted
            ),
            # 3. Rohan Verma -> NextGen Frontend -> IN PROGRESS (Round 1 Passed, Round 2 Scheduled)
            (
                f"rohan.verma@{SYNTHETIC_DOMAIN}",
                job_fe,
                fe_rounds,
                ApplicationStatus.INTERVIEW,
                [
                    (1, StudentAttendance.ATTENDED, StaffVerification.VERIFIED, RoundResult.PASSED),
                    (2, StudentAttendance.NOT_REPORTED, StaffVerification.PENDING, RoundResult.PENDING),
                ],
                None,
                False,
            ),
            # 4. Priya Nair -> Apex Software Engineer -> REJECTED (Failed Round 2)
            (
                f"priya.nair@{SYNTHETIC_DOMAIN}",
                job_apex,
                apex_rounds,
                ApplicationStatus.REJECTED,
                [
                    (1, StudentAttendance.ATTENDED, StaffVerification.VERIFIED, RoundResult.PASSED),
                    (2, StudentAttendance.ATTENDED, StaffVerification.VERIFIED, RoundResult.FAILED),
                ],
                None,
                False,
            ),
            # 5. Vikram Singh -> CyberShield QA -> UNDER REVIEW / ATTENDANCE REPORTED
            (
                f"vikram.singh@{SYNTHETIC_DOMAIN}",
                job_qa,
                qa_rounds,
                ApplicationStatus.INTERVIEW,
                [
                    (1, StudentAttendance.ATTENDED, StaffVerification.PENDING, RoundResult.PENDING),
                    (2, StudentAttendance.NOT_REPORTED, StaffVerification.PENDING, RoundResult.PENDING),
                ],
                None,
                False,
            ),
            # 6. Ananya Iyer -> BlueWave Cloud -> PENDING (Fresh applicant)
            (
                f"ananya.iyer@{SYNTHETIC_DOMAIN}",
                job_cloud,
                cloud_rounds,
                ApplicationStatus.INTERVIEW,
                [
                    (1, StudentAttendance.NOT_REPORTED, StaffVerification.PENDING, RoundResult.PENDING),
                    (2, StudentAttendance.NOT_REPORTED, StaffVerification.PENDING, RoundResult.PENDING),
                    (3, StudentAttendance.NOT_REPORTED, StaffVerification.PENDING, RoundResult.PENDING),
                ],
                None,
                False,
            ),
            # 7. Karthik Rajan -> NextGen Frontend -> WITHDRAWN
            (
                f"karthik.rajan@{SYNTHETIC_DOMAIN}",
                job_fe,
                fe_rounds,
                ApplicationStatus.WITHDRAWN,
                [
                    (1, StudentAttendance.NOT_REPORTED, StaffVerification.PENDING, RoundResult.PENDING),
                ],
                None,
                False,
            ),
        ]

        for s_email, job, tmpl_rounds, app_status, round_outcomes, offer_ctc, offer_accepted in scenarios:
            student = self.student_cache[s_email]
            resume = self.resume_cache.get(student.id)
            if not resume:
                continue

            app_stmt = select(Application).where(
                Application.student_id == student.id,
                Application.job_id == job.id,
            )
            app = (await self.db.scalars(app_stmt)).first()

            if app is None:
                app = Application(
                    student_id=student.id,
                    job_id=job.id,
                    resume_id=resume.id,
                    status=app_status,
                )
                self.db.add(app)
                await self.db.flush()
                self.stats["applications_created"] += 1

                # Create deep snapshots from templates
                for jr in tmpl_rounds:
                    # Match outcome if planned
                    match = next((o for o in round_outcomes if o[0] == jr.round_number), None)
                    att = match[1] if match else StudentAttendance.NOT_REPORTED
                    ver = match[2] if match else StaffVerification.PENDING
                    res = match[3] if match else RoundResult.PENDING

                    r_status = RoundStatus.SCHEDULED
                    if res == RoundResult.PASSED or res == RoundResult.FAILED:
                        r_status = RoundStatus.COMPLETED

                    app_round = ApplicationRound(
                        application_id=app.id,
                        job_round_id=jr.id,  # Isolated snapshot FK with ON DELETE SET NULL
                        round_number=jr.round_number,
                        round_type=jr.round_type,
                        title=jr.title,
                        description=jr.description,
                        schedule_type=jr.schedule_type,
                        available_from=jr.available_from,
                        available_until=jr.available_until,
                        duration_minutes=jr.duration_minutes,
                        meeting_link=jr.meeting_link,
                        test_link=jr.test_link,
                        instructions=jr.instructions,
                        status=r_status,
                        result=res,
                        student_attendance=att,
                        student_action_at=self.base_time - timedelta(days=1) if att != StudentAttendance.NOT_REPORTED else None,
                        staff_verification=ver,
                        staff_verified_at=self.base_time if ver != StaffVerification.PENDING else None,
                        staff_verified_by_id=staff_user.id if ver != StaffVerification.PENDING else None,
                    )
                    self.db.add(app_round)
                    self.stats["application_rounds_created"] += 1

                await self.db.flush()

            # Seed Placement if offered
            if offer_ctc is not None and app.status == ApplicationStatus.OFFERED:
                p_stmt = select(Placement).where(Placement.application_id == app.id)
                placement = (await self.db.scalars(p_stmt)).first()

                if placement is None:
                    placement = Placement(
                        application_id=app.id,
                        final_package_ctc=offer_ctc,
                        placement_date=self.base_time.date() - timedelta(days=2),
                        offer_accepted=offer_accepted,
                    )
                    self.db.add(placement)
                    self.stats["placements_created"] += 1

    async def run(self) -> None:
        """Executes the seeding workflow."""
        print("\n[*] Starting seeding procedure...")
        staff_user = await self.seed_staff()
        await self.seed_departments()
        await self.seed_skills()
        await self.seed_students()
        await self.seed_companies()
        await self.seed_jobs_and_rounds()
        await self.seed_applications_and_workflows(staff_user)

        if self.dry_run:
            await self.db.rollback()
            print("\n[DRY RUN COMPLETED] All changes rolled back. Database remains untouched.")
        else:
            await self.db.commit()
            print("\n[SUCCESS] All synthetic demo records persisted to the local database.")

        self.print_summary()

    def print_summary(self) -> None:
        """Prints a human-readable execution summary."""
        print("\n" + "=" * 70)
        print(" SEEDING EXECUTION SUMMARY")
        print("=" * 70)
        print(f" Demo Staff Accounts Created/Verified: {self.stats['staff_created']}")
        print(f" Academic Departments Verified:         {self.stats['departments_verified']}")
        print(f" Master Catalog Skills Created:         {self.stats['skills_created']}")
        print(f" Student Profiles Created:              {self.stats['students_created']}")
        print(f" Student Skills Assigned:               {self.stats['student_skills_created']}")
        print(f" Synthetic Resumes Uploaded:            {self.stats['resumes_created']}")
        print(f" Partner Companies Created:             {self.stats['companies_created']}")
        print(f" Job Postings Created:                  {self.stats['jobs_created']}")
        print(f" JobRound Templates Created:            {self.stats['job_rounds_created']}")
        print(f" Student Applications Created:          {self.stats['applications_created']}")
        print(f" ApplicationRound Snapshots Created:    {self.stats['application_rounds_created']}")
        print(f" Placement Records Created:             {self.stats['placements_created']}")
        print("=" * 70)
        print("\n[LOCAL DEMO CREDENTIALS]")
        print(f" Staff User:   staff.demo@{SYNTHETIC_DOMAIN}")
        print(f" Student User: aarav.sharma@{SYNTHETIC_DOMAIN}  (Readiness: Strong, Placed)")
        print(f" Student User: rohan.verma@{SYNTHETIC_DOMAIN}   (Readiness: Good, Interview)")
        print(f" Student User: karthik.rajan@{SYNTHETIC_DOMAIN} (Readiness: Developing)")
        print(f" Student User: pooja.das@{SYNTHETIC_DOMAIN}     (Readiness: Needs Improvement)")
        print(f" Shared Demo Password: [SET AT RUNTIME — DO NOT STORE IN GIT]")
        print("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safe, Idempotent Synthetic Demo Data Seeder for Career Compass AI.",
    )
    parser.add_argument(
        "--confirm-local-demo-db",
        action="store_true",
        help="Explicit confirmation required to write synthetic records to the local development database.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution in a rolled-back transaction without saving any changes.",
    )
    parser.add_argument(
        "--demo-password",
        type=str,
        default=None,
        help="Optional demo password for synthetic accounts. If omitted, prompts securely or generates one.",
    )
    parser.add_argument(
        "--base-date",
        type=str,
        default=None,
        help="Base ISO timestamp (e.g. 2026-10-11T12:00:00Z) for deterministic scheduling windows.",
    )
    return parser.parse_args()


async def async_main() -> None:
    args = parse_args()

    # Safety gate: verify target database host and name
    verify_database_safety(args.dry_run, args.confirm_local_demo_db)

    # Determine base demo date
    if args.base_date:
        try:
            base_time = datetime.fromisoformat(args.base_date).replace(tzinfo=timezone.utc)
        except ValueError:
            print("Invalid ISO date format for --base-date. Example: 2026-10-11T12:00:00")
            sys.exit(1)
    else:
        base_time = datetime.now(timezone.utc)

    # Prompt or generate password
    demo_password = args.demo_password
    if not demo_password:
        if sys.stdin.isatty():
            prompted = getpass.getpass("Enter password for synthetic demo accounts (or press Enter to auto-generate): ")
            if prompted.strip():
                demo_password = prompted.strip()

        if not demo_password:
            demo_password = f"Demo_{secrets.token_urlsafe(10)}!"
            print(f"\n[AUTO-GENERATED DEMO PASSWORD]: {demo_password}")
            print("(Note this down for logging into the local UI — it is not saved to disk!)\n")

    async with AsyncSessionLocal() as session:
        seeder = DemoDataSeeder(
            session=session,
            demo_password=demo_password,
            base_time=base_time,
            dry_run=args.dry_run,
        )
        await seeder.run()


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n[ABORTED] Seeding interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()

"""
Development CLI script to create or promote a Staff user.

Usage:
    python scripts/create_staff_user.py [--email EMAIL] [--password PASSWORD]

Default credentials (if omitted):
    Email: staff@example.com
    Password: StaffPassword123
"""

import argparse
import asyncio
import os
import sys

# Add project root to python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.db.session import AsyncSessionLocal
from app.core.security import hash_password
from app.shared.enums import RoleEnum
from app.modules.auth.repository import UserRepository


async def create_staff_user(email: str, password: str) -> None:
    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        existing = await user_repo.get_by_email(email)

        if existing is not None:
            existing.role = RoleEnum.STAFF
            existing.password_hash = hash_password(password)
            existing.is_active = True
            await db.commit()
            print(f"Updated existing user '{email}' to STAFF role with new password.")
        else:
            await user_repo.create(
                email=email,
                password_hash=hash_password(password),
                role=RoleEnum.STAFF,
            )
            await db.commit()
            print(f"Created new STAFF user: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or promote a STAFF user for local development.")
    parser.add_argument("--email", default="staff@example.com", help="Email for staff user")
    parser.add_argument("--password", default="StaffPassword123", help="Password for staff user")
    args = parser.parse_args()

    asyncio.run(create_staff_user(args.email, args.password))


if __name__ == "__main__":
    main()

import asyncio
import argparse
import sys
from uuid import uuid4
from datetime import datetime, timezone

# Add project root to path
sys.path.append('.')

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from sqlalchemy import text


async def create_admin(email: str, full_name: str, password: str):
    if len(password) < 8:
        print("ERROR: Password must be at least 8 characters.")
        sys.exit(1)

    async with AsyncSessionLocal() as db:
        # Check if email already exists
        result = await db.execute(
            text("SELECT id FROM users WHERE email = :email AND is_deleted = false"),
            {"email": email}
        )
        existing = result.fetchone()
        if existing:
            print(f"ERROR: A user with email '{email}' already exists.")
            sys.exit(1)

        user_id = str(uuid4())
        now = datetime.now(timezone.utc)
        hashed = hash_password(password)

        # Insert user
        await db.execute(text("""
            INSERT INTO users (
                id, email, hashed_password, full_name,
                is_active, email_verified_at,
                created_at, updated_at, is_deleted
            ) VALUES (
                :id, :email, :hashed_password, :full_name,
                true, :now,
                :now, :now, false
            )
        """), {
            "id": user_id,
            "email": email,
            "hashed_password": hashed,
            "full_name": full_name,
            "now": now
        })

        # Assign platform_admin role
        await db.execute(text("""
            INSERT INTO user_roles (id, user_id, role, created_at, updated_at, is_deleted)
            VALUES (:role_id, :user_id, 'platform_admin', :now, :now, false)
        """), {
            "role_id": str(uuid4()),
            "user_id": user_id,
            "now": now
        })

        await db.commit()

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  Platform admin created successfully")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  ID:    {user_id}")
        print(f"  Email: {email}")
        print(f"  Name:  {full_name}")
        print("  Role:  platform_admin")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a platform_admin account for Elite Coach AI"
    )
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--name", required=True, help="Admin full name")
    parser.add_argument("--password", required=True, help="Admin password (min 8 chars)")

    args = parser.parse_args()
    asyncio.run(create_admin(args.email, args.name, args.password))
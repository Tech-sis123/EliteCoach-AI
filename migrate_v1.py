import asyncio
from sqlalchemy import text
from app.core.database import engine
from app.core.database import Base
import app.models  # noqa: F401


async def table_exists(conn, table_name: str) -> bool:
    result = await conn.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = :table_name
            );
            """
        ),
        {"table_name": table_name},
    )
    return bool(result.scalar())


def _find_table_by_name(table_name: str):
    for table in Base.metadata.tables.values():
        if table.name == table_name:
            return table
    return None


async def ensure_table_exists(conn, table_name: str) -> bool:
    if await table_exists(conn, table_name):
        return True

    table = _find_table_by_name(table_name)
    if table is None:
        print(f"Table '{table_name}' not found in SQLAlchemy metadata.")
        return False

    print(f"Table '{table_name}' does not exist. Creating it...")
    await conn.run_sync(lambda sync_conn: table.create(bind=sync_conn, checkfirst=True))
    return await table_exists(conn, table_name)

async def migrate():
    print("Ensuring base schema exists...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Checking for missing columns in 'users' table...")
    async with engine.begin() as conn:
        if not await ensure_table_exists(conn, "users"):
            print("Could not ensure 'users' table exists; skipping users patch.")
        else:

            # Columns to check and add if missing
            columns_to_add = {
                "reset_token_hash": "VARCHAR",
                "verification_token_hash": "VARCHAR",
                "phone": "VARCHAR",
                "avatar_url": "VARCHAR",
                "subject_area": "VARCHAR",
                "email_verified_at": "TIMESTAMP WITH TIME ZONE",
                "is_deleted": "BOOLEAN DEFAULT FALSE"
            }

            for column_name, column_type in columns_to_add.items():
                result = await conn.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = :table_name AND column_name = :column_name;
                        """
                    ),
                    {"table_name": "users", "column_name": column_name},
                )
                if not result.fetchone():
                    print(f"Adding column '{column_name}' to 'users' table...")
                    await conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type};"))
                else:
                    print(f"Column '{column_name}' already exists.")

    print("Checking for missing columns in 'escalations' table...")
    async with engine.begin() as conn:
        if not await ensure_table_exists(conn, "escalations"):
            print("Could not ensure 'escalations' table exists; skipping escalations patch.")
        else:
            escalation_columns = {
                "manual_reason": "VARCHAR(500)",
                "resolved_at": "TIMESTAMP WITH TIME ZONE"
            }
            for column_name, column_type in escalation_columns.items():
                result = await conn.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = :table_name AND column_name = :column_name;
                        """
                    ),
                    {"table_name": "escalations", "column_name": column_name},
                )
                if not result.fetchone():
                    print(f"Adding column '{column_name}' to 'escalations' table...")
                    await conn.execute(text(f"ALTER TABLE escalations ADD COLUMN {column_name} {column_type};"))
                else:
                    print(f"Column '{column_name}' already exists.")

    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())

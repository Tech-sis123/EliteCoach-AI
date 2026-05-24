import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    print("Checking for missing columns in 'users' table...")
    async with engine.begin() as conn:
        # Check if reset_token_hash exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='reset_token_hash';
        """))
        if not result.fetchone():
            print("Adding column 'reset_token_hash' to 'users' table...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_hash VARCHAR;"))
        else:
            print("Column 'reset_token_hash' already exists.")

        # Check if verification_token_hash exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='verification_token_hash';
        """))
        if not result.fetchone():
            print("Adding column 'verification_token_hash' to 'users' table...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN verification_token_hash VARCHAR;"))
        else:
            print("Column 'verification_token_hash' already exists.")

    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())

import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    print("Checking for missing columns in 'users' table...")
    async with engine.begin() as conn:
        # Columns to check and add if missing
        columns_to_add = {
            "reset_token_hash": "VARCHAR",
            "verification_token_hash": "VARCHAR",
            "phone": "VARCHAR",
            "avatar_url": "VARCHAR",
            "email_verified_at": "TIMESTAMP WITH TIME ZONE",
            "is_deleted": "BOOLEAN DEFAULT FALSE"
        }
        
        for column_name, column_type in columns_to_add.items():
            result = await conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='{column_name}';
            """))
            if not result.fetchone():
                print(f"Adding column '{column_name}' to 'users' table...")
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type};"))
            else:
                print(f"Column '{column_name}' already exists.")

    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())

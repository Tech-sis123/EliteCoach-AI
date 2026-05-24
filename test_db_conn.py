import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def test_db():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
            print("DB Connection Successful")
    except Exception as e:
        print(f"DB Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())

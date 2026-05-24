import asyncio
import uuid
from app.core.database import engine
from app.services.onboarding import onboarding_service
from app.schemas.learning import OnboardingStart, DiagnosticSubmit
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.users import User
from app.core.security import hash_password

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test_service_logic():
    async with async_session() as db:
        # 1. Create a dummy user
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email=f"test_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password=hash_password("password"),
            full_name="Test User"
        )
        db.add(user)
        await db.commit()
        print(f"User created: {user_id}")

        # 2. Start onboarding
        data = OnboardingStart(
            current_role="Coach",
            years_experience=5,
            career_goal="Master Coach",
            hours_per_week=20
        )
        questions = await onboarding_service.start_onboarding(db, user_id, data)
        print(f"Onboarding started, got {len(questions)} questions")
        
        # 3. Submit diagnostic
        if len(questions) > 0:
            submission = DiagnosticSubmit(
                answers={questions[0].id: "Expert"}
            )
            result = await onboarding_service.submit_diagnostic(db, user_id, submission)
            print(f"Diagnostic submitted, result: {result}")
        else:
            print("No questions found!")

if __name__ == "__main__":
    asyncio.run(test_service_logic())

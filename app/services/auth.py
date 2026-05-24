from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.users import User, UserRole, UserRoleEnum
from app.schemas.users import UserCreate
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from fastapi import HTTPException, status

class AuthService:
    async def register_user(self, db: AsyncSession, user_in: UserCreate):
        query = select(User).where(User.email == user_in.email)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        db_user = User(
            email=user_in.email,
            hashed_password=hash_password(user_in.password),
            full_name=user_in.full_name,
            phone=user_in.phone,
        )
        db.add(db_user)
        await db.flush()
        
        # Default role
        role = UserRole(user_id=db_user.id, role=UserRoleEnum.SOLO_LEARNER)
        db.add(role)
        
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def authenticate_user(self, db: AsyncSession, email: str, password: str):
        query = select(User).where(User.email == email).options(selectinload(User.roles))
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    async def create_tokens_for_user(self, db: AsyncSession, user: User):
        # In a real app, you'd get roles here
        roles = [r.role for r in user.roles]
        access_token = create_access_token(data={"sub": str(user.id), "roles": roles})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Hash and store refresh token in DB (omitted for brevity in skeleton)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

auth_service = AuthService()

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.models.users import User, UserRole, UserRoleEnum, RefreshToken
from app.schemas.users import UserCreate
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from fastapi import HTTPException, status
import hashlib
from datetime import datetime, timedelta
from app.core.config import settings

class AuthService:
    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

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
        roles = [r.role for r in user.roles]
        access_token = create_access_token(data={"sub": str(user.id), "roles": roles})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        token_hash = self._hash_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(db_refresh_token)
        await db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh_access_token(self, db: AsyncSession, refresh_token: str):
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
        
        user_id = payload.get("sub")
        token_hash = self._hash_token(refresh_token)
        
        query = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at == None,
            RefreshToken.expires_at > datetime.utcnow()
        ).options(selectinload(RefreshToken.user).selectinload(User.roles))
        
        result = await db.execute(query)
        db_token = result.scalar_one_or_none()
        
        if not db_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
        
        # Rotate: revoke old, issue new
        db_token.revoked_at = datetime.utcnow()
        await db.commit()
        
        return await self.create_tokens_for_user(db, db_token.user)

    async def logout(self, db: AsyncSession, refresh_token: str):
        token_hash = self._hash_token(refresh_token)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked_at=datetime.utcnow())
        )
        await db.commit()

    async def get_me(self, db: AsyncSession, user_id: str):
        # In this simplified model, org_id is not yet on the user model, 
        # but enterprise memberships might have it. Let's check first.
        query = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # We need to add org_id logic later when we have more context on enterprise
        return user

auth_service = AuthService()

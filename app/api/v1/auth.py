from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.users import UserCreate, UserRead, Token
from app.schemas.auth import RefreshRequest, LogoutRequest, UserMe, ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth import auth_service
from app.api.deps import get_current_user
from app.models.users import User
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

@router.post("/register", response_model=UserRead)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db, user_in)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return await auth_service.create_tokens_for_user(db, user)

@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh_access_token(db, request.refresh_token)

@router.post("/logout")
async def logout(request: LogoutRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await auth_service.logout(db, request.refresh_token)
    return {"detail": "Logged out successfully"}

@router.get("/me", response_model=UserMe)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await auth_service.get_me(db, str(current_user.id))
    return {
        **user.__dict__,
        "roles": [r.role for r in user.roles],
        "org_id": None # Placeholder until enterprise logic is fully integrated
    }

@router.get("/verify-email/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    # TBD: Implementation for email verification
    return {"detail": "Email verified"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    # Security requirement: always return 200
    return {"detail": "If that email exists, a reset link has been sent"}

@router.post("/reset-password/{token}")
async def reset_password(token: str, request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    # TBD: Implementation for password reset
    return {"detail": "Password reset successfully"}

@router.post("/social")
async def social_login(
    provider: str,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Placeholder for Google/LinkedIn OAuth2 exchange."""
    return {"detail": f"Social login with {provider} triggered"}

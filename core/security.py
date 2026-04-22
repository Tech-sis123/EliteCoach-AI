from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
import logging
from services.identity_service_client import identity_service

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(request: Request) -> dict:
    """Extract and validate user from JWT token"""
    
    # Get Authorization header
    authorization: str = request.headers.get("Authorization")
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    # Verify token with identity service
    is_valid = await identity_service.verify_token(token)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get user profile from identity service
    user = await identity_service.get_user_profile(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not retrieve user profile"
        )
    
    return user


async def get_current_learner(request: Request) -> dict:
    """Get current user and verify they are a learner"""
    user = await get_current_user(request)
    
    # Check if user role is learner
    if user.get("role") not in ["learner", "org_admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only learners can access this resource"
        )
    
    return user


async def get_current_tutor(request: Request) -> dict:
    """Get current user and verify they are a tutor"""
    user = await get_current_user(request)
    
    # Check if user role is tutor
    if user.get("role") not in ["tutor", "org_admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors can access this resource"
        )
    
    return user


async def get_current_admin(request: Request) -> dict:
    """Get current user and verify they are an admin"""
    user = await get_current_user(request)
    
    # Check if user role is org_admin or super_admin
    if user.get("role") not in ["org_admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


def get_token_from_request(request: Request) -> Optional[str]:
    """Extract token from Authorization header"""
    authorization: str = request.headers.get("Authorization")
    
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None

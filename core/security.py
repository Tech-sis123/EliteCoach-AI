from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
import logging
from services.identity_service_client import identity_service

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(request: Request) -> dict:
    """Extract and validate user from JWT token"""
    if request.method == "OPTIONS":
        return {}
    
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
    
    # Get user profile from identity service (this validates the token)
    user = await identity_service.get_user_profile(token)
    
    if not user:
        logger.warning(f"Authentication failed: Identity service returned no user for token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    logger.info(f"User authenticated: {user.get('email')} with role: {user.get('role')}")
    return user


async def get_current_learner(request: Request) -> dict:
    """Get current user and verify they are a learner"""
    user = await get_current_user(request)
    
    # Check if user role/type is learner
    # The Identity Service uses 'userType' or 'persona'
    role = user.get("userType") or user.get("persona") or user.get("role")
    
    # RELAXED CHECK: Treat 'tutor' as a learner for access to learning resources,
    # or handle the case where role is None.
    if role and role not in ["learner", "tutor", "org_admin", "super_admin"]:
        logger.warning(f"Permission denied: User {user.get('email')} has insufficient role: {role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Resource access denied (Current role: {role})"
        )
    
    return user


async def get_current_tutor(request: Request) -> dict:
    """Get current user and verify they are a tutor"""
    user = await get_current_user(request)
    
    # Check if user role/type is tutor
    role = user.get("userType") or user.get("role")
    if role and role not in ["tutor", "org_admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only tutors can access this resource (Current role: {role})"
        )
    
    return user


async def get_current_admin(request: Request) -> dict:
    """Get current user and verify they are an admin"""
    user = await get_current_user(request)
    
    # Check if user role/type is org_admin or super_admin
    role = user.get("userType") or user.get("role")
    if role not in ["org_admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Admin access required (Current role: {role})"
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

from fastapi import HTTPException, status, Depends
from typing import List, Optional
from app.models.users import User, UserRoleEnum
import uuid

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: dict = None): # Placeholder for actual auth dependency
        # In a real app, 'user' would be injected by another dependency
        # user_roles = [r.role for r in user.roles]
        # if "platform_admin" in user_roles:
        #     return True
        # if not any(role in self.allowed_roles for role in user_roles):
        #     raise HTTPException(status_code=403, detail="Insufficient role")
        return True

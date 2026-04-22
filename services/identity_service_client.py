from typing import Optional, Dict, Any
import httpx
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class IdentityServiceClient:
    """Client to communicate with the Identity Service microservice"""
    
    def __init__(self):
        self.base_url = settings.IDENTITY_SERVICE_URL
        self.timeout = httpx.Timeout(10.0)
    
    async def get_user_profile(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user profile from identity service"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/profile",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get user profile: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error calling identity service: {str(e)}")
            return None
    
    async def verify_token(self, token: str) -> bool:
        """Verify token with identity service"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/auth/verify-token",
                    headers=headers
                )
                
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return False
    
    async def extract_email_from_token(self, token: str) -> Optional[str]:
        """Extract email from token (can be done locally or with service)"""
        user_profile = await self.get_user_profile(token)
        if user_profile:
            return user_profile.get("email")
        return None
    
    async def register_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create user through identity service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json=user_data
                )
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"Failed to register user: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return None
    
    async def login_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Login user through identity service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={"email": email, "password": password}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to login user: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error logging in user: {str(e)}")
            return None
    
    async def verify_otp(self, email: str, otp: str) -> bool:
        """Verify OTP through identity service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/verify/otp-email",
                    json={"email": email, "otp": otp}
                )
                
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return False
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/auth/refresh",
                    json={"refreshToken": refresh_token}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to refresh token: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None
    
    async def logout_user(self, access_token: str) -> bool:
        """Logout user"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/logout",
                    json={"accessToken": access_token}
                )
                
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error logging out user: {str(e)}")
            return False


# Singleton instance
identity_service = IdentityServiceClient()

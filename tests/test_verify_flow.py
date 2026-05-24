import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.users import User
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_registration_and_verification_flow(client: AsyncClient, db: AsyncSession):
    email = "fakorodehenry@gmail.com"
    password = "securePassword123"
    full_name = "Henry Fakorode"
    
    # 1. Mock the notification service to prevent real email sending
    with patch("app.services.notification.notification_service.send_email") as mock_send:
        mock_send.return_value = None
        
        # 2. Register the user
        response = await client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "phone": "+2348000000000"
        })
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == email
        
        # 3. Try to login BEFORE verification (Should FAIL)
        login_response = await client.post("/api/v1/auth/login", data={
            "username": email,
            "password": password
        })
        assert login_response.status_code == 403
        assert "verify your email" in login_response.json()["detail"]
        
        # 4. Check that the email send was called
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        html_content = kwargs.get("html_content")
        
        # 4. Extract the 4-digit OTP from the mocked email content
        # It's inside a div with 32px font size. We use \s* to handle potential newlines/whitespace
        import re
        otp_match = re.search(r">\s*(\d{4})\s*<", html_content)
        assert otp_match is not None
        otp = otp_match.group(1)
        assert len(otp) == 4
        
        # 5. Verify the email via the API using the OTP
        verify_response = await client.get(f"/api/v1/auth/verify-email/{otp}")
        assert verify_response.status_code == 200
        assert verify_response.json()["detail"] == "Email verified successfully"
        
        # 6. Verify in DB that email_verified_at is set
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one()
        assert user.email_verified_at is not None
        assert user.verification_token_hash is None

        print(f"\n[SUCCESS] User {email} registered and verified with 4-digit OTP.")
        print(f"[OTP] Captured code: {otp}")

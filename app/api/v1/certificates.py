from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.assessment import assessment_service
from app.api.deps import get_current_user
from app.models.users import User
import uuid

router = APIRouter()

@router.get("/me")
async def get_my_certificates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all certificates for the current logged-in user"""
    return await assessment_service.get_user_certificates(db, current_user.id)

@router.get("/{verification_id}")
async def verify_certificate(
    verification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """PUBLIC: Verify a certificate by ID"""
    return await assessment_service.get_certificate_by_verification(db, verification_id)

@router.post("/{id}/download")
async def download_certificate(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.assessments import Certificate
    from sqlalchemy import select
    cert_query = select(Certificate).where(Certificate.id == id)
    cert = (await db.execute(cert_query)).scalar_one_or_none()
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.learner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this certificate")
    
    return {
        "download_url": cert.pdf_url,
        "expires_in_seconds": 3600
    }

@router.post("/{id}/share/linkedin")
async def share_linkedin(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.assessments import Certificate
    from sqlalchemy import select
    cert_query = select(Certificate).where(Certificate.id == id)
    cert = (await db.execute(cert_query)).scalar_one_or_none()
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.learner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this certificate")
    
    return {"share_url": cert.linkedin_share_url or "https://www.linkedin.com/profile/add"}

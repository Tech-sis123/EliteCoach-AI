from fastapi import APIRouter
from app.api.v1 import (
    auth, onboarding, ai_tutor, assessments, tutor_cms, 
    tutor_inbox, enterprise, admin, payments, courses, 
    learning, certificates, notifications, escalations
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(ai_tutor.router, prefix="/ai", tags=["ai"])
api_router.include_router(learning.router, prefix="/learning", tags=["learning"])
api_router.include_router(escalations.router, prefix="/escalations", tags=["escalations"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])
api_router.include_router(tutor_cms.router, prefix="/cms", tags=["cms"])
api_router.include_router(tutor_inbox.router, prefix="/inbox", tags=["inbox"])
api_router.include_router(enterprise.router, prefix="/enterprise", tags=["enterprise"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

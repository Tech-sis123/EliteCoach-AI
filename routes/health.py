from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1",
    tags=["health"]
)


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "learning-service",
        "version": "1.0.0"
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check for k8s/container orchestration"""
    # Add checks for dependencies (DB, RabbitMQ, etc.)
    return {
        "ready": True,
        "service": "learning-service"
    }

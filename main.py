from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from core.config import settings
from core.database import Base, engine
from routes import tutor_sessions, learning_paths, assessments, health

# Create tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(tutor_sessions.router)
app.include_router(learning_paths.router)
app.include_router(assessments.router)

@app.get("/ping")
def ping():
    return {"status": "alive"}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting AI Tutor Engine Service...")
    
    # Seed database with essential records
    try:
        from seed_db import seed_database
        seed_database()
    except Exception as e:
        logger.error(f"Failed to seed database: {e}")
    
    # Connect to RabbitMQ
    from services.event_publisher import event_publisher
    try:
        await event_publisher.connect()
    except Exception as e:
        logger.warning(f"Could not connect to RabbitMQ: {e}")
    
    logger.info("AI Tutor Engine Service started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Tutor Engine Service...")
    
    from services.event_publisher import event_publisher
    await event_publisher.disconnect()
    
    logger.info("AI Tutor Engine Service shut down")

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "AI Tutor Engine",
        "version": settings.API_VERSION,
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3002,
        reload=settings.DEBUG
    )

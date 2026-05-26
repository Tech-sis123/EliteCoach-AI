from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router
import contextlib

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    setup_logging()
    yield
    # Shutdown logic

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    version="0.1.0",
)

# CORS
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "project": settings.PROJECT_NAME}

app.include_router(api_router, prefix=settings.API_V1_STR)

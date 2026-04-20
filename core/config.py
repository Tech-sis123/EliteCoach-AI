from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # API Configuration
    API_TITLE: str = "AI Tutor Engine"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Advanced AI-powered tutoring platform"
    
    # Database
    DATABASE_URL: str = "sqlite:///./tutor.db"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    
    # Identity Service (Microservice)
    IDENTITY_SERVICE_URL: str = "http://localhost:8001"
    
    # JWT Settings (for local token validation if needed)
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://localhost:8001"]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

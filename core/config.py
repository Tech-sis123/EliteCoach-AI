from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # API Configuration
    API_TITLE: str = "AI Tutor Engine"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Advanced AI-powered tutoring platform"
    
    # Database
    DATABASE_URL: str = "sqlite:///./tutor.db"
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqps://fgdhsoso:pryLIv09-J5eYzCw-NjWT41RJEBVQZds@seal.lmq.cloudamqp.com/fgdhsoso"
    RABBITMQ_EXCHANGE: str = "elite-coach-events"
    RABBITMQ_QUEUE: str = "notification-queue"
    RABBITMQ_ROUTING_KEY_PREFIX: str = "learner.#"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    
    # Identity Service (Microservice)
    IDENTITY_SERVICE_URL: str = "http://localhost:8083"
    
    # JWT Settings (for local token validation if needed)
    SECRET_KEY: str = "mysecret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000","https://elite-coach-seven.vercel.app", "http://localhost:8001"]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True


settings = Settings()

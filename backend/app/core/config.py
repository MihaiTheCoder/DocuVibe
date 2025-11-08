"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database - Azure PostgreSQL compatible
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://vibedocs:password@localhost:5432/vibedocs"
    )

    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # Qdrant - Azure App Service compatible
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_HTTPS: bool = os.getenv("QDRANT_HTTPS", "false").lower() == "true"
    QDRANT_API_KEY: Optional[str] = None

    @property
    def QDRANT_URL(self) -> str:
        """Build Qdrant URL from components"""
        protocol = "https" if self.QDRANT_HTTPS else "http"
        return f"{protocol}://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

    # Azure Blob Storage (replaces MinIO for Azure deployments)
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    AZURE_STORAGE_CONTAINER: str = "documents"

    # MinIO (for local development)
    MINIO_URL: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "vibedocs"

    # Use Azure Blob Storage if connection string is provided, otherwise MinIO
    USE_AZURE_STORAGE: bool = bool(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_REPO: str = "yourusername/vibedocs"
    LAZY_BIRD_API_URL: str = "https://api.lazy-bird.com"
    LAZY_BIRD_API_KEY: Optional[str] = None

    # Mistral OCR
    MISTRAL_OCR_URL: str = "http://localhost:8080"
    MISTRAL_OCR_API_KEY: Optional[str] = None

    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Environment
    ENVIRONMENT: str = "development"

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "VibeDocs"

    # Worker configuration
    DOCUMENT_WORKERS_COUNT: int = int(os.getenv("DOCUMENT_WORKERS_COUNT", "2"))
    WORKER_POLL_INTERVAL: int = int(os.getenv("WORKER_POLL_INTERVAL", "5"))  # seconds
    WORKER_LOCK_DURATION: int = int(os.getenv("WORKER_LOCK_DURATION", "300"))  # seconds

    # CORS - Allow all origins for dev/test
    BACKEND_CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
"""
VibeDocs - Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # Startup
    print("Starting VibeDocs Backend...")
    try:
        await init_db()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Continuing without database for hello world demo...")

    yield

    # Shutdown
    print("Shutting down VibeDocs Backend...")


app = FastAPI(
    title="VibeDocs API",
    description="AI-Powered Document Management for Romanian Hospitals",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Configuration - Allow all origins for dev/test
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth_router, prefix=settings.API_V1_STR)
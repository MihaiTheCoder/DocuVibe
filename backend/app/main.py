"""
VibeDocs - Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.auth import auth_router
from app.api.documents import documents_router
from app.api.organizations import organizations_router
from app.api.chat import chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # Startup
    print("Starting VibeDocs Backend...")
    await init_db()

    yield

    # Shutdown
    print("Shutting down VibeDocs Backend...")


app = FastAPI(
    title="VibeDocs API",
    description="AI-Powered Document Management for Romanian Hospitals",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents_router.router, prefix="/api/documents", tags=["Documents"])
app.include_router(organizations_router.router, prefix="/api/organizations", tags=["Organizations"])
app.include_router(chat_router.router, prefix="/api/chat", tags=["Chat"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "VibeDocs API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
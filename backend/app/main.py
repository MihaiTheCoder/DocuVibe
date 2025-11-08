"""
VibeDocs - Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.services.qdrant_service import qdrant_service
from app.workers.manager import worker_manager
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router
from app.api.routes.pipelines import router as pipelines_router
from app.api.routes.workflows import router as workflows_router
from app.api.routes.chat import router as chat_router
from app.api.routes.search import router as search_router
from app.api.routes.registry import router as registry_router
from app.api.routes.jobs import router as jobs_router


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

    # Initialize Qdrant service
    try:
        await qdrant_service.initialize()
    except Exception as e:
        print(f"Warning: Qdrant initialization failed: {e}")
        print("Search features may be limited without Qdrant...")

    # Start document processing workers
    try:
        num_workers = settings.DOCUMENT_WORKERS_COUNT
        if num_workers > 0:
            await worker_manager.start_workers(num_workers)
            print(f"Started {num_workers} document processing workers")
        else:
            print("Document processing workers disabled")
    except Exception as e:
        print(f"Warning: Failed to start workers: {e}")

    yield

    # Shutdown
    print("Shutting down VibeDocs Backend...")

    # Stop workers
    if worker_manager.running:
        await worker_manager.stop_workers()
        print("Document processing workers stopped")


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
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(pipelines_router, prefix=settings.API_V1_STR)
app.include_router(workflows_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(search_router, prefix=settings.API_V1_STR)
app.include_router(registry_router, prefix=settings.API_V1_STR)
app.include_router(jobs_router, prefix=settings.API_V1_STR)
"""
Health Check and Hello World Endpoints
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/")
async def hello_world():
    """
    Hello World endpoint - confirms backend is running

    Returns:
        dict: Welcome message with timestamp and status
    """
    return {
        "message": "Hello World from VibeDocs Backend!",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy"
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring

    Returns:
        dict: Service health status and version
    """
    return {
        "status": "healthy",
        "service": "VibeDocs API",
        "version": "0.1.0"
    }

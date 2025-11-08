"""
Processing Job Schemas

Pydantic models for processing job requests and responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.processing_job import JobStatus, JobType


class JobStatusResponse(BaseModel):
    """Response model for job status"""

    id: UUID
    job_type: JobType
    status: JobStatus
    document_id: UUID
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None
    retry_count: int = 0
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Response model for list of jobs"""

    jobs: list[JobStatusResponse]
    total: int
    pending_count: int
    processing_count: int
    completed_count: int
    failed_count: int

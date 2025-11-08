"""
Processing Jobs API Routes

Endpoints for managing and monitoring processing jobs.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.utils.auth import get_current_user
from app.middleware.organization import get_current_organization
from app.models.user import User
from app.models.organization import Organization
from app.models.processing_job import ProcessingJob, JobStatus
from app.schemas.processing_job import JobStatusResponse, JobListResponse


router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization)
) -> JobStatusResponse:
    """Get status of a specific processing job"""

    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    job = db.query(ProcessingJob).filter(
        ProcessingJob.id == job_uuid,
        ProcessingJob.organization_id == organization.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse.from_orm(job)


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    status: Optional[JobStatus] = None,
    document_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization)
) -> JobListResponse:
    """List processing jobs with optional filters"""

    # Base query
    query = db.query(ProcessingJob).filter(
        ProcessingJob.organization_id == organization.id
    )

    # Apply filters
    if status:
        query = query.filter(ProcessingJob.status == status)

    if document_id:
        try:
            doc_uuid = UUID(document_id)
            query = query.filter(ProcessingJob.document_id == doc_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document ID format")

    # Get total count
    total = query.count()

    # Get status counts
    status_counts = db.query(
        ProcessingJob.status,
        func.count(ProcessingJob.id)
    ).filter(
        ProcessingJob.organization_id == organization.id
    ).group_by(ProcessingJob.status).all()

    status_dict = {status.value: 0 for status in JobStatus}
    for status, count in status_counts:
        status_dict[status.value] = count

    # Get jobs with pagination
    jobs = query.order_by(ProcessingJob.created_at.desc()).limit(limit).offset(offset).all()

    return JobListResponse(
        jobs=[JobStatusResponse.from_orm(job) for job in jobs],
        total=total,
        pending_count=status_dict[JobStatus.PENDING.value],
        processing_count=status_dict[JobStatus.PROCESSING.value],
        completed_count=status_dict[JobStatus.COMPLETED.value],
        failed_count=status_dict[JobStatus.FAILED.value]
    )


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization)
) -> dict:
    """Cancel a pending or processing job"""

    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    job = db.query(ProcessingJob).filter(
        ProcessingJob.id == job_uuid,
        ProcessingJob.organization_id == organization.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job in {job.status} status"
        )

    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.utcnow()

    db.commit()

    return {"message": f"Job {job_id} cancelled successfully"}

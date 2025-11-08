"""
Processing Job Model

Tracks document processing jobs and their state.
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Enum, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.models.base import TenantModel


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    DOCUMENT_PROCESSING = "document_processing"
    DOCUMENT_REPROCESSING = "document_reprocessing"
    BULK_PROCESSING = "bulk_processing"


class ProcessingJob(TenantModel):
    __tablename__ = "processing_jobs"

    # Job identification
    job_type = Column(Enum(JobType), default=JobType.DOCUMENT_PROCESSING, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)

    # Related entities
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("pipelines.id"), nullable=True)

    # Processing metadata
    priority = Column(Integer, default=0)  # Higher number = higher priority
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Worker tracking
    worker_id = Column(String(100), nullable=True)  # ID of worker processing this job
    locked_at = Column(DateTime(timezone=True), nullable=True)  # When job was locked for processing
    lock_expires_at = Column(DateTime(timezone=True), nullable=True)  # Lock expiration for stuck jobs

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_ms = Column(BigInteger, nullable=True)

    # Results and errors
    result = Column(Text, nullable=True)  # JSON result data
    error_message = Column(Text, nullable=True)
    error_details = Column(Text, nullable=True)  # Stack trace or detailed error info

    # Relationships
    document = relationship("Document", back_populates="processing_jobs")
    pipeline = relationship("Pipeline", back_populates="processing_jobs")

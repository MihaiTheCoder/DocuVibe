# Document Ingestion with Async Processing Implementation Plan

## Overview

Implement a document ingestion system with asynchronous processing using PostgreSQL as the job queue. The system will handle document upload from the UI, save to blob storage, and process documents asynchronously using background workers that poll the database for pending jobs.

## Current State Analysis

Based on research of the codebase:

### What Already Exists:
- **Document Model** (`backend/app/models/document.py`): Has `status` field (pending, processing, ready, failed) for tracking processing state
- **Pipeline Model** (`backend/app/models/pipeline.py`): Database model for tracking different processing pipelines
- **Upload Endpoint** (`backend/app/api/routes/documents.py:40`): Fully functional, saves to blob storage and creates document with status="pending"
- **Blob Storage Service** (`backend/app/services/blob_storage.py`): Working Azure blob storage integration
- **Base Pipeline Class** (`backend/app/pipelines/base.py`): Abstract base class defining pipeline interface
- **Task Model** (`backend/app/models/task.py`): Available but not used for async processing yet
- **Reprocess Endpoint** (`backend/app/api/routes/documents.py:476`): Has TODO comment for background job trigger

### What's Missing:
- Background workers for processing documents
- Concrete pipeline implementations (PDF, image)
- Polling mechanism for job processing
- Job tracking and error handling
- Worker configuration system

### Key Discoveries:
- Document status field can serve as our job queue state tracker
- Pipeline registry pattern already exists for managing different pipelines
- Organization-based multi-tenancy is properly implemented
- Blob storage names are prefixed with organization_id for isolation

## Desired End State

A fully functional async document processing system where:
1. Users upload documents through the UI
2. Documents are immediately saved to blob storage with status="pending"
3. Background workers poll the database for pending documents
4. Workers process documents based on file type using appropriate pipelines
5. Processing results are saved back to the document record
6. System is easily extensible with new pipeline types

### Verification Criteria:
- Document upload returns immediately with job tracking info
- Background workers process documents within 5-10 seconds
- Failed processing is properly tracked with error messages
- Multiple workers can run concurrently without conflicts
- New pipeline types can be added with minimal code changes

## What We're NOT Doing

- External message queue systems (Redis, RabbitMQ, etc.)
- Complex job scheduling or priority systems
- Real-time processing notifications (WebSockets)
- Retry mechanisms with exponential backoff (simple retry only)
- Distributed locking beyond database row locks

## Implementation Approach

Use PostgreSQL as a simple job queue with polling workers that:
1. Select pending documents with row-level locking
2. Process documents using registered pipelines
3. Update document status and results
4. Handle errors gracefully

## Phase 1: Create Job Processing Table and Model

### Overview
Add a dedicated job processing table to track document processing jobs with proper state management and error tracking.

### Changes Required:

#### 1. Create ProcessingJob Model
**File**: `backend/app/models/processing_job.py` (new)
**Changes**: Create new model for job tracking

```python
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
```

#### 2. Update Document Model
**File**: `backend/app/models/document.py`
**Changes**: Add relationship to processing jobs

```python
# Add to imports
from sqlalchemy.orm import relationship

# Add to Document class
processing_jobs = relationship("ProcessingJob", back_populates="document", cascade="all, delete-orphan")
```

#### 3. Update Pipeline Model
**File**: `backend/app/models/pipeline.py`
**Changes**: Add relationship to processing jobs

```python
# Add to Pipeline class
processing_jobs = relationship("ProcessingJob", back_populates="pipeline", cascade="all, delete-orphan")
```

#### 4. Create Database Migration
**File**: `backend/migrations/versions/002_add_processing_jobs.py` (new)
**Changes**: Alembic migration for new table

```python
"""Add processing jobs table

Revision ID: 002
Revises: 001_initial_migration
Create Date: 2025-11-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    job_status = postgresql.ENUM('pending', 'processing', 'completed', 'failed', 'cancelled', name='jobstatus')
    job_type = postgresql.ENUM('document_processing', 'document_reprocessing', 'bulk_processing', name='jobtype')

    job_status.create(op.get_bind())
    job_type.create(op.get_bind())

    # Create processing_jobs table
    op.create_table('processing_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('job_type', job_type, nullable=False, default='document_processing'),
        sa.Column('status', job_status, nullable=False, default='pending'),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipelines.id'), nullable=True),
        sa.Column('priority', sa.Integer(), default=0),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('max_retries', sa.Integer(), default=3),
        sa.Column('worker_id', sa.String(100), nullable=True),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lock_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_ms', sa.BigInteger(), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True)
    )

    # Create indexes for efficient polling
    op.create_index('idx_processing_jobs_status_priority', 'processing_jobs', ['status', 'priority', 'created_at'])
    op.create_index('idx_processing_jobs_organization_status', 'processing_jobs', ['organization_id', 'status'])
    op.create_index('idx_processing_jobs_document_id', 'processing_jobs', ['document_id'])
    op.create_index('idx_processing_jobs_locked_at', 'processing_jobs', ['locked_at', 'lock_expires_at'])


def downgrade() -> None:
    op.drop_table('processing_jobs')

    # Drop enum types
    job_status = postgresql.ENUM('pending', 'processing', 'completed', 'failed', 'cancelled', name='jobstatus')
    job_type = postgresql.ENUM('document_processing', 'document_reprocessing', 'bulk_processing', name='jobtype')

    job_status.drop(op.get_bind())
    job_type.drop(op.get_bind())
```

### Success Criteria:

#### Automated Verification:
- [ ] Migration applies cleanly: `cd backend && alembic upgrade head`
- [ ] Models import without errors: `cd backend && python -c "from app.models.processing_job import ProcessingJob"`
- [ ] No linting errors: `cd backend && ruff check app/models/`

#### Manual Verification:
- [ ] ProcessingJob table created in database with all columns
- [ ] Indexes created for efficient polling
- [ ] Relationships work correctly between Document, Pipeline, and ProcessingJob

---

## Phase 2: Implement Worker Infrastructure

### Overview
Create the background worker system that polls for jobs and processes them.

### Changes Required:

#### 1. Create Worker Base Class
**File**: `backend/app/workers/base_worker.py` (new)
**Changes**: Base class for all workers

```python
"""
Base Worker Class

Provides common functionality for background workers.
"""

import asyncio
import logging
import signal
import sys
import uuid
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from abc import ABC, abstractmethod
import traceback

from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.processing_job import ProcessingJob, JobStatus
from app.models.document import Document


class BaseWorker(ABC):
    """Base class for background workers that process jobs from the database queue"""

    def __init__(
        self,
        worker_id: Optional[str] = None,
        poll_interval: int = 5,
        lock_duration: int = 300,  # 5 minutes
        batch_size: int = 1
    ):
        """
        Initialize worker

        Args:
            worker_id: Unique identifier for this worker instance
            poll_interval: Seconds between polling attempts
            lock_duration: Seconds to hold lock on job
            batch_size: Number of jobs to process at once
        """
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.poll_interval = poll_interval
        self.lock_duration = lock_duration
        self.batch_size = batch_size
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.worker_id}")
        self.running = False
        self._tasks = set()

    @abstractmethod
    async def process_job(self, job: ProcessingJob, db: Session) -> Dict[str, Any]:
        """
        Process a single job

        Args:
            job: The job to process
            db: Database session

        Returns:
            Dict with processing results

        Raises:
            Exception: If processing fails
        """
        pass

    @abstractmethod
    def can_process_job(self, job: ProcessingJob) -> bool:
        """
        Check if this worker can process the given job

        Args:
            job: The job to check

        Returns:
            True if worker can process this job type
        """
        pass

    async def claim_job(self, db: Session) -> Optional[ProcessingJob]:
        """
        Claim a pending job from the queue using pessimistic locking

        Returns:
            Claimed job or None if no jobs available
        """
        try:
            # Use a transaction with row-level locking
            now = datetime.utcnow()
            lock_expires = now + timedelta(seconds=self.lock_duration)

            # Query for available jobs
            # - Status is PENDING
            # - OR status is PROCESSING but lock expired (handle stuck jobs)
            # - Order by priority (desc) then created_at (asc)
            stmt = (
                select(ProcessingJob)
                .where(
                    or_(
                        ProcessingJob.status == JobStatus.PENDING,
                        and_(
                            ProcessingJob.status == JobStatus.PROCESSING,
                            ProcessingJob.lock_expires_at < now
                        )
                    )
                )
                .order_by(
                    ProcessingJob.priority.desc(),
                    ProcessingJob.created_at.asc()
                )
                .limit(1)
                .with_for_update(skip_locked=True)  # Skip locked rows
            )

            result = db.execute(stmt)
            job = result.scalar_one_or_none()

            if job and self.can_process_job(job):
                # Claim the job
                job.status = JobStatus.PROCESSING
                job.worker_id = self.worker_id
                job.locked_at = now
                job.lock_expires_at = lock_expires
                job.started_at = now
                db.commit()

                self.logger.info(f"Claimed job {job.id} for document {job.document_id}")
                return job

            return None

        except Exception as e:
            self.logger.error(f"Error claiming job: {e}")
            db.rollback()
            return None

    async def complete_job(self, job: ProcessingJob, result: Dict[str, Any], db: Session):
        """Mark job as completed with results"""
        try:
            now = datetime.utcnow()
            processing_time = (now - job.started_at).total_seconds() * 1000 if job.started_at else 0

            job.status = JobStatus.COMPLETED
            job.completed_at = now
            job.processing_time_ms = int(processing_time)
            job.result = str(result) if result else None
            job.error_message = None
            job.error_details = None

            db.commit()
            self.logger.info(f"Completed job {job.id} in {processing_time:.2f}ms")

        except Exception as e:
            self.logger.error(f"Error completing job {job.id}: {e}")
            db.rollback()
            raise

    async def fail_job(self, job: ProcessingJob, error: Exception, db: Session):
        """Mark job as failed with error details"""
        try:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(error)
            job.error_details = traceback.format_exc()
            job.retry_count += 1

            # If retries available, reset to pending
            if job.retry_count < job.max_retries:
                job.status = JobStatus.PENDING
                job.worker_id = None
                job.locked_at = None
                job.lock_expires_at = None
                self.logger.warning(f"Job {job.id} failed, will retry ({job.retry_count}/{job.max_retries})")
            else:
                self.logger.error(f"Job {job.id} failed after {job.retry_count} retries: {error}")

            db.commit()

        except Exception as e:
            self.logger.error(f"Error failing job {job.id}: {e}")
            db.rollback()

    async def process_loop(self):
        """Main processing loop"""
        self.logger.info(f"Worker {self.worker_id} starting processing loop")

        while self.running:
            try:
                # Get a database session
                db = SessionLocal()
                try:
                    # Try to claim a job
                    job = await self.claim_job(db)

                    if job:
                        try:
                            # Process the job
                            result = await self.process_job(job, db)
                            await self.complete_job(job, result, db)

                        except Exception as e:
                            self.logger.error(f"Error processing job {job.id}: {e}")
                            await self.fail_job(job, e, db)

                finally:
                    db.close()

                # Wait before next poll
                await asyncio.sleep(self.poll_interval)

            except Exception as e:
                self.logger.error(f"Unexpected error in processing loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def start(self):
        """Start the worker"""
        self.logger.info(f"Starting worker {self.worker_id}")
        self.running = True

        # Create processing task
        task = asyncio.create_task(self.process_loop())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def stop(self):
        """Stop the worker gracefully"""
        self.logger.info(f"Stopping worker {self.worker_id}")
        self.running = False

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self.logger.info(f"Worker {self.worker_id} stopped")

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(sig, frame):
            self.logger.info(f"Received signal {sig}, shutting down...")
            self.running = False
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
```

#### 2. Create Document Processing Worker
**File**: `backend/app/workers/document_worker.py` (new)
**Changes**: Worker specifically for document processing

```python
"""
Document Processing Worker

Processes document jobs using registered pipelines.
"""

import logging
from typing import Dict, Any
from pathlib import Path
import tempfile

from sqlalchemy.orm import Session

from app.workers.base_worker import BaseWorker
from app.models.processing_job import ProcessingJob, JobType
from app.models.document import Document
from app.pipelines.registry import pipeline_registry
from app.services.blob_storage import blob_storage
from app.pipelines.base import DocumentMetadata, ProcessingResult


class DocumentProcessingWorker(BaseWorker):
    """Worker that processes document jobs"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = logging.getLogger(f"DocumentWorker.{self.worker_id}")

    def can_process_job(self, job: ProcessingJob) -> bool:
        """Check if this worker can process document jobs"""
        return job.job_type in [
            JobType.DOCUMENT_PROCESSING,
            JobType.DOCUMENT_REPROCESSING
        ]

    async def process_job(self, job: ProcessingJob, db: Session) -> Dict[str, Any]:
        """
        Process a document job

        Args:
            job: The processing job
            db: Database session

        Returns:
            Processing results
        """
        # Get the document
        document = db.query(Document).filter(Document.id == job.document_id).first()
        if not document:
            raise ValueError(f"Document {job.document_id} not found")

        self.logger.info(f"Processing document {document.id} ({document.filename})")

        # Update document status
        document.status = "processing"
        document.processing_started_at = job.started_at
        db.commit()

        try:
            # Get the appropriate pipeline
            pipeline = pipeline_registry.get_pipeline(document.file_type)
            if not pipeline:
                raise ValueError(f"No pipeline found for file type: {document.file_type}")

            # Download document from blob storage to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(document.filename).suffix) as tmp_file:
                # Download blob content
                blob_name = document.blob_url.split('/')[-1]  # Extract blob name from URL
                blob_content = await blob_storage.download_document(blob_name)
                tmp_file.write(blob_content)
                tmp_file_path = tmp_file.name

            try:
                # Prepare metadata for pipeline
                metadata = DocumentMetadata(
                    organization_id=str(document.organization_id),
                    user_id=str(document.uploaded_by_id) if document.uploaded_by_id else None,
                    filename=document.filename,
                    file_type=document.file_type,
                    file_size=document.file_size,
                    custom_metadata=document.doc_metadata or {}
                )

                # Process with pipeline
                result: ProcessingResult = await pipeline.process(tmp_file_path, metadata)

                if result.success:
                    # Update document with results
                    document.status = "ready"
                    document.text_content = result.text_content
                    document.extracted_fields = result.extracted_fields
                    document.classification = result.classification

                    # Store embeddings in metadata for now (later move to Qdrant)
                    if result.embeddings:
                        if not document.doc_metadata:
                            document.doc_metadata = {}
                        document.doc_metadata["embeddings"] = result.embeddings

                    # Update pipeline reference
                    if job.pipeline_id:
                        document.pipeline_id = job.pipeline_id

                    document.processing_completed_at = job.completed_at
                    document.error_message = None

                    self.logger.info(f"Successfully processed document {document.id}")

                else:
                    # Processing failed
                    document.status = "failed"
                    document.error_message = result.error_message
                    document.processing_completed_at = job.completed_at

                    self.logger.warning(f"Pipeline processing failed for document {document.id}: {result.error_message}")

                db.commit()

                return {
                    "success": result.success,
                    "classification": result.classification,
                    "extracted_fields_count": len(result.extracted_fields) if result.extracted_fields else 0,
                    "text_length": len(result.text_content) if result.text_content else 0
                }

            finally:
                # Clean up temp file
                Path(tmp_file_path).unlink(missing_ok=True)

        except Exception as e:
            # Update document status on error
            document.status = "failed"
            document.error_message = str(e)
            db.commit()
            raise
```

#### 3. Update Blob Storage Service
**File**: `backend/app/services/blob_storage.py`
**Changes**: Add download method

```python
# Add to BlobStorageService class

async def download_document(self, blob_name: str) -> bytes:
    """
    Download a document from blob storage

    Args:
        blob_name: Name/path of the blob

    Returns:
        Document content as bytes

    Raises:
        NotImplementedError: If storage backend not configured
        Exception: If download fails
    """
    if not self.use_azure:
        raise NotImplementedError("Local storage not yet implemented")

    try:
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )

        # Download blob content
        blob_data = blob_client.download_blob()
        content = blob_data.readall()

        return content

    except Exception as e:
        logger.error(f"Failed to download blob {blob_name}: {str(e)}")
        raise
```

### Success Criteria:

#### Automated Verification:
- [ ] Worker modules import correctly: `cd backend && python -c "from app.workers.document_worker import DocumentProcessingWorker"`
- [ ] No linting errors: `cd backend && ruff check app/workers/`
- [ ] Type checking passes: `cd backend && mypy app/workers/`

#### Manual Verification:
- [ ] Worker can claim jobs from database
- [ ] Pessimistic locking prevents duplicate processing
- [ ] Failed jobs are retried up to max_retries
- [ ] Worker handles errors gracefully

---

## Phase 3: Implement Pipeline Implementations

### Overview
Create concrete pipeline implementations for PDF and image processing.

### Changes Required:

#### 1. Create Mock Pipeline for Initial Testing
**File**: `backend/app/pipelines/mock_pipeline.py` (new)
**Changes**: Simple pipeline for testing worker infrastructure

```python
"""
Mock Pipeline

Simple pipeline implementation for testing the worker infrastructure.
"""

import asyncio
import random
from typing import Optional
from pathlib import Path

from app.pipelines.base import DocumentPipeline, DocumentMetadata, ProcessingResult


class MockPipeline(DocumentPipeline):
    """Mock pipeline that simulates document processing"""

    def __init__(self):
        super().__init__("mock")

    async def process(
        self,
        file_path: str,
        metadata: DocumentMetadata
    ) -> ProcessingResult:
        """
        Simulate document processing

        Args:
            file_path: Path to the document file
            metadata: Document metadata

        Returns:
            Processing result
        """
        # Simulate processing time
        await asyncio.sleep(random.uniform(1, 3))

        # Read file size for simulation
        file_size = Path(file_path).stat().st_size

        # Simulate text extraction
        text_content = f"Mock extracted text from {metadata.filename}. File size: {file_size} bytes."

        # Simulate classification based on filename
        classification = "unknown"
        filename_lower = metadata.filename.lower()
        if "invoice" in filename_lower or "factura" in filename_lower:
            classification = "invoice"
        elif "contract" in filename_lower:
            classification = "contract"
        elif "receipt" in filename_lower or "bon" in filename_lower:
            classification = "receipt"

        # Simulate field extraction
        extracted_fields = {
            "mock_field_1": "value_1",
            "mock_field_2": "value_2",
            "file_size": file_size,
            "processing_pipeline": "mock"
        }

        # Simulate embeddings (random vector)
        embeddings = [random.random() for _ in range(384)]  # 384-dimension vector

        # Randomly fail 10% of the time for testing
        if random.random() < 0.1:
            return ProcessingResult(
                success=False,
                text_content=None,
                extracted_fields=None,
                classification=None,
                embeddings=None,
                error_message="Mock processing failure for testing"
            )

        return ProcessingResult(
            success=True,
            text_content=text_content,
            extracted_fields=extracted_fields,
            classification=classification,
            embeddings=embeddings,
            error_message=None
        )

    def supports_type(self, file_type: str) -> bool:
        """Check if this pipeline supports the file type"""
        # Support all file types for testing
        return True
```

#### 2. Create PDF Pipeline Skeleton
**File**: `backend/app/pipelines/pdf_pipeline.py` (new)
**Changes**: PDF processing pipeline (skeleton for now)

```python
"""
PDF Pipeline

Processes PDF documents using OCR and text extraction.
"""

import logging
from typing import Optional
from pathlib import Path

from app.pipelines.base import DocumentPipeline, DocumentMetadata, ProcessingResult


logger = logging.getLogger(__name__)


class PDFPipeline(DocumentPipeline):
    """Pipeline for processing PDF documents"""

    def __init__(self):
        super().__init__("pdf")

    async def process(
        self,
        file_path: str,
        metadata: DocumentMetadata
    ) -> ProcessingResult:
        """
        Process a PDF document

        Args:
            file_path: Path to the PDF file
            metadata: Document metadata

        Returns:
            Processing result
        """
        try:
            # TODO: Implement actual PDF processing
            # 1. Try to extract text directly from PDF
            # 2. If no text or minimal text, use OCR
            # 3. Extract structured fields based on classification
            # 4. Generate embeddings

            # For now, use mock processing
            text_content = f"PDF content from {metadata.filename} (not yet implemented)"

            return ProcessingResult(
                success=True,
                text_content=text_content,
                extracted_fields={"source": "pdf_pipeline"},
                classification="document",
                embeddings=None,
                error_message=None
            )

        except Exception as e:
            logger.error(f"Error processing PDF {metadata.filename}: {e}")
            return ProcessingResult(
                success=False,
                text_content=None,
                extracted_fields=None,
                classification=None,
                embeddings=None,
                error_message=str(e)
            )

    def supports_type(self, file_type: str) -> bool:
        """Check if this pipeline supports PDF files"""
        return file_type in ["application/pdf", "pdf"]
```

#### 3. Create Image Pipeline Skeleton
**File**: `backend/app/pipelines/image_pipeline.py` (new)
**Changes**: Image processing pipeline (skeleton for now)

```python
"""
Image Pipeline

Processes image documents (PNG, JPG) using OCR.
"""

import logging
from typing import Optional
from pathlib import Path

from app.pipelines.base import DocumentPipeline, DocumentMetadata, ProcessingResult


logger = logging.getLogger(__name__)


class ImagePipeline(DocumentPipeline):
    """Pipeline for processing image documents"""

    def __init__(self):
        super().__init__("image")

    async def process(
        self,
        file_path: str,
        metadata: DocumentMetadata
    ) -> ProcessingResult:
        """
        Process an image document

        Args:
            file_path: Path to the image file
            metadata: Document metadata

        Returns:
            Processing result
        """
        try:
            # TODO: Implement actual image processing
            # 1. Preprocess image (resize, denoise, etc.)
            # 2. Run OCR to extract text
            # 3. Extract structured fields based on classification
            # 4. Generate embeddings

            # For now, use mock processing
            text_content = f"Image content from {metadata.filename} (not yet implemented)"

            return ProcessingResult(
                success=True,
                text_content=text_content,
                extracted_fields={"source": "image_pipeline"},
                classification="document",
                embeddings=None,
                error_message=None
            )

        except Exception as e:
            logger.error(f"Error processing image {metadata.filename}: {e}")
            return ProcessingResult(
                success=False,
                text_content=None,
                extracted_fields=None,
                classification=None,
                embeddings=None,
                error_message=str(e)
            )

    def supports_type(self, file_type: str) -> bool:
        """Check if this pipeline supports image files"""
        return file_type in [
            "image/jpeg", "image/jpg", "image/png",
            "image/tiff", "image/bmp", "jpeg", "jpg",
            "png", "tiff", "bmp"
        ]
```

#### 4. Update Pipeline Registry
**File**: `backend/app/pipelines/registry.py` (new)
**Changes**: Initialize and register pipelines

```python
"""
Pipeline Registry

Manages registration and selection of document processing pipelines.
"""

from app.pipelines.base import PipelineRegistry
from app.pipelines.mock_pipeline import MockPipeline
from app.pipelines.pdf_pipeline import PDFPipeline
from app.pipelines.image_pipeline import ImagePipeline


# Create global registry instance
pipeline_registry = PipelineRegistry()

# Register pipelines
def initialize_pipelines():
    """Initialize and register all available pipelines"""

    # Register mock pipeline as default for testing
    mock_pipeline = MockPipeline()
    pipeline_registry.register_pipeline(mock_pipeline, is_default=True)

    # Register PDF pipeline
    pdf_pipeline = PDFPipeline()
    pipeline_registry.register_pipeline(pdf_pipeline, is_default=False)

    # Register image pipeline
    image_pipeline = ImagePipeline()
    pipeline_registry.register_pipeline(image_pipeline, is_default=False)

    return pipeline_registry


# Initialize on import
initialize_pipelines()
```

### Success Criteria:

#### Automated Verification:
- [ ] Pipeline modules import correctly: `cd backend && python -c "from app.pipelines.registry import pipeline_registry"`
- [ ] Registry returns correct pipeline for file types: `cd backend && python -c "from app.pipelines.registry import pipeline_registry; print(pipeline_registry.list_pipelines())"`
- [ ] No linting errors: `cd backend && ruff check app/pipelines/`

#### Manual Verification:
- [ ] Mock pipeline processes documents successfully
- [ ] PDF pipeline skeleton is ready for OCR integration
- [ ] Image pipeline skeleton is ready for OCR integration
- [ ] Pipeline registry correctly routes documents to pipelines

---

## Phase 4: Integrate Worker with API

### Overview
Update the API to create processing jobs when documents are uploaded and add worker startup to the application.

### Changes Required:

#### 1. Update Document Upload Endpoint
**File**: `backend/app/api/routes/documents.py`
**Changes**: Create processing job after upload

```python
# Add to imports
from app.models.processing_job import ProcessingJob, JobStatus, JobType

# Update upload endpoint (around line 40)
@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization)
) -> DocumentUploadResponse:
    """
    Upload a new document

    The document is saved to blob storage and a processing job is created.
    """
    # ... existing validation and upload code ...

    # After creating document (around line 104)
    db.commit()
    db.refresh(document)

    # Create processing job
    processing_job = ProcessingJob(
        organization_id=organization.id,
        job_type=JobType.DOCUMENT_PROCESSING,
        status=JobStatus.PENDING,
        document_id=document.id,
        priority=0,  # Default priority
        max_retries=3
    )

    db.add(processing_job)
    db.commit()
    db.refresh(processing_job)

    return DocumentUploadResponse(
        id=str(document.id),
        filename=document.filename,
        file_size=document.file_size,
        status=document.status,
        processing_job_id=str(processing_job.id)  # Return job ID for tracking
    )
```

#### 2. Update Document Reprocess Endpoint
**File**: `backend/app/api/routes/documents.py`
**Changes**: Create reprocessing job

```python
# Update reprocess endpoint (around line 476)
@router.post("/documents/{document_id}/reprocess", response_model=DocumentReprocessResponse)
async def reprocess_document(
    document_id: str,
    request: DocumentReprocessRequest = Body(default={}),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization)
) -> DocumentReprocessResponse:
    """Reprocess a document with optionally different pipeline"""

    # ... existing validation code ...

    # Reset document status (around line 529)
    document.status = "pending"
    document.processing_started_at = None
    document.processing_completed_at = None
    document.error_message = None

    # Create reprocessing job
    processing_job = ProcessingJob(
        organization_id=organization.id,
        job_type=JobType.DOCUMENT_REPROCESSING,
        status=JobStatus.PENDING,
        document_id=document.id,
        pipeline_id=request.pipeline_id if request.pipeline_id else None,
        priority=1,  # Higher priority for reprocessing
        max_retries=3
    )

    db.add(processing_job)
    db.commit()
    db.refresh(processing_job)

    return DocumentReprocessResponse(
        message=f"Document {document_id} queued for reprocessing",
        job_id=str(processing_job.id)
    )
```

#### 3. Create Worker Manager
**File**: `backend/app/workers/manager.py` (new)
**Changes**: Manage worker lifecycle

```python
"""
Worker Manager

Manages background worker processes.
"""

import asyncio
import logging
from typing import List, Optional
from contextlib import asynccontextmanager

from app.workers.document_worker import DocumentProcessingWorker
from app.core.config import settings


logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages background workers"""

    def __init__(self):
        self.workers: List[DocumentProcessingWorker] = []
        self.tasks: List[asyncio.Task] = []
        self.running = False

    async def start_workers(self, num_workers: int = 1):
        """
        Start worker processes

        Args:
            num_workers: Number of workers to start
        """
        if self.running:
            logger.warning("Workers already running")
            return

        logger.info(f"Starting {num_workers} document processing workers")

        for i in range(num_workers):
            worker = DocumentProcessingWorker(
                worker_id=f"doc-worker-{i}",
                poll_interval=settings.WORKER_POLL_INTERVAL,
                lock_duration=settings.WORKER_LOCK_DURATION
            )

            self.workers.append(worker)
            await worker.start()

        self.running = True
        logger.info(f"Started {num_workers} workers")

    async def stop_workers(self):
        """Stop all workers gracefully"""
        if not self.running:
            return

        logger.info("Stopping all workers")

        # Stop all workers
        for worker in self.workers:
            await worker.stop()

        self.workers.clear()
        self.running = False

        logger.info("All workers stopped")


# Global manager instance
worker_manager = WorkerManager()


@asynccontextmanager
async def worker_lifespan():
    """Context manager for worker lifecycle"""
    # Start workers
    num_workers = settings.DOCUMENT_WORKERS_COUNT
    if num_workers > 0:
        await worker_manager.start_workers(num_workers)
        logger.info(f"Document processing workers started: {num_workers}")
    else:
        logger.info("Document processing workers disabled (DOCUMENT_WORKERS_COUNT=0)")

    yield

    # Stop workers
    if worker_manager.running:
        await worker_manager.stop_workers()
        logger.info("Document processing workers stopped")
```

#### 4. Update Application Configuration
**File**: `backend/app/core/config.py`
**Changes**: Add worker configuration

```python
# Add to Settings class

# Worker configuration
DOCUMENT_WORKERS_COUNT: int = Field(default=2, env="DOCUMENT_WORKERS_COUNT")
WORKER_POLL_INTERVAL: int = Field(default=5, env="WORKER_POLL_INTERVAL")  # seconds
WORKER_LOCK_DURATION: int = Field(default=300, env="WORKER_LOCK_DURATION")  # seconds
```

#### 5. Update Main Application
**File**: `backend/app/main.py`
**Changes**: Start workers on application startup

```python
# Add to imports
from app.workers.manager import worker_manager

# Update lifespan context manager (around line 22)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # Startup
    print("Starting VibeDocs Backend...")

    # Initialize database
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
```

### Success Criteria:

#### Automated Verification:
- [ ] API starts without errors: `cd backend && uvicorn app.main:app --reload`
- [ ] Worker manager imports correctly: `cd backend && python -c "from app.workers.manager import worker_manager"`
- [ ] No linting errors: `cd backend && ruff check .`

#### Manual Verification:
- [ ] Document upload creates processing job
- [ ] Workers start automatically on application startup
- [ ] Workers process pending jobs within 5-10 seconds
- [ ] Multiple workers can run concurrently
- [ ] Workers stop gracefully on application shutdown

---

## Phase 5: Add Job Status Endpoint

### Overview
Add API endpoint to check job status and processing results.

### Changes Required:

#### 1. Create Job Status Schema
**File**: `backend/app/schemas/processing_job.py` (new)
**Changes**: Pydantic schemas for job responses

```python
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
```

#### 2. Create Jobs API Router
**File**: `backend/app/api/routes/jobs.py` (new)
**Changes**: Endpoints for job management

```python
"""
Processing Jobs API Routes

Endpoints for managing and monitoring processing jobs.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_organization
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
```

#### 3. Register Jobs Router
**File**: `backend/app/main.py`
**Changes**: Include jobs router

```python
# Add to imports
from app.api.routes.jobs import router as jobs_router

# Add after other router includes (around line 72)
app.include_router(jobs_router, prefix=settings.API_V1_STR)
```

### Success Criteria:

#### Automated Verification:
- [ ] Jobs API imports correctly: `cd backend && python -c "from app.api.routes.jobs import router"`
- [ ] Schemas import correctly: `cd backend && python -c "from app.schemas.processing_job import JobStatusResponse"`
- [ ] API starts with new endpoints: `cd backend && uvicorn app.main:app --reload`

#### Manual Verification:
- [ ] GET /api/v1/jobs/{job_id} returns job status
- [ ] GET /api/v1/jobs lists all jobs for organization
- [ ] POST /api/v1/jobs/{job_id}/cancel cancels pending jobs
- [ ] Job status transitions correctly: pending → processing → completed/failed

---

## Testing Strategy

### Unit Tests:
- Test job claiming with concurrent workers
- Test pessimistic locking behavior
- Test job retry logic
- Test pipeline registration and selection

### Integration Tests:
1. Upload a document via API
2. Verify processing job created
3. Wait for worker to process
4. Check document status updated to "ready"
5. Verify extracted content in document

### Manual Testing Steps:
1. Start the API with workers enabled:
   ```bash
   cd backend
   DOCUMENT_WORKERS_COUNT=2 uvicorn app.main:app --reload
   ```

2. Upload a test document:
   ```bash
   curl -X POST http://localhost:8000/api/v1/documents/upload \
     -H "Authorization: Bearer TOKEN" \
     -H "X-Organization-ID: ORG_ID" \
     -F "file=@test.pdf"
   ```

3. Check job status:
   ```bash
   curl http://localhost:8000/api/v1/jobs/{job_id} \
     -H "Authorization: Bearer TOKEN" \
     -H "X-Organization-ID: ORG_ID"
   ```

4. Verify document processed:
   ```bash
   curl http://localhost:8000/api/v1/documents/{document_id} \
     -H "Authorization: Bearer TOKEN" \
     -H "X-Organization-ID: ORG_ID"
   ```

## Performance Considerations

- Workers use pessimistic locking with `FOR UPDATE SKIP LOCKED` for efficient job claiming
- Polling interval configurable via `WORKER_POLL_INTERVAL` environment variable
- Lock duration prevents stuck jobs via `lock_expires_at` timeout
- Database indexes on status and priority for fast job selection
- Multiple workers can run concurrently without conflicts

## Migration Notes

For existing documents without processing jobs:
1. Set all documents with status="pending" to create new jobs
2. Or use the reprocess endpoint to trigger processing

## References

- Document Model: `backend/app/models/document.py`
- Processing Job Model: `backend/app/models/processing_job.py`
- Base Pipeline: `backend/app/pipelines/base.py`
- Worker Implementation: `backend/app/workers/document_worker.py`
- Upload Endpoint: `backend/app/api/routes/documents.py:40`
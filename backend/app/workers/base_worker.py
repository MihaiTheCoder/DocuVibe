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

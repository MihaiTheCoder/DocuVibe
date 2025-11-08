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

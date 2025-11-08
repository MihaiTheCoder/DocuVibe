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

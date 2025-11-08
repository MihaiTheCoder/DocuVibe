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

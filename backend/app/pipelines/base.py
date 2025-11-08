"""
Base Pipeline Architecture for Document Processing
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """Document metadata structure"""
    organization_id: str
    user_id: str
    filename: str
    file_type: str
    file_size: int
    custom_metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingResult:
    """Result from document processing"""
    success: bool
    text_content: Optional[str] = None
    extracted_fields: Optional[Dict[str, Any]] = None
    classification: Optional[str] = None
    embeddings: Optional[List[float]] = None
    error_message: Optional[str] = None


class DocumentPipeline(ABC):
    """
    Base class for all document processing pipelines
    Following vibe code principles: small, simple, extensible
    """

    def __init__(self, name: str):
        self.name = name
        self.extractors = {}

    @abstractmethod
    async def process(
        self,
        file_path: str,
        metadata: DocumentMetadata
    ) -> ProcessingResult:
        """
        Process a document and return extracted data
        Must be implemented by each pipeline
        """
        pass

    @abstractmethod
    def supports_type(self, file_type: str) -> bool:
        """
        Check if this pipeline can handle the file type
        """
        pass

    def register_extractor(self, doc_type: str, extractor):
        """
        Register a field extractor for specific document types
        """
        self.extractors[doc_type] = extractor
        logger.info(f"Registered {doc_type} extractor for {self.name} pipeline")

    async def extract_fields(
        self,
        text: str,
        doc_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract fields using registered extractor if available
        """
        if doc_type in self.extractors:
            extractor = self.extractors[doc_type]
            return await extractor.extract(text)
        return None


class FieldExtractor(ABC):
    """
    Base class for field extractors
    """

    @abstractmethod
    async def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract specific fields from text
        """
        pass


class PipelineRegistry:
    """
    Central registry for document pipelines
    Singleton pattern for global access
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pipelines = {}
            cls._instance.default_pipeline = None
        return cls._instance

    def register_pipeline(
        self,
        pipeline: DocumentPipeline,
        is_default: bool = False
    ):
        """
        Register a document processing pipeline
        """
        self.pipelines[pipeline.name] = pipeline
        if is_default:
            self.default_pipeline = pipeline
        logger.info(f"Registered pipeline: {pipeline.name}")

    def get_pipeline(self, file_type: str) -> Optional[DocumentPipeline]:
        """
        Get appropriate pipeline for file type
        """
        for pipeline in self.pipelines.values():
            if pipeline.supports_type(file_type):
                return pipeline
        return self.default_pipeline

    def list_pipelines(self) -> List[str]:
        """
        List all registered pipelines
        """
        return list(self.pipelines.keys())


# Global registry instance
pipeline_registry = PipelineRegistry()
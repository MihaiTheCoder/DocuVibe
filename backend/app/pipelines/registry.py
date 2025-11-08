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

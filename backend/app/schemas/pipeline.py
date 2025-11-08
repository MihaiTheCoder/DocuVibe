"""
Pipeline Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PipelineBase(BaseModel):
    """Base pipeline schema"""
    name: str = Field(..., min_length=1, max_length=255)
    type: Optional[str] = Field(None, description="Pipeline type (pdf, image, email, etc.)")
    config: dict = Field(default_factory=dict, description="Pipeline configuration")


class PipelineCreateRequest(PipelineBase):
    """Schema for creating a pipeline"""
    is_active: bool = True
    is_default: bool = False


class PipelineUpdateRequest(BaseModel):
    """Schema for updating a pipeline"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class PipelineResponse(PipelineBase):
    """Schema for pipeline response"""
    id: str
    organization_id: str
    is_active: bool
    is_default: bool
    documents_processed: int
    success_count: int
    failure_count: int
    avg_processing_time_ms: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PipelineDetailResponse(PipelineResponse):
    """Schema for detailed pipeline response"""
    pass


class PipelineStatsResponse(BaseModel):
    """Schema for pipeline statistics"""
    pipeline_id: str
    pipeline_name: str
    documents_processed: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_processing_time_ms: Optional[float] = None
    last_used: Optional[datetime] = None


class PipelineTestRequest(BaseModel):
    """Schema for testing a pipeline"""
    sample_file_id: str = Field(..., description="Document ID to use for testing")


class PipelineTestResult(BaseModel):
    """Schema for pipeline test result"""
    success: bool
    processing_time_ms: float
    text_content_preview: Optional[str] = None
    extracted_fields: dict = Field(default_factory=dict)
    classification: Optional[str] = None
    error_message: Optional[str] = None


class PipelineCloneRequest(BaseModel):
    """Schema for cloning a pipeline"""
    name: str = Field(..., min_length=1, max_length=255, description="Name for the cloned pipeline")

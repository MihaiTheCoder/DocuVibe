"""
Document Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentBase(BaseModel):
    """Base document schema"""
    filename: str
    file_type: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response"""
    id: str
    filename: str
    file_size: int
    status: str
    processing_job_id: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: str
    organization_id: str
    file_size: Optional[int] = None
    status: str
    stage: str
    classification: Optional[str] = None
    uploaded_by_id: Optional[str] = None
    assigned_to_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    """Schema for detailed document response"""
    text_content: Optional[str] = None
    metadata: dict = Field(default={}, alias="doc_metadata")
    extracted_fields: dict = {}
    blob_url: Optional[str] = None
    pipeline_id: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class DocumentUpdateRequest(BaseModel):
    """Schema for updating a document"""
    filename: Optional[str] = None
    classification: Optional[str] = None
    stage: Optional[str] = None
    metadata: Optional[dict] = None
    assigned_to_id: Optional[str] = None


class DocumentStageUpdateRequest(BaseModel):
    """Schema for updating document stage"""
    stage: str
    comment: Optional[str] = None


class DocumentAssignRequest(BaseModel):
    """Schema for assigning a document"""
    user_id: str


class DocumentApproveRequest(BaseModel):
    """Schema for approving a document"""
    comment: Optional[str] = None


class DocumentSignRequest(BaseModel):
    """Schema for signing a document"""
    signature_data: str


class DocumentArchiveRequest(BaseModel):
    """Schema for archiving a document"""
    reason: Optional[str] = None


class DocumentReprocessRequest(BaseModel):
    """Schema for reprocessing a document"""
    pipeline_id: Optional[str] = None


class PaginatedDocumentsResponse(BaseModel):
    """Schema for paginated documents response"""
    items: list[DocumentResponse]
    total: int
    page: int
    limit: int
    pages: int

    class Config:
        from_attributes = True

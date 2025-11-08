"""
Document Model
"""

from sqlalchemy import Column, String, BigInteger, DateTime, Text, JSON, UUID, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import TenantModel


class Document(TenantModel):
    """Document model for uploaded files and processing results"""

    __tablename__ = "documents"

    filename = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_size = Column(BigInteger)
    blob_url = Column(String(1000))
    status = Column(String(50), default="pending")  # pending, processing, ready, failed
    stage = Column(String(50), default="draft")  # draft, review, approved, signed, archived

    # Extracted content
    text_content = Column(Text)
    doc_metadata = Column(JSON, default={})
    extracted_fields = Column(JSON, default={})
    classification = Column(String(100))

    # Processing info
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("pipelines.id"))
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)

    # User tracking
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization", back_populates="documents")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id], back_populates="uploaded_documents")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_documents")
    pipeline = relationship("Pipeline", back_populates="documents")
    tasks = relationship("Task", back_populates="document")

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"

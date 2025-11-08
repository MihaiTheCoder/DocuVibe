"""
Pipeline Model
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, JSON, UUID, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import TenantModel


class Pipeline(TenantModel):
    """Pipeline model for document processing configuration"""

    __tablename__ = "pipelines"

    name = Column(String(255), nullable=False)
    type = Column(String(50))  # pdf, image, email, etc.
    config = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Statistics
    documents_processed = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_processing_time_ms = Column(Float)

    # Relationships
    organization = relationship("Organization", back_populates="pipelines")
    documents = relationship("Document", back_populates="pipeline")
    processing_jobs = relationship("ProcessingJob", back_populates="pipeline", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pipeline(id={self.id}, name={self.name}, type={self.type})>"

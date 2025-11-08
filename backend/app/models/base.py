"""
Base Model for Multi-tenant Architecture
"""

from sqlalchemy import Column, String, DateTime, UUID, ForeignKey
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class TenantModel(Base):
    """
    Abstract base model for all tenant-scoped models
    """

    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
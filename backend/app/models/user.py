"""
User Model
"""

from sqlalchemy import Column, String, Boolean, DateTime, JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class User(Base):
    """User model for authentication and profile management"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    picture_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    google_id = Column(String(255), unique=True)
    preferences = Column(JSON, default={})
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    organizations = relationship("UserOrganization", back_populates="user")
    uploaded_documents = relationship("Document", back_populates="uploaded_by", foreign_keys="Document.uploaded_by_id")
    assigned_documents = relationship("Document", back_populates="assigned_to", foreign_keys="Document.assigned_to_id")
    assigned_tasks = relationship("Task", back_populates="assigned_to", foreign_keys="Task.assigned_to_id")
    created_tasks = relationship("Task", back_populates="assigned_by", foreign_keys="Task.assigned_by_id")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

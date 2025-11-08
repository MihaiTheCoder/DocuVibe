"""
Organization Models
"""

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, JSON, UUID, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Organization(Base):
    """Organization model for multi-tenancy"""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255))
    settings = Column(JSON, default={})
    subscription_tier = Column(String(50), default="free")
    storage_quota_gb = Column(Integer, default=10)
    storage_used_bytes = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    users = relationship("UserOrganization", back_populates="organization")
    documents = relationship("Document", back_populates="organization")
    pipelines = relationship("Pipeline", back_populates="organization")
    workflows = relationship("Workflow", back_populates="organization")
    tasks = relationship("Task", back_populates="organization")
    notifications = relationship("Notification", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name})>"


class UserOrganization(Base):
    """Junction table for user-organization membership"""

    __tablename__ = "user_organizations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), primary_key=True)
    role = Column(String(50), default="member")  # admin, member
    invited_at = Column(DateTime(timezone=True))
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="organizations")
    organization = relationship("Organization", back_populates="users")

    def __repr__(self):
        return f"<UserOrganization(user_id={self.user_id}, organization_id={self.organization_id}, role={self.role})>"

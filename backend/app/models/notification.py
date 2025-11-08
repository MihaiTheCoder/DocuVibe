"""
Notification Model
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, UUID, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import TenantModel


class Notification(TenantModel):
    """Notification model for user alerts and messages"""

    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    type = Column(String(50))  # task_assigned, document_approved, etc.
    title = Column(String(255))
    message = Column(Text)
    data = Column(JSON)  # Additional context
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))

    # Relationships
    organization = relationship("Organization", back_populates="notifications")
    user = relationship("User")

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, is_read={self.is_read})>"

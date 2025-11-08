"""
Task Model
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, UUID, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import TenantModel


class Task(TenantModel):
    """Task model for assignments and workflows"""

    __tablename__ = "tasks"

    title = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50))  # review, approval, data_entry, etc.
    status = Column(String(50), default="pending")  # pending, in_progress, completed, rejected
    priority = Column(String(20), default="normal")  # low, normal, high, urgent

    # Assignment
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    claimed_at = Column(DateTime(timezone=True))

    # Related entities
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"))

    # Timing
    due_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Results
    result = Column(JSON)
    comment = Column(Text)

    # Relationships
    organization = relationship("Organization", back_populates="tasks")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_tasks")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id], back_populates="created_tasks")
    document = relationship("Document", back_populates="tasks")
    workflow_execution = relationship("WorkflowExecution", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"

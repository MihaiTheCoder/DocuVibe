"""
Workflow Models
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, UUID, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import TenantModel


class Workflow(TenantModel):
    """Workflow model for document processing automation"""

    __tablename__ = "workflows"

    name = Column(String(255), nullable=False)
    description = Column(Text)
    steps = Column(JSON)  # Array of step definitions
    triggers = Column(JSON)  # Event triggers
    created_by_ai = Column(Boolean, default=False)
    ai_prompt = Column(Text)  # Original prompt if AI-created

    # Relationships
    organization = relationship("Organization", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow")

    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name})>"


class WorkflowExecution(TenantModel):
    """WorkflowExecution model for tracking workflow runs"""

    __tablename__ = "workflow_executions"

    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"))
    status = Column(String(50))  # running, completed, failed
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    results = Column(JSON)

    # Relationships
    # Note: organization relationship is implicit through TenantModel.organization_id
    workflow = relationship("Workflow", back_populates="executions")
    tasks = relationship("Task", back_populates="workflow_execution")

    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"

"""
GitHub Integration Models
"""

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Integer, JSON
from sqlalchemy.types import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base


class IssueDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    UNKNOWN = "unknown"


class IssueStatus(str, enum.Enum):
    CREATED = "created"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    PR_CREATED = "pr_created"
    TESTING = "testing"
    MERGED = "merged"
    FAILED = "failed"
    CLOSED = "closed"


class GitHubIssue(Base):
    __tablename__ = "github_issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"))

    # GitHub data
    issue_number = Column(Integer)
    issue_url = Column(String(500))
    issue_title = Column(String(200), nullable=False)
    issue_body = Column(Text)
    difficulty = Column(String(50), default=IssueDifficulty.UNKNOWN.value)
    labels = Column(JSON, default=[])

    # Status tracking
    status = Column(String(50), default=IssueStatus.CREATED.value)
    pr_number = Column(Integer)
    pr_url = Column(String(500))
    auto_merge_enabled = Column(Boolean, default=False)

    # Metrics
    complexity_score = Column(Integer)  # 1-100 scale
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    ready_at = Column(DateTime)
    pr_created_at = Column(DateTime)
    merged_at = Column(DateTime)

    # Relationships
    organization = relationship("Organization")
    conversation = relationship("Conversation", back_populates="github_issues")
    message = relationship("Message")

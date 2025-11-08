# Chat UI with GitHub Integration Implementation Plan

## Overview

This plan implements a Chat UI feature that allows users to request features through natural language, automatically creates GitHub issues with difficulty classification (easy/medium/hard), leverages the lazy-bird tool for automated PR generation, and includes automatic merging for easy issues after successful tests.

## Current State Analysis

The VibeDocs project currently has:
- **Backend Chat API**: Basic endpoints implemented at `backend/app/api/routes/chat.py`
- **Chat Service**: Mock implementation at `backend/app/services/chat_service.py` with TODO for LLM integration
- **GitHub Config**: Partial configuration in `backend/app/core/config.py` (GITHUB_TOKEN, GITHUB_REPO, LAZY_BIRD_API_URL)
- **No Frontend Chat UI**: Referenced in plans but not implemented
- **No Database Models**: Chat/conversation persistence not implemented
- **No GitHub Integration**: No issue creation or PR management code

### Key Discoveries:
- Authentication and organization context already handled via middleware (`backend/app/middleware/organization.py`)
- JWT-based authentication with Google OAuth in place
- Multi-tenant architecture enforced at all API endpoints
- Azure Blob Storage for document management already configured
- Worker system exists for async processing (`backend/app/workers/`)

## Desired End State

A fully functional Chat UI where:
1. Users can type feature requests in natural language
2. System analyzes requests and creates GitHub issues with appropriate difficulty labels
3. Lazy-bird tool monitors "ready" issues and triggers Claude Code implementation
4. PRs are created automatically after successful test runs
5. Easy issues are auto-merged after passing CI/CD checks
6. Users receive real-time feedback on request status

### Verification Criteria:
- Chat UI accessible and responsive in the frontend
- GitHub issues created with correct labels and formatting
- Lazy-bird integration successfully picks up issues
- PRs generated with proper descriptions and test results
- Auto-merge working for easy issues only

## What We're NOT Doing

- Implementing complex AI/LLM for general chat (focusing on feature request processing)
- Creating a full conversational AI system for document queries
- Implementing real-time WebSocket chat (using polling for now)
- Building custom CI/CD pipelines (using GitHub Actions)
- Creating custom test runners (relying on lazy-bird's framework detection)

## Implementation Approach

We'll implement this in 5 phases:
1. Database models and persistence layer for chat/conversations
2. GitHub integration service for issue and PR management
3. Feature analysis and difficulty classification system
4. Backend API enhancement with real processing
5. Frontend Chat UI implementation
6. Lazy-bird integration and auto-merge logic

---

## Phase 1: Database Models and Persistence Layer

### Overview
Create database models for persisting conversations, messages, and GitHub integration tracking.

### Changes Required:

#### 1. Chat and Conversation Models
**File**: `backend/app/models/conversation.py` (new)
**Changes**: Create conversation and message models

```python
"""
Conversation and Message Models
"""

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.core.database import Base


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    RESOLVED = "resolved"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200))
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="conversations")
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    github_issues = relationship("GitHubIssue", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default={})  # For storing parsed intents, actions, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
```

#### 2. GitHub Integration Models
**File**: `backend/app/models/github_integration.py` (new)
**Changes**: Create models for tracking GitHub issues and PRs

```python
"""
GitHub Integration Models
"""

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Boolean, Integer, JSON
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
    difficulty = Column(Enum(IssueDifficulty), default=IssueDifficulty.UNKNOWN)
    labels = Column(JSON, default=[])

    # Status tracking
    status = Column(Enum(IssueStatus), default=IssueStatus.CREATED)
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
```

#### 3. Update Organization Model
**File**: `backend/app/models/organization.py`
**Changes**: Add relationships to conversations

```python
# Add to existing Organization model:
conversations = relationship("Conversation", back_populates="organization")
```

#### 4. Update User Model
**File**: `backend/app/models/user.py`
**Changes**: Add relationships to conversations

```python
# Add to existing User model:
conversations = relationship("Conversation", back_populates="user")
```

#### 5. Database Migration
**File**: `backend/alembic/versions/xxxx_add_chat_github_models.py` (new)
**Changes**: Create migration for new tables

```python
"""Add chat and GitHub integration models

Revision ID: xxxx
Revises: yyyy
Create Date: 2025-11-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('status', sa.Enum('active', 'archived', 'resolved', name='conversationstatus'), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_organization_id'), 'conversations', ['organization_id'])
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('user', 'assistant', 'system', name='messagerole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'])

    # Create github_issues table
    op.create_table(
        'github_issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('issue_number', sa.Integer(), nullable=True),
        sa.Column('issue_url', sa.String(500), nullable=True),
        sa.Column('issue_title', sa.String(200), nullable=False),
        sa.Column('issue_body', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.Enum('easy', 'medium', 'hard', 'unknown', name='issuedifficulty'), nullable=True),
        sa.Column('labels', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('created', 'ready', 'in_progress', 'pr_created', 'testing', 'merged', 'failed', 'closed', name='issuestatus'), nullable=True),
        sa.Column('pr_number', sa.Integer(), nullable=True),
        sa.Column('pr_url', sa.String(500), nullable=True),
        sa.Column('auto_merge_enabled', sa.Boolean(), nullable=True),
        sa.Column('complexity_score', sa.Integer(), nullable=True),
        sa.Column('estimated_hours', sa.Integer(), nullable=True),
        sa.Column('actual_hours', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('ready_at', sa.DateTime(), nullable=True),
        sa.Column('pr_created_at', sa.DateTime(), nullable=True),
        sa.Column('merged_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_github_issues_organization_id'), 'github_issues', ['organization_id'])
    op.create_index(op.f('ix_github_issues_status'), 'github_issues', ['status'])

def downgrade():
    op.drop_index(op.f('ix_github_issues_status'), table_name='github_issues')
    op.drop_index(op.f('ix_github_issues_organization_id'), table_name='github_issues')
    op.drop_table('github_issues')
    op.drop_index(op.f('ix_messages_conversation_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_organization_id'), table_name='conversations')
    op.drop_table('conversations')
    op.execute('DROP TYPE IF EXISTS conversationstatus')
    op.execute('DROP TYPE IF EXISTS messagerole')
    op.execute('DROP TYPE IF EXISTS issuedifficulty')
    op.execute('DROP TYPE IF EXISTS issuestatus')
```

### Success Criteria:

#### Automated Verification:
- [x] Database migration applies cleanly: `cd backend && alembic upgrade head`
- [x] Models import without errors: `cd backend && python -c "from app.models.conversation import Conversation, Message"`
- [x] Relationships work correctly: `cd backend && python -c "from app.models.github_integration import GitHubIssue"`

#### Manual Verification:
- [ ] Database tables created correctly with proper foreign keys
- [ ] Can create and query conversation/message records through SQLAlchemy

---

## Phase 2: GitHub Integration Service

### Overview
Implement GitHub API integration service for creating issues, managing PRs, and handling auto-merge.

### Changes Required:

#### 1. GitHub Service Implementation
**File**: `backend/app/services/github_service.py` (new)
**Changes**: Create comprehensive GitHub integration service

```python
"""
GitHub Integration Service
"""

import httpx
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
import logging

from app.core.config import settings
from app.models.github_integration import IssueDifficulty, IssueStatus

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for GitHub API integration"""

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = settings.GITHUB_TOKEN
        self.repo = settings.GITHUB_REPO

        if not self.token:
            raise ValueError("GITHUB_TOKEN not configured")

        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def create_issue(
        self,
        title: str,
        body: str,
        labels: List[str],
        difficulty: IssueDifficulty
    ) -> Dict[str, Any]:
        """
        Create a GitHub issue

        Args:
            title: Issue title
            body: Issue body (markdown)
            labels: List of labels to apply
            difficulty: Difficulty level (easy/medium/hard)

        Returns:
            GitHub issue data including number and URL
        """
        # Add difficulty label
        labels.append(difficulty.value)

        # Format issue body with lazy-bird compatibility
        formatted_body = self._format_issue_body(body, difficulty)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{self.repo}/issues",
                headers=self.headers,
                json={
                    "title": title,
                    "body": formatted_body,
                    "labels": labels
                }
            )

            if response.status_code != 201:
                raise Exception(f"Failed to create issue: {response.text}")

            data = response.json()
            return {
                "number": data["number"],
                "url": data["html_url"],
                "id": data["id"],
                "node_id": data["node_id"]
            }

    async def add_ready_label(self, issue_number: int) -> bool:
        """
        Add 'ready' label to trigger lazy-bird processing

        Args:
            issue_number: GitHub issue number

        Returns:
            True if successful
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/labels",
                headers=self.headers,
                json={"labels": ["ready"]}
            )

            return response.status_code == 200

    async def get_issue_status(self, issue_number: int) -> Dict[str, Any]:
        """
        Get current status of an issue

        Args:
            issue_number: GitHub issue number

        Returns:
            Issue status information
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{self.repo}/issues/{issue_number}",
                headers=self.headers
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get issue: {response.text}")

            data = response.json()

            # Check for linked PRs
            pr_info = await self._get_linked_pr(issue_number)

            return {
                "state": data["state"],
                "labels": [label["name"] for label in data["labels"]],
                "has_pr": pr_info is not None,
                "pr_number": pr_info["number"] if pr_info else None,
                "pr_url": pr_info["html_url"] if pr_info else None,
                "pr_state": pr_info["state"] if pr_info else None
            }

    async def get_pr_status(self, pr_number: int) -> Dict[str, Any]:
        """
        Get PR status including checks and reviews

        Args:
            pr_number: Pull request number

        Returns:
            PR status information
        """
        async with httpx.AsyncClient() as client:
            # Get PR details
            pr_response = await client.get(
                f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}",
                headers=self.headers
            )

            if pr_response.status_code != 200:
                raise Exception(f"Failed to get PR: {pr_response.text}")

            pr_data = pr_response.json()

            # Get check runs
            checks_response = await client.get(
                f"{self.base_url}/repos/{self.repo}/commits/{pr_data['head']['sha']}/check-runs",
                headers=self.headers
            )

            checks_data = checks_response.json() if checks_response.status_code == 200 else {"check_runs": []}

            # Get reviews
            reviews_response = await client.get(
                f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}/reviews",
                headers=self.headers
            )

            reviews_data = reviews_response.json() if reviews_response.status_code == 200 else []

            return {
                "state": pr_data["state"],
                "mergeable": pr_data.get("mergeable"),
                "merged": pr_data.get("merged", False),
                "checks_passing": self._are_checks_passing(checks_data["check_runs"]),
                "approved": self._is_approved(reviews_data),
                "head_sha": pr_data["head"]["sha"]
            }

    async def enable_auto_merge(self, pr_number: int) -> bool:
        """
        Enable auto-merge for a PR (requires GraphQL API)

        Args:
            pr_number: Pull request number

        Returns:
            True if successful
        """
        # Get PR node ID first
        async with httpx.AsyncClient() as client:
            pr_response = await client.get(
                f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}",
                headers=self.headers
            )

            if pr_response.status_code != 200:
                return False

            pr_data = pr_response.json()
            node_id = pr_data["node_id"]

            # Use GraphQL to enable auto-merge
            graphql_query = """
            mutation EnableAutoMerge($pullRequestId: ID!) {
                enablePullRequestAutoMerge(input: {
                    pullRequestId: $pullRequestId,
                    mergeMethod: SQUASH
                }) {
                    pullRequest {
                        autoMergeRequest {
                            enabledAt
                        }
                    }
                }
            }
            """

            response = await client.post(
                f"{self.base_url}/graphql",
                headers=self.headers,
                json={
                    "query": graphql_query,
                    "variables": {"pullRequestId": node_id}
                }
            )

            return response.status_code == 200

    async def merge_pr(self, pr_number: int, commit_message: str = None) -> bool:
        """
        Manually merge a PR

        Args:
            pr_number: Pull request number
            commit_message: Optional custom commit message

        Returns:
            True if successful
        """
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}/merge",
                headers=self.headers,
                json={
                    "merge_method": "squash",
                    "commit_title": commit_message or f"Merge PR #{pr_number}",
                    "commit_message": "Auto-merged by VibeDocs Chat UI"
                }
            )

            return response.status_code == 200

    async def _get_linked_pr(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """
        Find PR linked to an issue

        Args:
            issue_number: Issue number

        Returns:
            PR data if found, None otherwise
        """
        async with httpx.AsyncClient() as client:
            # Search for PRs that reference this issue
            search_response = await client.get(
                f"{self.base_url}/search/issues",
                headers=self.headers,
                params={
                    "q": f"repo:{self.repo} is:pr #{issue_number} in:body"
                }
            )

            if search_response.status_code == 200:
                data = search_response.json()
                if data["total_count"] > 0:
                    return data["items"][0]

            return None

    def _format_issue_body(self, body: str, difficulty: IssueDifficulty) -> str:
        """
        Format issue body for lazy-bird compatibility

        Args:
            body: Original issue body
            difficulty: Issue difficulty

        Returns:
            Formatted body with metadata and structure
        """
        return f"""## Feature Request

{body}

## Implementation Details

**Difficulty**: {difficulty.value}
**Auto-generated**: Yes
**Source**: VibeDocs Chat UI

## Acceptance Criteria

- [ ] Feature implemented according to specification
- [ ] Unit tests added and passing
- [ ] Integration tests passing
- [ ] Code reviewed and approved
- [ ] Documentation updated if necessary

## Technical Notes

This issue was automatically created from a user feature request via the VibeDocs Chat UI.
It has been classified as **{difficulty.value}** based on complexity analysis.

{'' if difficulty != IssueDifficulty.EASY else '**Note**: This issue is marked for automatic merging after successful tests.'}

---
*Generated by VibeDocs Chat UI*
"""

    def _are_checks_passing(self, check_runs: List[Dict[str, Any]]) -> bool:
        """
        Check if all CI checks are passing

        Args:
            check_runs: List of check run data

        Returns:
            True if all checks pass
        """
        if not check_runs:
            return True  # No checks configured

        for check in check_runs:
            if check["status"] != "completed":
                return False
            if check["conclusion"] not in ["success", "neutral", "skipped"]:
                return False

        return True

    def _is_approved(self, reviews: List[Dict[str, Any]]) -> bool:
        """
        Check if PR has required approvals

        Args:
            reviews: List of review data

        Returns:
            True if approved
        """
        # Get latest review from each user
        user_reviews = {}
        for review in reviews:
            user = review["user"]["login"]
            if user not in user_reviews or review["submitted_at"] > user_reviews[user]["submitted_at"]:
                user_reviews[user] = review

        # Check if any review is approved
        for review in user_reviews.values():
            if review["state"] == "APPROVED":
                return True

        return False
```

#### 2. Update Configuration
**File**: `backend/app/core/config.py`
**Changes**: Ensure all GitHub settings are properly configured

```python
# Already exists, but verify these are present:
GITHUB_TOKEN: Optional[str] = None
GITHUB_REPO: str = "yourusername/vibedocs"  # Update default
LAZY_BIRD_API_URL: str = "https://api.lazy-bird.com"
LAZY_BIRD_API_KEY: Optional[str] = None

# Add new settings:
GITHUB_AUTO_MERGE_EASY: bool = True
GITHUB_REQUIRE_APPROVAL_FOR_MERGE: bool = False  # Set to True in production
```

### Success Criteria:

#### Automated Verification:
- [ ] GitHub service imports correctly: `cd backend && python -c "from app.services.github_service import GitHubService"`
- [ ] Configuration loads properly: `cd backend && python -c "from app.core.config import settings; print(settings.GITHUB_TOKEN)"`

#### Manual Verification:
- [ ] Can create test issue via GitHub API (requires valid token)
- [ ] Can query issue/PR status
- [ ] Auto-merge configuration works for test repo

---

## Phase 3: Feature Analysis and Difficulty Classification

### Overview
Implement AI-powered feature analysis to understand user requests and classify difficulty.

### Changes Required:

#### 1. Feature Analyzer Service
**File**: `backend/app/services/feature_analyzer.py` (new)
**Changes**: Create service for analyzing feature requests

```python
"""
Feature Analysis Service
"""

import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import logging

from app.models.github_integration import IssueDifficulty

logger = logging.getLogger(__name__)


@dataclass
class FeatureAnalysis:
    """Analysis result for a feature request"""
    title: str
    description: str
    difficulty: IssueDifficulty
    complexity_score: int  # 1-100
    estimated_hours: int
    components: List[str]  # Affected components
    risks: List[str]
    requirements: List[str]
    labels: List[str]  # GitHub labels to apply


class FeatureAnalyzer:
    """Service for analyzing and classifying feature requests"""

    # Keywords indicating complexity
    COMPLEXITY_INDICATORS = {
        "easy": [
            "simple", "basic", "minor", "small", "typo", "text", "label",
            "color", "style", "css", "rename", "update message", "tooltip"
        ],
        "medium": [
            "add", "new feature", "integrate", "api", "endpoint", "component",
            "validation", "form", "table", "list", "search", "filter"
        ],
        "hard": [
            "complex", "architecture", "refactor", "migration", "security",
            "performance", "real-time", "websocket", "machine learning",
            "ai", "optimization", "scale", "distributed"
        ]
    }

    # Component detection patterns
    COMPONENT_PATTERNS = {
        "frontend": ["ui", "frontend", "react", "component", "page", "view", "style"],
        "backend": ["api", "backend", "server", "database", "endpoint", "service"],
        "database": ["database", "table", "migration", "schema", "model", "query"],
        "authentication": ["auth", "login", "oauth", "permission", "role", "access"],
        "integration": ["integrate", "third-party", "external", "api", "webhook"],
        "testing": ["test", "testing", "unit test", "integration test", "e2e"],
        "documentation": ["docs", "documentation", "readme", "comment", "guide"],
        "deployment": ["deploy", "deployment", "ci/cd", "docker", "kubernetes"]
    }

    def analyze_feature_request(self, message: str) -> FeatureAnalysis:
        """
        Analyze a feature request message

        Args:
            message: User's feature request message

        Returns:
            FeatureAnalysis object with classification
        """
        # Extract title and description
        title, description = self._extract_title_and_description(message)

        # Detect components
        components = self._detect_components(message.lower())

        # Calculate complexity
        complexity_score, difficulty = self._calculate_complexity(
            message.lower(),
            components
        )

        # Estimate hours
        estimated_hours = self._estimate_hours(complexity_score, difficulty)

        # Identify risks
        risks = self._identify_risks(message.lower(), components)

        # Extract requirements
        requirements = self._extract_requirements(message)

        # Generate labels
        labels = self._generate_labels(components, difficulty)

        return FeatureAnalysis(
            title=title,
            description=description,
            difficulty=difficulty,
            complexity_score=complexity_score,
            estimated_hours=estimated_hours,
            components=components,
            risks=risks,
            requirements=requirements,
            labels=labels
        )

    def _extract_title_and_description(self, message: str) -> Tuple[str, str]:
        """
        Extract a title and description from the message

        Args:
            message: User message

        Returns:
            Tuple of (title, description)
        """
        lines = message.strip().split('\n')

        # First line or first sentence as title
        if lines:
            first_line = lines[0].strip()
            # Limit title length
            if len(first_line) > 100:
                # Find first sentence
                sentences = re.split(r'[.!?]', first_line)
                if sentences:
                    title = sentences[0].strip()[:100]
                else:
                    title = first_line[:100]
            else:
                title = first_line

            # Rest as description
            if len(lines) > 1:
                description = '\n'.join(lines[1:]).strip()
            else:
                description = message.strip()
        else:
            title = "Feature Request"
            description = message.strip()

        # Clean up title
        title = re.sub(r'^(I want|I need|Can you|Please|Could you)\s+', '', title, flags=re.IGNORECASE)
        title = title.capitalize()

        return title, description

    def _detect_components(self, message_lower: str) -> List[str]:
        """
        Detect which components are affected

        Args:
            message_lower: Lowercase message

        Returns:
            List of component names
        """
        detected = []

        for component, keywords in self.COMPONENT_PATTERNS.items():
            if any(keyword in message_lower for keyword in keywords):
                detected.append(component)

        # Default to general if nothing detected
        if not detected:
            detected = ["general"]

        return detected

    def _calculate_complexity(
        self,
        message_lower: str,
        components: List[str]
    ) -> Tuple[int, IssueDifficulty]:
        """
        Calculate complexity score and difficulty

        Args:
            message_lower: Lowercase message
            components: Detected components

        Returns:
            Tuple of (complexity_score, difficulty)
        """
        score = 0

        # Check for complexity indicators
        easy_count = sum(1 for word in self.COMPLEXITY_INDICATORS["easy"] if word in message_lower)
        medium_count = sum(1 for word in self.COMPLEXITY_INDICATORS["medium"] if word in message_lower)
        hard_count = sum(1 for word in self.COMPLEXITY_INDICATORS["hard"] if word in message_lower)

        # Base score from indicators
        score += easy_count * 5
        score += medium_count * 15
        score += hard_count * 30

        # Adjust based on component count
        score += len(components) * 10

        # Adjust based on message length (more detailed = more complex)
        word_count = len(message_lower.split())
        if word_count > 100:
            score += 20
        elif word_count > 50:
            score += 10
        elif word_count < 20:
            score -= 10

        # Check for specific patterns
        if "from scratch" in message_lower or "new system" in message_lower:
            score += 30
        if "small change" in message_lower or "quick fix" in message_lower:
            score -= 20

        # Normalize score
        score = max(1, min(100, score))

        # Determine difficulty
        if score <= 30:
            difficulty = IssueDifficulty.EASY
        elif score <= 70:
            difficulty = IssueDifficulty.MEDIUM
        else:
            difficulty = IssueDifficulty.HARD

        return score, difficulty

    def _estimate_hours(self, complexity_score: int, difficulty: IssueDifficulty) -> int:
        """
        Estimate hours based on complexity

        Args:
            complexity_score: Complexity score (1-100)
            difficulty: Difficulty level

        Returns:
            Estimated hours
        """
        if difficulty == IssueDifficulty.EASY:
            return max(1, complexity_score // 10)
        elif difficulty == IssueDifficulty.MEDIUM:
            return max(4, complexity_score // 5)
        else:
            return max(8, complexity_score // 3)

    def _identify_risks(self, message_lower: str, components: List[str]) -> List[str]:
        """
        Identify potential risks

        Args:
            message_lower: Lowercase message
            components: Detected components

        Returns:
            List of risk descriptions
        """
        risks = []

        # Security risks
        if any(word in message_lower for word in ["auth", "security", "permission", "access"]):
            risks.append("Security implications - requires careful review")

        # Performance risks
        if any(word in message_lower for word in ["scale", "performance", "optimize", "real-time"]):
            risks.append("Performance impact - requires load testing")

        # Data risks
        if any(word in message_lower for word in ["migration", "database", "schema"]):
            risks.append("Data migration required - backup recommended")

        # Integration risks
        if "integration" in components or "external" in message_lower:
            risks.append("External dependency - may affect reliability")

        # Breaking changes
        if any(word in message_lower for word in ["refactor", "redesign", "breaking"]):
            risks.append("Potential breaking changes - version planning needed")

        return risks

    def _extract_requirements(self, message: str) -> List[str]:
        """
        Extract specific requirements from message

        Args:
            message: User message

        Returns:
            List of requirements
        """
        requirements = []

        # Look for bullet points or numbered lists
        lines = message.split('\n')
        for line in lines:
            line = line.strip()
            if re.match(r'^[-*•]\s+', line):
                requirement = re.sub(r'^[-*•]\s+', '', line)
                requirements.append(requirement)
            elif re.match(r'^\d+[.)]\s+', line):
                requirement = re.sub(r'^\d+[.)]\s+', '', line)
                requirements.append(requirement)

        # Look for "should" or "must" statements
        should_patterns = re.findall(
            r'(?:should|must|need to|has to)\s+([^.,\n]+)',
            message,
            re.IGNORECASE
        )
        for pattern in should_patterns[:3]:  # Limit to 3
            if pattern not in requirements:
                requirements.append(pattern.strip())

        return requirements

    def _generate_labels(
        self,
        components: List[str],
        difficulty: IssueDifficulty
    ) -> List[str]:
        """
        Generate GitHub labels

        Args:
            components: Detected components
            difficulty: Difficulty level

        Returns:
            List of label names
        """
        labels = ["feature-request", "auto-generated"]

        # Add component labels
        for component in components:
            if component != "general":
                labels.append(f"component:{component}")

        # Note: difficulty label is added separately in GitHub service

        return labels
```

### Success Criteria:

#### Automated Verification:
- [ ] Feature analyzer imports correctly: `cd backend && python -c "from app.services.feature_analyzer import FeatureAnalyzer"`
- [ ] Analysis works on sample text: `cd backend && python -c "from app.services.feature_analyzer import FeatureAnalyzer; fa = FeatureAnalyzer(); print(fa.analyze_feature_request('Add a button'))"`

#### Manual Verification:
- [ ] Correctly classifies easy/medium/hard features
- [ ] Extracts meaningful titles and descriptions
- [ ] Identifies relevant components

---

## Phase 4: Enhanced Chat Service

### Overview
Update the chat service to use real feature analysis and GitHub integration.

### Changes Required:

#### 1. Enhanced Chat Service
**File**: `backend/app/services/chat_service.py`
**Changes**: Replace mock implementation with real processing

```python
"""
Enhanced Chat Service with GitHub Integration
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import asyncio
from datetime import datetime
import logging

from app.schemas.workflow import (
    ChatMessageRequest,
    ChatResponse,
    ChatAction,
    ConversationResponse
)
from app.models.conversation import Conversation, Message, MessageRole, ConversationStatus
from app.models.github_integration import GitHubIssue, IssueStatus
from app.services.github_service import GitHubService
from app.services.feature_analyzer import FeatureAnalyzer
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedChatService:
    """Enhanced chat service with GitHub integration"""

    def __init__(self, db: Session, organization_id: str, user_id: str):
        self.db = db
        self.organization_id = organization_id
        self.user_id = user_id
        self.github_service = GitHubService() if settings.GITHUB_TOKEN else None
        self.feature_analyzer = FeatureAnalyzer()

    async def process_message(
        self,
        request: ChatMessageRequest
    ) -> ChatResponse:
        """
        Process a chat message with feature request detection

        Args:
            request: Chat message request

        Returns:
            ChatResponse with processing results
        """
        # Get or create conversation
        conversation_id = request.context.get("conversation_id")
        conversation = self._get_or_create_conversation(conversation_id, request.message)

        # Save user message
        user_message = self._save_message(
            conversation.id,
            MessageRole.USER,
            request.message,
            metadata=request.context
        )

        # Analyze message for feature request
        is_feature_request = self._is_feature_request(request.message)

        if is_feature_request and self.github_service:
            # Process as feature request
            response = await self._process_feature_request(
                request.message,
                conversation,
                user_message
            )
        else:
            # Process as general query
            response = await self._process_general_query(
                request.message,
                conversation
            )

        # Save assistant message
        self._save_message(
            conversation.id,
            MessageRole.ASSISTANT,
            response.message,
            metadata={"results": response.results, "actions": [a.dict() for a in response.suggested_actions]}
        )

        response.conversation_id = str(conversation.id)
        return response

    async def _process_feature_request(
        self,
        message: str,
        conversation: Conversation,
        user_message: Message
    ) -> ChatResponse:
        """
        Process a feature request and create GitHub issue

        Args:
            message: User message
            conversation: Conversation object
            user_message: Message object

        Returns:
            ChatResponse
        """
        # Analyze the feature request
        analysis = self.feature_analyzer.analyze_feature_request(message)

        # Create GitHub issue
        try:
            issue_data = await self.github_service.create_issue(
                title=analysis.title,
                body=analysis.description,
                labels=analysis.labels,
                difficulty=analysis.difficulty
            )

            # Save GitHub issue to database
            github_issue = GitHubIssue(
                organization_id=uuid.UUID(self.organization_id),
                conversation_id=conversation.id,
                message_id=user_message.id,
                issue_number=issue_data["number"],
                issue_url=issue_data["url"],
                issue_title=analysis.title,
                issue_body=analysis.description,
                difficulty=analysis.difficulty,
                labels=analysis.labels,
                status=IssueStatus.CREATED,
                complexity_score=analysis.complexity_score,
                estimated_hours=analysis.estimated_hours,
                auto_merge_enabled=(
                    analysis.difficulty == "easy" and settings.GITHUB_AUTO_MERGE_EASY
                )
            )
            self.db.add(github_issue)
            self.db.commit()

            # Prepare response
            response_message = f"""I've created a GitHub issue for your feature request:

**Issue #{issue_data['number']}**: {analysis.title}
**URL**: {issue_data['url']}
**Difficulty**: {analysis.difficulty.value}
**Estimated Hours**: {analysis.estimated_hours}

{f"**Components**: {', '.join(analysis.components)}" if analysis.components else ""}
{f"**Risks**: {', '.join(analysis.risks)}" if analysis.risks else ""}

The issue has been classified as **{analysis.difficulty.value}** based on complexity analysis.
{"This issue will be automatically merged after successful tests since it's marked as easy." if analysis.difficulty == "easy" else "This issue will require manual review before merging."}

Would you like me to mark this issue as 'ready' for automated implementation?"""

            suggested_actions = [
                ChatAction(
                    action_type="mark_ready",
                    label="Mark issue as ready for implementation",
                    parameters={
                        "issue_id": str(github_issue.id),
                        "issue_number": issue_data["number"]
                    }
                ),
                ChatAction(
                    action_type="view_issue",
                    label="View issue on GitHub",
                    parameters={"url": issue_data["url"]}
                )
            ]

            results = [{
                "type": "github_issue",
                "data": {
                    "id": str(github_issue.id),
                    "number": issue_data["number"],
                    "url": issue_data["url"],
                    "title": analysis.title,
                    "difficulty": analysis.difficulty.value,
                    "estimated_hours": analysis.estimated_hours
                }
            }]

        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            response_message = f"""I understood your feature request but encountered an error creating the GitHub issue:

{str(e)}

Please check that GitHub integration is properly configured."""

            suggested_actions = []
            results = []

        return ChatResponse(
            message=response_message,
            results=results,
            suggested_actions=suggested_actions
        )

    async def _process_general_query(
        self,
        message: str,
        conversation: Conversation
    ) -> ChatResponse:
        """
        Process a general query (non-feature request)

        Args:
            message: User message
            conversation: Conversation object

        Returns:
            ChatResponse
        """
        # Check for status queries
        if "status" in message.lower() and "issue" in message.lower():
            return await self._check_issue_status(message, conversation)

        # Default response
        return ChatResponse(
            message="""I can help you with:
1. Creating feature requests (just describe what you need)
2. Checking issue status (ask about status of issue #X)
3. Document search and management

How can I assist you today?""",
            results=[],
            suggested_actions=[]
        )

    async def _check_issue_status(
        self,
        message: str,
        conversation: Conversation
    ) -> ChatResponse:
        """
        Check status of GitHub issues

        Args:
            message: User message
            conversation: Conversation object

        Returns:
            ChatResponse with status information
        """
        # Extract issue number from message
        import re
        match = re.search(r'#(\d+)', message)

        if match and self.github_service:
            issue_number = int(match.group(1))

            try:
                status = await self.github_service.get_issue_status(issue_number)

                response_message = f"""Issue #{issue_number} Status:
**State**: {status['state']}
**Labels**: {', '.join(status['labels'])}
{f"**Pull Request**: #{status['pr_number']} - {status['pr_url']}" if status['has_pr'] else "**Pull Request**: Not created yet"}
{f"**PR State**: {status['pr_state']}" if status.get('pr_state') else ""}"""

                results = [{"type": "issue_status", "data": status}]

            except Exception as e:
                response_message = f"Failed to check issue status: {str(e)}"
                results = []

        else:
            response_message = "Please specify an issue number (e.g., 'Check status of issue #123')"
            results = []

        return ChatResponse(
            message=response_message,
            results=results,
            suggested_actions=[]
        )

    def get_conversations(self) -> List[ConversationResponse]:
        """
        Get conversation history for the current user and organization

        Returns:
            List of conversations
        """
        conversations = self.db.query(Conversation).filter(
            Conversation.organization_id == uuid.UUID(self.organization_id),
            Conversation.user_id == uuid.UUID(self.user_id),
            Conversation.status != ConversationStatus.ARCHIVED
        ).order_by(Conversation.updated_at.desc()).limit(20).all()

        return [
            ConversationResponse(
                id=str(conv.id),
                title=conv.title or f"Conversation {conv.created_at.strftime('%Y-%m-%d')}",
                last_message=self._get_last_message(conv),
                message_count=len(conv.messages),
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
            for conv in conversations
        ]

    async def mark_issue_ready(self, issue_id: str) -> bool:
        """
        Mark a GitHub issue as ready for implementation

        Args:
            issue_id: Database ID of the GitHub issue

        Returns:
            True if successful
        """
        issue = self.db.query(GitHubIssue).filter(
            GitHubIssue.id == uuid.UUID(issue_id),
            GitHubIssue.organization_id == uuid.UUID(self.organization_id)
        ).first()

        if not issue or not self.github_service:
            return False

        try:
            # Add ready label to trigger lazy-bird
            success = await self.github_service.add_ready_label(issue.issue_number)

            if success:
                issue.status = IssueStatus.READY
                issue.ready_at = datetime.utcnow()
                self.db.commit()

                # If easy issue, enable auto-merge on the eventual PR
                if issue.difficulty == "easy" and issue.auto_merge_enabled:
                    # This will be handled by a background job that monitors for PR creation
                    pass

            return success

        except Exception as e:
            logger.error(f"Failed to mark issue ready: {e}")
            return False

    def _get_or_create_conversation(
        self,
        conversation_id: Optional[str],
        first_message: str
    ) -> Conversation:
        """
        Get existing conversation or create new one

        Args:
            conversation_id: Optional existing conversation ID
            first_message: First message for title generation

        Returns:
            Conversation object
        """
        if conversation_id:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == uuid.UUID(conversation_id),
                Conversation.organization_id == uuid.UUID(self.organization_id)
            ).first()

            if conversation:
                return conversation

        # Create new conversation
        title = first_message[:100] if len(first_message) > 100 else first_message
        conversation = Conversation(
            organization_id=uuid.UUID(self.organization_id),
            user_id=uuid.UUID(self.user_id),
            title=title,
            status=ConversationStatus.ACTIVE
        )
        self.db.add(conversation)
        self.db.commit()

        return conversation

    def _save_message(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> Message:
        """
        Save a message to the database

        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional metadata

        Returns:
            Message object
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.db.add(message)
        self.db.commit()

        return message

    def _is_feature_request(self, message: str) -> bool:
        """
        Determine if a message is a feature request

        Args:
            message: User message

        Returns:
            True if likely a feature request
        """
        feature_indicators = [
            "add", "create", "implement", "build", "make",
            "feature", "functionality", "ability",
            "i want", "i need", "we need", "can you",
            "it should", "it would be nice"
        ]

        message_lower = message.lower()
        return any(indicator in message_lower for indicator in feature_indicators)

    def _get_last_message(self, conversation: Conversation) -> str:
        """
        Get the last message from a conversation

        Args:
            conversation: Conversation object

        Returns:
            Last message content or empty string
        """
        if conversation.messages:
            last_message = sorted(
                conversation.messages,
                key=lambda m: m.created_at,
                reverse=True
            )[0]
            return last_message.content[:100]

        return ""
```

#### 2. Update Chat Routes
**File**: `backend/app/api/routes/chat.py`
**Changes**: Use enhanced service and add new endpoints

```python
"""
Enhanced Chat Interface Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.schemas.workflow import (
    ChatMessageRequest,
    ChatResponse,
    ConversationResponse
)
from app.utils.auth import get_current_user
from app.middleware.organization import get_current_organization
from app.services.chat_service import EnhancedChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Send a chat message and get AI response"""
    service = EnhancedChatService(
        db,
        str(organization.id),
        str(current_user.id)
    )

    try:
        response = await service.process_message(request)
        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Get conversation history"""
    service = EnhancedChatService(
        db,
        str(organization.id),
        str(current_user.id)
    )

    try:
        conversations = service.get_conversations()
        return conversations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversations: {str(e)}"
        )


@router.post("/mark-ready/{issue_id}")
async def mark_issue_ready(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Mark a GitHub issue as ready for implementation"""
    service = EnhancedChatService(
        db,
        str(organization.id),
        str(current_user.id)
    )

    try:
        success = await service.mark_issue_ready(issue_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to mark issue as ready"
            )

        return {"success": True, "message": "Issue marked as ready"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark issue ready: {str(e)}"
        )
```

### Success Criteria:

#### Automated Verification:
- [ ] Enhanced chat service imports correctly: `cd backend && python -c "from app.services.chat_service import EnhancedChatService"`
- [ ] All models import correctly: `cd backend && python -c "from app.models.conversation import Conversation, Message"`
- [ ] API routes compile without errors: `cd backend && python -c "from app.api.routes.chat import router"`

#### Manual Verification:
- [ ] Can process feature requests and create GitHub issues
- [ ] Conversation history is persisted correctly
- [ ] Issue status checking works

---

## Phase 5: Frontend Chat UI Implementation

### Overview
Create the frontend React components for the chat interface.

### Changes Required:

#### 1. Chat Components
**File**: `frontend/src/components/chat/ChatInterface.jsx` (new)
**Changes**: Create main chat interface component

```jsx
import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../../hooks/useChat';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import ChatActions from './ChatActions';

const ChatInterface = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  const {
    messages,
    isLoading,
    sendMessage,
    conversations,
    loadConversation,
    executeAction
  } = useChat();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (message) => {
    const response = await sendMessage(message, conversationId);
    if (response && !conversationId) {
      setConversationId(response.conversation_id);
    }
  };

  const handleActionClick = async (action) => {
    if (action.action_type === 'mark_ready') {
      await executeAction(action);
    } else if (action.action_type === 'view_issue') {
      window.open(action.parameters.url, '_blank');
    }
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-4 right-4 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-colors z-50"
        aria-label="Toggle chat"
      >
        {isOpen ? (
          <svg className="w-6 h-6 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-4l-4 4z" />
          </svg>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-20 right-4 w-96 h-[600px] bg-white rounded-lg shadow-xl z-40 flex flex-col">
          {/* Header */}
          <div className="bg-blue-600 text-white p-4 rounded-t-lg">
            <h3 className="text-lg font-semibold">VibeDocs Assistant</h3>
            <p className="text-sm opacity-90">Request features or ask questions</p>
          </div>

          {/* Conversation List (if no active conversation) */}
          {!conversationId && conversations.length > 0 && (
            <div className="p-4 border-b">
              <div className="text-sm text-gray-600 mb-2">Recent Conversations</div>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {conversations.slice(0, 3).map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => {
                      setConversationId(conv.id);
                      loadConversation(conv.id);
                    }}
                    className="w-full text-left p-2 hover:bg-gray-50 rounded text-sm"
                  >
                    <div className="font-medium truncate">{conv.title}</div>
                    <div className="text-gray-500 text-xs">
                      {new Date(conv.updated_at).toLocaleDateString()}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 mt-8">
                <p className="mb-2">👋 Hi! I can help you with:</p>
                <ul className="text-sm space-y-1">
                  <li>• Creating feature requests</li>
                  <li>• Checking issue status</li>
                  <li>• Searching documents</li>
                </ul>
                <p className="mt-4 text-sm">Just describe what you need!</p>
              </div>
            )}

            {messages.map((message, index) => (
              <div key={index}>
                <ChatMessage message={message} />
                {message.suggested_actions && message.suggested_actions.length > 0 && (
                  <ChatActions
                    actions={message.suggested_actions}
                    onActionClick={handleActionClick}
                  />
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center space-x-2 text-gray-500">
                <div className="animate-pulse">●</div>
                <div className="animate-pulse animation-delay-200">●</div>
                <div className="animate-pulse animation-delay-400">●</div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={isLoading}
          />
        </div>
      )}
    </>
  );
};

export default ChatInterface;
```

**File**: `frontend/src/components/chat/ChatMessage.jsx` (new)
```jsx
import React from 'react';
import ReactMarkdown from 'react-markdown';

const ChatMessage = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-lg px-4 py-2 ${
        isUser
          ? 'bg-blue-600 text-white'
          : 'bg-gray-100 text-gray-900'
      }`}>
        <ReactMarkdown className="prose prose-sm">
          {message.content}
        </ReactMarkdown>

        {message.results && message.results.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-300">
            {message.results.map((result, idx) => (
              <div key={idx} className="text-xs">
                {result.type === 'github_issue' && (
                  <div className="space-y-1">
                    <div>Issue #{result.data.number}</div>
                    <div>Difficulty: {result.data.difficulty}</div>
                    <div>Est. Hours: {result.data.estimated_hours}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
```

**File**: `frontend/src/components/chat/ChatInput.jsx` (new)
```jsx
import React, { useState } from 'react';

const ChatInput = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t">
      <div className="flex space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={disabled}
          className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </form>
  );
};

export default ChatInput;
```

**File**: `frontend/src/components/chat/ChatActions.jsx` (new)
```jsx
import React from 'react';

const ChatActions = ({ actions, onActionClick }) => {
  return (
    <div className="mt-2 space-y-2">
      {actions.map((action, index) => (
        <button
          key={index}
          onClick={() => onActionClick(action)}
          className="w-full text-left px-3 py-2 bg-blue-50 hover:bg-blue-100 rounded text-sm text-blue-700 transition-colors"
        >
          {action.label}
        </button>
      ))}
    </div>
  );
};

export default ChatActions;
```

#### 2. Chat Hook
**File**: `frontend/src/hooks/useChat.js` (new)
```javascript
import { useState, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { chatApi } from '../api/chat';

export const useChat = () => {
  const [messages, setMessages] = useState([]);

  const { data: conversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: chatApi.getConversations,
    staleTime: 30000
  });

  const sendMessageMutation = useMutation({
    mutationFn: ({ message, conversationId }) =>
      chatApi.sendMessage(message, conversationId),
    onSuccess: (response) => {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: response.message, ...response }
      ]);
    }
  });

  const markReadyMutation = useMutation({
    mutationFn: (issueId) => chatApi.markIssueReady(issueId),
    onSuccess: () => {
      // Could show a toast notification
      console.log('Issue marked as ready');
    }
  });

  const sendMessage = useCallback(async (message, conversationId) => {
    // Add user message immediately
    setMessages(prev => [...prev, { role: 'user', content: message }]);

    // Send to backend
    const response = await sendMessageMutation.mutateAsync({
      message,
      conversationId
    });

    return response;
  }, [sendMessageMutation]);

  const loadConversation = useCallback(async (conversationId) => {
    // Load conversation messages
    const messages = await chatApi.getConversationMessages(conversationId);
    setMessages(messages);
  }, []);

  const executeAction = useCallback(async (action) => {
    if (action.action_type === 'mark_ready') {
      await markReadyMutation.mutateAsync(action.parameters.issue_id);
    }
    // Add other action handlers as needed
  }, [markReadyMutation]);

  return {
    messages,
    conversations: conversations || [],
    isLoading: sendMessageMutation.isPending,
    sendMessage,
    loadConversation,
    executeAction
  };
};
```

#### 3. Chat API Client
**File**: `frontend/src/api/chat.js` (new)
```javascript
import { apiClient } from './client';

export const chatApi = {
  sendMessage: async (message, conversationId = null) => {
    const response = await apiClient.post('/chat/message', {
      message,
      context: conversationId ? { conversation_id: conversationId } : {}
    });
    return response.data;
  },

  getConversations: async () => {
    const response = await apiClient.get('/chat/conversations');
    return response.data;
  },

  getConversationMessages: async (conversationId) => {
    // This endpoint would need to be added to the backend
    const response = await apiClient.get(`/chat/conversations/${conversationId}/messages`);
    return response.data;
  },

  markIssueReady: async (issueId) => {
    const response = await apiClient.post(`/chat/mark-ready/${issueId}`);
    return response.data;
  }
};
```

#### 4. Add Chat to Main App
**File**: `frontend/src/App.jsx`
**Changes**: Add ChatInterface component

```jsx
// Add import
import ChatInterface from './components/chat/ChatInterface';

// Add inside the main App component (at the end of the component)
return (
  <>
    {/* Existing app content */}
    <ChatInterface />
  </>
);
```

### Success Criteria:

#### Automated Verification:
- [ ] Frontend builds without errors: `cd frontend && npm run build`
- [ ] No linting errors: `cd frontend && npm run lint`
- [ ] Type checking passes: `cd frontend && npm run type-check`

#### Manual Verification:
- [ ] Chat UI opens and closes properly
- [ ] Can send messages and receive responses
- [ ] Feature requests create GitHub issues
- [ ] Actions buttons work (mark ready, view issue)
- [ ] Conversation history displays correctly

---

## Phase 6: Lazy-Bird Integration and Auto-Merge

### Overview
Set up background job to monitor GitHub PRs and enable auto-merge for easy issues.

### Changes Required:

#### 1. GitHub Monitor Worker
**File**: `backend/app/workers/github_monitor.py` (new)
**Changes**: Create worker to monitor GitHub activity

```python
"""
GitHub Monitor Worker

Monitors GitHub issues and PRs for auto-merge functionality.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import SessionLocal
from app.models.github_integration import GitHubIssue, IssueStatus, IssueDifficulty
from app.services.github_service import GitHubService
from app.core.config import settings

logger = logging.getLogger(__name__)


class GitHubMonitor:
    """Monitor GitHub issues and PRs for automation"""

    def __init__(self):
        self.github_service = GitHubService() if settings.GITHUB_TOKEN else None
        self.check_interval = 60  # Check every minute

    async def run(self):
        """Main monitoring loop"""
        if not self.github_service:
            logger.warning("GitHub token not configured, monitor disabled")
            return

        logger.info("GitHub monitor started")

        while True:
            try:
                await self.check_issues()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(self.check_interval)

    async def check_issues(self):
        """Check all active issues for updates"""
        db: Session = SessionLocal()

        try:
            # Get issues that need checking
            issues = db.query(GitHubIssue).filter(
                GitHubIssue.status.in_([
                    IssueStatus.READY,
                    IssueStatus.IN_PROGRESS,
                    IssueStatus.PR_CREATED,
                    IssueStatus.TESTING
                ])
            ).all()

            for issue in issues:
                await self.check_issue(issue, db)

            db.commit()

        except Exception as e:
            logger.error(f"Error checking issues: {e}")
            db.rollback()
        finally:
            db.close()

    async def check_issue(self, issue: GitHubIssue, db: Session):
        """
        Check individual issue status

        Args:
            issue: GitHub issue to check
            db: Database session
        """
        try:
            # Get issue status from GitHub
            status = await self.github_service.get_issue_status(issue.issue_number)

            # Check if PR was created
            if status["has_pr"] and issue.status != IssueStatus.PR_CREATED:
                issue.pr_number = status["pr_number"]
                issue.pr_url = status["pr_url"]
                issue.status = IssueStatus.PR_CREATED
                issue.pr_created_at = datetime.utcnow()

                # If easy issue, enable auto-merge
                if issue.difficulty == IssueDifficulty.EASY and issue.auto_merge_enabled:
                    await self.enable_auto_merge(issue)

            # Check PR status if we have one
            if issue.pr_number:
                await self.check_pr_status(issue, db)

            # Update issue if it's been closed
            if status["state"] == "closed" and issue.status != IssueStatus.CLOSED:
                issue.status = IssueStatus.CLOSED

        except Exception as e:
            logger.error(f"Error checking issue {issue.issue_number}: {e}")

    async def check_pr_status(self, issue: GitHubIssue, db: Session):
        """
        Check PR status and handle auto-merge

        Args:
            issue: GitHub issue with PR
            db: Database session
        """
        try:
            pr_status = await self.github_service.get_pr_status(issue.pr_number)

            # Update testing status
            if pr_status["checks_passing"] and issue.status == IssueStatus.PR_CREATED:
                issue.status = IssueStatus.TESTING

            # Check if ready to merge
            if (
                pr_status["mergeable"] and
                pr_status["checks_passing"] and
                issue.difficulty == IssueDifficulty.EASY and
                issue.auto_merge_enabled
            ):
                # For easy issues, auto-merge if checks pass
                if not settings.GITHUB_REQUIRE_APPROVAL_FOR_MERGE or pr_status["approved"]:
                    success = await self.github_service.merge_pr(
                        issue.pr_number,
                        f"Auto-merge: {issue.issue_title}"
                    )

                    if success:
                        issue.status = IssueStatus.MERGED
                        issue.merged_at = datetime.utcnow()
                        logger.info(f"Auto-merged PR #{issue.pr_number}")

            # Check if already merged
            if pr_status["merged"]:
                issue.status = IssueStatus.MERGED
                issue.merged_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error checking PR {issue.pr_number}: {e}")

    async def enable_auto_merge(self, issue: GitHubIssue):
        """
        Enable auto-merge for a PR

        Args:
            issue: GitHub issue with PR
        """
        try:
            # Wait a moment for GitHub to process the PR
            await asyncio.sleep(5)

            success = await self.github_service.enable_auto_merge(issue.pr_number)

            if success:
                logger.info(f"Enabled auto-merge for PR #{issue.pr_number}")
            else:
                logger.warning(f"Failed to enable auto-merge for PR #{issue.pr_number}")

        except Exception as e:
            logger.error(f"Error enabling auto-merge: {e}")


# Function to run the monitor
async def run_github_monitor():
    """Run the GitHub monitor"""
    monitor = GitHubMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(run_github_monitor())
```

#### 2. Add Monitor to Main Application
**File**: `backend/app/main.py`
**Changes**: Start GitHub monitor on application startup

```python
# Add import
from app.workers.github_monitor import run_github_monitor

# Add to startup event (after existing startup code)
@app.on_event("startup")
async def startup_event():
    # ... existing code ...

    # Start GitHub monitor in background
    if settings.GITHUB_TOKEN:
        asyncio.create_task(run_github_monitor())
        logger.info("GitHub monitor started")
```

#### 3. Environment Configuration
**File**: `backend/.env.example` (new)
**Changes**: Document required environment variables

```bash
# GitHub Integration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=yourusername/vibedocs

# Lazy-Bird Integration (optional - for direct API calls)
LAZY_BIRD_API_URL=https://api.lazy-bird.com
LAZY_BIRD_API_KEY=your_lazy_bird_api_key

# Auto-merge Settings
GITHUB_AUTO_MERGE_EASY=true
GITHUB_REQUIRE_APPROVAL_FOR_MERGE=false  # Set to true in production
```

### Success Criteria:

#### Automated Verification:
- [ ] GitHub monitor imports correctly: `cd backend && python -c "from app.workers.github_monitor import GitHubMonitor"`
- [ ] Application starts with monitor: `cd backend && python -m uvicorn app.main:app`

#### Manual Verification:
- [ ] Monitor detects new PRs within 1 minute
- [ ] Auto-merge triggers for easy issues after tests pass
- [ ] PR status updates correctly in database
- [ ] Issue status transitions work properly

---

## Testing Strategy

### Unit Tests:

#### Backend Tests:
- Test feature analyzer classification logic
- Test GitHub API service methods
- Test chat service message processing
- Test conversation persistence

#### Frontend Tests:
- Test chat component rendering
- Test message send/receive flow
- Test action button handlers
- Test conversation switching

### Integration Tests:

1. **End-to-End Feature Request Flow:**
   - User types feature request in chat
   - System creates GitHub issue
   - Issue gets marked as ready
   - Lazy-bird picks up issue
   - PR gets created
   - Tests run
   - Auto-merge triggers (for easy issues)

2. **Chat Conversation Flow:**
   - Create conversation
   - Send multiple messages
   - Load conversation history
   - Switch between conversations

### Manual Testing Steps:

1. **Setup Verification:**
   - Configure GitHub token with repo permissions
   - Install lazy-bird on development machine
   - Configure lazy-bird for the repository

2. **Feature Request Testing:**
   - Open chat UI
   - Type: "Add a button to export data as CSV"
   - Verify issue created with "easy" label
   - Mark issue as ready
   - Verify lazy-bird picks it up within 60 seconds
   - Monitor PR creation and auto-merge

3. **Complex Feature Testing:**
   - Type: "Implement real-time WebSocket notifications"
   - Verify issue created with "hard" label
   - Verify no auto-merge enabled
   - Check manual review required

## Performance Considerations

- **Chat Response Time**: Target < 2 seconds for feature analysis
- **GitHub API Rate Limits**: Monitor usage, implement caching if needed
- **Database Queries**: Index conversation_id and organization_id columns
- **Polling Interval**: 60 seconds for GitHub monitor (configurable)

## Migration Notes

1. Run database migrations to create new tables
2. Configure GitHub personal access token with repo scope
3. Set up lazy-bird on the development/CI server
4. Configure GitHub repository settings to allow auto-merge
5. Test with a few simple issues before enabling for production

## Security Considerations

- GitHub token stored securely in environment variables
- Organization-scoped access enforced for all chat operations
- Input sanitization for feature descriptions
- Rate limiting on chat endpoints to prevent abuse
- Audit logging for all GitHub operations

## References

- GitHub API Documentation: https://docs.github.com/en/rest
- Lazy-Bird Documentation: https://github.com/yusufkaraaslan/lazy-bird
- Original VibeDocs Architecture: `CLAUDE.md`
- Existing API Structure: `thoughts/shared/plans/2025-11-08-rest-api-specification.md`
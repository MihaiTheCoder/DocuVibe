# VibeDocs REST API Specification Implementation Plan

## Overview

Comprehensive REST API specification for VibeDocs document management system supporting document processing, pipeline management, workflows, search, and task management with multi-tenant architecture.

## Current State Analysis

The backend is in "hello world" state with:
- Base infrastructure (FastAPI, SQLAlchemy, multi-tenant base model)
- Pipeline base classes and registry pattern
- Azure Blob Storage service
- Only 2 health check endpoints exist (`/api/v1/`, `/api/v1/health`)

### Key Discoveries:
- Multi-tenant base model exists at [backend/app/models/base.py:12]
- Pipeline architecture defined at [backend/app/pipelines/base.py:35]
- Blob storage service ready at [backend/app/services/blob_storage.py]
- All endpoints will be prefixed with `/api/v1` per [backend/app/core/config.py:78]

## Desired End State

A fully functional REST API with:
- Complete authentication system with Google OAuth
- Document upload, processing, and management
- Configurable pipeline management
- Workflow creation and execution
- Advanced search capabilities (text + semantic)
- User and organization management
- Task assignment and tracking system
- Real-time notifications support

### Success Verification:
- All 60+ endpoints documented and tested
- Swagger/OpenAPI documentation available at `/api/v1/docs`
- Multi-tenant security enforced on all endpoints
- Response times under 500ms for standard operations

## What We're NOT Doing

- WebSocket implementation (will use polling for now)
- Batch operations (will add in Phase 2)
- Advanced RBAC beyond admin/member roles
- External API integrations (except Google OAuth)
- GraphQL endpoints

## Implementation Approach

RESTful API following OpenAPI 3.0 specification with:
- JWT-based authentication
- Organization context via headers
- Pydantic for request/response validation
- Consistent error handling
- Rate limiting per organization

## Phase 1: Core Models and Authentication

### Overview
Establish database models, authentication system, and organization context middleware.

### Changes Required:

#### 1. Database Models
**Files to create:**

**`backend/app/models/user.py`**
```python
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid

class User(Base):
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

    # Relationships
    organizations = relationship("UserOrganization", back_populates="user")
    documents = relationship("Document", back_populates="uploaded_by")
    tasks = relationship("Task", back_populates="assigned_to")
```

**`backend/app/models/organization.py`**
```python
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255))
    settings = Column(JSON, default={})
    subscription_tier = Column(String(50), default="free")
    storage_quota_gb = Column(Integer, default=10)
    storage_used_bytes = Column(BigInteger, default=0)

    # Relationships
    users = relationship("UserOrganization", back_populates="organization")
    documents = relationship("Document", back_populates="organization")

class UserOrganization(Base):
    __tablename__ = "user_organizations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), primary_key=True)
    role = Column(String(50), default="member")  # admin, member
    invited_at = Column(DateTime(timezone=True))
    joined_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="organizations")
    organization = relationship("Organization", back_populates="users")
```

**`backend/app/models/document.py`**
```python
class Document(TenantModel):
    __tablename__ = "documents"

    filename = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_size = Column(BigInteger)
    blob_url = Column(String(1000))
    status = Column(String(50), default="pending")  # pending, processing, ready, failed
    stage = Column(String(50), default="draft")  # draft, review, approved, signed, archived

    # Extracted content
    text_content = Column(Text)
    metadata = Column(JSON, default={})
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
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    pipeline = relationship("Pipeline")
    tasks = relationship("Task", back_populates="document")
```

#### 2. Authentication Endpoints
**File: `backend/app/api/routes/auth.py`**

```python
@router.get("/google/login")
async def google_login():
    """Redirect to Google OAuth"""
    # Returns Google OAuth URL

@router.get("/google/callback")
async def google_callback(code: str):
    """Handle Google OAuth callback"""
    # Exchange code for token
    # Create/update user
    # Return JWT token

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user"""
    # Invalidate token

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    # Return user profile
```

### Success Criteria:

#### Automated Verification:
- [ ] Database migrations apply: `alembic upgrade head`
- [ ] Models import successfully: `python -c "from app.models import user, organization, document"`
- [ ] Unit tests pass: `pytest tests/models/`
- [ ] Auth endpoints return 200: `curl localhost:8000/api/v1/auth/google/login`

#### Manual Verification:
- [ ] Google OAuth flow completes successfully
- [ ] JWT tokens are issued and validated
- [ ] Organization context is enforced

---

## Phase 2: Document Management Endpoints

### Overview
Implement complete document upload, processing, and management endpoints.

### API Endpoints:

#### Document Operations
```
POST   /api/v1/documents/upload
       Request: multipart/form-data with file and metadata
       Response: DocumentResponse with id, status, processing_job_id

GET    /api/v1/documents
       Query: ?status=ready&stage=approved&page=1&limit=20
       Response: PaginatedList[DocumentResponse]

GET    /api/v1/documents/{document_id}
       Response: DocumentDetailResponse with full metadata

PUT    /api/v1/documents/{document_id}
       Request: DocumentUpdateRequest (metadata, classification, stage)
       Response: DocumentResponse

DELETE /api/v1/documents/{document_id}
       Response: {"success": true}

GET    /api/v1/documents/{document_id}/download
       Response: File stream with proper headers

POST   /api/v1/documents/{document_id}/reprocess
       Request: ReprocessRequest (pipeline_id optional)
       Response: {"job_id": "...", "status": "queued"}

# Document Stages
PUT    /api/v1/documents/{document_id}/stage
       Request: {"stage": "review", "comment": "Ready for review"}
       Response: DocumentResponse

POST   /api/v1/documents/{document_id}/assign
       Request: {"user_id": "..."}
       Response: DocumentResponse

POST   /api/v1/documents/{document_id}/approve
       Request: {"comment": "Approved"}
       Response: DocumentResponse

POST   /api/v1/documents/{document_id}/sign
       Request: {"signature_data": "..."}
       Response: DocumentResponse

POST   /api/v1/documents/{document_id}/archive
       Request: {"reason": "..."}
       Response: DocumentResponse
```

### Success Criteria:

#### Automated Verification:
- [ ] File upload endpoint accepts multipart data: `curl -F file=@test.pdf /api/v1/documents/upload`
- [ ] Document list endpoint returns paginated results
- [ ] Stage transitions follow valid workflow rules
- [ ] Unit tests pass: `pytest tests/api/test_documents.py`

#### Manual Verification:
- [ ] Large files (>100MB) upload successfully
- [ ] Download preserves original filename
- [ ] Reprocessing triggers background job

---

## Phase 3: Pipeline Management CRUD

### Overview
Enable dynamic pipeline creation, configuration, and management.

### API Endpoints:

#### Pipeline CRUD
```
POST   /api/v1/pipelines
       Request: {
         "name": "Invoice Processor",
         "type": "pdf",
         "config": {
           "ocr_enabled": true,
           "language": "ro",
           "extractors": ["invoice", "receipt"]
         }
       }
       Response: PipelineResponse

GET    /api/v1/pipelines
       Response: List[PipelineResponse]

GET    /api/v1/pipelines/{pipeline_id}
       Response: PipelineDetailResponse

PUT    /api/v1/pipelines/{pipeline_id}
       Request: PipelineUpdateRequest
       Response: PipelineResponse

DELETE /api/v1/pipelines/{pipeline_id}
       Response: {"success": true}

# Pipeline Operations
POST   /api/v1/pipelines/{pipeline_id}/test
       Request: {"sample_file_id": "..."}
       Response: TestResultResponse

GET    /api/v1/pipelines/{pipeline_id}/stats
       Response: PipelineStatsResponse (success_rate, avg_time, etc.)

POST   /api/v1/pipelines/{pipeline_id}/clone
       Request: {"name": "New Pipeline Name"}
       Response: PipelineResponse
```

### Database Model:
**`backend/app/models/pipeline.py`**
```python
class Pipeline(TenantModel):
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
```

### Success Criteria:

#### Automated Verification:
- [ ] Pipeline CRUD operations work: `pytest tests/api/test_pipelines.py`
- [ ] Default pipeline cannot be deleted
- [ ] Pipeline config validates against schema

#### Manual Verification:
- [ ] Pipeline changes affect document processing
- [ ] Statistics update correctly

---

## Phase 4: Workflow and AI/Chat Endpoints

### Overview
Implement workflow creation via AI assistance and chat interface.

### API Endpoints:

#### Workflow Management
```
POST   /api/v1/workflows/create-from-chat
       Request: {
         "prompt": "Create a workflow for invoice approval",
         "context": {"department": "Finance"}
       }
       Response: WorkflowResponse

GET    /api/v1/workflows
       Response: List[WorkflowResponse]

GET    /api/v1/workflows/{workflow_id}
       Response: WorkflowDetailResponse

POST   /api/v1/workflows/{workflow_id}/execute
       Request: {"document_ids": [...], "parameters": {...}}
       Response: WorkflowExecutionResponse

# Chat Interface
POST   /api/v1/chat/message
       Request: {
         "message": "Find all invoices from last month",
         "context": {"conversation_id": "..."}
       }
       Response: ChatResponse with results and suggested actions

GET    /api/v1/chat/conversations
       Response: List[ConversationResponse]

POST   /api/v1/chat/suggest-workflow
       Request: {"document_type": "invoice"}
       Response: WorkflowSuggestionResponse
```

### Database Model:
**`backend/app/models/workflow.py`**
```python
class Workflow(TenantModel):
    __tablename__ = "workflows"

    name = Column(String(255))
    description = Column(Text)
    steps = Column(JSON)  # Array of step definitions
    triggers = Column(JSON)  # Event triggers
    created_by_ai = Column(Boolean, default=False)
    ai_prompt = Column(Text)  # Original prompt if AI-created

class WorkflowExecution(TenantModel):
    __tablename__ = "workflow_executions"

    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"))
    status = Column(String(50))  # running, completed, failed
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    results = Column(JSON)
```

### Success Criteria:

#### Automated Verification:
- [ ] Workflow creation from chat prompt works
- [ ] Workflow execution creates tasks
- [ ] Chat queries return relevant results

#### Manual Verification:
- [ ] AI suggestions are contextually relevant
- [ ] Workflow execution updates document stages correctly

---

## Phase 5: Search and Registry Endpoints

### Overview
Implement advanced search with text and semantic capabilities.

### API Endpoints:

#### Search Operations
```
POST   /api/v1/search/documents
       Request: {
         "query": "invoices from Supplier X",
         "filters": {
           "date_range": {"from": "2024-01-01", "to": "2024-12-31"},
           "stage": ["approved", "signed"],
           "classification": "invoice"
         },
         "search_type": "hybrid"  // text, semantic, hybrid
       }
       Response: SearchResultsResponse

POST   /api/v1/search/semantic
       Request: {
         "query": "documents about office supplies",
         "top_k": 10,
         "threshold": 0.7
       }
       Response: SemanticSearchResponse

GET    /api/v1/search/facets
       Query: ?field=classification&field=stage
       Response: FacetsResponse with counts

# Registry/Metadata Search
GET    /api/v1/registry/search
       Query: ?metadata.vendor=SupplierX&metadata.amount_gt=1000
       Response: List[DocumentResponse]

POST   /api/v1/registry/query
       Request: {
         "sql": "SELECT * FROM documents WHERE metadata->>'vendor' = $1",
         "params": ["SupplierX"]
       }
       Response: QueryResultResponse
```

### Success Criteria:

#### Automated Verification:
- [ ] Text search returns relevant results
- [ ] Semantic search uses vector embeddings
- [ ] Faceted search provides accurate counts

#### Manual Verification:
- [ ] Search results are relevant and ranked properly
- [ ] Complex queries execute within 2 seconds

---

## Phase 6: User and Profile Management

### Overview
Implement user profile management and notification preferences.

### API Endpoints:

#### User Management
```
GET    /api/v1/users
       Response: List[UserResponse] (org members only)

GET    /api/v1/users/{user_id}
       Response: UserDetailResponse

PUT    /api/v1/users/profile
       Request: {
         "full_name": "...",
         "preferences": {
           "language": "ro",
           "theme": "dark",
           "notifications": {...}
         }
       }
       Response: UserResponse

# Notifications
GET    /api/v1/users/notifications
       Query: ?unread=true&limit=20
       Response: List[NotificationResponse]

PUT    /api/v1/users/notifications/{notification_id}/read
       Response: NotificationResponse

POST   /api/v1/users/notifications/settings
       Request: {
         "email_enabled": true,
         "types": ["task_assigned", "document_approved"]
       }
       Response: NotificationSettingsResponse
```

### Database Model:
**`backend/app/models/notification.py`**
```python
class Notification(TenantModel):
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    type = Column(String(50))  # task_assigned, document_approved, etc.
    title = Column(String(255))
    message = Column(Text)
    data = Column(JSON)  # Additional context
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
```

### Success Criteria:

#### Automated Verification:
- [ ] Profile updates persist correctly
- [ ] Notification preferences filter correctly
- [ ] Unread count is accurate

#### Manual Verification:
- [ ] Theme preference applies in UI
- [ ] Email notifications respect preferences

---

## Phase 7: Task Management

### Overview
Implement task assignment, claiming, and completion system.

### API Endpoints:

#### Task Management
```
POST   /api/v1/tasks
       Request: {
         "title": "Review invoice",
         "description": "...",
         "document_id": "...",
         "assigned_to_id": "...",
         "due_date": "2024-12-31T23:59:59Z"
       }
       Response: TaskResponse

GET    /api/v1/tasks
       Query: ?assigned_to=me&status=pending&sort=due_date
       Response: List[TaskResponse]

GET    /api/v1/tasks/{task_id}
       Response: TaskDetailResponse

PUT    /api/v1/tasks/{task_id}
       Request: TaskUpdateRequest
       Response: TaskResponse

# Task Actions
POST   /api/v1/tasks/{task_id}/assign
       Request: {"user_id": "..."}
       Response: TaskResponse

POST   /api/v1/tasks/{task_id}/claim
       Response: TaskResponse (assigns to current user)

POST   /api/v1/tasks/{task_id}/complete
       Request: {"comment": "...", "result": {...}}
       Response: TaskResponse

POST   /api/v1/tasks/{task_id}/reject
       Request: {"reason": "..."}
       Response: TaskResponse

# Task Templates
GET    /api/v1/tasks/templates
       Response: List[TaskTemplateResponse]

POST   /api/v1/tasks/from-template
       Request: {"template_id": "...", "parameters": {...}}
       Response: TaskResponse
```

### Database Model:
**`backend/app/models/task.py`**
```python
class Task(TenantModel):
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
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    document = relationship("Document")
```

### Success Criteria:

#### Automated Verification:
- [ ] Task CRUD operations work correctly
- [ ] Task assignment creates notifications
- [ ] Completed tasks update related documents

#### Manual Verification:
- [ ] Task list filters work correctly
- [ ] Due date reminders are sent
- [ ] Task templates create consistent tasks

---

## Phase 8: Organization Management

### Overview
Implement organization settings and member management.

### API Endpoints:

#### Organization Management
```
GET    /api/v1/organizations/current
       Response: OrganizationDetailResponse

PUT    /api/v1/organizations/current
       Request: {
         "display_name": "...",
         "settings": {...}
       }
       Response: OrganizationResponse

# Member Management
GET    /api/v1/organizations/members
       Response: List[OrganizationMemberResponse]

POST   /api/v1/organizations/members/invite
       Request: {"email": "...", "role": "member"}
       Response: InvitationResponse

PUT    /api/v1/organizations/members/{user_id}/role
       Request: {"role": "admin"}
       Response: OrganizationMemberResponse

DELETE /api/v1/organizations/members/{user_id}
       Response: {"success": true}
```

### Success Criteria:

#### Automated Verification:
- [ ] Organization updates persist
- [ ] Member role changes take effect immediately
- [ ] Invitation emails are sent

#### Manual Verification:
- [ ] Settings changes reflect in application behavior
- [ ] Role-based access control works correctly

---

## Testing Strategy

### Unit Tests:
- Test all models and schemas
- Test service layer business logic
- Mock external services (Qdrant, OCR, Azure)

### Integration Tests:
- Test complete API flows
- Test multi-tenant isolation
- Test authentication and authorization

### Manual Testing Steps:
1. Complete document lifecycle (upload → process → approve → archive)
2. Create and execute workflow via chat
3. Perform complex searches
4. Assign and complete tasks
5. Test organization member management

## Performance Considerations

- Implement pagination on all list endpoints (default 20, max 100)
- Add database indexes on frequently queried fields
- Cache organization settings and user preferences
- Use background jobs for document processing
- Implement rate limiting (100 req/min per org)

## Migration Notes

Since this is a greenfield implementation:
1. Create initial Alembic migration with all models
2. Seed database with test organization and admin user
3. Import any existing documents if migrating from legacy system

## Security Considerations

- All endpoints require authentication (except auth endpoints)
- Organization context enforced at middleware level
- SQL injection prevention via SQLAlchemy ORM
- File upload validation (type, size, virus scan)
- Rate limiting per organization
- Audit logging for sensitive operations

## API Documentation

- Auto-generate OpenAPI spec via FastAPI
- Interactive documentation at `/api/v1/docs`
- ReDoc documentation at `/api/v1/redoc`
- Postman collection export available

## Error Response Format

All errors follow consistent format:
```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Document with id 123 not found",
    "details": {...},
    "timestamp": "2024-11-08T10:30:00Z"
  }
}
```

## References

- Original requirements: User-provided UI action list
- FastAPI documentation: https://fastapi.tiangolo.com/
- SQLAlchemy patterns: https://docs.sqlalchemy.org/
- OpenAPI specification: https://swagger.io/specification/
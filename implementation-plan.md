# VibeDocs - AI-Powered Document Management System Implementation Plan

## Overview

VibeDocs is a privacy-first, multi-tenant document management system designed specifically for Romanian Hospital Managers. It leverages open-source AI models for document processing while maintaining a clean, modular architecture that's "vibe code friendly" - emphasizing small files, low complexity, and repeated patterns.

## Current State Analysis

- **Starting Point**: Greenfield project - completely blank
- **Target Users**: Romanian Hospital Managers
- **Key Requirements**: Privacy-first (no cloud AI), multi-tenant, extensible document pipelines
- **Technical Constraints**: Must be vibe code friendly (small files, low complexity, minimal dependencies)

## Desired End State

A fully functional document management system with:
- Multi-tenant support with organization management
- Automated document processing with OCR and classification
- Hybrid search (vector + full-text) via Qdrant
- Extensible document pipeline architecture
- Chat UI for feature requests with GitHub integration
- Per-tenant customization capabilities

## Technology Stack

### Backend (Python/FastAPI)
```
- FastAPI (0.115.0) - Modern, fast web framework
- SQLAlchemy (2.0) - ORM for database operations
- Alembic - Database migrations
- Pydantic (2.9) - Data validation
- python-jose - JWT token handling
- google-auth - Google OAuth integration
- qdrant-client - Vector database client
- Pillow - Image processing
- pypdf - PDF processing
- celery - Async task processing
- redis - Task queue backend
- httpx - HTTP client for API calls
```

### Frontend (React)
```
- React (18.3) - UI framework
- Vite - Build tool (fast, simple)
- React Router (6.0) - Routing
- Tanstack Query - Data fetching & caching
- Zustand - Simple state management
- Tailwind CSS - Utility-first CSS
- Shadcn/ui - Component library (copy-paste, no dependency)
- react-dropzone - File uploads
```

### Infrastructure
```
- PostgreSQL - Main database
- Qdrant - Vector database
- Redis - Cache & queue
- MinIO - S3-compatible file storage (self-hosted)
```

## Project Structure

```
VibeDocs/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth/
│   │   │   │   ├── google.py         # Google OAuth endpoints
│   │   │   │   └── tokens.py         # JWT management
│   │   │   ├── documents/
│   │   │   │   ├── upload.py         # Document upload
│   │   │   │   ├── search.py         # Search endpoints
│   │   │   │   └── classify.py       # Classification endpoints
│   │   │   ├── organizations/
│   │   │   │   ├── crud.py           # Org CRUD operations
│   │   │   │   └── invites.py        # Invitation system
│   │   │   ├── chat/
│   │   │   │   └── features.py       # Feature request handler
│   │   │   └── tenants/
│   │   │       └── custom.py         # Tenant customizations
│   │   ├── core/
│   │   │   ├── config.py             # Configuration
│   │   │   ├── database.py           # Database setup
│   │   │   ├── security.py           # Security utilities
│   │   │   └── tenant.py             # Tenant context
│   │   ├── models/
│   │   │   ├── user.py               # User model
│   │   │   ├── organization.py       # Organization model
│   │   │   ├── document.py           # Document model
│   │   │   └── base.py               # Base model with tenant
│   │   ├── pipelines/
│   │   │   ├── base.py               # Base pipeline class
│   │   │   ├── pdf/
│   │   │   │   ├── processor.py      # PDF processing
│   │   │   │   └── extractor.py      # PDF text extraction
│   │   │   ├── image/
│   │   │   │   ├── processor.py      # Image processing
│   │   │   │   └── ocr.py            # OCR with Mistral
│   │   │   └── extractors/
│   │   │       ├── invoice.py        # Invoice field extraction
│   │   │       ├── receipt.py        # Receipt field extraction
│   │   │       ├── contract.py       # Contract party extraction
│   │   │       └── identity.py       # ID owner extraction
│   │   ├── services/
│   │   │   ├── qdrant.py             # Qdrant operations
│   │   │   ├── classifier.py         # Document classifier
│   │   │   ├── embeddings.py         # Embedding generation
│   │   │   ├── storage.py            # MinIO operations
│   │   │   └── github.py             # GitHub integration
│   │   └── workers/
│   │       ├── celery.py             # Celery setup
│   │       └── tasks.py              # Background tasks
│   ├── migrations/                    # Alembic migrations
│   ├── tests/                         # Test files
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   │   ├── GoogleLogin.tsx   # Google login button
│   │   │   │   └── ProtectedRoute.tsx
│   │   │   ├── documents/
│   │   │   │   ├── UploadZone.tsx    # Drag & drop upload
│   │   │   │   ├── DocumentList.tsx  # Document grid/list
│   │   │   │   ├── DocumentView.tsx  # Document viewer
│   │   │   │   └── SearchBar.tsx     # Search interface
│   │   │   ├── organizations/
│   │   │   │   ├── OrgSelector.tsx   # Organization switcher
│   │   │   │   ├── InviteModal.tsx   # Invite users
│   │   │   │   └── CreateOrg.tsx     # Create organization
│   │   │   ├── chat/
│   │   │   │   ├── ChatWidget.tsx    # Chat UI
│   │   │   │   └── FeatureRequest.tsx
│   │   │   └── common/
│   │   │       ├── Layout.tsx        # Main layout
│   │   │       ├── Button.tsx        # Reusable button
│   │   │       └── Card.tsx          # Card component
│   │   ├── hooks/
│   │   │   ├── useAuth.ts            # Auth hook
│   │   │   ├── useOrganization.ts    # Org context
│   │   │   └── useDocuments.ts       # Document operations
│   │   ├── services/
│   │   │   ├── api.ts                # API client setup
│   │   │   ├── auth.ts               # Auth service
│   │   │   └── documents.ts          # Document service
│   │   ├── stores/
│   │   │   ├── authStore.ts          # Auth state
│   │   │   └── orgStore.ts           # Organization state
│   │   ├── pages/
│   │   │   ├── Login.tsx             # Login page
│   │   │   ├── Dashboard.tsx         # Main dashboard
│   │   │   ├── Documents.tsx         # Document management
│   │   │   └── Settings.tsx          # Settings page
│   │   └── App.tsx                   # Root component
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml                 # Local development setup
├── .env.example                       # Environment variables template
└── README.md                          # Project documentation
```

## Implementation Phases

### Phase 1: Core Infrastructure Setup

#### Overview
Set up the basic project structure, authentication, and multi-tenant database schema.

#### Changes Required:

**1. Backend Core Setup**
```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    QDRANT_URL: str
    MINIO_URL: str
    REDIS_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
```

```python
# backend/app/models/base.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class TenantModel(Base):
    __abstract__ = True

    organization_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**2. Database Schema**
```sql
-- Multi-tenant schema design
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    settings JSONB,
    created_at TIMESTAMP
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    google_id VARCHAR(255),
    created_at TIMESTAMP
);

CREATE TABLE organization_members (
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(50),
    PRIMARY KEY (organization_id, user_id)
);

CREATE TABLE documents (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    filename VARCHAR(255),
    file_type VARCHAR(50),
    storage_path TEXT,
    metadata JSONB,
    classification VARCHAR(100),
    vector_id VARCHAR(255),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP
);
```

#### Success Criteria:

**Automated Verification:**
- [ ] Database migrations apply: `alembic upgrade head`
- [ ] FastAPI server starts: `uvicorn app.main:app --reload`
- [ ] Authentication endpoints work: `curl localhost:8000/api/auth/google`
- [ ] Tests pass: `pytest tests/`

**Manual Verification:**
- [ ] Can login with Google OAuth
- [ ] Can create and switch organizations
- [ ] Multi-tenant isolation works

---

### Phase 2: Document Processing Pipeline

#### Overview
Implement the extensible document processing pipeline with OCR and classification.

#### Changes Required:

**1. Base Pipeline Architecture**
```python
# backend/app/pipelines/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class DocumentPipeline(ABC):
    """Base class for all document pipelines"""

    @abstractmethod
    async def process(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process document and return extracted data"""
        pass

    @abstractmethod
    def supports_type(self, file_type: str) -> bool:
        """Check if pipeline supports file type"""
        pass

class PipelineRegistry:
    """Registry for document pipelines"""
    def __init__(self):
        self.pipelines = {}
        self.extractors = {}

    def register_pipeline(self, name: str, pipeline: DocumentPipeline):
        self.pipelines[name] = pipeline

    def register_extractor(self, doc_type: str, extractor):
        self.extractors[doc_type] = extractor

    def get_pipeline(self, file_type: str):
        for pipeline in self.pipelines.values():
            if pipeline.supports_type(file_type):
                return pipeline
        return None

pipeline_registry = PipelineRegistry()
```

**2. OCR Integration**
```python
# backend/app/pipelines/image/ocr.py
import httpx
from typing import Dict, Any

class MistralOCR:
    """Mistral OCR service wrapper"""

    async def extract_text(self, image_path: str) -> str:
        # Implementation for Mistral OCR
        # Using local deployment for privacy
        pass
```

**3. Qdrant Integration**
```python
# backend/app/services/qdrant.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

class QdrantService:
    def __init__(self, url: str):
        self.client = QdrantClient(url=url)

    async def create_collection(self, org_id: str):
        collection_name = f"org_{org_id}"
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )

    async def hybrid_search(self, org_id: str, query: str, vector: list, limit: int = 10):
        # Implement hybrid search combining vector and full-text
        pass
```

#### Success Criteria:

**Automated Verification:**
- [ ] Pipeline tests pass: `pytest tests/pipelines/`
- [ ] OCR endpoint works: `curl -F "file=@test.jpg" localhost:8000/api/documents/upload`
- [ ] Qdrant connection works: `python -m app.services.qdrant`

**Manual Verification:**
- [ ] Can upload and process PDFs
- [ ] Can upload and OCR images
- [ ] Search returns relevant results

---

### Phase 3: Frontend Implementation

#### Overview
Build the React frontend with modular, tenant-customizable components.

#### Changes Required:

**1. Component Structure**
```tsx
// frontend/src/components/documents/UploadZone.tsx
import { useDropzone } from 'react-dropzone';
import { useDocuments } from '@/hooks/useDocuments';

export const UploadZone = () => {
  const { uploadDocument } = useDocuments();

  const { getRootProps, getInputProps } = useDropzone({
    onDrop: async (files) => {
      for (const file of files) {
        await uploadDocument(file);
      }
    }
  });

  return (
    <div {...getRootProps()} className="border-2 border-dashed p-8">
      <input {...getInputProps()} />
      <p>Drop documents here or click to select</p>
    </div>
  );
};
```

**2. State Management**
```ts
// frontend/src/stores/authStore.ts
import { create } from 'zustand';

interface AuthState {
  user: User | null;
  organization: Organization | null;
  setUser: (user: User) => void;
  setOrganization: (org: Organization) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  organization: null,
  setUser: (user) => set({ user }),
  setOrganization: (organization) => set({ organization }),
  logout: () => set({ user: null, organization: null })
}));
```

#### Success Criteria:

**Automated Verification:**
- [ ] Frontend builds: `npm run build`
- [ ] Type checking passes: `npm run type-check`
- [ ] Linting passes: `npm run lint`

**Manual Verification:**
- [ ] UI loads and renders correctly
- [ ] Can upload documents via drag & drop
- [ ] Search interface works
- [ ] Organization switcher functions

---

### Phase 4: Advanced Features

#### Overview
Implement classification, GitHub integration, and tenant customization.

#### Changes Required:

**1. Document Classification**
```python
# backend/app/services/classifier.py
from typing import List, Dict
import numpy as np

class ExtremeClassifier:
    """Extreme classification for document categorization"""

    def __init__(self):
        self.model = None
        self.categories = []

    async def train(self, documents: List[Dict], labels: List[str]):
        """Train classifier on user-labeled documents"""
        # Implement few-shot learning
        pass

    async def predict(self, document: Dict) -> str:
        """Predict document category"""
        pass
```

**2. GitHub Integration**
```python
# backend/app/services/github.py
import httpx
from typing import Dict

class GitHubService:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.lazy_bird_url = "https://api.lazy-bird.com"

    async def create_issue(self, title: str, description: str, difficulty: str):
        """Create GitHub issue with difficulty label"""
        labels = [difficulty]  # 'easy', 'medium', 'hard'
        # Create issue via GitHub API
        pass

    async def trigger_lazy_bird(self, issue_number: int):
        """Trigger lazy-bird to create PR"""
        # Call lazy-bird API
        pass
```

**3. Tenant Customization**
```python
# backend/app/api/tenants/custom.py
from typing import Dict, Any
import importlib

class TenantCustomizer:
    def __init__(self):
        self.custom_modules = {}

    def load_tenant_module(self, org_id: str, module_type: str):
        """Load custom module for tenant"""
        module_path = f"custom.{org_id}.{module_type}"
        try:
            module = importlib.import_module(module_path)
            return module
        except ImportError:
            return None

    def get_custom_ui_config(self, org_id: str) -> Dict[str, Any]:
        """Get custom UI configuration for tenant"""
        # Return tenant-specific UI config
        pass
```

#### Success Criteria:

**Automated Verification:**
- [ ] Classification tests pass: `pytest tests/services/test_classifier.py`
- [ ] GitHub integration works: `pytest tests/services/test_github.py`
- [ ] All tests pass: `pytest`

**Manual Verification:**
- [ ] Document classification improves with user feedback
- [ ] Chat UI creates GitHub issues
- [ ] Easy issues trigger PR creation
- [ ] Tenant customizations apply correctly

---

## Testing Strategy

### Unit Tests:
- Pipeline processors (PDF, Image, OCR)
- Document extractors (Invoice, Receipt, Contract, ID)
- Authentication and authorization
- Multi-tenant isolation

### Integration Tests:
- End-to-end document upload and processing
- Search functionality (vector + full-text)
- GitHub issue creation flow
- Organization management

### Manual Testing Steps:
1. Create organization and invite users
2. Upload various document types (PDF, JPG, PNG)
3. Verify OCR and extraction accuracy
4. Test search with Romanian and English queries
5. Request feature via chat and verify GitHub issue
6. Switch organizations and verify data isolation

## Performance Considerations

- Use Celery for async document processing
- Implement caching for frequently accessed documents
- Batch vector operations for Qdrant
- Lazy load document previews
- Implement pagination for document lists
- Use Redis for session management

## Security Considerations

- All document processing happens on-premise (no cloud AI)
- JWT tokens with organization scope
- Row-level security in PostgreSQL
- Encrypted file storage in MinIO
- Rate limiting on API endpoints
- CORS configuration for frontend

## Deployment Notes

### Docker Compose Setup:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: vibedocs
      POSTGRES_USER: vibedocs
      POSTGRES_PASSWORD: secret

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"

  redis:
    image: redis:7-alpine

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"

  backend:
    build: ./backend
    depends_on:
      - postgres
      - qdrant
      - redis
      - minio

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"

  celery:
    build: ./backend
    command: celery -A app.workers.celery worker
```

## Next Steps

1. **Immediate Actions:**
   - Initialize git repository
   - Set up Docker environment
   - Create basic project structure
   - Configure development environment

2. **Phase 1 Priority:**
   - Implement Google OAuth
   - Set up multi-tenant database
   - Create basic API structure

3. **Documentation:**
   - API documentation with Swagger
   - Deployment guide
   - Developer onboarding guide

## References

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Qdrant Documentation: https://qdrant.tech/documentation/
- Lazy Bird GitHub App: https://github.com/yusufkaraaslan/lazy-bird
- React + Vite Setup: https://vitejs.dev/guide/
- Shadcn/ui Components: https://ui.shadcn.com/
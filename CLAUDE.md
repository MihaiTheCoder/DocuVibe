# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VibeDocs is an AI-powered document management system optimized for Romanian hospital managers. It uses a React frontend with a Python backend, designed with multi-tenancy and privacy-first principles using only open-source models.

## Architecture Principles

### Vibe Code Friendly Design
- **Small Files**: Keep files under 200 lines where possible
- **Low Complexity**: Each function/component should do one thing well
- **Repeated Structure**: Use consistent patterns across similar features
- **Popular Libraries Only**: Stick to well-established, widely-used libraries
- **Minimal Dependencies**: Keep the dependency tree lean

### Tech Stack
**Frontend:**
- React (UI framework)
- React Router (routing)
- TanStack Query / React Query (server state)
- Tailwind CSS (styling)

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- Pydantic (validation)
- Qdrant (vector database for hybrid search)
- Mistral OCR (document processing)

**Authentication:**
- Google OAuth 2.0 for login

## Multi-Tenant Architecture

### Database Design
- All tables include `organization_id` foreign key
- Row-level security enforced at ORM/query level
- User can belong to multiple organizations via `user_organizations` junction table

### Organization Model
```
Organization:
  - id (UUID)
  - name (unique)
  - created_at
  - settings (JSON)

UserOrganization:
  - user_id
  - organization_id
  - role (admin/member)
  - invited_at
```

### Request Context
Every API request includes organization context via:
- Header: `X-Organization-ID`
- Middleware validates user has access to organization
- All queries automatically scoped to current organization

## Document Pipeline Architecture

### Pipeline Structure
Each document type (PDF, PNG/JPG) has its own processing pipeline:

```
Document Upload → Type Detection → Pipeline Routing → Processing → Classification → Storage
```

### Document Types & Pipelines

**PDF Pipeline:**
1. OCR with Mistral OCR
2. Text extraction
3. Vector embedding generation
4. Qdrant indexing (hybrid: vector + full-text)
5. Classification

**Image Pipeline (PNG/JPG):**
1. Image preprocessing
2. OCR with Mistral OCR
3. Text extraction
4. Vector embedding generation
5. Qdrant indexing
6. Classification

### Category-Specific Processing

After initial processing, documents are routed to category-specific extractors:

**Invoice Pipeline:**
- Extract: invoice_number, date, vendor, total_amount, tax, line_items
- Store in structured DB table

**Receipt Pipeline:**
- Extract: date, merchant, amount, category, payment_method
- Store in structured DB table

**Contract Pipeline:**
- Extract: parties, effective_date, expiration_date, key_terms
- Store in structured DB table

### Implementation Pattern
```
backend/pipelines/
  base.py           # BasePipeline abstract class
  pdf_pipeline.py   # PDF processing
  image_pipeline.py # Image processing
  extractors/
    invoice.py      # InvoiceExtractor
    receipt.py      # ReceiptExtractor
    contract.py     # ContractExtractor
```

Each pipeline is a class with a standard interface:
```python
class BasePipeline:
    async def process(self, file_path: str, organization_id: str) -> ProcessedDocument
    async def extract_text(self, file_path: str) -> str
    async def generate_embedding(self, text: str) -> List[float]
    async def classify(self, text: str, embedding: List[float]) -> DocumentCategory
```

## Qdrant Configuration

### Hybrid Search
Qdrant collections configured with:
- Vector search (embedding similarity)
- Full-text search (BM25)
- Filtered by organization_id (payload)

### Collection Schema
```python
{
    "vector": [384],  # embedding dimension
    "payload": {
        "organization_id": "uuid",
        "document_id": "uuid",
        "text": "string",
        "category": "string",
        "metadata": {}
    }
}
```

### Extreme Classification
- User provides labels for initial documents (10-20 examples per category)
- System trains a lightweight classifier using embeddings
- Classification model stored per organization
- Active learning: suggest uncertain documents for user review

## Frontend Structure

```
frontend/src/
  components/
    documents/
      DocumentUpload.jsx
      DocumentList.jsx
      DocumentViewer.jsx
    search/
      SearchBar.jsx
      SearchResults.jsx
    chat/
      ChatInterface.jsx
    organizations/
      OrgSelector.jsx
      OrgSettings.jsx
  hooks/
    useDocuments.js
    useSearch.js
    useAuth.js
  api/
    documents.js
    search.js
    auth.js
  pages/
    Dashboard.jsx
    Documents.jsx
    Search.jsx
    Settings.jsx
```

## Backend Structure

```
backend/
  api/
    routes/
      documents.py
      search.py
      organizations.py
      auth.py
  pipelines/
    base.py
    pdf_pipeline.py
    image_pipeline.py
    extractors/
  models/
    user.py
    organization.py
    document.py
  schemas/
    document.py
    organization.py
  services/
    qdrant_service.py
    ocr_service.py
    classification_service.py
  middleware/
    auth.py
    organization.py
  core/
    config.py
    database.py
```

## Development Commands

### Frontend (once initialized)
```bash
cd frontend
npm install
npm run dev        # Start development server
npm run build      # Production build
npm run lint       # Run ESLint
npm test           # Run tests
```

### Backend (once initialized)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload  # Start development server
pytest                     # Run tests
black .                    # Format code
ruff check .              # Lint code
```

## Code Style Guidelines

### Python
- Use `async/await` for all I/O operations
- Type hints on all function signatures
- Pydantic models for request/response validation
- Keep route handlers thin - business logic in services
- One service class per domain entity

### React
- Functional components with hooks only
- Custom hooks for reusable logic
- Colocate related components
- Props destructuring in component signatures
- Keep components under 150 lines

### File Naming
- Python: `snake_case.py`
- React: `PascalCase.jsx` for components, `camelCase.js` for utilities
- Tests: `test_*.py` or `*.test.js`

## Privacy & Security

### Data Privacy
- All LLM processing happens locally with open-source models
- No data sent to external APIs (except Google OAuth)
- Document content never leaves the server
- Vector embeddings stored in self-hosted Qdrant

### Security Practices
- Organization-scoped queries enforced at middleware level
- JWT tokens for session management
- Google OAuth for authentication only
- Input validation on all endpoints
- SQL injection protection via ORM

## Chat UI (Future Feature)

The chat interface will allow users to:
- Search documents conversationally
- Ask questions about document contents
- Request document summaries
- Get insights from document corpus

Implementation will use:
- RAG (Retrieval-Augmented Generation) with Qdrant
- Open-source LLM (to be selected)
- Streaming responses for better UX

## Testing Strategy

### Backend Tests
- Unit tests for services and pipelines
- Integration tests for API endpoints
- Fixtures for test data with multiple organizations
- Mock Qdrant and OCR services in tests

### Frontend Tests
- Component tests with React Testing Library
- Integration tests for user flows
- Mock API responses

## Common Development Patterns

### Adding a New Document Category
1. Create extractor class in `backend/pipelines/extractors/`
2. Define Pydantic schema for extracted fields
3. Create database model for structured data
4. Add category to classification enum
5. Register extractor in pipeline router

### Adding a New API Endpoint
1. Define route in appropriate `routes/` file
2. Create Pydantic request/response schemas
3. Implement business logic in service layer
4. Add organization context validation
5. Add tests

### Adding a New Frontend Component
1. Create component file in appropriate directory
2. Create custom hook if reusable logic needed
3. Add to parent component
4. Add basic tests

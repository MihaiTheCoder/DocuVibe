# Getting Started with VibeDocs

## Architecture Overview

VibeDocs follows a clean, modular architecture designed to be "vibe code friendly":
- **Small files** - Each module has a single, clear responsibility
- **Low complexity** - Simple, readable patterns throughout
- **Repeated structure** - Consistent patterns make the codebase predictable
- **Minimal dependencies** - Only essential, popular libraries

## Project Structure Explained

### Backend (`/backend`)
- **`app/api/`** - REST API endpoints, organized by feature
- **`app/core/`** - Core utilities (config, database, security)
- **`app/models/`** - SQLAlchemy database models
- **`app/pipelines/`** - Document processing pipelines (extensible)
- **`app/services/`** - Business logic and external integrations
- **`app/workers/`** - Background task processing with Celery

### Frontend (`/frontend`)
- **`src/components/`** - Reusable React components
- **`src/pages/`** - Page-level components
- **`src/hooks/`** - Custom React hooks
- **`src/services/`** - API client and services
- **`src/stores/`** - Zustand state management

## Quick Start

### Prerequisites
- Docker Desktop
- Python 3.11+
- Node.js 20+
- Google OAuth credentials (for authentication)

### Windows Setup

1. **Run the setup script:**
   ```cmd
   setup.bat
   ```

2. **Configure environment:**
   Edit `.env` file with your credentials:
   - Google OAuth credentials
   - GitHub token (for feature requests)
   - Any API keys needed

3. **Start the backend:**
   ```cmd
   cd backend
   venv\Scripts\activate
   uvicorn app.main:app --reload
   ```

4. **Start the frontend (new terminal):**
   ```cmd
   cd frontend
   npm run dev
   ```

5. **Access the application:**
   Open http://localhost:3000 in your browser

### Manual Setup (Mac/Linux)

1. **Start infrastructure:**
   ```bash
   docker-compose up -d postgres qdrant redis minio
   ```

2. **Setup backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   # alembic upgrade head  # Run when models are complete
   uvicorn app.main:app --reload
   ```

3. **Setup frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Development Workflow

### Adding a New Document Pipeline

1. Create a new pipeline in `backend/app/pipelines/`:
```python
# backend/app/pipelines/excel/processor.py
from app.pipelines.base import DocumentPipeline, ProcessingResult

class ExcelPipeline(DocumentPipeline):
    def __init__(self):
        super().__init__("excel")

    async def process(self, file_path: str, metadata):
        # Your processing logic here
        pass

    def supports_type(self, file_type: str) -> bool:
        return file_type in ['.xlsx', '.xls']
```

2. Register the pipeline:
```python
# In your initialization code
from app.pipelines.base import pipeline_registry
from app.pipelines.excel.processor import ExcelPipeline

pipeline_registry.register_pipeline(ExcelPipeline())
```

### Adding a Field Extractor

1. Create an extractor:
```python
# backend/app/pipelines/extractors/medical_record.py
from app.pipelines.base import FieldExtractor

class MedicalRecordExtractor(FieldExtractor):
    async def extract(self, text: str) -> Dict[str, Any]:
        # Extract patient info, diagnosis, etc.
        return {
            "patient_name": extracted_name,
            "diagnosis": extracted_diagnosis
        }
```

2. Register with a pipeline:
```python
pipeline.register_extractor("medical_record", MedicalRecordExtractor())
```

### Adding Tenant Customizations

1. Create tenant-specific module:
```python
# backend/custom/tenant_123/ui_config.py
def get_custom_config():
    return {
        "logo_url": "custom_logo.png",
        "primary_color": "#007bff",
        "features": ["custom_report"]
    }
```

2. Load in the application:
```python
from app.api.tenants.custom import TenantCustomizer
customizer = TenantCustomizer()
config = customizer.get_custom_ui_config(org_id)
```

## Key Concepts

### Multi-Tenancy
- Each user belongs to one or more organizations
- All data is scoped to organizations
- Tenant isolation at the database level

### Document Processing Pipeline
- Modular pipeline architecture
- Different processors for different file types
- Extensible field extraction
- Privacy-first with local AI models

### Vibe Code Principles
1. **Keep files small** - If a file exceeds 150 lines, consider splitting
2. **Repeat patterns** - Use the same structure across similar components
3. **Minimize complexity** - Prefer simple solutions over clever ones
4. **Document intent** - Clear comments explaining "why" not "what"

## Testing

### Backend Testing
```bash
cd backend
pytest                    # Run all tests
pytest tests/api/        # Test specific module
pytest -v               # Verbose output
pytest --cov=app        # With coverage
```

### Frontend Testing
```bash
cd frontend
npm test               # Run tests
npm run type-check     # TypeScript checking
npm run lint          # Linting
```

## Common Tasks

### Add a new API endpoint
1. Create route in `backend/app/api/`
2. Add Pydantic models for request/response
3. Implement business logic in services
4. Add tests

### Add a new React component
1. Create component in `frontend/src/components/`
2. Keep it small and focused
3. Use TypeScript for props
4. Add to a page or parent component

### Process a new document type
1. Create pipeline in `backend/app/pipelines/`
2. Register in pipeline registry
3. Add tests for processing
4. Update UI to handle new type

## Troubleshooting

### Docker services not starting
- Check Docker Desktop is running
- Ensure ports are not in use: 5432, 6333, 6379, 9000

### Backend import errors
- Ensure virtual environment is activated
- Check all requirements are installed: `pip install -r requirements.txt`

### Frontend build errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node version: Should be 20+

### Database connection issues
- Verify PostgreSQL is running: `docker ps`
- Check DATABASE_URL in .env
- Try restarting Docker services

## Next Steps

1. **Phase 1**: Complete authentication and multi-tenant setup
2. **Phase 2**: Implement document processing pipelines
3. **Phase 3**: Build the React frontend
4. **Phase 4**: Add advanced features (classification, GitHub integration)

See [implementation-plan.md](implementation-plan.md) for detailed implementation phases.

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Docker Documentation](https://docs.docker.com/)

## Support

For issues or questions:
- Check the [implementation plan](implementation-plan.md)
- Review the README
- Create an issue in the GitHub repository
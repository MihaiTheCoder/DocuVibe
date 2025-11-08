# VibeDocs

AI-Powered Document Management System for Romanian Hospital Managers

## Features

- 🔒 **Privacy-First**: All AI processing happens on-premise using open-source models
- 🏢 **Multi-Tenant**: Support for multiple organizations with data isolation
- 📄 **Smart Document Processing**: OCR, classification, and field extraction
- 🔍 **Hybrid Search**: Vector embeddings + full-text search via Qdrant
- 🤖 **AI-Powered Classification**: Learn from user feedback to auto-classify documents
- 💬 **Feature Request Chat**: Automated GitHub issue creation and PR generation
- 🎨 **Customizable**: Per-tenant UI and processing customization

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18 with TypeScript and Vite
- **Database**: PostgreSQL (main) + Qdrant (vectors)
- **Queue**: Redis + Celery
- **Storage**: MinIO (S3-compatible)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+
- Google OAuth credentials

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vibedocs.git
cd vibedocs
```

2. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start infrastructure services:
```bash
docker-compose up -d postgres qdrant redis minio
```

4. Install backend dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the backend:
```bash
uvicorn app.main:app --reload
```

7. In a new terminal, install frontend dependencies:
```bash
cd frontend
npm install
```

8. Start the frontend:
```bash
npm run dev
```

9. Open http://localhost:3000 in your browser

## Development

### Backend Development

```bash
cd backend
# Run tests
pytest

# Format code
black .

# Lint
pylint app/

# Type checking
mypy app/
```

### Frontend Development

```bash
cd frontend
# Run tests
npm test

# Type checking
npm run type-check

# Lint
npm run lint

# Format
npm run format
```

## Architecture

The system follows a clean, modular architecture:

- **Small Files**: Each file has a single responsibility
- **Low Complexity**: Simple, readable code patterns
- **Repeated Structure**: Consistent patterns across modules
- **Minimal Dependencies**: Only essential, popular libraries

See [implementation-plan.md](implementation-plan.md) for detailed architecture documentation.

## License

MIT
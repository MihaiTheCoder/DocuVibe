# Fix Dependency Alignment Between Local and Production Implementation Plan

## Overview

This plan addresses the critical issue where production deployments fail due to dependency mismatches between local development and production environments. Specifically, the `email-validator` package is missing from the main requirements.txt but required by Pydantic's EmailStr type, causing deployment crashes.

## Current State Analysis

The backend currently uses a two-tier requirements strategy:
- **requirements.txt** (56 lines) - Full dependencies including ML/AI packages, used locally
- **requirements-minimal.txt** (28 lines) - Minimal dependencies for deployment

The `email-validator` package exists only in requirements-minimal.txt but not in requirements.txt, while the EmailStr type is actively used in `backend/app/schemas/auth.py:25`.

### Key Discoveries:
- Deployment workflow swaps requirements files during build (`backend-deploy.yml:35-37`)
- Local development uses requirements.txt without email-validator
- Production uses requirements-minimal.txt with email-validator
- This inverted dependency causes local tests to miss production issues

## Desired End State

A robust dependency management system where:
1. Local development environment exactly matches production dependencies
2. Development-only tools are clearly separated from runtime dependencies
3. Dependency changes are automatically tested before deployment
4. Clear documentation guides developers on dependency management

### Verification Criteria:
- Application runs locally with same dependencies as production
- CI/CD pipeline validates dependency compatibility
- No more "works locally but fails in production" scenarios
- Clear separation between runtime and development dependencies

## What We're NOT Doing

- Containerizing the application (Docker) - future enhancement
- Switching to Poetry or other dependency managers - maintaining pip for simplicity
- Implementing multi-stage builds - keeping current deployment strategy
- Adding complex dependency resolution tools - using pip-tools for simplicity

## Implementation Approach

We'll implement pip-tools to manage dependencies with a single source of truth, separating runtime from development dependencies while ensuring local/production parity.

## Phase 1: Immediate Fix - Add Missing Dependency

### Overview
Quick fix to unblock deployments by adding email-validator to main requirements.txt.

### Changes Required:

#### 1. Update Main Requirements File
**File**: `backend/requirements.txt`
**Changes**: Add email-validator package to validation section

```diff
 # Validation & Settings
 pydantic==2.9.2
 pydantic-settings==2.5.2
 python-dotenv==1.0.1
+email-validator==2.1.0
```

### Success Criteria:

#### Automated Verification:
- [ ] Backend starts locally: `cd backend && python -m uvicorn app.main:app --reload`
- [ ] Import test passes: `cd backend && python -c "from pydantic import EmailStr"`
- [ ] No import errors in logs

#### Manual Verification:
- [ ] Authentication endpoints work correctly
- [ ] User profile displays email properly
- [ ] No EmailStr validation errors

---

## Phase 2: Implement pip-tools for Dependency Management

### Overview
Set up pip-tools to manage dependencies from source files, ensuring consistency across environments.

### Changes Required:

#### 1. Install pip-tools
**File**: Create new `backend/requirements-dev.txt`
**Changes**: Add development tool

```txt
# Development tools
pip-tools==7.4.1
```

#### 2. Create Source Requirements Files
**File**: `backend/requirements.in`
**Changes**: Define runtime dependencies only

```txt
# Core
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9
gunicorn==22.0.0

# Database
sqlalchemy==2.0.35
alembic==1.13.2
psycopg2-binary==2.9.9

# Azure Services
azure-storage-blob==12.19.0
azure-identity==1.15.0

# Validation & Settings
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
email-validator==2.1.0

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
google-auth==2.35.0
google-auth-oauthlib==1.2.0
httpx==0.27.2
```

**File**: `backend/requirements-dev.in`
**Changes**: Define development dependencies

```txt
# Include base requirements
-r requirements.in

# Vector Database
qdrant-client==1.11.1

# Document Processing
pypdf==4.3.1
pillow==10.4.0
python-magic==0.4.27

# Task Queue
celery==5.3.6
redis==5.0.8

# Storage
minio==7.2.8

# ML/AI
numpy==1.26.4
scikit-learn==1.5.2
sentence-transformers==3.0.1

# Testing
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0

# Development
black==24.8.0
pylint==3.2.7
mypy==1.11.2
pip-tools==7.4.1
```

#### 3. Create Makefile for Dependency Management
**File**: `backend/Makefile`
**Changes**: Add dependency compilation commands

```makefile
.PHONY: compile-deps sync-deps update-deps test-deps

# Compile dependencies from .in files
compile-deps:
	pip-compile requirements.in -o requirements.txt
	pip-compile requirements-dev.in -o requirements-dev.txt

# Sync current environment with compiled dependencies
sync-deps:
	pip-sync requirements.txt

sync-dev-deps:
	pip-sync requirements-dev.txt

# Update dependencies to latest versions
update-deps:
	pip-compile --upgrade requirements.in -o requirements.txt
	pip-compile --upgrade requirements-dev.in -o requirements-dev.txt

# Test that production dependencies work
test-deps:
	pip-sync requirements.txt
	python -c "from pydantic import EmailStr; print('Dependencies OK')"
	python -m uvicorn app.main:app --port 8001 --reload &
	sleep 5
	curl -f http://localhost:8001/health || (pkill -f "uvicorn app.main:app" && exit 1)
	pkill -f "uvicorn app.main:app"
```

### Success Criteria:

#### Automated Verification:
- [ ] Compile dependencies: `cd backend && make compile-deps`
- [ ] Generated requirements.txt contains all runtime dependencies
- [ ] Generated requirements-dev.txt contains all dependencies
- [ ] Sync works: `make sync-deps`
- [ ] Test passes: `make test-deps`

#### Manual Verification:
- [ ] Local environment matches production after `make sync-deps`
- [ ] Development tools available after `make sync-dev-deps`
- [ ] No dependency conflicts

---

## Phase 3: Update CI/CD Pipeline

### Overview
Modify deployment workflow to use new dependency structure and add validation.

### Changes Required:

#### 1. Update GitHub Actions Workflow
**File**: `.github/workflows/backend-deploy.yml`
**Changes**: Use compiled requirements and add validation

```yaml
name: Deploy Backend to Azure

on:
  push:
    branches: [master]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-deploy.yml'
  workflow_dispatch:

env:
  AZURE_WEBAPP_NAME: app-vibedocs-backend-dev
  PYTHON_VERSION: '3.11'

jobs:
  validate-dependencies:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: Test production dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        python -c "from pydantic import EmailStr"
        python -c "import app.main"

  build-and-deploy:
    needs: validate-dependencies
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        # Use the compiled production requirements
        pip install -r backend/requirements.txt

    - name: Create deployment package
      run: |
        cd backend
        # No longer need to swap files - requirements.txt is production-ready
        zip -r ../deploy.zip . -x "*.pyc" -x "__pycache__/*" -x "venv/*" -x "*.in" -x "requirements-dev.txt" -x "Makefile"

    # Rest of deployment steps remain the same...
```

#### 2. Add Pre-commit Hook for Dependency Validation
**File**: `backend/.pre-commit-config.yaml`
**Changes**: Ensure .in files stay in sync

```yaml
repos:
  - repo: local
    hooks:
      - id: check-requirements-sync
        name: Check requirements are compiled
        entry: bash -c 'cd backend && pip-compile --quiet --dry-run requirements.in | diff requirements.txt - || (echo "Requirements out of sync. Run: make compile-deps" && exit 1)'
        language: system
        files: ^backend/requirements\.(in|txt)$
```

### Success Criteria:

#### Automated Verification:
- [ ] CI pipeline passes with new structure
- [ ] Dependency validation step catches missing packages
- [ ] Deployment uses correct requirements.txt
- [ ] Pre-commit hook detects out-of-sync dependencies

#### Manual Verification:
- [ ] Deployment succeeds with new requirements
- [ ] Application runs correctly in production
- [ ] No missing dependency errors

---

## Phase 4: Documentation and Developer Workflow

### Overview
Document the new dependency management system and update developer onboarding.

### Changes Required:

#### 1. Update README
**File**: `backend/README.md`
**Changes**: Add dependency management section

```markdown
## Dependency Management

We use pip-tools to manage Python dependencies, ensuring consistency between local development and production environments.

### Structure
- `requirements.in` - Runtime dependencies (used in production)
- `requirements-dev.in` - Development dependencies (includes runtime + dev tools)
- `requirements.txt` - Compiled runtime dependencies (auto-generated, do not edit)
- `requirements-dev.txt` - Compiled development dependencies (auto-generated, do not edit)

### Common Commands

```bash
# Set up local development environment
make sync-dev-deps

# Set up production-like environment
make sync-deps

# Add a new runtime dependency
echo "package==1.0.0" >> requirements.in
make compile-deps
make sync-deps

# Add a new development dependency
echo "package==1.0.0" >> requirements-dev.in
make compile-deps
make sync-dev-deps

# Update all dependencies to latest versions
make update-deps

# Test production dependencies work
make test-deps
```

### Important Notes
- NEVER manually edit requirements.txt or requirements-dev.txt
- Always add new dependencies to .in files
- Run `make compile-deps` after modifying .in files
- Use `make sync-deps` to test with production dependencies locally
```

#### 2. Remove Obsolete File
**File**: Delete `backend/requirements-minimal.txt`
**Changes**: No longer needed with new structure

### Success Criteria:

#### Automated Verification:
- [ ] Documentation builds without errors
- [ ] All make commands work as documented
- [ ] Old requirements-minimal.txt file removed

#### Manual Verification:
- [ ] New developer can set up environment following docs
- [ ] Dependency addition workflow is clear
- [ ] No references to old requirements-minimal.txt

---

## Testing Strategy

### Unit Tests:
- Test that all imports work with production dependencies
- Validate EmailStr fields process correctly
- Ensure no development dependencies imported in production code

### Integration Tests:
- Full application startup with production dependencies
- Authentication flow with email validation
- API endpoints respond correctly

### Manual Testing Steps:
1. Fresh clone of repository
2. Run `make sync-deps` (production deps only)
3. Start application locally
4. Test authentication with Google OAuth
5. Verify user profile shows email correctly
6. Run `make test-deps` to validate

## Performance Considerations

- Compiled requirements.txt will have exact versions, improving pip install speed
- Smaller production dependencies (no ML packages) reduce deployment time
- Clear separation prevents accidental inclusion of heavy dev dependencies

## Migration Notes

For existing deployments:
1. Deploy Phase 1 first to fix immediate issue
2. Test thoroughly in staging
3. Roll out remaining phases gradually
4. Keep requirements-minimal.txt during transition period
5. Remove after confirming new structure works

## References

- Original error: Production crash due to missing email-validator
- pip-tools documentation: https://pip-tools.readthedocs.io/
- Current deployment workflow: `.github/workflows/backend-deploy.yml`
- Azure App Service docs: https://docs.microsoft.com/en-us/azure/app-service/
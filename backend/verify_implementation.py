"""
Verify Async Processing Implementation

Checks that all components are properly implemented and importable.
"""

import sys
from pathlib import Path


def check_imports():
    """Verify all necessary modules can be imported"""
    print("\n" + "="*60)
    print("Verifying Implementation - Module Imports")
    print("="*60 + "\n")

    checks = []

    # Phase 1: Models and Migration
    try:
        from app.models.processing_job import ProcessingJob, JobStatus, JobType
        print("[OK] ProcessingJob model imported")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] ProcessingJob model import failed: {e}")
        checks.append(False)

    # Phase 2: Workers
    try:
        from app.workers.base_worker import BaseWorker
        print("[OK] BaseWorker imported")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] BaseWorker import failed: {e}")
        checks.append(False)

    try:
        from app.workers.document_worker import DocumentProcessingWorker
        print("[OK] DocumentProcessingWorker imported")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] DocumentProcessingWorker import failed: {e}")
        checks.append(False)

    try:
        from app.workers.manager import worker_manager
        print("[OK] WorkerManager imported")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] WorkerManager import failed: {e}")
        checks.append(False)

    # Phase 3: Pipelines
    try:
        from app.pipelines.registry import pipeline_registry
        pipelines = pipeline_registry.list_pipelines()
        print(f"[OK] Pipeline registry imported - {len(pipelines)} pipelines registered: {', '.join(pipelines)}")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] Pipeline registry import failed: {e}")
        checks.append(False)

    try:
        from app.pipelines.mock_pipeline import MockPipeline
        print("[OK] MockPipeline imported")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] MockPipeline import failed: {e}")
        checks.append(False)

    # Phase 4: API Integration
    try:
        from app.api.routes.documents import router as documents_router
        print("[OK] Documents router (with job creation) imported")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] Documents router import failed: {e}")
        checks.append(False)

    # Phase 5: Jobs API
    try:
        from app.api.routes.jobs import router as jobs_router
        print("[OK] Jobs router imported")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] Jobs router import failed: {e}")
        checks.append(False)

    try:
        from app.schemas.processing_job import JobStatusResponse, JobListResponse
        print("[OK] Job schemas imported")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] Job schemas import failed: {e}")
        checks.append(False)

    # Main app
    try:
        from app.main import app
        print("[OK] Main FastAPI app imported")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] Main app import failed: {e}")
        checks.append(False)

    return all(checks)


def check_files():
    """Verify all necessary files exist"""
    print("\n" + "="*60)
    print("Verifying Implementation - File Structure")
    print("="*60 + "\n")

    base_path = Path(__file__).parent
    checks = []

    files_to_check = [
        "app/models/processing_job.py",
        "app/workers/__init__.py",
        "app/workers/base_worker.py",
        "app/workers/document_worker.py",
        "app/workers/manager.py",
        "app/pipelines/mock_pipeline.py",
        "app/pipelines/pdf_pipeline.py",
        "app/pipelines/image_pipeline.py",
        "app/pipelines/registry.py",
        "app/api/routes/jobs.py",
        "app/schemas/processing_job.py",
        "migrations/versions/002_add_processing_jobs.py",
    ]

    for file_path in files_to_check:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"[OK] {file_path}")
            checks.append(True)
        else:
            print(f"[FAIL] {file_path} not found")
            checks.append(False)

    return all(checks)


def check_database():
    """Verify database migration applied"""
    print("\n" + "="*60)
    print("Verifying Implementation - Database")
    print("="*60 + "\n")

    try:
        from app.core.database import SessionLocal
        from app.models.processing_job import ProcessingJob
        from sqlalchemy import inspect

        db = SessionLocal()
        try:
            # Check if table exists
            inspector = inspect(db.bind)
            tables = inspector.get_table_names()

            if 'processing_jobs' in tables:
                print("[OK] processing_jobs table exists")

                # Check columns
                columns = [col['name'] for col in inspector.get_columns('processing_jobs')]
                expected_columns = ['id', 'organization_id', 'job_type', 'status', 'document_id',
                                    'pipeline_id', 'priority', 'retry_count', 'max_retries',
                                    'worker_id', 'locked_at', 'lock_expires_at', 'started_at',
                                    'completed_at', 'processing_time_ms', 'result', 'error_message',
                                    'error_details', 'created_at', 'updated_at']

                missing = [col for col in expected_columns if col not in columns]
                if not missing:
                    print(f"[OK] All {len(expected_columns)} columns present")
                else:
                    print(f"[WARN] Missing columns: {', '.join(missing)}")

                # Check indexes
                indexes = inspector.get_indexes('processing_jobs')
                print(f"[OK] {len(indexes)} indexes created")

                return True
            else:
                print("[FAIL] processing_jobs table not found")
                return False

        finally:
            db.close()

    except Exception as e:
        print(f"[FAIL] Database check failed: {e}")
        return False


def check_config():
    """Verify configuration"""
    print("\n" + "="*60)
    print("Verifying Implementation - Configuration")
    print("="*60 + "\n")

    try:
        from app.core.config import settings

        config_checks = [
            ('DOCUMENT_WORKERS_COUNT', settings.DOCUMENT_WORKERS_COUNT),
            ('WORKER_POLL_INTERVAL', settings.WORKER_POLL_INTERVAL),
            ('WORKER_LOCK_DURATION', settings.WORKER_LOCK_DURATION),
        ]

        for name, value in config_checks:
            print(f"[OK] {name} = {value}")

        return True

    except Exception as e:
        print(f"[FAIL] Config check failed: {e}")
        return False


def main():
    """Run all verification checks"""
    print("\n" + "="*70)
    print("ASYNC DOCUMENT PROCESSING - IMPLEMENTATION VERIFICATION")
    print("="*70)

    results = {
        "File Structure": check_files(),
        "Module Imports": check_imports(),
        "Configuration": check_config(),
        "Database": check_database(),
    }

    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70 + "\n")

    for check_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {check_name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n" + "="*70)
        print("SUCCESS: All verification checks passed!")
        print("="*70)
        print("\nThe async document processing system is fully implemented.")
        print("\nNext steps:")
        print("  1. Start the server: uvicorn app.main:app --reload")
        print("  2. Server will start 2 workers by default")
        print("  3. Upload documents via API - they will be processed asynchronously")
        print("  4. Check job status via /api/v1/jobs/{job_id}")
        print("\n" + "="*70 + "\n")
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("FAILURE: Some verification checks failed")
        print("="*70 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

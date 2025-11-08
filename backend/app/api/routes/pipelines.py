"""
Pipeline Management Routes

Handles pipeline creation, configuration, and management.
All endpoints require authentication and organization context.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid
import time

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.pipeline import Pipeline
from app.models.document import Document
from app.schemas.pipeline import (
    PipelineCreateRequest,
    PipelineUpdateRequest,
    PipelineResponse,
    PipelineDetailResponse,
    PipelineStatsResponse,
    PipelineTestRequest,
    PipelineTestResult,
    PipelineCloneRequest
)
from app.utils.auth import get_current_user
from app.middleware.organization import get_current_organization

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.post("", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    pipeline_data: PipelineCreateRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Create a new pipeline

    Args:
        pipeline_data: Pipeline creation data
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Created pipeline information
    """
    # Check if pipeline name already exists in this organization
    existing_pipeline = db.query(Pipeline).filter(
        Pipeline.organization_id == organization.id,
        Pipeline.name == pipeline_data.name
    ).first()

    if existing_pipeline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pipeline with name '{pipeline_data.name}' already exists"
        )

    # If setting as default, unset other defaults
    if pipeline_data.is_default:
        db.query(Pipeline).filter(
            Pipeline.organization_id == organization.id,
            Pipeline.is_default == True
        ).update({"is_default": False})

    # Create pipeline
    pipeline = Pipeline(
        organization_id=organization.id,
        name=pipeline_data.name,
        type=pipeline_data.type,
        config=pipeline_data.config,
        is_active=pipeline_data.is_active,
        is_default=pipeline_data.is_default,
        documents_processed=0,
        success_count=0,
        failure_count=0
    )

    try:
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)

        return PipelineResponse(
            id=str(pipeline.id),
            organization_id=str(pipeline.organization_id),
            name=pipeline.name,
            type=pipeline.type,
            config=pipeline.config,
            is_active=pipeline.is_active,
            is_default=pipeline.is_default,
            documents_processed=pipeline.documents_processed,
            success_count=pipeline.success_count,
            failure_count=pipeline.failure_count,
            avg_processing_time_ms=pipeline.avg_processing_time_ms,
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pipeline: {str(e)}"
        )


@router.get("", response_model=List[PipelineResponse])
async def list_pipelines(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    List all pipelines in the organization

    Args:
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        List of pipelines
    """
    pipelines = db.query(Pipeline).filter(
        Pipeline.organization_id == organization.id
    ).order_by(Pipeline.is_default.desc(), Pipeline.name).all()

    return [
        PipelineResponse(
            id=str(pipeline.id),
            organization_id=str(pipeline.organization_id),
            name=pipeline.name,
            type=pipeline.type,
            config=pipeline.config,
            is_active=pipeline.is_active,
            is_default=pipeline.is_default,
            documents_processed=pipeline.documents_processed,
            success_count=pipeline.success_count,
            failure_count=pipeline.failure_count,
            avg_processing_time_ms=pipeline.avg_processing_time_ms,
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at
        )
        for pipeline in pipelines
    ]


@router.get("/{pipeline_id}", response_model=PipelineDetailResponse)
async def get_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Get pipeline details by ID

    Args:
        pipeline_id: Pipeline UUID
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Detailed pipeline information
    """
    # Validate UUID
    try:
        pipeline_uuid = uuid.UUID(pipeline_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pipeline ID format"
        )

    # Get pipeline
    pipeline = db.query(Pipeline).filter(
        Pipeline.id == pipeline_uuid,
        Pipeline.organization_id == organization.id
    ).first()

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )

    return PipelineDetailResponse(
        id=str(pipeline.id),
        organization_id=str(pipeline.organization_id),
        name=pipeline.name,
        type=pipeline.type,
        config=pipeline.config,
        is_active=pipeline.is_active,
        is_default=pipeline.is_default,
        documents_processed=pipeline.documents_processed,
        success_count=pipeline.success_count,
        failure_count=pipeline.failure_count,
        avg_processing_time_ms=pipeline.avg_processing_time_ms,
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at
    )


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: str,
    update_data: PipelineUpdateRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Update pipeline configuration

    Args:
        pipeline_id: Pipeline UUID
        update_data: Pipeline update data
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Updated pipeline information
    """
    # Validate UUID
    try:
        pipeline_uuid = uuid.UUID(pipeline_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pipeline ID format"
        )

    # Get pipeline
    pipeline = db.query(Pipeline).filter(
        Pipeline.id == pipeline_uuid,
        Pipeline.organization_id == organization.id
    ).first()

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )

    # Check if name already exists (if changing name)
    if update_data.name and update_data.name != pipeline.name:
        existing_pipeline = db.query(Pipeline).filter(
            Pipeline.organization_id == organization.id,
            Pipeline.name == update_data.name,
            Pipeline.id != pipeline_uuid
        ).first()

        if existing_pipeline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pipeline with name '{update_data.name}' already exists"
            )

    # If setting as default, unset other defaults
    if update_data.is_default and not pipeline.is_default:
        db.query(Pipeline).filter(
            Pipeline.organization_id == organization.id,
            Pipeline.is_default == True
        ).update({"is_default": False})

    # Update fields
    if update_data.name is not None:
        pipeline.name = update_data.name
    if update_data.type is not None:
        pipeline.type = update_data.type
    if update_data.config is not None:
        pipeline.config = update_data.config
    if update_data.is_active is not None:
        pipeline.is_active = update_data.is_active
    if update_data.is_default is not None:
        pipeline.is_default = update_data.is_default

    pipeline.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(pipeline)

        return PipelineResponse(
            id=str(pipeline.id),
            organization_id=str(pipeline.organization_id),
            name=pipeline.name,
            type=pipeline.type,
            config=pipeline.config,
            is_active=pipeline.is_active,
            is_default=pipeline.is_default,
            documents_processed=pipeline.documents_processed,
            success_count=pipeline.success_count,
            failure_count=pipeline.failure_count,
            avg_processing_time_ms=pipeline.avg_processing_time_ms,
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update pipeline: {str(e)}"
        )


@router.delete("/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Delete a pipeline

    Args:
        pipeline_id: Pipeline UUID
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Success confirmation
    """
    # Validate UUID
    try:
        pipeline_uuid = uuid.UUID(pipeline_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pipeline ID format"
        )

    # Get pipeline
    pipeline = db.query(Pipeline).filter(
        Pipeline.id == pipeline_uuid,
        Pipeline.organization_id == organization.id
    ).first()

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )

    # Prevent deletion of default pipeline
    if pipeline.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default pipeline. Set another pipeline as default first."
        )

    # Check if pipeline is in use by documents
    documents_count = db.query(Document).filter(
        Document.pipeline_id == pipeline_uuid
    ).count()

    if documents_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete pipeline. It is used by {documents_count} document(s)."
        )

    try:
        db.delete(pipeline)
        db.commit()

        return {"success": True, "message": "Pipeline deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete pipeline: {str(e)}"
        )


@router.post("/{pipeline_id}/test", response_model=PipelineTestResult)
async def test_pipeline(
    pipeline_id: str,
    test_data: PipelineTestRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Test a pipeline with a sample file

    Args:
        pipeline_id: Pipeline UUID
        test_data: Test request with sample file ID
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Test result with processing details
    """
    # Validate pipeline UUID
    try:
        pipeline_uuid = uuid.UUID(pipeline_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pipeline ID format"
        )

    # Validate sample file UUID
    try:
        sample_file_uuid = uuid.UUID(test_data.sample_file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sample file ID format"
        )

    # Get pipeline
    pipeline = db.query(Pipeline).filter(
        Pipeline.id == pipeline_uuid,
        Pipeline.organization_id == organization.id
    ).first()

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )

    # Get sample document
    sample_doc = db.query(Document).filter(
        Document.id == sample_file_uuid,
        Document.organization_id == organization.id
    ).first()

    if not sample_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample document not found"
        )

    # Simulate pipeline test (in real implementation, this would run actual pipeline)
    start_time = time.time()

    try:
        # TODO: Actually run the pipeline processing here
        # For now, return a simulated result
        processing_time_ms = (time.time() - start_time) * 1000

        return PipelineTestResult(
            success=True,
            processing_time_ms=processing_time_ms,
            text_content_preview=sample_doc.text_content[:200] if sample_doc.text_content else None,
            extracted_fields=sample_doc.extracted_fields or {},
            classification=sample_doc.classification,
            error_message=None
        )

    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000

        return PipelineTestResult(
            success=False,
            processing_time_ms=processing_time_ms,
            text_content_preview=None,
            extracted_fields={},
            classification=None,
            error_message=str(e)
        )


@router.get("/{pipeline_id}/stats", response_model=PipelineStatsResponse)
async def get_pipeline_stats(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Get pipeline statistics

    Args:
        pipeline_id: Pipeline UUID
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Pipeline statistics including success rate and timing
    """
    # Validate UUID
    try:
        pipeline_uuid = uuid.UUID(pipeline_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pipeline ID format"
        )

    # Get pipeline
    pipeline = db.query(Pipeline).filter(
        Pipeline.id == pipeline_uuid,
        Pipeline.organization_id == organization.id
    ).first()

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )

    # Calculate success rate
    total_processed = pipeline.documents_processed
    success_rate = (pipeline.success_count / total_processed * 100) if total_processed > 0 else 0.0

    # Get last used timestamp
    last_doc = db.query(Document).filter(
        Document.pipeline_id == pipeline_uuid
    ).order_by(Document.processing_completed_at.desc()).first()

    last_used = last_doc.processing_completed_at if last_doc and last_doc.processing_completed_at else None

    return PipelineStatsResponse(
        pipeline_id=str(pipeline.id),
        pipeline_name=pipeline.name,
        documents_processed=pipeline.documents_processed,
        success_count=pipeline.success_count,
        failure_count=pipeline.failure_count,
        success_rate=round(success_rate, 2),
        avg_processing_time_ms=pipeline.avg_processing_time_ms,
        last_used=last_used
    )


@router.post("/{pipeline_id}/clone", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def clone_pipeline(
    pipeline_id: str,
    clone_data: PipelineCloneRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Clone an existing pipeline

    Args:
        pipeline_id: Pipeline UUID to clone
        clone_data: Clone request with new name
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Cloned pipeline information
    """
    # Validate UUID
    try:
        pipeline_uuid = uuid.UUID(pipeline_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pipeline ID format"
        )

    # Get source pipeline
    source_pipeline = db.query(Pipeline).filter(
        Pipeline.id == pipeline_uuid,
        Pipeline.organization_id == organization.id
    ).first()

    if not source_pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )

    # Check if new name already exists
    existing_pipeline = db.query(Pipeline).filter(
        Pipeline.organization_id == organization.id,
        Pipeline.name == clone_data.name
    ).first()

    if existing_pipeline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pipeline with name '{clone_data.name}' already exists"
        )

    # Create cloned pipeline
    cloned_pipeline = Pipeline(
        organization_id=organization.id,
        name=clone_data.name,
        type=source_pipeline.type,
        config=source_pipeline.config.copy() if source_pipeline.config else {},
        is_active=True,
        is_default=False,  # Cloned pipelines are never default
        documents_processed=0,
        success_count=0,
        failure_count=0
    )

    try:
        db.add(cloned_pipeline)
        db.commit()
        db.refresh(cloned_pipeline)

        return PipelineResponse(
            id=str(cloned_pipeline.id),
            organization_id=str(cloned_pipeline.organization_id),
            name=cloned_pipeline.name,
            type=cloned_pipeline.type,
            config=cloned_pipeline.config,
            is_active=cloned_pipeline.is_active,
            is_default=cloned_pipeline.is_default,
            documents_processed=cloned_pipeline.documents_processed,
            success_count=cloned_pipeline.success_count,
            failure_count=cloned_pipeline.failure_count,
            avg_processing_time_ms=cloned_pipeline.avg_processing_time_ms,
            created_at=cloned_pipeline.created_at,
            updated_at=cloned_pipeline.updated_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone pipeline: {str(e)}"
        )

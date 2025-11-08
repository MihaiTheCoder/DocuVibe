"""
Workflow Management Routes

Handles workflow creation via AI, execution, and management.
All endpoints require authentication and organization context.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.workflow import Workflow, WorkflowExecution
from app.schemas.workflow import (
    WorkflowCreateFromChatRequest,
    WorkflowUpdateRequest,
    WorkflowResponse,
    WorkflowDetailResponse,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowSuggestionRequest,
    WorkflowSuggestionResponse
)
from app.utils.auth import get_current_user
from app.middleware.organization import get_current_organization
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/create-from-chat", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_from_chat(
    request: WorkflowCreateFromChatRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Create a workflow from natural language prompt using AI

    Args:
        request: Chat request with prompt and context
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Created workflow information
    """
    service = WorkflowService(db, str(organization.id))

    try:
        workflow = service.create_workflow_from_chat(request)

        return WorkflowResponse(
            id=str(workflow.id),
            organization_id=str(workflow.organization_id),
            name=workflow.name,
            description=workflow.description,
            steps=workflow.steps,
            triggers=workflow.triggers,
            created_by_ai=workflow.created_by_ai,
            ai_prompt=workflow.ai_prompt,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    List all workflows in the organization

    Args:
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        List of workflows
    """
    service = WorkflowService(db, str(organization.id))
    workflows = service.get_workflows()

    return [
        WorkflowResponse(
            id=str(workflow.id),
            organization_id=str(workflow.organization_id),
            name=workflow.name,
            description=workflow.description,
            steps=workflow.steps,
            triggers=workflow.triggers,
            created_by_ai=workflow.created_by_ai,
            ai_prompt=workflow.ai_prompt,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at
        )
        for workflow in workflows
    ]


@router.get("/{workflow_id}", response_model=WorkflowDetailResponse)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Get workflow details by ID

    Args:
        workflow_id: Workflow UUID
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Detailed workflow information
    """
    # Validate UUID
    try:
        workflow_uuid = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )

    service = WorkflowService(db, str(organization.id))
    workflow = service.get_workflow_by_id(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    # Get execution count
    execution_count = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow_uuid
    ).count()

    # Get last execution
    last_execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow_uuid
    ).order_by(WorkflowExecution.started_at.desc()).first()

    return WorkflowDetailResponse(
        id=str(workflow.id),
        organization_id=str(workflow.organization_id),
        name=workflow.name,
        description=workflow.description,
        steps=workflow.steps,
        triggers=workflow.triggers,
        created_by_ai=workflow.created_by_ai,
        ai_prompt=workflow.ai_prompt,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        execution_count=execution_count,
        last_executed_at=last_execution.started_at if last_execution else None
    )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    update_data: WorkflowUpdateRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Update workflow configuration

    Args:
        workflow_id: Workflow UUID
        update_data: Workflow update data
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Updated workflow information
    """
    # Validate UUID
    try:
        uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )

    service = WorkflowService(db, str(organization.id))
    workflow = service.update_workflow(workflow_id, update_data)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return WorkflowResponse(
        id=str(workflow.id),
        organization_id=str(workflow.organization_id),
        name=workflow.name,
        description=workflow.description,
        steps=workflow.steps,
        triggers=workflow.triggers,
        created_by_ai=workflow.created_by_ai,
        ai_prompt=workflow.ai_prompt,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at
    )


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Delete a workflow

    Args:
        workflow_id: Workflow UUID
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Success confirmation
    """
    # Validate UUID
    try:
        uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )

    service = WorkflowService(db, str(organization.id))
    success = service.delete_workflow(workflow_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return {"success": True, "message": "Workflow deleted successfully"}


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Execute a workflow with given parameters

    Args:
        workflow_id: Workflow UUID
        request: Execution request with document IDs and parameters
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Workflow execution information
    """
    # Validate UUID
    try:
        uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )

    service = WorkflowService(db, str(organization.id))

    try:
        execution = service.execute_workflow(workflow_id, request)

        return WorkflowExecutionResponse(
            id=str(execution.id),
            workflow_id=str(execution.workflow_id),
            organization_id=str(execution.organization_id),
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            results=execution.results,
            created_at=execution.created_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute workflow: {str(e)}"
        )


@router.post("/suggest", response_model=WorkflowSuggestionResponse)
async def suggest_workflow(
    request: WorkflowSuggestionRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered workflow suggestions based on document type or use case

    Args:
        request: Suggestion request
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Workflow suggestion
    """
    service = WorkflowService(db, str(organization.id))

    try:
        suggestion = service.suggest_workflow(request)
        return suggestion

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate workflow suggestion: {str(e)}"
        )

"""
Document Management Routes

Handles document upload, processing, retrieval, and lifecycle management.
All endpoints require authentication and organization context.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import Optional, List
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.document import Document
from app.models.processing_job import ProcessingJob, JobStatus, JobType
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentDetailResponse,
    DocumentUpdateRequest,
    DocumentStageUpdateRequest,
    DocumentAssignRequest,
    DocumentApproveRequest,
    DocumentSignRequest,
    DocumentArchiveRequest,
    DocumentReprocessRequest,
    PaginatedDocumentsResponse
)
from app.utils.auth import get_current_user
from app.middleware.organization import get_current_organization
from app.services.blob_storage import blob_storage

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Upload a new document

    Args:
        file: The document file to upload
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        DocumentUploadResponse with document details and processing status
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    # Determine file type
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    file_type = f"application/{file_extension}"

    # Get file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    # Check storage quota (basic check)
    if organization.storage_used_bytes + file_size > (organization.storage_quota_gb * 1024 * 1024 * 1024):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Storage quota exceeded"
        )

    try:
        # Upload to blob storage
        blob_name = await blob_storage.upload_document(file, str(organization.id))
        blob_url = await blob_storage.get_document_url(blob_name)

        # Create document record
        document = Document(
            organization_id=organization.id,
            filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            blob_url=blob_url,
            status="pending",
            stage="draft",
            uploaded_by_id=current_user.id
        )

        db.add(document)

        # Update organization storage usage
        organization.storage_used_bytes += file_size

        db.commit()
        db.refresh(document)

        # Create processing job
        processing_job = ProcessingJob(
            organization_id=organization.id,
            job_type=JobType.DOCUMENT_PROCESSING,
            status=JobStatus.PENDING,
            document_id=document.id,
            priority=0,  # Default priority
            max_retries=3
        )

        db.add(processing_job)
        db.commit()
        db.refresh(processing_job)

        return DocumentUploadResponse(
            id=str(document.id),
            filename=document.filename,
            file_size=file_size,
            status=document.status,
            processing_job_id=str(processing_job.id)
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("", response_model=PaginatedDocumentsResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    stage: Optional[str] = Query(None, description="Filter by stage"),
    classification: Optional[str] = Query(None, description="Filter by classification"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    List documents with pagination and filtering

    Args:
        page: Page number (1-indexed)
        limit: Number of items per page (max 100)
        status: Filter by document status
        stage: Filter by document stage
        classification: Filter by document classification
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Paginated list of documents
    """
    # Build query
    query = db.query(Document).filter(Document.organization_id == organization.id)

    # Apply filters
    if status:
        query = query.filter(Document.status == status)
    if stage:
        query = query.filter(Document.stage == stage)
    if classification:
        query = query.filter(Document.classification == classification)

    # Get total count
    total = query.count()

    # Apply sorting
    sort_column = getattr(Document, sort_by, Document.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Apply pagination
    offset = (page - 1) * limit
    documents = query.offset(offset).limit(limit).all()

    # Calculate total pages
    pages = (total + limit - 1) // limit

    return PaginatedDocumentsResponse(
        items=[DocumentResponse(
            id=str(doc.id),
            organization_id=str(doc.organization_id),
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status=doc.status,
            stage=doc.stage,
            classification=doc.classification,
            uploaded_by_id=str(doc.uploaded_by_id) if doc.uploaded_by_id else None,
            assigned_to_id=str(doc.assigned_to_id) if doc.assigned_to_id else None,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        ) for doc in documents],
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Get document details by ID

    Args:
        document_id: Document UUID
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Detailed document information
    """
    # Validate UUID
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    # Get document
    document = db.query(Document).filter(
        Document.id == doc_uuid,
        Document.organization_id == organization.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return DocumentDetailResponse(
        id=str(document.id),
        organization_id=str(document.organization_id),
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        status=document.status,
        stage=document.stage,
        classification=document.classification,
        text_content=document.text_content,
        doc_metadata=document.doc_metadata or {},
        extracted_fields=document.extracted_fields or {},
        blob_url=document.blob_url,
        pipeline_id=str(document.pipeline_id) if document.pipeline_id else None,
        processing_started_at=document.processing_started_at,
        processing_completed_at=document.processing_completed_at,
        error_message=document.error_message,
        uploaded_by_id=str(document.uploaded_by_id) if document.uploaded_by_id else None,
        assigned_to_id=str(document.assigned_to_id) if document.assigned_to_id else None,
        created_at=document.created_at,
        updated_at=document.updated_at
    )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    update_data: DocumentUpdateRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Update document metadata

    Args:
        document_id: Document UUID
        update_data: Document update request data
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Updated document information
    """
    # Validate UUID
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    # Get document
    document = db.query(Document).filter(
        Document.id == doc_uuid,
        Document.organization_id == organization.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Update fields
    if update_data.filename is not None:
        document.filename = update_data.filename
    if update_data.classification is not None:
        document.classification = update_data.classification
    if update_data.stage is not None:
        document.stage = update_data.stage
    if update_data.metadata is not None:
        document.doc_metadata = update_data.metadata
    if update_data.assigned_to_id is not None:
        try:
            assigned_user_uuid = uuid.UUID(update_data.assigned_to_id)
            document.assigned_to_id = assigned_user_uuid
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )

    document.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(document)

        return DocumentResponse(
            id=str(document.id),
            organization_id=str(document.organization_id),
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            stage=document.stage,
            classification=document.classification,
            uploaded_by_id=str(document.uploaded_by_id) if document.uploaded_by_id else None,
            assigned_to_id=str(document.assigned_to_id) if document.assigned_to_id else None,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Delete a document

    Args:
        document_id: Document UUID
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Success confirmation
    """
    # Validate UUID
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    # Get document
    document = db.query(Document).filter(
        Document.id == doc_uuid,
        Document.organization_id == organization.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    try:
        # Delete from blob storage
        if document.blob_url:
            blob_name = document.blob_url.split('/')[-1]  # Extract blob name
            await blob_storage.delete_document(blob_name)

        # Update organization storage usage
        if document.file_size:
            organization.storage_used_bytes -= document.file_size

        # Delete from database
        db.delete(document)
        db.commit()

        return {"success": True, "message": "Document deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Download document file

    Args:
        document_id: Document UUID
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        File stream with proper headers
    """
    # Validate UUID
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    # Get document
    document = db.query(Document).filter(
        Document.id == doc_uuid,
        Document.organization_id == organization.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if not document.blob_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found in storage"
        )

    # For now, return a redirect to the blob URL
    # In production, you might want to stream the file through the API
    return {
        "download_url": document.blob_url,
        "filename": document.filename,
        "file_type": document.file_type
    }


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    request_data: DocumentReprocessRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Reprocess a document with optionally different pipeline

    Args:
        document_id: Document UUID
        request_data: Reprocess request with optional pipeline_id
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Job status information
    """
    # Validate UUID
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    # Get document
    document = db.query(Document).filter(
        Document.id == doc_uuid,
        Document.organization_id == organization.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Validate pipeline ID if provided
    if request_data.pipeline_id:
        try:
            pipeline_uuid = uuid.UUID(request_data.pipeline_id)
            document.pipeline_id = pipeline_uuid
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pipeline ID format"
            )

    # Update document status
    document.status = "pending"
    document.processing_started_at = None
    document.processing_completed_at = None
    document.error_message = None
    document.updated_at = datetime.utcnow()

    try:
        db.commit()

        # Create reprocessing job
        processing_job = ProcessingJob(
            organization_id=organization.id,
            job_type=JobType.DOCUMENT_REPROCESSING,
            status=JobStatus.PENDING,
            document_id=document.id,
            pipeline_id=document.pipeline_id,
            priority=1,  # Higher priority for reprocessing
            max_retries=3
        )

        db.add(processing_job)
        db.commit()
        db.refresh(processing_job)

        return {
            "job_id": str(processing_job.id),
            "status": "queued",
            "document_id": str(document.id)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue reprocessing: {str(e)}"
        )


@router.put("/{document_id}/stage", response_model=DocumentResponse)
async def update_document_stage(
    document_id: str,
    stage_data: DocumentStageUpdateRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Update document stage

    Args:
        document_id: Document UUID
        stage_data: Stage update request with stage and optional comment
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Updated document information
    """
    # Validate UUID
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    # Get document
    document = db.query(Document).filter(
        Document.id == doc_uuid,
        Document.organization_id == organization.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Validate stage transition
    valid_stages = ["draft", "review", "approved", "signed", "archived"]
    if stage_data.stage not in valid_stages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage. Must be one of: {', '.join(valid_stages)}"
        )

    # Update stage
    document.stage = stage_data.stage
    document.updated_at = datetime.utcnow()

    # TODO: Store comment in audit log or metadata
    if stage_data.comment:
        if not document.doc_metadata:
            document.doc_metadata = {}
        if "stage_history" not in document.doc_metadata:
            document.doc_metadata["stage_history"] = []
        document.doc_metadata["stage_history"].append({
            "stage": stage_data.stage,
            "comment": stage_data.comment,
            "updated_by": str(current_user.id),
            "updated_at": datetime.utcnow().isoformat()
        })

    try:
        db.commit()
        db.refresh(document)

        return DocumentResponse(
            id=str(document.id),
            organization_id=str(document.organization_id),
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            stage=document.stage,
            classification=document.classification,
            uploaded_by_id=str(document.uploaded_by_id) if document.uploaded_by_id else None,
            assigned_to_id=str(document.assigned_to_id) if document.assigned_to_id else None,
            created_at=document.created_at,
            updated_at=document.updated_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document stage: {str(e)}"
        )


@router.post("/{document_id}/assign", response_model=DocumentResponse)
async def assign_document(
    document_id: str,
    assign_data: DocumentAssignRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Assign document to a user

    Args:
        document_id: Document UUID
        assign_data: Assignment request with user_id
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Updated document information
    """
    # Validate document UUID
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    # Validate user UUID
    try:
        user_uuid = uuid.UUID(assign_data.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    # Get document
    document = db.query(Document).filter(
        Document.id == doc_uuid,
        Document.organization_id == organization.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # TODO: Verify user belongs to organization

    # Assign document
    document.assigned_to_id = user_uuid
    document.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(document)

        # TODO: Create notification for assigned user

        return DocumentResponse(
            id=str(document.id),
            organization_id=str(document.organization_id),
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            stage=document.stage,
            classification=document.classification,
            uploaded_by_id=str(document.uploaded_by_id) if document.uploaded_by_id else None,
            assigned_to_id=str(document.assigned_to_id) if document.assigned_to_id else None,
            created_at=document.created_at,
            updated_at=document.updated_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign document: {str(e)}"
        )


@router.post("/{document_id}/approve", response_model=DocumentResponse)
async def approve_document(
    document_id: str,
    approve_data: DocumentApproveRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Approve a document

    Args:
        document_id: Document UUID
        approve_data: Approval request with optional comment
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Updated document information
    """
    # Validate UUID
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    # Get document
    document = db.query(Document).filter(
        Document.id == doc_uuid,
        Document.organization_id == organization.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Update to approved stage
    document.stage = "approved"
    document.updated_at = datetime.utcnow()

    # Store approval metadata
    if not document.doc_metadata:
        document.doc_metadata = {}
    document.doc_metadata["approved_by"] = str(current_user.id)
    document.doc_metadata["approved_at"] = datetime.utcnow().isoformat()
    if approve_data.comment:
        document.doc_metadata["approval_comment"] = approve_data.comment

    try:
        db.commit()
        db.refresh(document)

        return DocumentResponse(
            id=str(document.id),
            organization_id=str(document.organization_id),
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            stage=document.stage,
            classification=document.classification,
            uploaded_by_id=str(document.uploaded_by_id) if document.uploaded_by_id else None,
            assigned_to_id=str(document.assigned_to_id) if document.assigned_to_id else None,
            created_at=document.created_at,
            updated_at=document.updated_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve document: {str(e)}"
        )


@router.post("/{document_id}/sign", response_model=DocumentResponse)
async def sign_document(
    document_id: str,
    sign_data: DocumentSignRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Sign a document

    Args:
        document_id: Document UUID
        sign_data: Signature request with signature_data
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Updated document information
    """
    # Validate UUID
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    # Get document
    document = db.query(Document).filter(
        Document.id == doc_uuid,
        Document.organization_id == organization.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Document should be approved before signing
    if document.stage not in ["approved", "signed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be approved before signing"
        )

    # Update to signed stage
    document.stage = "signed"
    document.updated_at = datetime.utcnow()

    # Store signature metadata
    if not document.doc_metadata:
        document.doc_metadata = {}
    if "signatures" not in document.doc_metadata:
        document.doc_metadata["signatures"] = []

    document.doc_metadata["signatures"].append({
        "signed_by": str(current_user.id),
        "signed_at": datetime.utcnow().isoformat(),
        "signature_data": sign_data.signature_data
    })

    try:
        db.commit()
        db.refresh(document)

        return DocumentResponse(
            id=str(document.id),
            organization_id=str(document.organization_id),
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            stage=document.stage,
            classification=document.classification,
            uploaded_by_id=str(document.uploaded_by_id) if document.uploaded_by_id else None,
            assigned_to_id=str(document.assigned_to_id) if document.assigned_to_id else None,
            created_at=document.created_at,
            updated_at=document.updated_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sign document: {str(e)}"
        )


@router.post("/{document_id}/archive", response_model=DocumentResponse)
async def archive_document(
    document_id: str,
    archive_data: DocumentArchiveRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Archive a document

    Args:
        document_id: Document UUID
        archive_data: Archive request with optional reason
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Updated document information
    """
    # Validate UUID
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    # Get document
    document = db.query(Document).filter(
        Document.id == doc_uuid,
        Document.organization_id == organization.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Update to archived stage
    document.stage = "archived"
    document.updated_at = datetime.utcnow()

    # Store archive metadata
    if not document.doc_metadata:
        document.doc_metadata = {}
    document.doc_metadata["archived_by"] = str(current_user.id)
    document.doc_metadata["archived_at"] = datetime.utcnow().isoformat()
    if archive_data.reason:
        document.doc_metadata["archive_reason"] = archive_data.reason

    try:
        db.commit()
        db.refresh(document)

        return DocumentResponse(
            id=str(document.id),
            organization_id=str(document.organization_id),
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            stage=document.stage,
            classification=document.classification,
            uploaded_by_id=str(document.uploaded_by_id) if document.uploaded_by_id else None,
            assigned_to_id=str(document.assigned_to_id) if document.assigned_to_id else None,
            created_at=document.created_at,
            updated_at=document.updated_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive document: {str(e)}"
        )
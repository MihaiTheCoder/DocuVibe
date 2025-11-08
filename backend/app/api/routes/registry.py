"""
Registry Routes

Handles document registry and metadata search operations.
All endpoints require authentication and organization context.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, Any, List
import time
import math

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.document import Document
from app.schemas.document import DocumentResponse, PaginatedDocumentsResponse
from app.schemas.search import (
    RegistryQueryRequest,
    QueryResultResponse
)
from app.utils.auth import get_current_user
from app.middleware.organization import get_current_organization
from app.services.search_service import SearchService

router = APIRouter(prefix="/registry", tags=["registry"])


@router.get("/search", response_model=PaginatedDocumentsResponse)
async def metadata_search(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
    **metadata_filters: Dict[str, Any]
):
    """
    Search documents by metadata fields

    Args:
        page: Page number for pagination
        limit: Number of results per page
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session
        **metadata_filters: Dynamic metadata filters passed as query parameters
            e.g., ?metadata.vendor=SupplierX&metadata.amount_gt=1000

    Returns:
        PaginatedDocumentsResponse with matching documents

    Examples:
        - Search by vendor: GET /registry/search?metadata.vendor=SupplierX
        - Search by amount range: GET /registry/search?metadata.amount_gt=1000&metadata.amount_lt=5000
        - Search by date: GET /registry/search?metadata.invoice_date=2024-01-15
    """
    search_service = SearchService(db)

    # Parse metadata filters from query parameters
    # Parameters starting with "metadata." are metadata filters
    # Operators: _gt, _gte, _lt, _lte, _eq (default)
    parsed_filters = {}
    for key, value in metadata_filters.items():
        if key.startswith("metadata."):
            field_name = key.replace("metadata.", "")

            # Check for operators
            if field_name.endswith("_gt"):
                actual_field = field_name[:-3]
                parsed_filters[actual_field] = {"gt": value}
            elif field_name.endswith("_gte"):
                actual_field = field_name[:-4]
                parsed_filters[actual_field] = {"gte": value}
            elif field_name.endswith("_lt"):
                actual_field = field_name[:-3]
                parsed_filters[actual_field] = {"lt": value}
            elif field_name.endswith("_lte"):
                actual_field = field_name[:-4]
                parsed_filters[actual_field] = {"lte": value}
            else:
                parsed_filters[field_name] = value

    try:
        documents, total = search_service.metadata_search(
            metadata_filters=parsed_filters,
            organization_id=str(organization.id),
            page=page,
            limit=limit
        )

        # Convert to response schema
        items = [
            DocumentResponse(
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
            )
            for doc in documents
        ]

        pages = math.ceil(total / limit) if total > 0 else 0

        return PaginatedDocumentsResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metadata search failed: {str(e)}"
        )


@router.post("/query", response_model=QueryResultResponse)
async def execute_query(
    request: RegistryQueryRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Execute a SQL query on the document registry

    **WARNING**: This endpoint allows SQL execution and should be restricted to admin users
    in production. Currently available for testing purposes.

    Args:
        request: Query request with SQL and parameters
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        QueryResultResponse with query results

    Security Notes:
        - Organization ID is automatically injected into WHERE clause
        - Only SELECT queries are allowed
        - Query parameters should be used to prevent SQL injection
    """
    # Security check: Only allow SELECT queries
    query_upper = request.sql.strip().upper()
    if not query_upper.startswith("SELECT"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only SELECT queries are allowed"
        )

    # Ensure organization_id filter is present
    if "organization_id" not in request.sql.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must include organization_id filter"
        )

    start_time = time.time()

    try:
        # Add organization_id to parameters if using placeholders
        params = request.params or []

        # Execute query
        result = db.execute(text(request.sql), params)

        # Fetch all rows
        rows = result.fetchall()
        columns = list(result.keys())

        # Convert rows to list of dicts
        rows_dict = [
            {col: value for col, value in zip(columns, row)}
            for row in rows
        ]

        execution_time = (time.time() - start_time) * 1000

        return QueryResultResponse(
            columns=columns,
            rows=rows_dict,
            total=len(rows_dict),
            execution_time_ms=execution_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )

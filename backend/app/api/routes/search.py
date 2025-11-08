"""
Search Routes

Handles document search operations including text, semantic, and hybrid search.
All endpoints require authentication and organization context.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.schemas.search import (
    DocumentSearchRequest,
    SemanticSearchRequest,
    SearchResultsResponse,
    SemanticSearchResponse,
    FacetsResponse
)
from app.utils.auth import get_current_user
from app.middleware.organization import get_current_organization
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/documents", response_model=SearchResultsResponse)
async def search_documents(
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Search documents using text, semantic, or hybrid search

    Args:
        request: Search request with query, filters, and search type
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        SearchResultsResponse with matching documents and relevance scores
    """
    search_service = SearchService(db)

    try:
        if request.search_type == "text":
            results, total, execution_time = await search_service.text_search(
                query_text=request.query,
                organization_id=str(organization.id),
                filters=request.filters,
                page=request.page,
                limit=request.limit
            )
        elif request.search_type == "semantic":
            semantic_results, execution_time = await search_service.semantic_search(
                query_text=request.query,
                organization_id=str(organization.id),
                top_k=request.limit,
                threshold=0.7,
                filters=request.filters
            )
            # Convert semantic results to search result items
            from app.schemas.search import SearchResultItem
            results = [
                SearchResultItem(
                    id=r.id,
                    filename=r.filename,
                    classification=r.classification,
                    stage="",
                    status="",
                    text_snippet=r.text_snippet,
                    relevance_score=r.similarity_score,
                    created_at=None,
                    metadata=r.metadata
                )
                for r in semantic_results
            ]
            total = len(results)
        else:  # hybrid
            results, total, execution_time = await search_service.hybrid_search(
                query_text=request.query,
                organization_id=str(organization.id),
                filters=request.filters,
                page=request.page,
                limit=request.limit
            )

        pages = math.ceil(total / request.limit) if total > 0 else 0

        return SearchResultsResponse(
            items=results,
            total=total,
            query=request.query,
            search_type=request.search_type,
            page=request.page,
            limit=request.limit,
            pages=pages,
            execution_time_ms=execution_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Perform semantic search using vector embeddings

    Args:
        request: Semantic search request with query and parameters
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        SemanticSearchResponse with similar documents and similarity scores
    """
    search_service = SearchService(db)

    try:
        results, execution_time = await search_service.semantic_search(
            query_text=request.query,
            organization_id=str(organization.id),
            top_k=request.top_k,
            threshold=request.threshold,
            filters=request.filters
        )

        return SemanticSearchResponse(
            results=results,
            query=request.query,
            total=len(results),
            execution_time_ms=execution_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}"
        )


@router.get("/facets", response_model=FacetsResponse)
async def get_facets(
    field: List[str] = Query(..., description="Fields to get facet counts for"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Get faceted counts for specified fields

    Args:
        field: List of fields to get facet counts for (e.g., classification, stage, status)
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        FacetsResponse with counts for each field value
    """
    search_service = SearchService(db)

    try:
        facets = search_service.get_facets(
            fields=field,
            organization_id=str(organization.id)
        )

        return FacetsResponse(facets=facets)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get facets: {str(e)}"
        )

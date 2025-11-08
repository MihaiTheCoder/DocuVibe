"""
Search Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Any
from datetime import datetime


class DateRangeFilter(BaseModel):
    """Schema for date range filter"""
    from_date: Optional[datetime] = Field(None, alias="from")
    to_date: Optional[datetime] = Field(None, alias="to")


class SearchFilters(BaseModel):
    """Schema for search filters"""
    date_range: Optional[DateRangeFilter] = None
    stage: Optional[list[str]] = None
    classification: Optional[str] = None
    uploaded_by_id: Optional[str] = None
    assigned_to_id: Optional[str] = None
    status: Optional[list[str]] = None


class DocumentSearchRequest(BaseModel):
    """Schema for document search request"""
    query: str = Field(..., description="Search query text")
    filters: Optional[SearchFilters] = None
    search_type: Literal["text", "semantic", "hybrid"] = Field(
        default="hybrid",
        description="Type of search to perform"
    )
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class SemanticSearchRequest(BaseModel):
    """Schema for semantic search request"""
    query: str = Field(..., description="Semantic query text")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold"
    )
    filters: Optional[SearchFilters] = None


class SearchResultItem(BaseModel):
    """Schema for a single search result"""
    id: str
    filename: str
    classification: Optional[str] = None
    stage: str
    status: str
    text_snippet: Optional[str] = None
    relevance_score: float = Field(..., description="Search relevance score")
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: dict = {}


class SearchResultsResponse(BaseModel):
    """Schema for search results response"""
    items: list[SearchResultItem]
    total: int
    query: str
    search_type: str
    page: int
    limit: int
    pages: int
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")


class SemanticSearchResult(BaseModel):
    """Schema for semantic search result"""
    id: str
    filename: str
    text_snippet: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    classification: Optional[str] = None
    metadata: dict = {}


class SemanticSearchResponse(BaseModel):
    """Schema for semantic search response"""
    results: list[SemanticSearchResult]
    query: str
    total: int
    execution_time_ms: float


class FacetCount(BaseModel):
    """Schema for facet count"""
    value: str
    count: int


class FacetsResponse(BaseModel):
    """Schema for facets response"""
    facets: dict[str, list[FacetCount]] = Field(
        ...,
        description="Map of field name to list of value counts"
    )


class RegistrySearchRequest(BaseModel):
    """Schema for registry metadata search"""
    metadata_filters: dict[str, Any] = Field(
        ...,
        description="Metadata key-value filters"
    )
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class RegistryQueryRequest(BaseModel):
    """Schema for registry SQL query"""
    sql: str = Field(..., description="SQL query to execute")
    params: Optional[list] = Field(default=[], description="Query parameters")


class QueryResultResponse(BaseModel):
    """Schema for SQL query result response"""
    columns: list[str]
    rows: list[dict]
    total: int
    execution_time_ms: float

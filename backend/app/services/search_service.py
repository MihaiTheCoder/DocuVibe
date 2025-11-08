"""
Search Service

Handles document search operations including text search, semantic search, and hybrid search.
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, case
from datetime import datetime
import time
import logging

from app.models.document import Document
from app.schemas.search import (
    SearchFilters,
    SearchResultItem,
    SemanticSearchResult,
    FacetCount
)
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)


class SearchService:
    """Service for document search operations"""

    def __init__(self, db: Session):
        self.db = db

    def _apply_filters(self, query, filters: Optional[SearchFilters], organization_id: str):
        """Apply filters to a query"""
        # Always filter by organization
        query = query.filter(Document.organization_id == organization_id)

        if not filters:
            return query

        # Date range filter
        if filters.date_range:
            if filters.date_range.from_date:
                query = query.filter(Document.created_at >= filters.date_range.from_date)
            if filters.date_range.to_date:
                query = query.filter(Document.created_at <= filters.date_range.to_date)

        # Stage filter
        if filters.stage:
            query = query.filter(Document.stage.in_(filters.stage))

        # Classification filter
        if filters.classification:
            query = query.filter(Document.classification == filters.classification)

        # Status filter
        if filters.status:
            query = query.filter(Document.status.in_(filters.status))

        # Uploaded by filter
        if filters.uploaded_by_id:
            query = query.filter(Document.uploaded_by_id == filters.uploaded_by_id)

        # Assigned to filter
        if filters.assigned_to_id:
            query = query.filter(Document.assigned_to_id == filters.assigned_to_id)

        return query

    async def text_search(
        self,
        query_text: str,
        organization_id: str,
        filters: Optional[SearchFilters] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[SearchResultItem], int, float]:
        """Perform text search on documents"""
        start_time = time.time()

        # Build base query
        base_query = self.db.query(Document)

        # Apply filters
        base_query = self._apply_filters(base_query, filters, organization_id)

        # Text search on filename and text_content
        search_filter = or_(
            Document.filename.ilike(f"%{query_text}%"),
            Document.text_content.ilike(f"%{query_text}%"),
            Document.classification.ilike(f"%{query_text}%")
        )
        base_query = base_query.filter(search_filter)

        # Get total count
        total = base_query.count()

        # Apply pagination
        offset = (page - 1) * limit
        documents = base_query.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()

        # Convert to search result items
        results = []
        for doc in documents:
            # Extract text snippet
            snippet = self._extract_snippet(doc.text_content, query_text)

            # Calculate relevance score (simple text match score)
            score = self._calculate_text_relevance(doc, query_text)

            results.append(SearchResultItem(
                id=str(doc.id),
                filename=doc.filename,
                classification=doc.classification,
                stage=doc.stage,
                status=doc.status,
                text_snippet=snippet,
                relevance_score=score,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                metadata=doc.metadata or {}
            ))

        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        return results, total, execution_time

    async def semantic_search(
        self,
        query_text: str,
        organization_id: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[SearchFilters] = None
    ) -> Tuple[List[SemanticSearchResult], float]:
        """Perform semantic search using vector embeddings"""
        start_time = time.time()

        # Generate embedding for query
        # For now, we'll return empty results since we don't have embeddings yet
        # This will be implemented when we integrate with the embedding model
        query_embedding = await self._generate_embedding(query_text)

        # Search Qdrant
        filter_dict = {}
        if filters and filters.classification:
            filter_dict["classification"] = filters.classification

        qdrant_results = await qdrant_service.search_similar(
            query_embedding=query_embedding,
            organization_id=organization_id,
            limit=top_k,
            threshold=threshold,
            filters=filter_dict
        )

        # Get document details from database
        results = []
        if qdrant_results:
            document_ids = [r["document_id"] for r in qdrant_results]
            documents = self.db.query(Document).filter(
                Document.id.in_(document_ids),
                Document.organization_id == organization_id
            ).all()

            # Create a mapping for quick lookup
            doc_map = {str(doc.id): doc for doc in documents}

            # Build results
            for qr in qdrant_results:
                doc_id = qr["document_id"]
                if doc_id in doc_map:
                    doc = doc_map[doc_id]
                    results.append(SemanticSearchResult(
                        id=str(doc.id),
                        filename=doc.filename,
                        text_snippet=self._extract_snippet(qr["text"], query_text, max_length=200),
                        similarity_score=qr["score"],
                        classification=doc.classification,
                        metadata=doc.metadata or {}
                    ))

        execution_time = (time.time() - start_time) * 1000

        return results, execution_time

    async def hybrid_search(
        self,
        query_text: str,
        organization_id: str,
        filters: Optional[SearchFilters] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[SearchResultItem], int, float]:
        """Perform hybrid search combining text and semantic search"""
        start_time = time.time()

        # Perform both text and semantic search
        text_results, text_total, _ = await self.text_search(
            query_text,
            organization_id,
            filters,
            page=1,
            limit=limit * 2  # Get more results to merge
        )

        semantic_results, _ = await self.semantic_search(
            query_text,
            organization_id,
            top_k=limit * 2,
            threshold=0.5,
            filters=filters
        )

        # Merge results by combining scores
        merged_results = self._merge_search_results(text_results, semantic_results)

        # Apply pagination to merged results
        offset = (page - 1) * limit
        paginated_results = merged_results[offset:offset + limit]

        execution_time = (time.time() - start_time) * 1000

        return paginated_results, len(merged_results), execution_time

    def get_facets(
        self,
        fields: List[str],
        organization_id: str,
        filters: Optional[SearchFilters] = None
    ) -> Dict[str, List[FacetCount]]:
        """Get faceted counts for specified fields"""
        facets = {}

        base_query = self.db.query(Document)
        base_query = self._apply_filters(base_query, filters, organization_id)

        for field in fields:
            if field == "classification":
                counts = base_query.with_entities(
                    Document.classification,
                    func.count(Document.id).label('count')
                ).filter(
                    Document.classification.isnot(None)
                ).group_by(
                    Document.classification
                ).all()

                facets["classification"] = [
                    FacetCount(value=value, count=count)
                    for value, count in counts
                ]

            elif field == "stage":
                counts = base_query.with_entities(
                    Document.stage,
                    func.count(Document.id).label('count')
                ).group_by(
                    Document.stage
                ).all()

                facets["stage"] = [
                    FacetCount(value=value, count=count)
                    for value, count in counts
                ]

            elif field == "status":
                counts = base_query.with_entities(
                    Document.status,
                    func.count(Document.id).label('count')
                ).group_by(
                    Document.status
                ).all()

                facets["status"] = [
                    FacetCount(value=value, count=count)
                    for value, count in counts
                ]

        return facets

    def metadata_search(
        self,
        metadata_filters: Dict[str, Any],
        organization_id: str,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Document], int]:
        """Search documents by metadata fields"""
        query = self.db.query(Document).filter(
            Document.organization_id == organization_id
        )

        # Apply metadata filters using JSON operators
        for key, value in metadata_filters.items():
            if isinstance(value, dict):
                # Handle operators like _gt, _lt, etc.
                for op, op_value in value.items():
                    if op == "gt":
                        query = query.filter(
                            func.cast(Document.metadata[key].astext, type_=type(op_value)) > op_value
                        )
                    elif op == "gte":
                        query = query.filter(
                            func.cast(Document.metadata[key].astext, type_=type(op_value)) >= op_value
                        )
                    elif op == "lt":
                        query = query.filter(
                            func.cast(Document.metadata[key].astext, type_=type(op_value)) < op_value
                        )
                    elif op == "lte":
                        query = query.filter(
                            func.cast(Document.metadata[key].astext, type_=type(op_value)) <= op_value
                        )
            else:
                # Simple equality
                query = query.filter(Document.metadata[key].astext == str(value))

        total = query.count()
        offset = (page - 1) * limit
        documents = query.offset(offset).limit(limit).all()

        return documents, total

    # Helper methods

    def _extract_snippet(
        self,
        text: Optional[str],
        query: str,
        max_length: int = 200
    ) -> Optional[str]:
        """Extract a relevant snippet from text around the query"""
        if not text:
            return None

        text_lower = text.lower()
        query_lower = query.lower()

        # Find first occurrence of query
        pos = text_lower.find(query_lower)
        if pos == -1:
            # Query not found, return beginning of text
            return text[:max_length] + "..." if len(text) > max_length else text

        # Extract snippet around query
        start = max(0, pos - max_length // 2)
        end = min(len(text), pos + len(query) + max_length // 2)

        snippet = text[start:end]

        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet

    def _calculate_text_relevance(self, document: Document, query: str) -> float:
        """Calculate a simple text relevance score"""
        score = 0.0
        query_lower = query.lower()

        # Filename match (highest weight)
        if document.filename and query_lower in document.filename.lower():
            score += 0.5

        # Classification match
        if document.classification and query_lower in document.classification.lower():
            score += 0.3

        # Content match (lower weight)
        if document.text_content and query_lower in document.text_content.lower():
            score += 0.2

        return min(score, 1.0)

    def _merge_search_results(
        self,
        text_results: List[SearchResultItem],
        semantic_results: List[SemanticSearchResult]
    ) -> List[SearchResultItem]:
        """Merge text and semantic search results"""
        # Create a map of document IDs to combined scores
        score_map: Dict[str, Dict[str, Any]] = {}

        # Add text results
        for result in text_results:
            score_map[result.id] = {
                "result": result,
                "text_score": result.relevance_score,
                "semantic_score": 0.0
            }

        # Add semantic results
        for result in semantic_results:
            if result.id in score_map:
                score_map[result.id]["semantic_score"] = result.similarity_score
            else:
                # Create SearchResultItem from SemanticSearchResult
                score_map[result.id] = {
                    "result": SearchResultItem(
                        id=result.id,
                        filename=result.filename,
                        classification=result.classification,
                        stage="",  # Not available in semantic result
                        status="",  # Not available in semantic result
                        text_snippet=result.text_snippet,
                        relevance_score=result.similarity_score,
                        created_at=datetime.utcnow(),  # Will be updated from DB
                        metadata=result.metadata
                    ),
                    "text_score": 0.0,
                    "semantic_score": result.similarity_score
                }

        # Calculate combined scores and sort
        merged = []
        for doc_id, scores in score_map.items():
            # Weighted combination: 60% semantic, 40% text
            combined_score = (scores["semantic_score"] * 0.6) + (scores["text_score"] * 0.4)
            result = scores["result"]
            result.relevance_score = combined_score
            merged.append(result)

        # Sort by combined score
        merged.sort(key=lambda x: x.relevance_score, reverse=True)

        return merged

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using a sentence transformer model"""
        # Placeholder - return zero vector for now
        # This will be implemented when we integrate with the embedding model
        # For example: sentence-transformers/all-MiniLM-L6-v2
        return [0.0] * 384  # 384 is the dimension for all-MiniLM-L6-v2

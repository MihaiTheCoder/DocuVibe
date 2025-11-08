"""
Qdrant Vector Database Service

This service handles vector search operations using Qdrant for semantic search.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.core.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for interacting with Qdrant vector database"""

    def __init__(self):
        """Initialize Qdrant client"""
        self.client: Optional[QdrantClient] = None
        self.collection_name = "documents"
        self.vector_size = 384  # Default for sentence-transformers/all-MiniLM-L6-v2

    async def initialize(self):
        """Initialize connection to Qdrant"""
        try:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                https=settings.QDRANT_HTTPS,
                api_key=settings.QDRANT_API_KEY,
                timeout=30.0
            )

            # Check if collection exists, create if not
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )

            logger.info("Qdrant service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            # Don't raise - allow app to start even if Qdrant is not available
            self.client = None

    async def add_document(
        self,
        document_id: str,
        text: str,
        embedding: List[float],
        organization_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add or update a document in Qdrant"""
        if not self.client:
            logger.warning("Qdrant client not initialized")
            return False

        try:
            payload = {
                "document_id": document_id,
                "organization_id": organization_id,
                "text": text,
                "metadata": metadata or {},
                "indexed_at": datetime.utcnow().isoformat()
            }

            point = PointStruct(
                id=document_id,
                vector=embedding,
                payload=payload
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            logger.info(f"Added document {document_id} to Qdrant")
            return True

        except Exception as e:
            logger.error(f"Failed to add document to Qdrant: {e}")
            return False

    async def search_similar(
        self,
        query_embedding: List[float],
        organization_id: str,
        limit: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        if not self.client:
            logger.warning("Qdrant client not initialized")
            return []

        try:
            # Build filter for organization
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="organization_id",
                        match=MatchValue(value=organization_id)
                    )
                ]
            )

            # Add additional filters if provided
            if filters:
                if "classification" in filters and filters["classification"]:
                    query_filter.must.append(
                        FieldCondition(
                            key="metadata.classification",
                            match=MatchValue(value=filters["classification"])
                        )
                    )

            # Perform search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                score_threshold=threshold
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "document_id": result.payload.get("document_id"),
                    "text": result.payload.get("text", ""),
                    "score": result.score,
                    "metadata": result.payload.get("metadata", {})
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search Qdrant: {e}")
            return []

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from Qdrant"""
        if not self.client:
            logger.warning("Qdrant client not initialized")
            return False

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[document_id]
            )
            logger.info(f"Deleted document {document_id} from Qdrant")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document from Qdrant: {e}")
            return False

    async def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the collection"""
        if not self.client:
            return None

        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "name": info.config.params.vectors.size,
                "vector_size": info.config.params.vectors.size,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None


# Global instance
qdrant_service = QdrantService()

"""
Azure Blob Storage Service

Handles document upload, retrieval, and deletion from Azure Blob Storage.
Falls back to MinIO for local development if Azure connection is not configured.
"""

from azure.storage.blob import BlobServiceClient, BlobClient
from fastapi import UploadFile
import uuid
from typing import Optional
from app.core.config import settings


class BlobStorageService:
    """Service for managing documents in Azure Blob Storage"""

    def __init__(self):
        """Initialize Blob Storage client"""
        if settings.USE_AZURE_STORAGE:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
            self.container_name = settings.AZURE_STORAGE_CONTAINER
            self.use_azure = True
        else:
            # For local development, this would use MinIO
            # Not implemented in this hello world version
            self.use_azure = False

    async def upload_document(
        self,
        file: UploadFile,
        organization_id: str
    ) -> str:
        """
        Upload document to Azure Blob Storage

        Args:
            file: The uploaded file
            organization_id: Organization ID for file organization

        Returns:
            str: Blob name (path) of uploaded file
        """
        if not self.use_azure:
            raise NotImplementedError("MinIO storage not implemented in hello world version")

        # Generate unique blob name
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        blob_name = f"{organization_id}/{uuid.uuid4()}.{file_extension}"

        # Get blob client
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )

        # Upload file
        contents = await file.read()
        blob_client.upload_blob(contents, overwrite=True)

        return blob_name

    async def get_document_url(self, blob_name: str) -> str:
        """
        Get URL for document access

        Args:
            blob_name: The blob name (path) of the document

        Returns:
            str: URL to access the document
        """
        if not self.use_azure:
            raise NotImplementedError("MinIO storage not implemented in hello world version")

        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        return blob_client.url

    async def delete_document(self, blob_name: str) -> bool:
        """
        Delete document from storage

        Args:
            blob_name: The blob name (path) of the document

        Returns:
            bool: True if deletion successful
        """
        if not self.use_azure:
            raise NotImplementedError("MinIO storage not implemented in hello world version")

        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        blob_client.delete_blob()
        return True

    async def download_document(self, blob_name: str) -> bytes:
        """
        Download a document from blob storage

        Args:
            blob_name: Name/path of the blob

        Returns:
            Document content as bytes

        Raises:
            NotImplementedError: If storage backend not configured
            Exception: If download fails
        """
        if not self.use_azure:
            raise NotImplementedError("Local storage not yet implemented")

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            # Download blob content
            blob_data = blob_client.download_blob()
            content = blob_data.readall()

            return content

        except Exception as e:
            raise Exception(f"Failed to download blob {blob_name}: {str(e)}")

    def is_configured(self) -> bool:
        """Check if blob storage is properly configured"""
        return self.use_azure


# Create singleton instance
blob_storage = BlobStorageService()

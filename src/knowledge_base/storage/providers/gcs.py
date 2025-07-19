"""
Google Cloud Storage (GCS) provider for the knowledge base system.

This module implements a vector store provider that uses Google Cloud Storage (GCS)
for storing and retrieving document chunks.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple

from google.cloud import storage
from google.api_core import exceptions

from ...core.types import Document, TextChunk
from ...core.exceptions import StorageError
from ..base import BaseVectorStore


class GCSVectorStore(BaseVectorStore):
    """
    Vector store implementation using Google Cloud Storage (GCS).
    
    This provider stores document chunks as JSON objects in a GCS bucket.
    It supports both Application Default Credentials (ADC) for local development
    and Service Account keys for production/automation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the GCS vector store with configuration.
        
        Args:
            config: Configuration dictionary with GCS-specific settings:
                - bucket_name: Name of the GCS bucket to use
                - auth_method: Authentication method ('adc' or 'service_account')
                - service_account_key_path: Path to service account key file (if using service_account)
        
        Raises:
            ValueError: If required configuration is missing
        """
        super().__init__(config)
        self.bucket_name = self.config.get("bucket_name")
        if not self.bucket_name:
            raise ValueError("GCSVectorStore requires a 'bucket_name' in the configuration.")
        
        self.storage_client = None
        self.bucket = None
    
    async def initialize(self) -> None:
        """
        Initialize the GCS connection and resources.
        
        This method authenticates with GCS and sets up the bucket connection.
        
        Raises:
            StorageError: If initialization fails
        """
        try:
            # Run authentication in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.storage_client = await loop.run_in_executor(None, self._authenticate)
            self.bucket = self.storage_client.bucket(self.bucket_name)
            
            # Check if bucket exists
            if not await loop.run_in_executor(None, self.bucket.exists):
                raise StorageError(f"GCS bucket '{self.bucket_name}' does not exist")
            
            self._initialized = True
        except Exception as e:
            raise StorageError(f"Failed to initialize GCS vector store: {str(e)}") from e
    
    def _authenticate(self) -> storage.Client:
        """
        Authenticate with GCS using the configured method.
        
        Returns:
            Authenticated GCS client
            
        Raises:
            ValueError: If the authentication method is not supported
            FileNotFoundError: If the service account key file is not found
        """
        auth_method = self.config.get("auth_method", "adc")  # Default to ADC

        if auth_method == "adc":
            try:
                return storage.Client()
            except exceptions.DefaultCredentialsError as e:
                raise ValueError(
                    "Could not find Application Default Credentials. "
                    "Please run 'gcloud auth application-default login' in your terminal."
                ) from e

        elif auth_method == "service_account":
            creds_path = self.config.get("service_account_key_path")
            if not creds_path or not os.path.exists(creds_path):
                raise FileNotFoundError(
                    f"Service account key file not found at '{creds_path}'."
                )
            return storage.Client.from_service_account_json(creds_path)
        
        else:
            raise ValueError(f"Unsupported GCS auth_method: '{auth_method}'. Use 'adc' or 'service_account'.")
    
    async def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Add texts to the GCS vector store.
        
        Args:
            texts: List of text strings to add
            metadatas: Optional list of metadata dictionaries, one per text
            ids: Optional list of IDs to assign to the texts
            embeddings: Optional list of pre-computed embeddings
            
        Returns:
            List of IDs for the added texts
            
        Raises:
            StorageError: If adding texts fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        # Prepare chunks
        from uuid import uuid4
        
        if ids is None:
            ids = [str(uuid4()) for _ in texts]
        
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        chunks = []
        for i, (text, metadata, id) in enumerate(zip(texts, metadatas, ids)):
            chunk = {
                "id": id,
                "text": text,
                "metadata": metadata,
            }
            if embeddings and i < len(embeddings):
                chunk["embedding"] = embeddings[i]
            chunks.append(chunk)
        
        # Store chunks
        try:
            loop = asyncio.get_event_loop()
            tasks = []
            for chunk in chunks:
                tasks.append(loop.run_in_executor(
                    None, 
                    self._store_chunk, 
                    chunk
                ))
            await asyncio.gather(*tasks)
            return ids
        except Exception as e:
            raise StorageError(f"Failed to add texts to GCS: {str(e)}") from e
    
    def _store_chunk(self, chunk: Dict[str, Any]) -> None:
        """
        Store a single chunk in GCS.
        
        Args:
            chunk: Chunk dictionary to store
            
        Raises:
            Exception: If storing fails
        """
        blob = self.bucket.blob(f"{chunk['id']}.json")
        blob.upload_from_string(
            json.dumps(chunk),
            content_type="application/json"
        )
    
    async def add_documents(
        self,
        documents: List[Document]
    ) -> List[str]:
        """
        Add documents to the GCS vector store.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            List of document IDs for the added documents
            
        Raises:
            StorageError: If adding documents fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        try:
            texts = [doc.content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            ids = [doc.id for doc in documents]
            
            # Store document metadata separately
            loop = asyncio.get_event_loop()
            tasks = []
            for doc in documents:
                doc_metadata = {
                    "id": doc.id,
                    "type": doc.type.value if hasattr(doc.type, "value") else str(doc.type),
                    "metadata": doc.metadata
                }
                tasks.append(loop.run_in_executor(
                    None,
                    self._store_document_metadata,
                    doc.id,
                    doc_metadata
                ))
            await asyncio.gather(*tasks)
            
            # Store the document contents as chunks
            return await self.add_texts(texts, metadatas, ids)
        except Exception as e:
            raise StorageError(f"Failed to add documents to GCS: {str(e)}") from e
    
    def _store_document_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> None:
        """
        Store document metadata in GCS.
        
        Args:
            doc_id: Document ID
            metadata: Document metadata dictionary
            
        Raises:
            Exception: If storing fails
        """
        blob = self.bucket.blob(f"docs/{doc_id}.json")
        blob.upload_from_string(
            json.dumps(metadata),
            content_type="application/json"
        )
    
    async def add_chunks(
        self,
        chunks: List[TextChunk]
    ) -> List[str]:
        """
        Add text chunks to the GCS vector store.
        
        Args:
            chunks: List of TextChunk objects to add
            
        Returns:
            List of chunk IDs for the added chunks
            
        Raises:
            StorageError: If adding chunks fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        try:
            texts = [chunk.text for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            ids = [chunk.id for chunk in chunks]
            embeddings = [chunk.embedding for chunk in chunks if chunk.embedding is not None]
            
            if embeddings and len(embeddings) != len(chunks):
                embeddings = None  # If not all chunks have embeddings, don't use any
            
            return await self.add_texts(texts, metadatas, ids, embeddings)
        except Exception as e:
            raise StorageError(f"Failed to add chunks to GCS: {str(e)}") from e
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            Document object if found, None otherwise
            
        Raises:
            StorageError: If retrieval fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Get document metadata
            doc_blob = self.bucket.blob(f"docs/{document_id}.json")
            exists = await loop.run_in_executor(None, doc_blob.exists)
            if not exists:
                return None
            
            doc_data = json.loads(await loop.run_in_executor(None, doc_blob.download_as_string))
            
            # Get document content
            content_blob = self.bucket.blob(f"{document_id}.json")
            exists = await loop.run_in_executor(None, content_blob.exists)
            if not exists:
                return None
            
            content_data = json.loads(await loop.run_in_executor(None, content_blob.download_as_string))
            
            # Create Document object
            from ...core.types import DocumentType
            
            doc_type = doc_data.get("type", "text")
            try:
                doc_type = DocumentType(doc_type)
            except ValueError:
                doc_type = DocumentType.TEXT
            
            return Document(
                id=document_id,
                content=content_data.get("text", ""),
                type=doc_type,
                metadata=doc_data.get("metadata", {})
            )
        except Exception as e:
            raise StorageError(f"Failed to get document from GCS: {str(e)}") from e
    
    async def get_chunk(self, chunk_id: str) -> Optional[TextChunk]:
        """
        Get a specific chunk by ID.
        
        Args:
            chunk_id: ID of the chunk to retrieve
            
        Returns:
            TextChunk object if found, None otherwise
            
        Raises:
            StorageError: If retrieval fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Get chunk data
            blob = self.bucket.blob(f"{chunk_id}.json")
            exists = await loop.run_in_executor(None, blob.exists)
            if not exists:
                return None
            
            chunk_data = json.loads(await loop.run_in_executor(None, blob.download_as_string))
            
            # Create TextChunk object
            return TextChunk(
                id=chunk_id,
                text=chunk_data.get("text", ""),
                document_id=chunk_data.get("metadata", {}).get("document_id", ""),
                metadata=chunk_data.get("metadata", {}),
                embedding=chunk_data.get("embedding")
            )
        except Exception as e:
            raise StorageError(f"Failed to get chunk from GCS: {str(e)}") from e
    
    async def get_chunks(
        self,
        chunk_ids: List[str]
    ) -> List[TextChunk]:
        """
        Get multiple chunks by their IDs.
        
        Args:
            chunk_ids: List of chunk IDs to retrieve
            
        Returns:
            List of TextChunk objects for the found chunks
            
        Raises:
            StorageError: If retrieval fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            tasks = []
            for chunk_id in chunk_ids:
                tasks.append(self.get_chunk(chunk_id))
            
            chunks = await asyncio.gather(*tasks)
            return [chunk for chunk in chunks if chunk is not None]
        except Exception as e:
            raise StorageError(f"Failed to get chunks from GCS: {str(e)}") from e
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filter: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> List[Tuple[TextChunk, float]]:
        """
        Search for similar texts using semantic similarity.
        
        Note: This implementation does not perform true vector similarity search
        as GCS does not support vector operations. It returns the most recent chunks.
        For production use, consider using a dedicated vector database.
        
        Args:
            query: Query text or embedding to search for
            k: Number of results to return
            filter: Optional metadata filters to apply
            embedding: Optional pre-computed query embedding
            
        Returns:
            List of tuples containing (TextChunk, similarity_score)
            
        Raises:
            StorageError: If search fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # List blobs (excluding document metadata)
            blobs = await loop.run_in_executor(
                None,
                lambda: list(self.storage_client.list_blobs(
                    self.bucket_name,
                    prefix="",
                    max_results=100  # Limit to avoid too many results
                ))
            )
            
            # Filter out document metadata blobs
            chunk_blobs = [blob for blob in blobs if not blob.name.startswith("docs/")]
            
            # Sort by last modified (most recent first)
            chunk_blobs.sort(key=lambda blob: blob.updated, reverse=True)
            
            # Limit to k results
            chunk_blobs = chunk_blobs[:k]
            
            # Get chunk data
            chunks = []
            for blob in chunk_blobs:
                chunk_id = blob.name.replace(".json", "")
                chunk = await self.get_chunk(chunk_id)
                if chunk:
                    # Apply filter if provided
                    if filter:
                        match = True
                        for key, value in filter.items():
                            if key not in chunk.metadata or chunk.metadata[key] != value:
                                match = False
                                break
                        if not match:
                            continue
                    
                    # Add to results with a dummy score
                    chunks.append((chunk, 0.9))
            
            return chunks
        except Exception as e:
            raise StorageError(f"Failed to perform similarity search in GCS: {str(e)}") from e
    
    async def keyword_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[TextChunk, float]]:
        """
        Search for texts using keyword matching.
        
        Note: This implementation does not perform true keyword search
        as GCS does not support text search. It returns the most recent chunks.
        For production use, consider using a dedicated vector database.
        
        Args:
            query: Query text to search for
            k: Number of results to return
            filter: Optional metadata filters to apply
            
        Returns:
            List of tuples containing (TextChunk, relevance_score)
            
        Raises:
            StorageError: If search fails
        """
        # For GCS, keyword search is the same as similarity search
        # since we don't have true search capabilities
        return await self.similarity_search(query, k, filter)
    
    async def delete(self, ids: List[str]) -> bool:
        """
        Delete texts from the vector store by IDs.
        
        Args:
            ids: List of IDs to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If deletion fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            tasks = []
            for id in ids:
                blob = self.bucket.blob(f"{id}.json")
                tasks.append(loop.run_in_executor(None, blob.delete))
            
            await asyncio.gather(*tasks)
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete chunks from GCS: {str(e)}") from e
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its chunks.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If deletion fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Delete document metadata
            doc_blob = self.bucket.blob(f"docs/{document_id}.json")
            await loop.run_in_executor(None, doc_blob.delete)
            
            # Delete document content
            content_blob = self.bucket.blob(f"{document_id}.json")
            await loop.run_in_executor(None, content_blob.delete)
            
            # Find and delete all chunks with this document_id
            blobs = await loop.run_in_executor(
                None,
                lambda: list(self.storage_client.list_blobs(self.bucket_name))
            )
            
            tasks = []
            for blob in blobs:
                if blob.name.endswith(".json") and not blob.name.startswith("docs/"):
                    try:
                        chunk_data = json.loads(await loop.run_in_executor(None, blob.download_as_string))
                        if chunk_data.get("metadata", {}).get("document_id") == document_id:
                            tasks.append(loop.run_in_executor(None, blob.delete))
                    except Exception:
                        # Skip if we can't read the chunk
                        pass
            
            await asyncio.gather(*tasks)
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete document from GCS: {str(e)}") from e
    
    async def update_metadata(
        self,
        id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for a specific text or document.
        
        Args:
            id: ID of the text or document
            metadata: New metadata to apply (will be merged with existing)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If update fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Check if it's a document
            doc_blob = self.bucket.blob(f"docs/{id}.json")
            doc_exists = await loop.run_in_executor(None, doc_blob.exists)
            
            if doc_exists:
                # Update document metadata
                doc_data = json.loads(await loop.run_in_executor(None, doc_blob.download_as_string))
                doc_data["metadata"] = {**doc_data.get("metadata", {}), **metadata}
                await loop.run_in_executor(
                    None,
                    lambda: doc_blob.upload_from_string(
                        json.dumps(doc_data),
                        content_type="application/json"
                    )
                )
            
            # Update chunk metadata
            chunk_blob = self.bucket.blob(f"{id}.json")
            chunk_exists = await loop.run_in_executor(None, chunk_blob.exists)
            
            if chunk_exists:
                chunk_data = json.loads(await loop.run_in_executor(None, chunk_blob.download_as_string))
                chunk_data["metadata"] = {**chunk_data.get("metadata", {}), **metadata}
                await loop.run_in_executor(
                    None,
                    lambda: chunk_blob.upload_from_string(
                        json.dumps(chunk_data),
                        content_type="application/json"
                    )
                )
            
            return doc_exists or chunk_exists
        except Exception as e:
            raise StorageError(f"Failed to update metadata in GCS: {str(e)}") from e
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics like document count, chunk count, etc.
            
        Raises:
            StorageError: If retrieving stats fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # List all blobs
            blobs = await loop.run_in_executor(
                None,
                lambda: list(self.storage_client.list_blobs(self.bucket_name))
            )
            
            # Count documents and chunks
            doc_count = sum(1 for blob in blobs if blob.name.startswith("docs/"))
            chunk_count = sum(1 for blob in blobs if not blob.name.startswith("docs/") and blob.name.endswith(".json"))
            
            # Calculate total size
            total_size = sum(blob.size for blob in blobs)
            
            return {
                "document_count": doc_count,
                "chunk_count": chunk_count,
                "total_size_bytes": total_size,
                "provider": "gcs",
                "bucket_name": self.bucket_name
            }
        except Exception as e:
            raise StorageError(f"Failed to get stats from GCS: {str(e)}") from e
    
    async def clear(self) -> bool:
        """
        Clear all data from the vector store.
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If clearing fails
        """
        if not self._initialized:
            raise StorageError("GCS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # List all blobs
            blobs = await loop.run_in_executor(
                None,
                lambda: list(self.storage_client.list_blobs(self.bucket_name))
            )
            
            # Delete all blobs
            tasks = []
            for blob in blobs:
                tasks.append(loop.run_in_executor(None, blob.delete))
            
            await asyncio.gather(*tasks)
            return True
        except Exception as e:
            raise StorageError(f"Failed to clear GCS vector store: {str(e)}") from e
    
    async def close(self) -> None:
        """
        Close the vector store connection and cleanup resources.
        
        Raises:
            StorageError: If closing fails
        """
        # GCS client doesn't need explicit closing
        self._initialized = False
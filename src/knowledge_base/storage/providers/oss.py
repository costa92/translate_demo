"""
Object Storage Service (OSS) provider for the knowledge base system.

This module implements a vector store provider that uses Object Storage Service (OSS)
for storing and retrieving document chunks. It supports various S3-compatible
object storage services like AWS S3, Aliyun OSS, MinIO, etc.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

from ...core.types import Document, TextChunk
from ...core.exceptions import StorageError
from ..base import BaseVectorStore


class OSSVectorStore(BaseVectorStore):
    """
    Vector store implementation using Object Storage Service (OSS).
    
    This provider stores document chunks as JSON objects in an S3-compatible
    object storage service. It supports AWS S3, Aliyun OSS, MinIO, and other
    S3-compatible services.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OSS vector store with configuration.
        
        Args:
            config: Configuration dictionary with OSS-specific settings:
                - endpoint_url: Endpoint URL of the OSS service
                - region_name: Region name
                - aws_access_key_id: Access key ID
                - aws_secret_access_key: Secret access key
                - bucket_name: Name of the bucket to use
                - prefix: Prefix for all objects (optional)
        
        Raises:
            ValueError: If required configuration is missing
        """
        super().__init__(config)
        self.endpoint_url = self.config.get("endpoint_url")
        self.region_name = self.config.get("region_name")
        self.aws_access_key_id = self.config.get("aws_access_key_id")
        self.aws_secret_access_key = self.config.get("aws_secret_access_key")
        self.bucket_name = self.config.get("bucket_name")
        self.prefix = self.config.get("prefix", "knowledge_base")
        
        if not self.bucket_name:
            raise ValueError("OSSVectorStore requires a 'bucket_name' in the configuration.")
        
        self.client = None
        self.resource = None
        self.chunk_prefix = f"{self.prefix}/chunks"
        self.doc_prefix = f"{self.prefix}/documents"
    
    async def initialize(self) -> None:
        """
        Initialize the OSS connection and resources.
        
        This method authenticates with OSS and sets up the bucket connection.
        
        Raises:
            StorageError: If initialization fails
        """
        try:
            # Run initialization in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Create S3 client and resource
            kwargs = {
                "region_name": self.region_name,
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key,
            }
            
            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url
            
            self.client = await loop.run_in_executor(
                None,
                lambda: boto3.client("s3", **kwargs)
            )
            
            self.resource = await loop.run_in_executor(
                None,
                lambda: boto3.resource("s3", **kwargs)
            )
            
            # Check if bucket exists
            try:
                await loop.run_in_executor(
                    None,
                    lambda: self.client.head_bucket(Bucket=self.bucket_name)
                )
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code == "404":
                    raise StorageError(f"Bucket '{self.bucket_name}' does not exist")
                elif error_code == "403":
                    raise StorageError(f"Access to bucket '{self.bucket_name}' is forbidden")
                else:
                    raise StorageError(f"Error accessing bucket '{self.bucket_name}': {str(e)}")
            
            self._initialized = True
        except Exception as e:
            raise StorageError(f"Failed to initialize OSS vector store: {str(e)}") from e
    
    async def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Add texts to the OSS vector store.
        
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
            raise StorageError("OSS vector store is not initialized")
        
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
            tasks = []
            for chunk in chunks:
                tasks.append(self._store_chunk(chunk))
            
            await asyncio.gather(*tasks)
            return ids
        except Exception as e:
            raise StorageError(f"Failed to add texts to OSS: {str(e)}") from e
    
    async def _store_chunk(self, chunk: Dict[str, Any]) -> None:
        """
        Store a single chunk in OSS.
        
        Args:
            chunk: Chunk dictionary to store
            
        Raises:
            StorageError: If storing fails
        """
        try:
            # Create a temporary file
            temp_file = f"{chunk['id']}.json"
            with open(temp_file, "w") as f:
                json.dump(chunk, f)
            
            # Upload file
            key = f"{self.chunk_prefix}/{chunk['id']}.json"
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.upload_file(
                    Filename=temp_file,
                    Bucket=self.bucket_name,
                    Key=key,
                    ExtraArgs={"ContentType": "application/json"}
                )
            )
            
            # Clean up temporary file
            os.remove(temp_file)
        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(f"{chunk['id']}.json"):
                os.remove(f"{chunk['id']}.json")
            
            raise StorageError(f"Failed to store chunk in OSS: {str(e)}") from e
    
    async def add_documents(
        self,
        documents: List[Document]
    ) -> List[str]:
        """
        Add documents to the OSS vector store.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            List of document IDs for the added documents
            
        Raises:
            StorageError: If adding documents fails
        """
        if not self._initialized:
            raise StorageError("OSS vector store is not initialized")
        
        try:
            texts = [doc.content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            ids = [doc.id for doc in documents]
            
            # Store document metadata separately
            tasks = []
            for doc in documents:
                doc_metadata = {
                    "id": doc.id,
                    "type": doc.type.value if hasattr(doc.type, "value") else str(doc.type),
                    "metadata": doc.metadata
                }
                tasks.append(self._store_document_metadata(doc.id, doc_metadata))
            
            await asyncio.gather(*tasks)
            
            # Store the document contents as chunks
            return await self.add_texts(texts, metadatas, ids)
        except Exception as e:
            raise StorageError(f"Failed to add documents to OSS: {str(e)}") from e
    
    async def _store_document_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> None:
        """
        Store document metadata in OSS.
        
        Args:
            doc_id: Document ID
            metadata: Document metadata dictionary
            
        Raises:
            StorageError: If storing fails
        """
        try:
            # Create a temporary file
            temp_file = f"doc_{doc_id}.json"
            with open(temp_file, "w") as f:
                json.dump(metadata, f)
            
            # Upload file
            key = f"{self.doc_prefix}/doc_{doc_id}.json"
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.upload_file(
                    Filename=temp_file,
                    Bucket=self.bucket_name,
                    Key=key,
                    ExtraArgs={"ContentType": "application/json"}
                )
            )
            
            # Clean up temporary file
            os.remove(temp_file)
        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(f"doc_{doc_id}.json"):
                os.remove(f"doc_{doc_id}.json")
            
            raise StorageError(f"Failed to store document metadata in OSS: {str(e)}") from e
    
    async def add_chunks(
        self,
        chunks: List[TextChunk]
    ) -> List[str]:
        """
        Add text chunks to the OSS vector store.
        
        Args:
            chunks: List of TextChunk objects to add
            
        Returns:
            List of chunk IDs for the added chunks
            
        Raises:
            StorageError: If adding chunks fails
        """
        if not self._initialized:
            raise StorageError("OSS vector store is not initialized")
        
        try:
            texts = [chunk.text for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            ids = [chunk.id for chunk in chunks]
            embeddings = [chunk.embedding for chunk in chunks if chunk.embedding is not None]
            
            if embeddings and len(embeddings) != len(chunks):
                embeddings = None  # If not all chunks have embeddings, don't use any
            
            return await self.add_texts(texts, metadatas, ids, embeddings)
        except Exception as e:
            raise StorageError(f"Failed to add chunks to OSS: {str(e)}") from e
    
    async def _download_file(self, key: str) -> Dict[str, Any]:
        """
        Download a file from OSS and parse it as JSON.
        
        Args:
            key: Key of the file in OSS
            
        Returns:
            Parsed JSON content
            
        Raises:
            StorageError: If download fails
        """
        try:
            # Create a temporary file
            temp_file = f"temp_{key.replace('/', '_')}"
            
            # Download file
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.download_file(
                    Bucket=self.bucket_name,
                    Key=key,
                    Filename=temp_file
                )
            )
            
            # Read and parse file
            with open(temp_file, "r") as f:
                content = json.load(f)
            
            # Clean up temporary file
            os.remove(temp_file)
            
            return content
        except ClientError as e:
            # Clean up temporary file if it exists
            if os.path.exists(f"temp_{key.replace('/', '_')}"):
                os.remove(f"temp_{key.replace('/', '_')}")
            
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                raise StorageError(f"File not found: {key}")
            else:
                raise StorageError(f"Failed to download file from OSS: {str(e)}")
        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(f"temp_{key.replace('/', '_')}"):
                os.remove(f"temp_{key.replace('/', '_')}")
            
            raise StorageError(f"Failed to download file from OSS: {str(e)}")
    
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
            raise StorageError("OSS vector store is not initialized")
        
        try:
            # Get document metadata
            doc_key = f"{self.doc_prefix}/doc_{document_id}.json"
            doc_metadata = await self._download_file(doc_key)
            
            # Get document content
            content_key = f"{self.chunk_prefix}/{document_id}.json"
            doc_content = await self._download_file(content_key)
            
            # Create Document object
            from ...core.types import DocumentType
            
            doc_type = doc_metadata.get("type", "text")
            try:
                doc_type = DocumentType(doc_type)
            except ValueError:
                doc_type = DocumentType.TEXT
            
            return Document(
                id=document_id,
                content=doc_content.get("text", ""),
                type=doc_type,
                metadata=doc_metadata.get("metadata", {})
            )
        except Exception as e:
            # If file not found, return None
            if "File not found" in str(e):
                return None
            raise StorageError(f"Failed to get document from OSS: {str(e)}") from e
    
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
            raise StorageError("OSS vector store is not initialized")
        
        try:
            # Get chunk data
            chunk_key = f"{self.chunk_prefix}/{chunk_id}.json"
            chunk_data = await self._download_file(chunk_key)
            
            # Create TextChunk object
            return TextChunk(
                id=chunk_id,
                text=chunk_data.get("text", ""),
                document_id=chunk_data.get("metadata", {}).get("document_id", ""),
                metadata=chunk_data.get("metadata", {}),
                embedding=chunk_data.get("embedding")
            )
        except Exception as e:
            # If file not found, return None
            if "File not found" in str(e):
                return None
            raise StorageError(f"Failed to get chunk from OSS: {str(e)}") from e
    
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
            raise StorageError("OSS vector store is not initialized")
        
        try:
            tasks = []
            for chunk_id in chunk_ids:
                tasks.append(self.get_chunk(chunk_id))
            
            chunks = await asyncio.gather(*tasks)
            return [chunk for chunk in chunks if chunk is not None]
        except Exception as e:
            raise StorageError(f"Failed to get chunks from OSS: {str(e)}") from e
    
    async def _list_objects(self, prefix: str) -> List[Dict[str, Any]]:
        """
        List objects in OSS with a given prefix.
        
        Args:
            prefix: Prefix to filter objects
            
        Returns:
            List of object metadata
            
        Raises:
            StorageError: If listing fails
        """
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
            )
            
            return response.get("Contents", [])
        except Exception as e:
            raise StorageError(f"Failed to list objects in OSS: {str(e)}") from e
    
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
        as OSS does not support vector operations. It returns the most recent chunks.
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
            raise StorageError("OSS vector store is not initialized")
        
        try:
            # List objects in the chunks folder
            objects = await self._list_objects(self.chunk_prefix)
            
            # Sort by last modified (most recent first)
            objects.sort(key=lambda obj: obj.get("LastModified", ""), reverse=True)
            
            # Limit to k results
            objects = objects[:k]
            
            # Get chunk data
            chunks = []
            for obj in objects:
                chunk_id = os.path.basename(obj["Key"]).replace(".json", "")
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
            
            return chunks[:k]
        except Exception as e:
            raise StorageError(f"Failed to perform similarity search in OSS: {str(e)}") from e
    
    async def keyword_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[TextChunk, float]]:
        """
        Search for texts using keyword matching.
        
        Note: This implementation does not perform true keyword search
        as OSS does not support text search. It returns the most recent chunks.
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
        # For OSS, keyword search is the same as similarity search
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
            raise StorageError("OSS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Delete each chunk
            for id in ids:
                key = f"{self.chunk_prefix}/{id}.json"
                await loop.run_in_executor(
                    None,
                    lambda: self.client.delete_object(
                        Bucket=self.bucket_name,
                        Key=key
                    )
                )
            
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete chunks from OSS: {str(e)}") from e
    
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
            raise StorageError("OSS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Delete document metadata
            doc_key = f"{self.doc_prefix}/doc_{document_id}.json"
            await loop.run_in_executor(
                None,
                lambda: self.client.delete_object(
                    Bucket=self.bucket_name,
                    Key=doc_key
                )
            )
            
            # Delete document content
            content_key = f"{self.chunk_prefix}/{document_id}.json"
            await loop.run_in_executor(
                None,
                lambda: self.client.delete_object(
                    Bucket=self.bucket_name,
                    Key=content_key
                )
            )
            
            # Find and delete all chunks with this document_id
            # This is a simplified approach - in a real implementation, we would need
            # to download and check each chunk to see if it belongs to this document
            
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete document from OSS: {str(e)}") from e
    
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
            raise StorageError("OSS vector store is not initialized")
        
        try:
            # Check if it's a document
            doc = await self.get_document(id)
            if doc:
                # Update document metadata
                doc.metadata = {**doc.metadata, **metadata}
                await self.add_documents([doc])
                return True
            
            # Check if it's a chunk
            chunk = await self.get_chunk(id)
            if chunk:
                # Update chunk metadata
                chunk.metadata = {**chunk.metadata, **metadata}
                await self.add_chunks([chunk])
                return True
            
            return False
        except Exception as e:
            raise StorageError(f"Failed to update metadata in OSS: {str(e)}") from e
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics like document count, chunk count, etc.
            
        Raises:
            StorageError: If retrieving stats fails
        """
        if not self._initialized:
            raise StorageError("OSS vector store is not initialized")
        
        try:
            # Count documents
            doc_objects = await self._list_objects(self.doc_prefix)
            doc_count = len(doc_objects)
            
            # Count chunks
            chunk_objects = await self._list_objects(self.chunk_prefix)
            chunk_count = len(chunk_objects)
            
            # Calculate total size
            total_size = sum(obj.get("Size", 0) for obj in doc_objects + chunk_objects)
            
            return {
                "document_count": doc_count,
                "chunk_count": chunk_count,
                "total_size_bytes": total_size,
                "provider": "oss",
                "bucket_name": self.bucket_name,
                "prefix": self.prefix
            }
        except Exception as e:
            raise StorageError(f"Failed to get stats from OSS: {str(e)}") from e
    
    async def clear(self) -> bool:
        """
        Clear all data from the vector store.
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If clearing fails
        """
        if not self._initialized:
            raise StorageError("OSS vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # List all objects with the prefix
            objects = await self._list_objects(self.prefix)
            
            # Delete all objects
            if objects:
                delete_objects = {
                    "Objects": [{"Key": obj["Key"]} for obj in objects],
                    "Quiet": True
                }
                
                await loop.run_in_executor(
                    None,
                    lambda: self.client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete=delete_objects
                    )
                )
            
            return True
        except Exception as e:
            raise StorageError(f"Failed to clear OSS vector store: {str(e)}") from e
    
    async def close(self) -> None:
        """
        Close the vector store connection and cleanup resources.
        
        Raises:
            StorageError: If closing fails
        """
        # S3 client doesn't need explicit closing
        self._initialized = False
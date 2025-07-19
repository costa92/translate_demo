"""
Pinecone vector store implementation for the unified knowledge base system.

This module provides a vector store implementation using Pinecone, a managed
vector database service optimized for vector search at scale.

Features:
- High-performance vector search
- Automatic scaling
- Metadata filtering
- Namespace support
- Cloud-based persistence
"""

import logging
import uuid
import json
from typing import List, Dict, Any, Optional, Tuple, Union, cast
from collections import defaultdict

from ...core.types import Document, TextChunk
from ...core.exceptions import (
    StorageError, 
    StorageConnectionError, 
    DocumentNotFoundError, 
    ChunkNotFoundError,
    MissingConfigurationError
)
from ..base import BaseVectorStore
from .utils import (
    generate_uuid,
    document_to_metadata,
    chunk_to_metadata,
    metadata_to_document,
    metadata_to_chunk
)

logger = logging.getLogger(__name__)

try:
    import pinecone
    from pinecone import Pinecone, Index
    PINECONE_AVAILABLE = True
except ImportError:
    logger.warning("Pinecone not installed. To use PineconeVectorStore, install with: pip install pinecone-client")
    PINECONE_AVAILABLE = False


class PineconeVectorStore(BaseVectorStore):
    """
    Pinecone-based vector store implementation.
    
    This class provides a vector store implementation using Pinecone, a managed
    vector database service optimized for vector search at scale.
    
    Required configuration:
    - api_key: Pinecone API key
    - index_name: Name of the Pinecone index to use
    
    Optional configuration:
    - environment: Pinecone environment (default: "us-west1-gcp")
    - namespace: Namespace within the index (default: "default")
    - dimension: Vector dimension (required when creating a new index)
    - metric: Distance metric to use (default: "cosine")
    - pod_type: Pod type for the index (default: "p1")
    - metadata_config: Metadata configuration for the index
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Pinecone vector store with configuration."""
        super().__init__(config)
        
        if not PINECONE_AVAILABLE:
            raise ImportError(
                "Pinecone is not installed. Please install it with: pip install pinecone-client"
            )
        
        # Extract configuration
        self.api_key = config.get("api_key")
        self.index_name = config.get("index_name")
        self.environment = config.get("environment", "us-west1-gcp")
        self.namespace = config.get("namespace", "default")
        self.dimension = config.get("dimension")
        self.metric = config.get("metric", "cosine")
        self.pod_type = config.get("pod_type", "p1")
        self.metadata_config = config.get("metadata_config")
        
        # Validate required configuration
        if not self.api_key:
            raise MissingConfigurationError("api_key")
        if not self.index_name:
            raise MissingConfigurationError("index_name")
        
        # Client and index will be initialized in initialize()
        self._client = None
        self._index = None
        
        # Document ID to chunk IDs mapping for efficient document deletion
        self._document_chunks: Dict[str, List[str]] = defaultdict(list)
        
        logger.info(f"PineconeVectorStore initialized with index: {self.index_name}")
    
    async def initialize(self) -> None:
        """Initialize Pinecone client and index."""
        if self._initialized:
            return
        
        try:
            # Initialize Pinecone client
            self._client = Pinecone(api_key=self.api_key, environment=self.environment)
            
            # Check if index exists
            index_list = self._client.list_indexes()
            index_exists = any(index.name == self.index_name for index in index_list.indexes)
            
            if not index_exists:
                if not self.dimension:
                    raise MissingConfigurationError("dimension (required when creating a new index)")
                
                # Create index
                self._client.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec={"pod_type": self.pod_type},
                    metadata_config=self.metadata_config
                )
                logger.info(f"Created Pinecone index: {self.index_name}")
            
            # Connect to index
            self._index = self._client.Index(self.index_name)
            
            # Load document to chunks mapping
            await self._load_document_chunks_mapping()
            
            self._initialized = True
            logger.info(f"PineconeVectorStore initialized successfully with index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize PineconeVectorStore: {e}")
            raise StorageConnectionError("pinecone", str(e))
    
    async def _load_document_chunks_mapping(self) -> None:
        """Load document to chunks mapping from the index."""
        try:
            # Query for chunks to build the document-chunks mapping
            # Since we can't fetch all vectors at once, we'll use a query with a filter
            # This is not efficient for large collections but works for initialization
            
            # We need to have a vector for the query, so we'll create a zero vector
            if not self.dimension:
                # Try to get dimension from index stats
                stats = self._index.describe_index_stats()
                self.dimension = stats.dimension
                if not self.dimension:
                    logger.warning("Could not determine vector dimension, skipping document-chunks mapping load")
                    return
            
            zero_vector = [0.0] * self.dimension
            
            # Query for chunks
            result = self._index.query(
                vector=zero_vector,
                top_k=10000,  # Use a large number to get as many as possible
                namespace=self.namespace,
                filter={"type": "chunk"},
                include_metadata=True
            )
            
            # Build document-chunks mapping
            self._document_chunks = defaultdict(list)
            for match in result.matches:
                chunk_id = match.id
                metadata = match.metadata
                document_id = metadata.get("document_id")
                if document_id:
                    self._document_chunks[document_id].append(chunk_id)
            
            logger.debug(f"Loaded document-chunks mapping for {len(self._document_chunks)} documents")
            
        except Exception as e:
            logger.warning(f"Failed to load document-chunks mapping: {e}")
    
    async def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Add texts to the vector store.
        
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
            await self.initialize()
        
        if not texts:
            return []
        
        # Generate IDs if not provided
        if ids is None:
            ids = [generate_uuid() for _ in texts]
        
        # Ensure metadatas list has correct length
        if metadatas is None:
            metadatas = [{} for _ in texts]
        elif len(metadatas) != len(texts):
            raise ValueError("metadatas length must match texts length")
        
        # Ensure embeddings are provided
        if embeddings is None:
            raise ValueError("embeddings must be provided for Pinecone")
        elif len(embeddings) != len(texts):
            raise ValueError("embeddings length must match texts length")
        
        try:
            # Prepare vectors for upsert
            vectors = []
            for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
                # Add text to metadata
                metadata_with_text = {**metadata, "text": text}
                
                # Process document_id in metadata for document-chunk mapping
                document_id = metadata.get("document_id")
                if document_id:
                    self._document_chunks[document_id].append(ids[i])
                
                vectors.append({
                    "id": ids[i],
                    "values": embedding,
                    "metadata": metadata_with_text
                })
            
            # Upsert vectors in batches (Pinecone has a limit on batch size)
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i+batch_size]
                self._index.upsert(vectors=batch, namespace=self.namespace)
            
            logger.info(f"Added {len(texts)} texts to Pinecone index")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add texts to Pinecone: {e}")
            raise StorageError(f"Failed to add texts: {e}", operation="add_texts", provider="pinecone")
    
    async def add_documents(
        self,
        documents: List[Document]
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            List of document IDs for the added documents
            
        Raises:
            StorageError: If adding documents fails
        """
        if not self._initialized:
            await self.initialize()
        
        if not documents:
            return []
        
        try:
            document_ids = []
            
            for document in documents:
                # Store document as a special entry with document metadata
                metadata = document_to_metadata(document)
                
                # Add text to metadata
                metadata["text"] = document.content
                
                # We need an embedding for the document
                # Since Pinecone requires embeddings, we'll use a placeholder
                # In a real implementation, you would compute an embedding for the document
                if not self.dimension:
                    # Try to get dimension from index stats
                    stats = self._index.describe_index_stats()
                    self.dimension = stats.dimension
                    if not self.dimension:
                        raise StorageError(
                            "Could not determine vector dimension for Pinecone index",
                            operation="add_documents",
                            provider="pinecone"
                        )
                
                placeholder_embedding = [0.0] * self.dimension
                
                # Add document to index
                self._index.upsert(
                    vectors=[{
                        "id": document.id,
                        "values": placeholder_embedding,
                        "metadata": metadata
                    }],
                    namespace=self.namespace
                )
                
                document_ids.append(document.id)
                
                # Initialize document-chunks mapping entry
                if document.id not in self._document_chunks:
                    self._document_chunks[document.id] = []
            
            logger.info(f"Added {len(documents)} documents to Pinecone index")
            return document_ids
            
        except Exception as e:
            logger.error(f"Failed to add documents to Pinecone: {e}")
            raise StorageError(f"Failed to add documents: {e}", operation="add_documents", provider="pinecone")
    
    async def add_chunks(
        self,
        chunks: List[TextChunk]
    ) -> List[str]:
        """
        Add text chunks to the vector store.
        
        Args:
            chunks: List of TextChunk objects to add
            
        Returns:
            List of chunk IDs for the added chunks
            
        Raises:
            StorageError: If adding chunks fails
        """
        if not self._initialized:
            await self.initialize()
        
        if not chunks:
            return []
        
        try:
            # Check if all chunks have embeddings
            missing_embeddings = [chunk for chunk in chunks if chunk.embedding is None]
            if missing_embeddings:
                raise ValueError(f"{len(missing_embeddings)} chunks are missing embeddings")
            
            # Prepare vectors for upsert
            vectors = []
            for chunk in chunks:
                # Prepare metadata
                metadata = chunk_to_metadata(chunk)
                
                # Add text to metadata
                metadata["text"] = chunk.text
                
                vectors.append({
                    "id": chunk.id,
                    "values": chunk.embedding,
                    "metadata": metadata
                })
                
                # Update document-chunks mapping
                if chunk.document_id:
                    self._document_chunks[chunk.document_id].append(chunk.id)
            
            # Upsert vectors in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i+batch_size]
                self._index.upsert(vectors=batch, namespace=self.namespace)
            
            logger.info(f"Added {len(chunks)} chunks to Pinecone index")
            return [chunk.id for chunk in chunks]
            
        except Exception as e:
            logger.error(f"Failed to add chunks to Pinecone: {e}")
            raise StorageError(f"Failed to add chunks: {e}", operation="add_chunks", provider="pinecone")
    
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
            await self.initialize()
        
        try:
            # Query for document by ID
            result = self._index.fetch(ids=[document_id], namespace=self.namespace)
            
            if document_id not in result.vectors:
                return None
            
            # Extract document data
            vector_data = result.vectors[document_id]
            metadata = vector_data.metadata
            
            # Check if this is a document entry
            if metadata.get("type") != "document":
                return None
            
            # Extract content
            content = metadata.get("text", "")
            
            # Create document object
            document = metadata_to_document(document_id, content, metadata)
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to get document from Pinecone: {e}")
            raise StorageError(f"Failed to get document: {e}", operation="get_document", provider="pinecone")
    
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
            await self.initialize()
        
        try:
            # Query for chunk by ID
            result = self._index.fetch(ids=[chunk_id], namespace=self.namespace)
            
            if chunk_id not in result.vectors:
                return None
            
            # Extract chunk data
            vector_data = result.vectors[chunk_id]
            metadata = vector_data.metadata
            embedding = vector_data.values
            
            # Check if this is a chunk entry
            if metadata.get("type") != "chunk":
                return None
            
            # Extract text
            text = metadata.get("text", "")
            
            # Create chunk object
            chunk = metadata_to_chunk(chunk_id, text, metadata, embedding)
            
            return chunk
            
        except Exception as e:
            logger.error(f"Failed to get chunk from Pinecone: {e}")
            raise StorageError(f"Failed to get chunk: {e}", operation="get_chunk", provider="pinecone")
    
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
            await self.initialize()
        
        if not chunk_ids:
            return []
        
        try:
            chunks = []
            
            # Fetch chunks in batches (Pinecone has a limit on batch size)
            batch_size = 100
            for i in range(0, len(chunk_ids), batch_size):
                batch_ids = chunk_ids[i:i+batch_size]
                result = self._index.fetch(ids=batch_ids, namespace=self.namespace)
                
                for chunk_id, vector_data in result.vectors.items():
                    metadata = vector_data.metadata
                    embedding = vector_data.values
                    
                    # Check if this is a chunk entry
                    if metadata.get("type") != "chunk":
                        continue
                    
                    # Extract text
                    text = metadata.get("text", "")
                    
                    # Create chunk object
                    chunk = metadata_to_chunk(chunk_id, text, metadata, embedding)
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks from Pinecone: {e}")
            raise StorageError(f"Failed to get chunks: {e}", operation="get_chunks", provider="pinecone")
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filter: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> List[Tuple[TextChunk, float]]:
        """
        Search for similar texts using semantic similarity.
        
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
            await self.initialize()
        
        if embedding is None:
            raise ValueError("embedding must be provided for Pinecone similarity search")
        
        try:
            # Prepare filter
            filter_dict = {"type": "chunk"}
            if filter:
                for key, value in filter.items():
                    filter_dict[key] = value
            
            # Perform query
            result = self._index.query(
                vector=embedding,
                top_k=k,
                namespace=self.namespace,
                filter=filter_dict,
                include_values=True,
                include_metadata=True
            )
            
            # Process results
            chunks_with_scores = []
            for match in result.matches:
                chunk_id = match.id
                score = match.score
                metadata = match.metadata
                embedding = match.values
                
                # Extract text
                text = metadata.get("text", "")
                
                # Create chunk object
                chunk = metadata_to_chunk(chunk_id, text, metadata, embedding)
                
                chunks_with_scores.append((chunk, score))
            
            return chunks_with_scores
            
        except Exception as e:
            logger.error(f"Failed to perform similarity search in Pinecone: {e}")
            raise StorageError(f"Failed to perform similarity search: {e}", operation="similarity_search", provider="pinecone")
    
    async def keyword_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[TextChunk, float]]:
        """
        Search for texts using keyword matching.
        
        Args:
            query: Query text to search for
            k: Number of results to return
            filter: Optional metadata filters to apply
            
        Returns:
            List of tuples containing (TextChunk, relevance_score)
            
        Raises:
            StorageError: If search fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Pinecone doesn't have native keyword search, so we'll use a workaround
            # We'll get all chunks that match the filter and then do a simple keyword matching
            
            # Prepare filter
            filter_dict = {"type": "chunk"}
            if filter:
                for key, value in filter.items():
                    filter_dict[key] = value
            
            # Get all chunks matching the filter
            # Since we can't fetch all vectors at once, we'll use a query with a placeholder vector
            # This is not efficient for large collections
            if not self.dimension:
                # Try to get dimension from index stats
                stats = self._index.describe_index_stats()
                self.dimension = stats.dimension
                if not self.dimension:
                    raise StorageError(
                        "Could not determine vector dimension for Pinecone index",
                        operation="keyword_search",
                        provider="pinecone"
                    )
            
            placeholder_vector = [0.0] * self.dimension
            result = self._index.query(
                vector=placeholder_vector,
                top_k=1000,  # Fetch a large number of results
                namespace=self.namespace,
                filter=filter_dict,
                include_values=True,
                include_metadata=True
            )
            
            # Perform simple keyword matching
            chunks_with_scores = []
            query_terms = query.lower().split()
            
            for match in result.matches:
                chunk_id = match.id
                metadata = match.metadata
                embedding = match.values
                
                # Extract text
                text = metadata.get("text", "")
                text_lower = text.lower()
                
                # Simple term frequency scoring
                score = sum(text_lower.count(term) for term in query_terms) / max(1, len(query_terms))
                
                # Only include results with at least one matching term
                if score > 0:
                    # Create chunk object
                    chunk = metadata_to_chunk(chunk_id, text, metadata, embedding)
                    
                    chunks_with_scores.append((chunk, score))
            
            # Sort by score (descending) and limit to k results
            chunks_with_scores.sort(key=lambda x: x[1], reverse=True)
            return chunks_with_scores[:k]
            
        except Exception as e:
            logger.error(f"Failed to perform keyword search in Pinecone: {e}")
            raise StorageError(f"Failed to perform keyword search: {e}", operation="keyword_search", provider="pinecone")
    
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
            await self.initialize()
        
        if not ids:
            return True
        
        try:
            # Delete entries from Pinecone
            self._index.delete(ids=ids, namespace=self.namespace)
            
            # Update document-chunks mapping
            for document_id, chunk_ids in list(self._document_chunks.items()):
                self._document_chunks[document_id] = [
                    chunk_id for chunk_id in chunk_ids if chunk_id not in ids
                ]
                if not self._document_chunks[document_id]:
                    del self._document_chunks[document_id]
            
            logger.info(f"Deleted {len(ids)} entries from Pinecone index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete entries from Pinecone: {e}")
            raise StorageError(f"Failed to delete entries: {e}", operation="delete", provider="pinecone")
    
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
            await self.initialize()
        
        try:
            # Get all chunk IDs for this document
            chunk_ids = self._document_chunks.get(document_id, [])
            
            # Add document ID itself to the list of IDs to delete
            ids_to_delete = chunk_ids + [document_id]
            
            if ids_to_delete:
                # Delete all entries
                self._index.delete(ids=ids_to_delete, namespace=self.namespace)
                
                # Remove from document-chunks mapping
                if document_id in self._document_chunks:
                    del self._document_chunks[document_id]
                
                logger.info(f"Deleted document {document_id} with {len(chunk_ids)} chunks from Pinecone index")
            else:
                logger.warning(f"Document {document_id} not found in Pinecone index")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document from Pinecone: {e}")
            raise StorageError(f"Failed to delete document: {e}", operation="delete_document", provider="pinecone")
    
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
            await self.initialize()
        
        try:
            # Get current entry
            result = self._index.fetch(ids=[id], namespace=self.namespace)
            
            if id not in result.vectors:
                logger.warning(f"Entry {id} not found in Pinecone index")
                return False
            
            # Extract current data
            vector_data = result.vectors[id]
            current_metadata = vector_data.metadata
            current_values = vector_data.values
            
            # Merge metadata
            updated_metadata = {**current_metadata, **metadata}
            
            # Update entry
            self._index.upsert(
                vectors=[{
                    "id": id,
                    "values": current_values,
                    "metadata": updated_metadata
                }],
                namespace=self.namespace
            )
            
            logger.info(f"Updated metadata for entry {id} in Pinecone index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metadata in Pinecone: {e}")
            raise StorageError(f"Failed to update metadata: {e}", operation="update_metadata", provider="pinecone")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics like document count, chunk count, etc.
            
        Raises:
            StorageError: If retrieving stats fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get index statistics
            stats = self._index.describe_index_stats()
            
            # Extract namespace statistics
            namespace_stats = stats.namespaces.get(self.namespace, {})
            vector_count = namespace_stats.vector_count if namespace_stats else 0
            
            return {
                "total_vectors": stats.total_vector_count,
                "namespace_vectors": vector_count,
                "dimension": stats.dimension,
                "index_name": self.index_name,
                "namespace": self.namespace,
                "document_count": len(self._document_chunks),
                "provider": "pinecone"
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats from Pinecone: {e}")
            raise StorageError(f"Failed to get stats: {e}", operation="get_stats", provider="pinecone")
    
    async def clear(self) -> bool:
        """
        Clear all data from the vector store.
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If clearing fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Delete all vectors in the namespace
            self._index.delete(delete_all=True, namespace=self.namespace)
            
            # Clear document-chunks mapping
            self._document_chunks.clear()
            
            logger.info(f"Cleared all data from Pinecone index {self.index_name} namespace {self.namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear Pinecone index: {e}")
            raise StorageError(f"Failed to clear index: {e}", operation="clear", provider="pinecone")
    
    async def close(self) -> None:
        """
        Close the vector store connection and cleanup resources.
        
        Raises:
            StorageError: If closing fails
        """
        try:
            # Pinecone doesn't have an explicit close method
            # Just reset our instance variables
            self._client = None
            self._index = None
            self._document_chunks.clear()
            self._initialized = False
            
            logger.info("Closed PineconeVectorStore connection")
            
        except Exception as e:
            logger.error(f"Error closing PineconeVectorStore: {e}")
            raise StorageError(f"Error closing PineconeVectorStore: {e}", operation="close", provider="pinecone")
"""
Weaviate vector store implementation for the unified knowledge base system.

This module provides a vector store implementation using Weaviate, an open-source
vector search engine with a GraphQL API.

Features:
- Semantic search with GraphQL
- Schema-based data modeling
- Cross-references between objects
- Automatic vectorization (optional)
- Cloud or self-hosted deployment
"""

import logging
import uuid
import json
from typing import List, Dict, Any, Optional, Tuple, Union, cast

from ...core.types import Document, TextChunk
from ...core.exceptions import (
    StorageError, 
    StorageConnectionError, 
    DocumentNotFoundError, 
    ChunkNotFoundError,
    MissingConfigurationError
)
from ..base import BaseVectorStore

logger = logging.getLogger(__name__)

try:
    import weaviate
    from weaviate.client import Client
    from weaviate.util import generate_uuid5
    WEAVIATE_AVAILABLE = True
except ImportError:
    logger.warning("Weaviate not installed. To use WeaviateVectorStore, install with: pip install weaviate-client")
    WEAVIATE_AVAILABLE = False


class WeaviateVectorStore(BaseVectorStore):
    """
    Weaviate-based vector store implementation.
    
    This class provides a vector store implementation using Weaviate, an open-source
    vector search engine with a GraphQL API.
    
    Required configuration:
    - url: Weaviate server URL
    
    Optional configuration:
    - api_key: API key for authentication
    - document_class: Class name for documents (default: "Document")
    - chunk_class: Class name for chunks (default: "Chunk")
    - batch_size: Batch size for operations (default: 100)
    - additional_headers: Additional headers for requests
    - timeout: Request timeout in seconds (default: 60)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Weaviate vector store with configuration."""
        super().__init__(config)
        
        if not WEAVIATE_AVAILABLE:
            raise ImportError(
                "Weaviate is not installed. Please install it with: pip install weaviate-client"
            )
        
        # Extract configuration
        self.url = config.get("url")
        self.api_key = config.get("api_key")
        self.document_class = config.get("document_class", "Document")
        self.chunk_class = config.get("chunk_class", "Chunk")
        self.batch_size = config.get("batch_size", 100)
        self.additional_headers = config.get("additional_headers")
        self.timeout = config.get("timeout", 60)
        
        # Validate required configuration
        if not self.url:
            raise MissingConfigurationError("url")
        
        # Client will be initialized in initialize()
        self._client = None
        
        # Document ID to chunk IDs mapping for efficient document deletion
        self._document_chunks: Dict[str, List[str]] = {}
        
        logger.info(f"WeaviateVectorStore initialized with URL: {self.url}")
    
    async def initialize(self) -> None:
        """Initialize Weaviate client and schema."""
        if self._initialized:
            return
        
        try:
            # Initialize authentication
            auth_config = None
            if self.api_key:
                auth_config = weaviate.auth.AuthApiKey(api_key=self.api_key)
            
            # Initialize client
            self._client = weaviate.Client(
                url=self.url,
                auth_client_secret=auth_config,
                additional_headers=self.additional_headers,
                timeout_config=(self.timeout, self.timeout)
            )
            
            # Check if Weaviate is ready
            if not self._client.is_ready():
                raise StorageConnectionError("weaviate", "Weaviate server is not ready")
            
            # Create schema if it doesn't exist
            await self._create_schema()
            
            # Load document to chunks mapping
            await self._load_document_chunks_mapping()
            
            self._initialized = True
            logger.info("WeaviateVectorStore initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WeaviateVectorStore: {e}")
            raise StorageConnectionError("weaviate", str(e))
    
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
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # Ensure metadatas list has correct length
        if metadatas is None:
            metadatas = [{} for _ in texts]
        elif len(metadatas) != len(texts):
            raise ValueError("metadatas length must match texts length")
        
        try:
            # Start a batch process
            with self._client.batch as batch:
                batch.batch_size = self.batch_size
                
                for i, (text, metadata) in enumerate(zip(texts, metadatas)):
                    # Prepare properties
                    properties = {
                        "content": text,
                        "type": "chunk",
                    }
                    
                    # Add metadata
                    for key, value in metadata.items():
                        if key not in properties and isinstance(value, (str, int, float, bool)):
                            properties[key] = value
                    
                    # Process document_id in metadata for document-chunk mapping
                    document_id = metadata.get("document_id")
                    if document_id:
                        properties["documentId"] = document_id
                        if document_id not in self._document_chunks:
                            self._document_chunks[document_id] = []
                        self._document_chunks[document_id].append(ids[i])
                    
                    # Add vector if provided
                    vector = embeddings[i] if embeddings and i < len(embeddings) else None
                    
                    # Add object to batch
                    batch.add_data_object(
                        data_object=properties,
                        class_name=self.chunk_class,
                        uuid=ids[i],
                        vector=vector
                    )
            
            logger.info(f"Added {len(texts)} texts to Weaviate")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add texts to Weaviate: {e}")
            raise StorageError(f"Failed to add texts: {e}", operation="add_texts", provider="weaviate")
    
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
            
            # Start a batch process
            with self._client.batch as batch:
                batch.batch_size = self.batch_size
                
                for document in documents:
                    # Prepare properties
                    properties = {
                        "content": document.content,
                        "type": "document",
                        "documentType": document.type.value if hasattr(document.type, "value") else str(document.type),
                        "source": document.source or "",
                        "createdAt": document.created_at.isoformat() if document.created_at else "",
                    }
                    
                    # Add metadata
                    if document.metadata:
                        for key, value in document.metadata.items():
                            if key not in properties and isinstance(value, (str, int, float, bool)):
                                properties[key] = value
                    
                    # Add object to batch
                    batch.add_data_object(
                        data_object=properties,
                        class_name=self.document_class,
                        uuid=document.id
                    )
                    
                    document_ids.append(document.id)
                    
                    # Initialize document-chunks mapping entry
                    if document.id not in self._document_chunks:
                        self._document_chunks[document.id] = []
            
            logger.info(f"Added {len(documents)} documents to Weaviate")
            return document_ids
            
        except Exception as e:
            logger.error(f"Failed to add documents to Weaviate: {e}")
            raise StorageError(f"Failed to add documents: {e}", operation="add_documents", provider="weaviate")
    
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
            # Start a batch process
            with self._client.batch as batch:
                batch.batch_size = self.batch_size
                
                for chunk in chunks:
                    # Prepare properties
                    properties = {
                        "content": chunk.text,
                        "type": "chunk",
                        "documentId": chunk.document_id,
                        "startIndex": chunk.start_index,
                        "endIndex": chunk.end_index,
                    }
                    
                    # Add metadata
                    if chunk.metadata:
                        for key, value in chunk.metadata.items():
                            if key not in properties and isinstance(value, (str, int, float, bool)):
                                properties[key] = value
                    
                    # Add object to batch
                    batch.add_data_object(
                        data_object=properties,
                        class_name=self.chunk_class,
                        uuid=chunk.id,
                        vector=chunk.embedding
                    )
                    
                    # Update document-chunks mapping
                    if chunk.document_id not in self._document_chunks:
                        self._document_chunks[chunk.document_id] = []
                    self._document_chunks[chunk.document_id].append(chunk.id)
            
            logger.info(f"Added {len(chunks)} chunks to Weaviate")
            return [chunk.id for chunk in chunks]
            
        except Exception as e:
            logger.error(f"Failed to add chunks to Weaviate: {e}")
            raise StorageError(f"Failed to add chunks: {e}", operation="add_chunks", provider="weaviate")
    
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
            result = self._client.data_object.get_by_id(
                document_id,
                class_name=self.document_class,
                with_vector=False
            )
            
            if not result:
                return None
            
            # Extract document data
            properties = result.get("properties", {})
            
            # Check if this is a document entry
            if properties.get("type") != "document":
                return None
            
            # Extract content
            content = properties.get("content", "")
            
            # Parse document type
            from ...core.types import DocumentType
            try:
                doc_type = DocumentType(properties.get("documentType", "text"))
            except ValueError:
                doc_type = DocumentType.TEXT
            
            # Parse created_at
            from datetime import datetime
            created_at = datetime.now()
            if "createdAt" in properties and properties["createdAt"]:
                try:
                    created_at = datetime.fromisoformat(properties["createdAt"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            # Create document object
            from ...core.types import Document
            document = Document(
                id=document_id,
                content=content,
                type=doc_type,
                source=properties.get("source"),
                metadata={k: v for k, v in properties.items() if k not in ["content", "type", "documentType", "source", "createdAt"]},
                created_at=created_at
            )
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to get document from Weaviate: {e}")
            raise StorageError(f"Failed to get document: {e}", operation="get_document", provider="weaviate")
    
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
            result = self._client.data_object.get_by_id(
                chunk_id,
                class_name=self.chunk_class,
                with_vector=True
            )
            
            if not result:
                return None
            
            # Extract chunk data
            properties = result.get("properties", {})
            vector = result.get("vector")
            
            # Check if this is a chunk entry
            if properties.get("type") != "chunk":
                return None
            
            # Extract text
            text = properties.get("content", "")
            
            # Create chunk object
            from ...core.types import TextChunk
            chunk = TextChunk(
                id=chunk_id,
                text=text,
                document_id=properties.get("documentId", "unknown"),
                metadata={k: v for k, v in properties.items() if k not in ["content", "type", "documentId", "startIndex", "endIndex"]},
                embedding=vector,
                start_index=properties.get("startIndex", 0),
                end_index=properties.get("endIndex", len(text))
            )
            
            return chunk
            
        except Exception as e:
            logger.error(f"Failed to get chunk from Weaviate: {e}")
            raise StorageError(f"Failed to get chunk: {e}", operation="get_chunk", provider="weaviate")
    
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
            
            # Get chunks one by one (Weaviate doesn't have a batch get by ID)
            for chunk_id in chunk_ids:
                chunk = await self.get_chunk(chunk_id)
                if chunk:
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks from Weaviate: {e}")
            raise StorageError(f"Failed to get chunks: {e}", operation="get_chunks", provider="weaviate")
    
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
        
        try:
            # Prepare filter
            where_filter = {
                "path": ["type"],
                "operator": "Equal",
                "valueString": "chunk"
            }
            
            if filter:
                additional_filters = []
                for key, value in filter.items():
                    if key == "document_id":
                        additional_filters.append({
                            "path": ["documentId"],
                            "operator": "Equal",
                            "valueString": value
                        })
                    elif isinstance(value, str):
                        additional_filters.append({
                            "path": [key],
                            "operator": "Equal",
                            "valueString": value
                        })
                    elif isinstance(value, (int, float)):
                        additional_filters.append({
                            "path": [key],
                            "operator": "Equal",
                            "valueNumber": value
                        })
                    elif isinstance(value, bool):
                        additional_filters.append({
                            "path": [key],
                            "operator": "Equal",
                            "valueBoolean": value
                        })
                
                if additional_filters:
                    where_filter = {
                        "operator": "And",
                        "operands": [where_filter] + additional_filters
                    }
            
            # Perform query
            if embedding:
                # Use vector search with provided embedding
                result = self._client.query.get(
                    self.chunk_class,
                    ["content", "documentId", "startIndex", "endIndex", "_additional {id vector}"]
                ).with_where(where_filter).with_near_vector({
                    "vector": embedding,
                    "certainty": 0.7
                }).with_limit(k).do()
            else:
                # Use text search
                result = self._client.query.get(
                    self.chunk_class,
                    ["content", "documentId", "startIndex", "endIndex", "_additional {id vector}"]
                ).with_where(where_filter).with_near_text({
                    "concepts": [query],
                    "certainty": 0.7
                }).with_limit(k).do()
            
            # Process results
            chunks_with_scores = []
            
            if result and "data" in result and "Get" in result["data"]:
                objects = result["data"]["Get"].get(self.chunk_class, [])
                
                for obj in objects:
                    chunk_id = obj["_additional"]["id"]
                    vector = obj["_additional"].get("vector")
                    content = obj.get("content", "")
                    document_id = obj.get("documentId", "unknown")
                    start_index = obj.get("startIndex", 0)
                    end_index = obj.get("endIndex", len(content))
                    
                    # Extract metadata
                    metadata = {k: v for k, v in obj.items() if k not in ["content", "documentId", "startIndex", "endIndex", "_additional"]}
                    
                    # Create chunk object
                    from ...core.types import TextChunk
                    chunk = TextChunk(
                        id=chunk_id,
                        text=content,
                        document_id=document_id,
                        metadata=metadata,
                        embedding=vector,
                        start_index=start_index,
                        end_index=end_index
                    )
                    
                    # Calculate score (Weaviate returns certainty, which is already between 0 and 1)
                    # If certainty is not available, use a default score of 1.0
                    score = obj["_additional"].get("certainty", 1.0)
                    
                    chunks_with_scores.append((chunk, score))
            
            return chunks_with_scores
            
        except Exception as e:
            logger.error(f"Failed to perform similarity search in Weaviate: {e}")
            raise StorageError(f"Failed to perform similarity search: {e}", operation="similarity_search", provider="weaviate")
    
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
            # Prepare filter
            where_filter = {
                "path": ["type"],
                "operator": "Equal",
                "valueString": "chunk"
            }
            
            if filter:
                additional_filters = []
                for key, value in filter.items():
                    if key == "document_id":
                        additional_filters.append({
                            "path": ["documentId"],
                            "operator": "Equal",
                            "valueString": value
                        })
                    elif isinstance(value, str):
                        additional_filters.append({
                            "path": [key],
                            "operator": "Equal",
                            "valueString": value
                        })
                    elif isinstance(value, (int, float)):
                        additional_filters.append({
                            "path": [key],
                            "operator": "Equal",
                            "valueNumber": value
                        })
                    elif isinstance(value, bool):
                        additional_filters.append({
                            "path": [key],
                            "operator": "Equal",
                            "valueBoolean": value
                        })
                
                if additional_filters:
                    where_filter = {
                        "operator": "And",
                        "operands": [where_filter] + additional_filters
                    }
            
            # Perform BM25 search (keyword search)
            result = self._client.query.get(
                self.chunk_class,
                ["content", "documentId", "startIndex", "endIndex", "_additional {id vector score}"]
            ).with_where(where_filter).with_bm25(
                query=query
            ).with_limit(k).do()
            
            # Process results
            chunks_with_scores = []
            
            if result and "data" in result and "Get" in result["data"]:
                objects = result["data"]["Get"].get(self.chunk_class, [])
                
                for obj in objects:
                    chunk_id = obj["_additional"]["id"]
                    vector = obj["_additional"].get("vector")
                    content = obj.get("content", "")
                    document_id = obj.get("documentId", "unknown")
                    start_index = obj.get("startIndex", 0)
                    end_index = obj.get("endIndex", len(content))
                    
                    # Extract metadata
                    metadata = {k: v for k, v in obj.items() if k not in ["content", "documentId", "startIndex", "endIndex", "_additional"]}
                    
                    # Create chunk object
                    from ...core.types import TextChunk
                    chunk = TextChunk(
                        id=chunk_id,
                        text=content,
                        document_id=document_id,
                        metadata=metadata,
                        embedding=vector,
                        start_index=start_index,
                        end_index=end_index
                    )
                    
                    # Get score and normalize it to [0, 1]
                    # BM25 scores can be any positive number, higher is better
                    # We'll normalize by dividing by the maximum score in the result set
                    score = obj["_additional"].get("score", 0.0)
                    
                    chunks_with_scores.append((chunk, score))
            
            # Normalize scores if we have results
            if chunks_with_scores:
                max_score = max(score for _, score in chunks_with_scores)
                if max_score > 0:
                    chunks_with_scores = [(chunk, score / max_score) for chunk, score in chunks_with_scores]
            
            return chunks_with_scores
            
        except Exception as e:
            logger.error(f"Failed to perform keyword search in Weaviate: {e}")
            raise StorageError(f"Failed to perform keyword search: {e}", operation="keyword_search", provider="weaviate")
    
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
            # Delete entries from Weaviate
            for id in ids:
                # Check if ID belongs to Document or Chunk class
                try:
                    self._client.data_object.delete(
                        id,
                        class_name=self.document_class
                    )
                except Exception:
                    try:
                        self._client.data_object.delete(
                            id,
                            class_name=self.chunk_class
                        )
                    except Exception:
                        logger.warning(f"Failed to delete object with ID {id}")
            
            # Update document-chunks mapping
            for document_id, chunk_ids in list(self._document_chunks.items()):
                self._document_chunks[document_id] = [
                    chunk_id for chunk_id in chunk_ids if chunk_id not in ids
                ]
                if not self._document_chunks[document_id]:
                    del self._document_chunks[document_id]
            
            logger.info(f"Deleted {len(ids)} entries from Weaviate")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete entries from Weaviate: {e}")
            raise StorageError(f"Failed to delete entries: {e}", operation="delete", provider="weaviate")
    
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
            
            # Delete document
            try:
                self._client.data_object.delete(
                    document_id,
                    class_name=self.document_class
                )
            except Exception as e:
                logger.warning(f"Failed to delete document {document_id}: {e}")
            
            # Delete chunks
            for chunk_id in chunk_ids:
                try:
                    self._client.data_object.delete(
                        chunk_id,
                        class_name=self.chunk_class
                    )
                except Exception as e:
                    logger.warning(f"Failed to delete chunk {chunk_id}: {e}")
            
            # Remove from document-chunks mapping
            if document_id in self._document_chunks:
                del self._document_chunks[document_id]
            
            logger.info(f"Deleted document {document_id} with {len(chunk_ids)} chunks from Weaviate")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document from Weaviate: {e}")
            raise StorageError(f"Failed to delete document: {e}", operation="delete_document", provider="weaviate")
    
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
            # Try to get the object from both classes
            obj = None
            class_name = None
            
            try:
                obj = self._client.data_object.get_by_id(id, class_name=self.document_class)
                class_name = self.document_class
            except Exception:
                try:
                    obj = self._client.data_object.get_by_id(id, class_name=self.chunk_class)
                    class_name = self.chunk_class
                except Exception:
                    logger.warning(f"Object with ID {id} not found in Weaviate")
                    return False
            
            if not obj or not class_name:
                return False
            
            # Get current properties
            properties = obj.get("properties", {})
            
            # Merge metadata
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    properties[key] = value
            
            # Update object
            self._client.data_object.update(
                properties,
                class_name=class_name,
                uuid=id
            )
            
            logger.info(f"Updated metadata for object {id} in Weaviate")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metadata in Weaviate: {e}")
            raise StorageError(f"Failed to update metadata: {e}", operation="update_metadata", provider="weaviate")
    
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
            # Get schema
            schema = self._client.schema.get()
            
            # Get class statistics
            document_class_info = None
            chunk_class_info = None
            
            for class_info in schema.get("classes", []):
                if class_info.get("class") == self.document_class:
                    document_class_info = class_info
                elif class_info.get("class") == self.chunk_class:
                    chunk_class_info = class_info
            
            # Count objects
            document_count = 0
            chunk_count = 0
            
            if document_class_info:
                document_count_result = self._client.query.aggregate(self.document_class).with_meta_count().do()
                if document_count_result and "data" in document_count_result and "Aggregate" in document_count_result["data"]:
                    document_count = document_count_result["data"]["Aggregate"][self.document_class][0]["meta"]["count"]
            
            if chunk_class_info:
                chunk_count_result = self._client.query.aggregate(self.chunk_class).with_meta_count().do()
                if chunk_count_result and "data" in chunk_count_result and "Aggregate" in chunk_count_result["data"]:
                    chunk_count = chunk_count_result["data"]["Aggregate"][self.chunk_class][0]["meta"]["count"]
            
            return {
                "document_count": document_count,
                "chunk_count": chunk_count,
                "document_class": self.document_class,
                "chunk_class": self.chunk_class,
                "url": self.url,
                "document_ids": list(self._document_chunks.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats from Weaviate: {e}")
            raise StorageError(f"Failed to get stats: {e}", operation="get_stats", provider="weaviate")
    
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
            # Delete all objects from both classes
            self._client.batch.delete_objects(
                class_name=self.document_class,
                where={
                    "operator": "NotEqual",
                    "path": ["id"],
                    "valueString": "dummy"  # This will match all objects
                }
            )
            
            self._client.batch.delete_objects(
                class_name=self.chunk_class,
                where={
                    "operator": "NotEqual",
                    "path": ["id"],
                    "valueString": "dummy"  # This will match all objects
                }
            )
            
            # Clear document-chunks mapping
            self._document_chunks.clear()
            
            logger.info(f"Cleared Weaviate classes {self.document_class} and {self.chunk_class}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear Weaviate: {e}")
            raise StorageError(f"Failed to clear Weaviate: {e}", operation="clear", provider="weaviate")
    
    async def close(self) -> None:
        """
        Close the vector store connection and cleanup resources.
        
        Raises:
            StorageError: If closing fails
        """
        if not self._initialized:
            return
        
        try:
            # Weaviate client doesn't have an explicit close method
            # But we can reset our state
            self._client = None
            self._initialized = False
            
            logger.info("WeaviateVectorStore closed")
            
        except Exception as e:
            logger.error(f"Error closing WeaviateVectorStore: {e}")
            raise StorageError(f"Error closing WeaviateVectorStore: {e}", operation="close", provider="weaviate")
    
    async def _create_schema(self) -> None:
        """Create schema for document and chunk classes if they don't exist."""
        try:
            # Get current schema
            schema = self._client.schema.get()
            existing_classes = [cls["class"] for cls in schema.get("classes", [])]
            
            # Create Document class if it doesn't exist
            if self.document_class not in existing_classes:
                document_class = {
                    "class": self.document_class,
                    "description": "Document class for knowledge base",
                    "vectorizer": "none",  # We'll provide vectors manually
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Document content"
                        },
                        {
                            "name": "type",
                            "dataType": ["string"],
                            "description": "Object type (document)"
                        },
                        {
                            "name": "documentType",
                            "dataType": ["string"],
                            "description": "Document type (text, pdf, etc.)"
                        },
                        {
                            "name": "source",
                            "dataType": ["string"],
                            "description": "Document source"
                        },
                        {
                            "name": "createdAt",
                            "dataType": ["string"],
                            "description": "Document creation timestamp"
                        }
                    ]
                }
                
                self._client.schema.create_class(document_class)
                logger.info(f"Created {self.document_class} class in Weaviate")
            
            # Create Chunk class if it doesn't exist
            if self.chunk_class not in existing_classes:
                chunk_class = {
                    "class": self.chunk_class,
                    "description": "Text chunk class for knowledge base",
                    "vectorizer": "none",  # We'll provide vectors manually
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Chunk content"
                        },
                        {
                            "name": "type",
                            "dataType": ["string"],
                            "description": "Object type (chunk)"
                        },
                        {
                            "name": "documentId",
                            "dataType": ["string"],
                            "description": "ID of the parent document"
                        },
                        {
                            "name": "startIndex",
                            "dataType": ["int"],
                            "description": "Start index in the original document"
                        },
                        {
                            "name": "endIndex",
                            "dataType": ["int"],
                            "description": "End index in the original document"
                        }
                    ]
                }
                
                self._client.schema.create_class(chunk_class)
                logger.info(f"Created {self.chunk_class} class in Weaviate")
            
        except Exception as e:
            logger.error(f"Failed to create schema in Weaviate: {e}")
            raise StorageError(f"Failed to create schema: {e}", operation="create_schema", provider="weaviate")
    
    async def _load_document_chunks_mapping(self) -> None:
        """Load document to chunks mapping from Weaviate."""
        try:
            # Query for all chunks
            result = self._client.query.get(
                self.chunk_class,
                ["documentId", "_additional {id}"]
            ).with_where({
                "path": ["type"],
                "operator": "Equal",
                "valueString": "chunk"
            }).with_limit(10000).do()  # Limit to 10000 chunks
            
            # Build document-chunks mapping
            self._document_chunks = {}
            
            if result and "data" in result and "Get" in result["data"]:
                objects = result["data"]["Get"].get(self.chunk_class, [])
                
                for obj in objects:
                    chunk_id = obj["_additional"]["id"]
                    document_id = obj.get("documentId")
                    if document_id:
                        if document_id not in self._document_chunks:
                            self._document_chunks[document_id] = []
                        self._document_chunks[document_id].append(chunk_id)
            
            logger.debug(f"Loaded document-chunks mapping with {len(self._document_chunks)} documents")
            
        except Exception as e:
            logger.warning(f"Failed to load document-chunks mapping: {e}")
            self._document_chunks = {}
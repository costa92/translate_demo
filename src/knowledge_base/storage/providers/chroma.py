"""
Chroma vector store implementation for the unified knowledge base system.

This module provides a vector store implementation using Chroma DB, an open-source
embedding database designed for AI applications.

Features:
- Efficient vector storage and retrieval
- Metadata filtering
- Collection-based organization
- Persistent storage
"""

import logging
import uuid
import os
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
    metadata_to_chunk,
    ensure_directory_exists
)

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.api import ClientAPI
    from chromadb.api.models.Collection import Collection
    CHROMA_AVAILABLE = True
except ImportError:
    logger.warning("ChromaDB not installed. To use ChromaVectorStore, install with: pip install chromadb")
    CHROMA_AVAILABLE = False


class ChromaVectorStore(BaseVectorStore):
    """
    ChromaDB-based vector store implementation.
    
    This class provides a vector store implementation using ChromaDB, an open-source
    embedding database designed for AI applications.
    
    Required configuration:
    - collection_name: Name of the ChromaDB collection to use
    
    Optional configuration:
    - persist_directory: Directory to persist ChromaDB data (if None, in-memory only)
    - chroma_server_host: Host for ChromaDB server (if None, use local instance)
    - chroma_server_port: Port for ChromaDB server
    - chroma_server_ssl: Whether to use SSL for ChromaDB server connection
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize ChromaDB vector store with configuration."""
        super().__init__(config)
        
        if not CHROMA_AVAILABLE:
            raise ImportError(
                "ChromaDB is not installed. Please install it with: pip install chromadb"
            )
        
        # Extract configuration
        self.collection_name = config.get("collection_name", "knowledge_base")
        self.persist_directory = config.get("persist_directory")
        self.chroma_server_host = config.get("chroma_server_host")
        self.chroma_server_port = config.get("chroma_server_port")
        self.chroma_server_ssl = config.get("chroma_server_ssl", False)
        
        # Client and collection will be initialized in initialize()
        self._client: Optional[ClientAPI] = None
        self._collection: Optional[Collection] = None
        
        # Document ID to chunk IDs mapping for efficient document deletion
        self._document_chunks: Dict[str, List[str]] = defaultdict(list)
        
        logger.info(f"ChromaVectorStore initialized with collection: {self.collection_name}")
    
    async def initialize(self) -> None:
        """Initialize ChromaDB client and collection."""
        if self._initialized:
            return
        
        try:
            # Initialize ChromaDB client
            if self.chroma_server_host:
                # Use HTTP client for remote ChromaDB server
                self._client = chromadb.HttpClient(
                    host=self.chroma_server_host,
                    port=self.chroma_server_port,
                    ssl=self.chroma_server_ssl
                )
                logger.info(f"Connected to ChromaDB server at {self.chroma_server_host}:{self.chroma_server_port}")
            else:
                # Use persistent or in-memory client
                settings = Settings()
                if self.persist_directory:
                    ensure_directory_exists(self.persist_directory)
                    settings = Settings(
                        persist_directory=self.persist_directory,
                        anonymized_telemetry=False
                    )
                    logger.info(f"Using persistent ChromaDB at {self.persist_directory}")
                else:
                    logger.info("Using in-memory ChromaDB")
                
                self._client = chromadb.Client(settings)
            
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Knowledge base collection"}
            )
            
            # Load document to chunks mapping
            await self._load_document_chunks_mapping()
            
            self._initialized = True
            logger.info(f"ChromaVectorStore initialized successfully with collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaVectorStore: {e}")
            raise StorageConnectionError("chroma", str(e))
    
    async def _load_document_chunks_mapping(self) -> None:
        """Load document to chunks mapping from the collection."""
        try:
            # Query for all chunks to build the document-chunks mapping
            result = self._collection.get(
                where={"type": "chunk"},
                include=["metadatas"]
            )
            
            # Build document-chunks mapping
            self._document_chunks = defaultdict(list)
            for i, chunk_id in enumerate(result["ids"]):
                metadata = result["metadatas"][i]
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
        
        # Process document_id in metadata for document-chunk mapping
        for i, metadata in enumerate(metadatas):
            document_id = metadata.get("document_id")
            if document_id:
                self._document_chunks[document_id].append(ids[i])
        
        try:
            # Add texts to ChromaDB collection
            self._collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            logger.info(f"Added {len(texts)} texts to ChromaDB collection")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add texts to ChromaDB: {e}")
            raise StorageError(f"Failed to add texts: {e}", operation="add_texts", provider="chroma")
    
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
            texts = []
            metadatas = []
            ids = []
            
            for document in documents:
                texts.append(document.content)
                metadatas.append(document_to_metadata(document))
                ids.append(document.id)
                
                # Initialize document-chunks mapping entry
                if document.id not in self._document_chunks:
                    self._document_chunks[document.id] = []
            
            # Add documents to collection
            self._collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to ChromaDB collection")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise StorageError(f"Failed to add documents: {e}", operation="add_documents", provider="chroma")
    
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
            texts = []
            metadatas = []
            ids = []
            embeddings = []
            
            for chunk in chunks:
                texts.append(chunk.text)
                metadatas.append(chunk_to_metadata(chunk))
                ids.append(chunk.id)
                
                # Add embedding if available
                if chunk.embedding:
                    embeddings.append(chunk.embedding)
                
                # Update document-chunks mapping
                if chunk.document_id:
                    self._document_chunks[chunk.document_id].append(chunk.id)
            
            # Add chunks to collection
            if embeddings and len(embeddings) == len(texts):
                self._collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                self._collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
            
            logger.info(f"Added {len(chunks)} chunks to ChromaDB collection")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add chunks to ChromaDB: {e}")
            raise StorageError(f"Failed to add chunks: {e}", operation="add_chunks", provider="chroma")
    
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
            result = self._collection.get(
                ids=[document_id],
                where={"type": "document"}
            )
            
            if not result["ids"]:
                return None
            
            # Extract document data
            content = result["documents"][0]
            metadata = result["metadatas"][0]
            
            # Create document object
            document = metadata_to_document(document_id, content, metadata)
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to get document from ChromaDB: {e}")
            raise StorageError(f"Failed to get document: {e}", operation="get_document", provider="chroma")
    
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
            result = self._collection.get(
                ids=[chunk_id],
                where={"type": "chunk"},
                include=["embeddings", "documents", "metadatas"]
            )
            
            if not result["ids"]:
                return None
            
            # Extract chunk data
            text = result["documents"][0]
            metadata = result["metadatas"][0]
            embedding = result["embeddings"][0] if result.get("embeddings") else None
            
            # Create chunk object
            chunk = metadata_to_chunk(chunk_id, text, metadata, embedding)
            
            return chunk
            
        except Exception as e:
            logger.error(f"Failed to get chunk from ChromaDB: {e}")
            raise StorageError(f"Failed to get chunk: {e}", operation="get_chunk", provider="chroma")
    
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
            # Query for chunks by IDs
            result = self._collection.get(
                ids=chunk_ids,
                where={"type": "chunk"},
                include=["embeddings", "documents", "metadatas"]
            )
            
            chunks = []
            for i, chunk_id in enumerate(result["ids"]):
                text = result["documents"][i]
                metadata = result["metadatas"][i]
                embedding = result["embeddings"][i] if result.get("embeddings") else None
                
                # Create chunk object
                chunk = metadata_to_chunk(chunk_id, text, metadata, embedding)
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks from ChromaDB: {e}")
            raise StorageError(f"Failed to get chunks: {e}", operation="get_chunks", provider="chroma")
    
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
            where_clause = {"type": "chunk"}
            if filter:
                for key, value in filter.items():
                    where_clause[key] = value
            
            # Perform query
            if embedding:
                result = self._collection.query(
                    query_embeddings=[embedding],
                    n_results=k,
                    where=where_clause,
                    include=["embeddings", "documents", "metadatas", "distances"]
                )
            else:
                result = self._collection.query(
                    query_texts=[query],
                    n_results=k,
                    where=where_clause,
                    include=["embeddings", "documents", "metadatas", "distances"]
                )
            
            # Process results
            chunks_with_scores = []
            for i, chunk_id in enumerate(result["ids"][0]):
                text = result["documents"][0][i]
                metadata = result["metadatas"][0][i]
                embedding = result["embeddings"][0][i] if result.get("embeddings") else None
                distance = result["distances"][0][i] if result.get("distances") else 0.0
                
                # Convert distance to similarity score (ChromaDB returns distances, lower is better)
                # Normalize to [0, 1] range where 1 is most similar
                similarity = 1.0 - min(1.0, max(0.0, distance))
                
                # Create chunk object
                chunk = metadata_to_chunk(chunk_id, text, metadata, embedding)
                
                chunks_with_scores.append((chunk, similarity))
            
            return chunks_with_scores
            
        except Exception as e:
            logger.error(f"Failed to perform similarity search in ChromaDB: {e}")
            raise StorageError(f"Failed to perform similarity search: {e}", operation="similarity_search", provider="chroma")
    
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
            # ChromaDB doesn't have native keyword search, so we'll use a workaround
            # We'll get all chunks that match the filter and then do a simple keyword matching
            
            # Prepare filter
            where_clause = {"type": "chunk"}
            if filter:
                for key, value in filter.items():
                    where_clause[key] = value
            
            # Get all chunks matching the filter
            result = self._collection.get(
                where=where_clause,
                include=["documents", "metadatas", "embeddings"]
            )
            
            # Perform simple keyword matching
            chunks_with_scores = []
            query_terms = query.lower().split()
            
            for i, chunk_id in enumerate(result["ids"]):
                text = result["documents"][i]
                metadata = result["metadatas"][i]
                embedding = result["embeddings"][i] if result.get("embeddings") else None
                
                # Simple term frequency scoring
                text_lower = text.lower()
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
            logger.error(f"Failed to perform keyword search in ChromaDB: {e}")
            raise StorageError(f"Failed to perform keyword search: {e}", operation="keyword_search", provider="chroma")
    
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
            # Delete entries from ChromaDB
            self._collection.delete(ids=ids)
            
            # Update document-chunks mapping
            for document_id, chunk_ids in list(self._document_chunks.items()):
                self._document_chunks[document_id] = [
                    chunk_id for chunk_id in chunk_ids if chunk_id not in ids
                ]
                if not self._document_chunks[document_id]:
                    del self._document_chunks[document_id]
            
            logger.info(f"Deleted {len(ids)} entries from ChromaDB collection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete entries from ChromaDB: {e}")
            raise StorageError(f"Failed to delete entries: {e}", operation="delete", provider="chroma")
    
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
                self._collection.delete(ids=ids_to_delete)
                
                # Remove from document-chunks mapping
                if document_id in self._document_chunks:
                    del self._document_chunks[document_id]
                
                logger.info(f"Deleted document {document_id} with {len(chunk_ids)} chunks from ChromaDB collection")
            else:
                logger.warning(f"Document {document_id} not found in ChromaDB collection")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document from ChromaDB: {e}")
            raise StorageError(f"Failed to delete document: {e}", operation="delete_document", provider="chroma")
    
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
            result = self._collection.get(
                ids=[id],
                include=["metadatas"]
            )
            
            if not result["ids"]:
                logger.warning(f"Entry {id} not found in ChromaDB collection")
                return False
            
            # Merge metadata
            current_metadata = result["metadatas"][0]
            updated_metadata = {**current_metadata, **metadata}
            
            # Update entry
            self._collection.update(
                ids=[id],
                metadatas=[updated_metadata]
            )
            
            logger.info(f"Updated metadata for entry {id} in ChromaDB collection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metadata in ChromaDB: {e}")
            raise StorageError(f"Failed to update metadata: {e}", operation="update_metadata", provider="chroma")
    
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
            # Get all entries
            result = self._collection.get(include=["metadatas"])
            
            # Count documents and chunks
            document_count = sum(1 for metadata in result["metadatas"] if metadata.get("type") == "document")
            chunk_count = sum(1 for metadata in result["metadatas"] if metadata.get("type") == "chunk")
            
            # Get collection info
            collection_info = self._collection.count()
            
            return {
                "total_entries": collection_info,
                "document_count": document_count,
                "chunk_count": chunk_count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory,
                "provider": "chroma"
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats from ChromaDB: {e}")
            raise StorageError(f"Failed to get stats: {e}", operation="get_stats", provider="chroma")
    
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
            # Get all IDs
            result = self._collection.get()
            ids = result["ids"]
            
            if ids:
                # Delete all entries
                self._collection.delete(ids=ids)
            
            # Clear document-chunks mapping
            self._document_chunks.clear()
            
            logger.info(f"Cleared all data from ChromaDB collection {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear ChromaDB collection: {e}")
            raise StorageError(f"Failed to clear collection: {e}", operation="clear", provider="chroma")
    
    async def close(self) -> None:
        """
        Close the vector store connection and cleanup resources.
        
        Raises:
            StorageError: If closing fails
        """
        try:
            # ChromaDB doesn't have an explicit close method
            # Just reset our instance variables
            self._client = None
            self._collection = None
            self._document_chunks.clear()
            self._initialized = False
            
            logger.info("Closed ChromaVectorStore connection")
            
        except Exception as e:
            logger.error(f"Error closing ChromaVectorStore: {e}")
            raise StorageError(f"Error closing ChromaVectorStore: {e}", operation="close", provider="chroma")
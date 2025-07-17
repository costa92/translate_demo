"""
Base storage interface for the knowledge base system.

This module defines the base interfaces for vector storage providers in the unified knowledge base system.
It provides abstract classes that all storage providers must implement to ensure consistent behavior.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, AsyncIterator
from contextlib import asynccontextmanager

from ..core.types import Document, TextChunk
from ..core.exceptions import StorageError


class BaseVectorStore(ABC):
    """
    Base abstract class for vector storage providers.
    
    This class defines the interface that all vector storage providers must implement.
    It provides methods for storing, retrieving, and searching vector embeddings and their
    associated text chunks.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the vector store with configuration.
        
        Args:
            config: Configuration dictionary for the vector store
        """
        self.config = config
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the vector store connection and resources.
        
        This method should be called before any other methods to set up
        necessary connections, create tables/collections if needed, and
        prepare the storage for operations.
        
        Raises:
            StorageError: If initialization fails
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics like document count, chunk count, etc.
            
        Raises:
            StorageError: If retrieving stats fails
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear all data from the vector store.
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If clearing fails
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the vector store connection and cleanup resources.
        
        This method should be called when the vector store is no longer needed
        to ensure proper cleanup of resources.
        
        Raises:
            StorageError: If closing fails
        """
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if the vector store is initialized."""
        return self._initialized
    
    @asynccontextmanager
    async def session(self):
        """
        Context manager for vector store sessions.
        
        This provides a convenient way to ensure proper initialization and cleanup:
        
        async with vector_store.session() as vs:
            await vs.add_texts(["text1", "text2"])
        
        Yields:
            The initialized vector store instance
            
        Raises:
            StorageError: If initialization or cleanup fails
        """
        if not self._initialized:
            await self.initialize()
        try:
            yield self
        finally:
            # Don't close the connection here, just end the session
            pass


class VectorStore:
    """
    Factory class for creating vector stores.
    
    This class provides methods for creating vector store instances based on
    configuration settings.
    """
    
    @staticmethod
    def create(config: Dict[str, Any]) -> BaseVectorStore:
        """
        Create a vector store based on configuration.
        
        Args:
            config: Configuration dictionary with storage settings
            
        Returns:
            Initialized BaseVectorStore instance
            
        Raises:
            ValueError: If the specified provider is unknown
        """
        provider = config.get("provider", "memory")
        
        if provider == "memory":
            from .providers.memory import MemoryVectorStore
            return MemoryVectorStore(config)
        elif provider == "notion":
            from .providers.notion import NotionVectorStore
            return NotionVectorStore(config)
        elif provider == "chroma":
            from .providers.chroma import ChromaVectorStore
            return ChromaVectorStore(config)
        elif provider == "pinecone":
            from .providers.pinecone import PineconeVectorStore
            return PineconeVectorStore(config)
        elif provider == "weaviate":
            from .providers.weaviate import WeaviateVectorStore
            return WeaviateVectorStore(config)
        else:
            raise ValueError(f"Unknown vector store provider: {provider}")
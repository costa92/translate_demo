"""Base classes for vector storage providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..core.types import Chunk, Vector, Metadata


class BaseVectorStore(ABC):
    """Abstract base class for vector storage providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the vector store with configuration."""
        self.config = config
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store connection and resources."""
        pass
    
    @abstractmethod
    async def add_chunks(self, chunks: List[Chunk]) -> bool:
        """
        Add chunks to the vector store.
        
        Args:
            chunks: List of chunks to add
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def search_similar(
        self, 
        query_vector: Vector, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector
            top_k: Number of results to return
            filters: Optional metadata filters
            min_score: Minimum similarity score
            
        Returns:
            List of search results with chunks and scores
        """
        pass
    
    @abstractmethod
    async def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """
        Get a specific chunk by ID.
        
        Args:
            chunk_id: Chunk identifier
            
        Returns:
            Chunk if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """
        Delete chunks by IDs.
        
        Args:
            chunk_ids: List of chunk IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks belonging to a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear all data from the vector store.
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the vector store connection and cleanup resources."""
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if the vector store is initialized."""
        return self._initialized
"""Vector store factory and main interface."""

import logging
from typing import List, Dict, Any, Optional

from ..core.config import StorageConfig
from ..core.exceptions import StorageError, ConfigurationError
from ..core.types import Chunk, Vector
from .base import BaseVectorStore
from .providers.memory import MemoryVectorStore

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector store factory and main interface.
    Provides a unified interface to different vector storage providers.
    """
    
    def __init__(self, config: StorageConfig):
        """Initialize vector store with configuration."""
        self.config = config
        self._provider: Optional[BaseVectorStore] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the vector store provider."""
        if self._initialized:
            return
        
        try:
            logger.info(f"Initializing vector store with provider: {self.config.provider}")
            
            # Create provider instance
            if self.config.provider == "memory":
                self._provider = MemoryVectorStore(self.config.__dict__)
            elif self.config.provider == "notion":
                from .providers.notion import NotionVectorStore
                self._provider = NotionVectorStore(self.config.__dict__)
            elif self.config.provider == "chroma":
                from .providers.chroma import ChromaVectorStore
                self._provider = ChromaVectorStore(self.config.__dict__)
            elif self.config.provider == "pinecone":
                from .providers.pinecone import PineconeVectorStore
                self._provider = PineconeVectorStore(self.config.__dict__)
            elif self.config.provider == "weaviate":
                from .providers.weaviate import WeaviateVectorStore
                self._provider = WeaviateVectorStore(self.config.__dict__)
            else:
                raise ConfigurationError(f"Unsupported vector store provider: {self.config.provider}")
            
            # Initialize the provider
            await self._provider.initialize()
            self._initialized = True
            
            logger.info(f"Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise StorageError(f"Vector store initialization failed: {e}")
    
    async def add_chunks(self, chunks: List[Chunk]) -> bool:
        """Add chunks to the vector store."""
        await self._ensure_initialized()
        
        if not chunks:
            return True
        
        try:
            logger.debug(f"Adding {len(chunks)} chunks to vector store")
            return await self._provider.add_chunks(chunks)
        except Exception as e:
            logger.error(f"Failed to add chunks: {e}")
            raise StorageError(f"Failed to add chunks: {e}", operation="add_chunks")
    
    async def search_similar(
        self, 
        query_vector: Vector, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        await self._ensure_initialized()
        
        try:
            logger.debug(f"Searching for {top_k} similar vectors")
            return await self._provider.search_similar(
                query_vector=query_vector,
                top_k=top_k,
                filters=filters,
                min_score=min_score
            )
        except Exception as e:
            logger.error(f"Failed to search similar vectors: {e}")
            raise StorageError(f"Failed to search similar vectors: {e}", operation="search_similar")
    
    async def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Get a specific chunk by ID."""
        await self._ensure_initialized()
        
        try:
            return await self._provider.get_chunk(chunk_id)
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id}: {e}")
            raise StorageError(f"Failed to get chunk: {e}", operation="get_chunk")
    
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """Delete chunks by IDs."""
        await self._ensure_initialized()
        
        if not chunk_ids:
            return True
        
        try:
            logger.debug(f"Deleting {len(chunk_ids)} chunks")
            return await self._provider.delete_chunks(chunk_ids)
        except Exception as e:
            logger.error(f"Failed to delete chunks: {e}")
            raise StorageError(f"Failed to delete chunks: {e}", operation="delete_chunks")
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks belonging to a document."""
        await self._ensure_initialized()
        
        try:
            logger.debug(f"Deleting document {document_id}")
            return await self._provider.delete_document(document_id)
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise StorageError(f"Failed to delete document: {e}", operation="delete_document")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        await self._ensure_initialized()
        
        try:
            stats = await self._provider.get_stats()
            stats["provider"] = self.config.provider
            stats["initialized"] = self._initialized
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "provider": self.config.provider,
                "initialized": self._initialized,
                "error": str(e)
            }
    
    async def clear(self) -> bool:
        """Clear all data from the vector store."""
        await self._ensure_initialized()
        
        try:
            logger.warning("Clearing all data from vector store")
            return await self._provider.clear()
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
            raise StorageError(f"Failed to clear vector store: {e}", operation="clear")
    
    async def close(self) -> None:
        """Close the vector store connection."""
        if self._provider:
            try:
                await self._provider.close()
                logger.info("Vector store closed")
            except Exception as e:
                logger.error(f"Error closing vector store: {e}")
        
        self._initialized = False
        self._provider = None
    
    async def _ensure_initialized(self) -> None:
        """Ensure the vector store is initialized."""
        if not self._initialized:
            await self.initialize()
    
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self.config.provider
    
    @property
    def is_initialized(self) -> bool:
        """Check if the vector store is initialized."""
        return self._initialized
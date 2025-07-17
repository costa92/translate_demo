"""In-memory vector store implementation."""

import asyncio
import logging
import math
from typing import List, Dict, Any, Optional
from collections import defaultdict

from ...core.types import Chunk, Vector
from ..base import BaseVectorStore

logger = logging.getLogger(__name__)


class MemoryVectorStore(BaseVectorStore):
    """
    In-memory vector store implementation.
    Suitable for development, testing, and small datasets.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize memory vector store."""
        super().__init__(config)
        
        # Storage
        self._chunks: Dict[str, Chunk] = {}
        self._vectors: Dict[str, Vector] = {}
        self._document_chunks: Dict[str, List[str]] = defaultdict(list)
        
        # Configuration
        self._max_chunks = config.get("max_chunks", 100000)
        
        logger.info(f"MemoryVectorStore initialized with max_chunks={self._max_chunks}")
    
    async def initialize(self) -> None:
        """Initialize the memory vector store."""
        if self._initialized:
            return
        
        logger.info("Initializing MemoryVectorStore")
        self._initialized = True
        logger.info("MemoryVectorStore initialized successfully")
    
    async def add_chunks(self, chunks: List[Chunk]) -> bool:
        """Add chunks to memory storage."""
        if not chunks:
            return True
        
        try:
            # Check capacity
            if len(self._chunks) + len(chunks) > self._max_chunks:
                logger.warning(f"Adding {len(chunks)} chunks would exceed max capacity {self._max_chunks}")
                return False
            
            for chunk in chunks:
                if not chunk.embedding:
                    logger.warning(f"Chunk {chunk.id} has no embedding, skipping")
                    continue
                
                # Store chunk and vector
                self._chunks[chunk.id] = chunk
                self._vectors[chunk.id] = chunk.embedding
                
                # Index by document
                self._document_chunks[chunk.document_id].append(chunk.id)
            
            logger.debug(f"Added {len(chunks)} chunks to memory store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add chunks to memory store: {e}")
            return False
    
    async def search_similar(
        self, 
        query_vector: Vector, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors using cosine similarity."""
        if not query_vector or not self._vectors:
            return []
        
        try:
            # Calculate similarities
            similarities = []
            
            for chunk_id, vector in self._vectors.items():
                chunk = self._chunks[chunk_id]
                
                # Apply filters
                if filters and not self._matches_filters(chunk, filters):
                    continue
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_vector, vector)
                
                if similarity >= min_score:
                    similarities.append({
                        "chunk": chunk,
                        "score": similarity,
                        "chunk_id": chunk_id
                    })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x["score"], reverse=True)
            results = similarities[:top_k]
            
            logger.debug(f"Found {len(results)} similar chunks out of {len(self._vectors)} total")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar vectors: {e}")
            return []
    
    async def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Get a specific chunk by ID."""
        return self._chunks.get(chunk_id)
    
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """Delete chunks by IDs."""
        try:
            deleted_count = 0
            
            for chunk_id in chunk_ids:
                if chunk_id in self._chunks:
                    chunk = self._chunks[chunk_id]
                    
                    # Remove from storage
                    del self._chunks[chunk_id]
                    del self._vectors[chunk_id]
                    
                    # Remove from document index
                    if chunk.document_id in self._document_chunks:
                        self._document_chunks[chunk.document_id].remove(chunk_id)
                        if not self._document_chunks[chunk.document_id]:
                            del self._document_chunks[chunk.document_id]
                    
                    deleted_count += 1
            
            logger.debug(f"Deleted {deleted_count} chunks from memory store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete chunks: {e}")
            return False
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks belonging to a document."""
        if document_id not in self._document_chunks:
            return True
        
        try:
            chunk_ids = self._document_chunks[document_id].copy()
            return await self.delete_chunks(chunk_ids)
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics."""
        return {
            "total_chunks": len(self._chunks),
            "total_documents": len(self._document_chunks),
            "max_chunks": self._max_chunks,
            "memory_usage_mb": self._estimate_memory_usage(),
            "avg_chunks_per_document": (
                len(self._chunks) / len(self._document_chunks) 
                if self._document_chunks else 0
            )
        }
    
    async def clear(self) -> bool:
        """Clear all data from memory store."""
        try:
            self._chunks.clear()
            self._vectors.clear()
            self._document_chunks.clear()
            
            logger.info("Memory store cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear memory store: {e}")
            return False
    
    async def close(self) -> None:
        """Close memory store (cleanup)."""
        await self.clear()
        self._initialized = False
        logger.info("MemoryVectorStore closed")
    
    def _cosine_similarity(self, vec1: Vector, vec2: Vector) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        try:
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            
            # Calculate magnitudes
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(b * b for b in vec2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = dot_product / (magnitude1 * magnitude2)
            
            # Ensure result is in [0, 1] range
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _matches_filters(self, chunk: Chunk, filters: Dict[str, Any]) -> bool:
        """Check if chunk matches the given filters."""
        try:
            for key, value in filters.items():
                if key == "document_id":
                    if chunk.document_id != value:
                        return False
                elif key in chunk.metadata:
                    if chunk.metadata[key] != value:
                        return False
                else:
                    # Filter key not found in chunk metadata
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return False
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB."""
        try:
            # Rough estimation
            chunk_size = sum(len(chunk.text.encode('utf-8')) for chunk in self._chunks.values())
            vector_size = sum(len(vector) * 8 for vector in self._vectors.values())  # 8 bytes per float
            metadata_size = sum(len(str(chunk.metadata).encode('utf-8')) for chunk in self._chunks.values())
            
            total_bytes = chunk_size + vector_size + metadata_size
            return total_bytes / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            logger.error(f"Error estimating memory usage: {e}")
            return 0.0
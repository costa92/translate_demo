"""
In-memory vector store implementation.

This module provides an in-memory vector store implementation for the unified knowledge base system.
It is suitable for development, testing, and small datasets.
"""

import asyncio
import logging
import math
import json
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import numpy as np

from ...core.types import Chunk, Vector
from ...core.exceptions import StorageError, ChunkNotFoundError
from ..base import BaseVectorStore

logger = logging.getLogger(__name__)


class MemoryVectorStore(BaseVectorStore):
    """
    In-memory vector store implementation.
    
    This class provides an in-memory implementation of the vector store interface.
    It is suitable for development, testing, and small datasets.
    
    Features:
    - Fast in-memory storage and retrieval
    - Vector similarity search using cosine similarity
    - Metadata filtering
    - Document-based organization
    - Optional persistence to disk
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize memory vector store with configuration."""
        super().__init__(config)
        
        # Storage structures
        self._chunks: Dict[str, Chunk] = {}
        self._vectors: Dict[str, Vector] = {}
        self._document_chunks: Dict[str, List[str]] = defaultdict(list)
        self._metadata_index: Dict[str, Dict[Any, List[str]]] = defaultdict(lambda: defaultdict(list))
        
        # Configuration
        self._max_chunks = config.get("max_chunks", 100000)
        self._persistence_enabled = config.get("persistence_enabled", False)
        self._persistence_path = config.get("persistence_path", "./kb_storage")
        self._auto_save = config.get("auto_save", False)
        self._auto_save_interval = config.get("auto_save_interval", 300)  # 5 minutes
        self._last_save_time = time.time()
        
        # Indexing configuration
        self._use_numpy = config.get("use_numpy", True)
        
        logger.info(f"MemoryVectorStore initialized with max_chunks={self._max_chunks}, "
                   f"persistence_enabled={self._persistence_enabled}")
    
    async def initialize(self) -> None:
        """Initialize the memory vector store."""
        if self._initialized:
            return
        
        logger.info("Initializing MemoryVectorStore")
        
        # Load data from disk if persistence is enabled
        if self._persistence_enabled:
            await self._load_from_disk()
            
            # Set up auto-save task if enabled
            if self._auto_save:
                # Note: In a real application, we would need to manage this task properly
                # This is a simplified implementation for demonstration purposes
                logger.info(f"Auto-save enabled with interval of {self._auto_save_interval} seconds")
        
        self._initialized = True
        logger.info("MemoryVectorStore initialized successfully")
    
    async def add_chunks(self, chunks: List[Chunk]) -> bool:
        """
        Add chunks to memory storage.
        
        Args:
            chunks: List of chunks to add
            
        Returns:
            True if successful, False otherwise
        """
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
                
                # Index by metadata
                for key, value in chunk.metadata.items():
                    if value is not None:  # Only index non-None values
                        self._metadata_index[key][value].append(chunk.id)
            
            # Auto-save if enabled and interval has passed
            if self._persistence_enabled and self._auto_save:
                current_time = time.time()
                if current_time - self._last_save_time > self._auto_save_interval:
                    await self._save_to_disk()
                    self._last_save_time = current_time
            
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
        """
        Search for similar vectors using cosine similarity.
        
        Args:
            query_vector: Query vector
            top_k: Number of results to return
            filters: Optional metadata filters
            min_score: Minimum similarity score
            
        Returns:
            List of search results with chunks and scores
        """
        if not query_vector or not self._vectors:
            return []
        
        try:
            # Apply filters first if provided to reduce computation
            candidate_ids = self._apply_filters(filters) if filters else list(self._vectors.keys())
            
            if not candidate_ids:
                logger.debug("No chunks match the provided filters")
                return []
            
            # Calculate similarities
            similarities = []
            
            # Use numpy for faster computation if enabled and available
            if self._use_numpy and len(candidate_ids) > 100:
                try:
                    similarities = self._batch_cosine_similarity(query_vector, candidate_ids)
                except ImportError:
                    logger.warning("NumPy not available, falling back to standard similarity calculation")
                    similarities = self._calculate_similarities(query_vector, candidate_ids, min_score)
            else:
                similarities = self._calculate_similarities(query_vector, candidate_ids, min_score)
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x["score"], reverse=True)
            results = similarities[:top_k]
            
            logger.debug(f"Found {len(results)} similar chunks out of {len(candidate_ids)} candidates")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar vectors: {e}")
            return []
    
    async def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """
        Get a specific chunk by ID.
        
        Args:
            chunk_id: Chunk identifier
            
        Returns:
            Chunk if found, None otherwise
        """
        chunk = self._chunks.get(chunk_id)
        if not chunk:
            logger.debug(f"Chunk not found: {chunk_id}")
        return chunk
    
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """
        Delete chunks by IDs.
        
        Args:
            chunk_ids: List of chunk IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not chunk_ids:
            return True
            
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
                    
                    # Remove from metadata index
                    for key, value in chunk.metadata.items():
                        if value is not None and key in self._metadata_index and value in self._metadata_index[key]:
                            self._metadata_index[key][value].remove(chunk_id)
                            if not self._metadata_index[key][value]:
                                del self._metadata_index[key][value]
                            if not self._metadata_index[key]:
                                del self._metadata_index[key]
                    
                    deleted_count += 1
            
            # Auto-save if enabled and chunks were deleted
            if self._persistence_enabled and self._auto_save and deleted_count > 0:
                current_time = time.time()
                if current_time - self._last_save_time > self._auto_save_interval:
                    await self._save_to_disk()
                    self._last_save_time = current_time
            
            logger.debug(f"Deleted {deleted_count} chunks from memory store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete chunks: {e}")
            return False
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks belonging to a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successful, False otherwise
        """
        if document_id not in self._document_chunks:
            logger.debug(f"Document not found: {document_id}")
            return True
        
        try:
            chunk_ids = self._document_chunks[document_id].copy()
            return await self.delete_chunks(chunk_ids)
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get memory store statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            document_count = len(self._document_chunks)
            chunk_count = len(self._chunks)
            
            return {
                "total_chunks": chunk_count,
                "total_documents": document_count,
                "max_chunks": self._max_chunks,
                "memory_usage_mb": self._estimate_memory_usage(),
                "avg_chunks_per_document": (
                    chunk_count / document_count if document_count > 0 else 0
                ),
                "persistence_enabled": self._persistence_enabled,
                "auto_save_enabled": self._auto_save if self._persistence_enabled else False,
                "metadata_keys": list(self._metadata_index.keys())
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "error": str(e),
                "total_chunks": len(self._chunks),
                "total_documents": len(self._document_chunks)
            }
    
    async def clear(self) -> bool:
        """
        Clear all data from memory store.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._chunks.clear()
            self._vectors.clear()
            self._document_chunks.clear()
            self._metadata_index.clear()
            
            # Delete persistence files if enabled
            if self._persistence_enabled:
                await self._delete_persistence_files()
            
            logger.info("Memory store cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear memory store: {e}")
            return False
    
    async def close(self) -> None:
        """Close memory store and save data if persistence is enabled."""
        try:
            # Save data if persistence is enabled
            if self._persistence_enabled:
                await self._save_to_disk()
            
            # Clear in-memory data
            self._chunks.clear()
            self._vectors.clear()
            self._document_chunks.clear()
            self._metadata_index.clear()
            
            self._initialized = False
            logger.info("MemoryVectorStore closed")
            
        except Exception as e:
            logger.error(f"Error closing memory store: {e}")
    
    async def save(self) -> bool:
        """
        Manually save data to disk if persistence is enabled.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._persistence_enabled:
            logger.warning("Persistence is not enabled, cannot save")
            return False
        
        try:
            await self._save_to_disk()
            return True
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return False
    
    async def load(self) -> bool:
        """
        Manually load data from disk if persistence is enabled.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._persistence_enabled:
            logger.warning("Persistence is not enabled, cannot load")
            return False
        
        try:
            await self._load_from_disk()
            return True
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False
    
    def _cosine_similarity(self, vec1: Vector, vec2: Vector) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score between 0 and 1
        """
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
    
    def _batch_cosine_similarity(self, query_vector: Vector, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Calculate cosine similarity for multiple vectors using NumPy for better performance.
        
        Args:
            query_vector: Query vector
            chunk_ids: List of chunk IDs to compare against
            
        Returns:
            List of dictionaries with chunk and score
        """
        try:
            import numpy as np
            
            # Convert query vector to numpy array
            query_array = np.array(query_vector, dtype=np.float32)
            query_norm = np.linalg.norm(query_array)
            
            if query_norm == 0:
                return []
            
            # Normalize query vector
            query_array = query_array / query_norm
            
            results = []
            
            # Process in batches to avoid memory issues with very large datasets
            batch_size = 1000
            for i in range(0, len(chunk_ids), batch_size):
                batch_ids = chunk_ids[i:i+batch_size]
                
                # Create matrix of vectors
                vectors = np.array([self._vectors[chunk_id] for chunk_id in batch_ids], dtype=np.float32)
                
                # Calculate norms
                norms = np.linalg.norm(vectors, axis=1)
                
                # Avoid division by zero
                valid_indices = norms > 0
                if not np.any(valid_indices):
                    continue
                
                # Normalize vectors
                vectors[valid_indices] = vectors[valid_indices] / norms[valid_indices].reshape(-1, 1)
                
                # Calculate dot products (cosine similarities for normalized vectors)
                similarities = np.dot(vectors, query_array)
                
                # Create result objects
                for j, chunk_id in enumerate(batch_ids):
                    if valid_indices[j]:
                        chunk = self._chunks[chunk_id]
                        score = float(similarities[j])
                        
                        if score > 0:  # Only include positive similarities
                            results.append({
                                "chunk": chunk,
                                "score": score,
                                "chunk_id": chunk_id
                            })
            
            return results
            
        except ImportError:
            # Fall back to standard method if NumPy is not available
            logger.warning("NumPy not available, falling back to standard similarity calculation")
            return self._calculate_similarities(query_vector, chunk_ids, 0.0)
    
    def _calculate_similarities(self, query_vector: Vector, chunk_ids: List[str], min_score: float) -> List[Dict[str, Any]]:
        """
        Calculate similarities using standard Python.
        
        Args:
            query_vector: Query vector
            chunk_ids: List of chunk IDs to compare against
            min_score: Minimum similarity score
            
        Returns:
            List of dictionaries with chunk and score
        """
        similarities = []
        
        for chunk_id in chunk_ids:
            vector = self._vectors[chunk_id]
            similarity = self._cosine_similarity(query_vector, vector)
            
            if similarity >= min_score:
                similarities.append({
                    "chunk": self._chunks[chunk_id],
                    "score": similarity,
                    "chunk_id": chunk_id
                })
        
        return similarities
    
    def _apply_filters(self, filters: Dict[str, Any]) -> List[str]:
        """
        Apply metadata filters to find matching chunk IDs.
        
        Args:
            filters: Dictionary of metadata filters
            
        Returns:
            List of chunk IDs that match the filters
        """
        if not filters:
            return list(self._chunks.keys())
        
        # Start with all chunks
        result_set = set(self._chunks.keys())
        
        for key, value in filters.items():
            if key == "document_id":
                # Filter by document ID
                doc_chunks = set(self._document_chunks.get(value, []))
                result_set &= doc_chunks
            elif key in self._metadata_index and value in self._metadata_index[key]:
                # Use metadata index for efficient filtering
                key_value_chunks = set(self._metadata_index[key][value])
                result_set &= key_value_chunks
            else:
                # If the key or value doesn't exist in the index, no chunks will match
                return []
            
            # Early termination if no chunks match
            if not result_set:
                return []
        
        return list(result_set)
    
    def _estimate_memory_usage(self) -> float:
        """
        Estimate memory usage in MB.
        
        Returns:
            Estimated memory usage in MB
        """
        try:
            # Rough estimation
            chunk_size = sum(len(chunk.text.encode('utf-8')) for chunk in self._chunks.values())
            vector_size = sum(len(vector) * 8 for vector in self._vectors.values())  # 8 bytes per float
            metadata_size = sum(len(str(chunk.metadata).encode('utf-8')) for chunk in self._chunks.values())
            
            # Add index sizes
            document_index_size = sum(len(doc_id.encode('utf-8')) + len(chunk_ids) * 24 
                                     for doc_id, chunk_ids in self._document_chunks.items())
            
            metadata_index_size = 0
            for key, value_dict in self._metadata_index.items():
                key_size = len(key.encode('utf-8'))
                for value, chunk_ids in value_dict.items():
                    value_size = len(str(value).encode('utf-8'))
                    metadata_index_size += key_size + value_size + len(chunk_ids) * 24
            
            total_bytes = chunk_size + vector_size + metadata_size + document_index_size + metadata_index_size
            return total_bytes / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            logger.error(f"Error estimating memory usage: {e}")
            return 0.0
    
    async def _save_to_disk(self) -> None:
        """Save data to disk."""
        if not self._persistence_enabled:
            return
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(self._persistence_path, exist_ok=True)
            
            # Save chunks
            chunks_path = os.path.join(self._persistence_path, "chunks.json")
            with open(chunks_path, 'w', encoding='utf-8') as f:
                # Convert chunks to serializable format
                serializable_chunks = {}
                for chunk_id, chunk in self._chunks.items():
                    serializable_chunks[chunk_id] = {
                        "id": chunk.id,
                        "document_id": chunk.document_id,
                        "text": chunk.text,
                        "metadata": chunk.metadata,
                        "start_index": chunk.start_index,
                        "end_index": chunk.end_index
                    }
                json.dump(serializable_chunks, f)
            
            # Save vectors
            vectors_path = os.path.join(self._persistence_path, "vectors.json")
            with open(vectors_path, 'w', encoding='utf-8') as f:
                json.dump(self._vectors, f)
            
            # Save document chunks index
            doc_chunks_path = os.path.join(self._persistence_path, "document_chunks.json")
            with open(doc_chunks_path, 'w', encoding='utf-8') as f:
                # Convert defaultdict to regular dict for serialization
                json.dump({k: v for k, v in self._document_chunks.items()}, f)
            
            # Save metadata index
            metadata_path = os.path.join(self._persistence_path, "metadata_index.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                # Convert nested defaultdict to regular dict for serialization
                serializable_index = {}
                for key, value_dict in self._metadata_index.items():
                    serializable_index[key] = {str(k): v for k, v in value_dict.items()}
                json.dump(serializable_index, f)
            
            # Save timestamp
            timestamp_path = os.path.join(self._persistence_path, "timestamp.txt")
            with open(timestamp_path, 'w') as f:
                f.write(str(time.time()))
            
            logger.info(f"Saved memory store data to {self._persistence_path}")
            self._last_save_time = time.time()
            
        except Exception as e:
            logger.error(f"Failed to save data to disk: {e}")
            raise StorageError(f"Failed to save data to disk: {e}")
    
    async def _load_from_disk(self) -> None:
        """Load data from disk."""
        if not self._persistence_enabled:
            return
        
        try:
            # Check if persistence directory exists
            if not os.path.exists(self._persistence_path):
                logger.info(f"Persistence directory {self._persistence_path} does not exist, skipping load")
                return
            
            # Check if all required files exist
            required_files = ["chunks.json", "vectors.json", "document_chunks.json", "metadata_index.json"]
            if not all(os.path.exists(os.path.join(self._persistence_path, f)) for f in required_files):
                logger.warning("Some persistence files are missing, skipping load")
                return
            
            # Load chunks
            chunks_path = os.path.join(self._persistence_path, "chunks.json")
            with open(chunks_path, 'r', encoding='utf-8') as f:
                serialized_chunks = json.load(f)
                
                # Convert to Chunk objects
                from ...core.types import Chunk
                self._chunks = {}
                for chunk_id, chunk_data in serialized_chunks.items():
                    self._chunks[chunk_id] = Chunk(
                        id=chunk_data["id"],
                        document_id=chunk_data["document_id"],
                        text=chunk_data["text"],
                        metadata=chunk_data["metadata"],
                        start_index=chunk_data["start_index"],
                        end_index=chunk_data["end_index"]
                    )
            
            # Load vectors
            vectors_path = os.path.join(self._persistence_path, "vectors.json")
            with open(vectors_path, 'r', encoding='utf-8') as f:
                self._vectors = json.load(f)
                
                # Update chunk embeddings
                for chunk_id, vector in self._vectors.items():
                    if chunk_id in self._chunks:
                        self._chunks[chunk_id].embedding = vector
            
            # Load document chunks index
            doc_chunks_path = os.path.join(self._persistence_path, "document_chunks.json")
            with open(doc_chunks_path, 'r', encoding='utf-8') as f:
                # Convert to defaultdict
                doc_chunks_dict = json.load(f)
                self._document_chunks = defaultdict(list)
                for doc_id, chunk_ids in doc_chunks_dict.items():
                    self._document_chunks[doc_id] = chunk_ids
            
            # Load metadata index
            metadata_path = os.path.join(self._persistence_path, "metadata_index.json")
            with open(metadata_path, 'r', encoding='utf-8') as f:
                # Convert to nested defaultdict
                metadata_dict = json.load(f)
                self._metadata_index = defaultdict(lambda: defaultdict(list))
                for key, value_dict in metadata_dict.items():
                    for value_str, chunk_ids in value_dict.items():
                        # Try to convert string values back to their original types
                        try:
                            # Try as number
                            if value_str.isdigit():
                                value = int(value_str)
                            elif value_str.replace('.', '', 1).isdigit() and value_str.count('.') <= 1:
                                value = float(value_str)
                            # Try as boolean
                            elif value_str.lower() in ('true', 'false'):
                                value = value_str.lower() == 'true'
                            else:
                                value = value_str
                        except:
                            value = value_str
                            
                        self._metadata_index[key][value] = chunk_ids
            
            logger.info(f"Loaded memory store data from {self._persistence_path}")
            
        except Exception as e:
            logger.error(f"Failed to load data from disk: {e}")
            raise StorageError(f"Failed to load data from disk: {e}")
    
    async def _delete_persistence_files(self) -> None:
        """Delete persistence files."""
        if not self._persistence_enabled:
            return
        
        try:
            # Check if persistence directory exists
            if not os.path.exists(self._persistence_path):
                return
            
            # Delete all files in the directory
            for filename in os.listdir(self._persistence_path):
                file_path = os.path.join(self._persistence_path, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            
            logger.info(f"Deleted persistence files from {self._persistence_path}")
            
        except Exception as e:
            logger.error(f"Failed to delete persistence files: {e}")
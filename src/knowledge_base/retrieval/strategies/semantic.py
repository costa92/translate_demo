"""
Semantic retrieval strategy implementation.

This module provides a retrieval strategy based on semantic similarity search.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

from ...core.config import Config
from ...core.types import TextChunk
from ...core.exceptions import RetrievalError
from ...storage.base import BaseVectorStore
from ..retriever import RetrievalStrategy

logger = logging.getLogger(__name__)


class SemanticStrategy(RetrievalStrategy):
    """Retrieval strategy based on semantic similarity search."""
    
    def __init__(self, config: Config):
        """Initialize the semantic retrieval strategy.
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
    
    async def retrieve(
        self,
        vector_store: BaseVectorStore,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Tuple[TextChunk, float]]:
        """Retrieve relevant chunks using semantic similarity search.
        
        Args:
            vector_store: Vector store to search in
            query: Query text
            k: Number of results to return
            filter: Optional metadata filters to apply
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            List of tuples containing (TextChunk, similarity_score)
            
        Raises:
            RetrievalError: If retrieval fails
        """
        try:
            # Use the vector store's similarity search
            results = await vector_store.similarity_search(
                query=query,
                k=k,
                filter=filter,
                embedding=kwargs.get("embedding")
            )
            
            logger.debug(f"Semantic search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            raise RetrievalError(f"Semantic retrieval failed: {e}")
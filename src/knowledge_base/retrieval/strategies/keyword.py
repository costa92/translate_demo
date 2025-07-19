"""
Keyword retrieval strategy implementation.

This module provides a retrieval strategy based on keyword matching.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

from ...core.config import Config
from ...core.types import TextChunk
from ...core.exceptions import RetrievalError
from ...storage.base import BaseVectorStore
from ..retriever import RetrievalStrategy

logger = logging.getLogger(__name__)


class KeywordStrategy(RetrievalStrategy):
    """Retrieval strategy based on keyword matching."""
    
    def __init__(self, config: Config):
        """Initialize the keyword retrieval strategy.
        
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
        """Retrieve relevant chunks using keyword matching.
        
        Args:
            vector_store: Vector store to search in
            query: Query text
            k: Number of results to return
            filter: Optional metadata filters to apply
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            List of tuples containing (TextChunk, relevance_score)
            
        Raises:
            RetrievalError: If retrieval fails
        """
        try:
            # Use the vector store's keyword search
            results = await vector_store.keyword_search(
                query=query,
                k=k,
                filter=filter
            )
            
            logger.debug(f"Keyword search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            raise RetrievalError(f"Keyword retrieval failed: {e}")
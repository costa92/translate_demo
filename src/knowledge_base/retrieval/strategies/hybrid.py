"""
Hybrid retrieval strategy implementation.

This module provides a retrieval strategy that combines semantic similarity and keyword matching.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
import logging
from collections import defaultdict

from ...core.config import Config
from ...core.types import TextChunk
from ...core.exceptions import RetrievalError
from ...storage.base import BaseVectorStore
from ..retriever import RetrievalStrategy
from .semantic import SemanticStrategy
from .keyword import KeywordStrategy

logger = logging.getLogger(__name__)


class HybridStrategy(RetrievalStrategy):
    """Retrieval strategy that combines semantic similarity and keyword matching."""
    
    def __init__(self, config: Config):
        """Initialize the hybrid retrieval strategy.
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        self.semantic_strategy = SemanticStrategy(config)
        self.keyword_strategy = KeywordStrategy(config)
        self.semantic_weight = config.retrieval.semantic_weight
        self.keyword_weight = config.retrieval.keyword_weight
    
    async def retrieve(
        self,
        vector_store: BaseVectorStore,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Tuple[TextChunk, float]]:
        """Retrieve relevant chunks using a combination of semantic and keyword search.
        
        Args:
            vector_store: Vector store to search in
            query: Query text
            k: Number of results to return
            filter: Optional metadata filters to apply
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            List of tuples containing (TextChunk, combined_score)
            
        Raises:
            RetrievalError: If retrieval fails
        """
        try:
            # Retrieve more results than needed from each strategy to ensure diversity
            expanded_k = min(k * 2, 100)  # Limit to avoid excessive retrieval
            
            # Get results from both strategies
            semantic_results = await self.semantic_strategy.retrieve(
                vector_store, query, expanded_k, filter, **kwargs
            )
            
            keyword_results = await self.keyword_strategy.retrieve(
                vector_store, query, expanded_k, filter, **kwargs
            )
            
            # Combine and score results
            combined_results = self._combine_results(
                semantic_results, keyword_results, k
            )
            
            logger.debug(f"Hybrid search for '{query}' returned {len(combined_results)} results")
            return combined_results
            
        except Exception as e:
            raise RetrievalError(f"Hybrid retrieval failed: {e}")
    
    def _combine_results(
        self,
        semantic_results: List[Tuple[TextChunk, float]],
        keyword_results: List[Tuple[TextChunk, float]],
        k: int
    ) -> List[Tuple[TextChunk, float]]:
        """Combine and score results from semantic and keyword searches.
        
        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            k: Number of results to return
            
        Returns:
            List of tuples containing (TextChunk, combined_score)
        """
        # Create a mapping of chunk ID to chunk and scores
        combined_scores = defaultdict(lambda: {"chunk": None, "semantic": 0.0, "keyword": 0.0})
        
        # Process semantic results
        for chunk, score in semantic_results:
            combined_scores[chunk.id]["chunk"] = chunk
            combined_scores[chunk.id]["semantic"] = score
        
        # Process keyword results
        for chunk, score in keyword_results:
            combined_scores[chunk.id]["chunk"] = chunk
            combined_scores[chunk.id]["keyword"] = score
        
        # Calculate combined scores
        scored_results = []
        for chunk_id, data in combined_scores.items():
            combined_score = (
                self.semantic_weight * data["semantic"] +
                self.keyword_weight * data["keyword"]
            )
            scored_results.append((data["chunk"], combined_score))
        
        # Sort by combined score and take top k
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:k]
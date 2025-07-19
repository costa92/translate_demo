"""
Reranking system for the unified knowledge base.

This module provides functionality to rerank retrieval results based on various strategies
to improve the relevance of the results.
"""

from typing import List, Dict, Any, Optional, Tuple, Type, Union, Callable
import logging
from abc import ABC, abstractmethod
import re
from collections import Counter

from ..core.config import Config
from ..core.types import TextChunk
from ..core.exceptions import RetrievalError

logger = logging.getLogger(__name__)


class RerankerStrategy(ABC):
    """Base abstract class for reranking strategies."""
    
    def __init__(self, config: Config):
        """Initialize the reranking strategy with configuration.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    @abstractmethod
    def rerank(
        self,
        query: str,
        results: List[Tuple[TextChunk, float]],
        **kwargs
    ) -> List[Tuple[TextChunk, float]]:
        """Rerank the retrieval results.
        
        Args:
            query: Original query text
            results: List of (TextChunk, score) tuples from the retriever
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            Reranked list of (TextChunk, score) tuples
        """
        pass


class ExactMatchReranker(RerankerStrategy):
    """Reranking strategy that boosts results containing exact query terms."""
    
    def __init__(self, config: Config):
        """Initialize the exact match reranker.
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        self.boost_factor = 0.2  # Score boost for exact matches
    
    def rerank(
        self,
        query: str,
        results: List[Tuple[TextChunk, float]],
        **kwargs
    ) -> List[Tuple[TextChunk, float]]:
        """Rerank results by boosting those with exact query term matches.
        
        Args:
            query: Original query text
            results: List of (TextChunk, score) tuples from the retriever
            **kwargs: Additional parameters including:
                - boost_factor: Score boost for exact matches (default: 0.2)
            
        Returns:
            Reranked list of (TextChunk, score) tuples
        """
        if not results:
            return []
        
        # Get boost factor from kwargs or use default
        boost_factor = kwargs.get("boost_factor", self.boost_factor)
        
        # Tokenize the query into terms
        query_terms = set(re.findall(r'\b\w+\b', query.lower()))
        
        # Skip reranking for very short queries
        if len(query_terms) <= 1:
            return results
        
        reranked_results = []
        for chunk, score in results:
            # Count exact matches in the chunk text
            chunk_text = chunk.text.lower()
            matches = sum(1 for term in query_terms if term in chunk_text)
            
            # Calculate match ratio (matches / total terms)
            match_ratio = matches / len(query_terms)
            
            # Apply boost based on match ratio
            new_score = score + (match_ratio * boost_factor)
            
            # Ensure score doesn't exceed 1.0
            new_score = min(new_score, 1.0)
            
            reranked_results.append((chunk, new_score))
        
        # Sort by new scores
        reranked_results.sort(key=lambda x: x[1], reverse=True)
        
        return reranked_results


class LengthNormalizedReranker(RerankerStrategy):
    """Reranking strategy that normalizes scores based on chunk length."""
    
    def __init__(self, config: Config):
        """Initialize the length normalized reranker.
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        self.length_penalty = 0.1  # Penalty factor for length normalization
    
    def rerank(
        self,
        query: str,
        results: List[Tuple[TextChunk, float]],
        **kwargs
    ) -> List[Tuple[TextChunk, float]]:
        """Rerank results by normalizing scores based on chunk length.
        
        Args:
            query: Original query text
            results: List of (TextChunk, score) tuples from the retriever
            **kwargs: Additional parameters including:
                - length_penalty: Penalty factor for length normalization (default: 0.1)
            
        Returns:
            Reranked list of (TextChunk, score) tuples
        """
        if not results:
            return []
        
        # Get length penalty from kwargs or use default
        length_penalty = kwargs.get("length_penalty", self.length_penalty)
        
        # Find average chunk length
        avg_length = sum(len(chunk.text) for chunk, _ in results) / len(results)
        
        reranked_results = []
        for chunk, score in results:
            # Calculate length ratio compared to average
            length_ratio = len(chunk.text) / avg_length
            
            # Apply length normalization
            # - Shorter chunks get a boost
            # - Longer chunks get a penalty
            length_factor = 1.0
            if length_ratio < 1.0:
                # Shorter chunks get a small boost
                length_factor = 1.0 + (length_penalty * (1.0 - length_ratio))
            else:
                # Longer chunks get a penalty
                length_factor = 1.0 - (length_penalty * (length_ratio - 1.0))
                length_factor = max(length_factor, 0.5)  # Limit the penalty
            
            new_score = score * length_factor
            
            reranked_results.append((chunk, new_score))
        
        # Sort by new scores
        reranked_results.sort(key=lambda x: x[1], reverse=True)
        
        return reranked_results


class MetadataBoostReranker(RerankerStrategy):
    """Reranking strategy that boosts results based on metadata fields."""
    
    def __init__(self, config: Config):
        """Initialize the metadata boost reranker.
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        self.boost_fields = {}  # Default empty, should be provided in kwargs
    
    def rerank(
        self,
        query: str,
        results: List[Tuple[TextChunk, float]],
        **kwargs
    ) -> List[Tuple[TextChunk, float]]:
        """Rerank results by boosting based on metadata fields.
        
        Args:
            query: Original query text
            results: List of (TextChunk, score) tuples from the retriever
            **kwargs: Additional parameters including:
                - boost_fields: Dict mapping metadata field names to boost factors
            
        Returns:
            Reranked list of (TextChunk, score) tuples
        """
        if not results:
            return []
        
        # Get boost fields from kwargs or use default
        boost_fields = kwargs.get("boost_fields", self.boost_fields)
        
        # Skip if no boost fields defined
        if not boost_fields:
            return results
        
        reranked_results = []
        for chunk, score in results:
            new_score = score
            
            # Apply boosts based on metadata fields
            for field, boost in boost_fields.items():
                if field in chunk.metadata:
                    # Apply boost based on field presence
                    new_score += boost
            
            # Ensure score doesn't exceed 1.0
            new_score = min(new_score, 1.0)
            
            reranked_results.append((chunk, new_score))
        
        # Sort by new scores
        reranked_results.sort(key=lambda x: x[1], reverse=True)
        
        return reranked_results


class EnsembleReranker(RerankerStrategy):
    """Reranking strategy that combines multiple rerankers."""
    
    def __init__(self, config: Config):
        """Initialize the ensemble reranker.
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        self.rerankers = []
        self.weights = []
    
    def add_reranker(self, reranker: RerankerStrategy, weight: float = 1.0) -> None:
        """Add a reranker to the ensemble.
        
        Args:
            reranker: Reranker strategy to add
            weight: Weight for this reranker's scores
        """
        self.rerankers.append(reranker)
        self.weights.append(weight)
    
    def rerank(
        self,
        query: str,
        results: List[Tuple[TextChunk, float]],
        **kwargs
    ) -> List[Tuple[TextChunk, float]]:
        """Rerank results using an ensemble of rerankers.
        
        Args:
            query: Original query text
            results: List of (TextChunk, score) tuples from the retriever
            **kwargs: Additional parameters to pass to individual rerankers
            
        Returns:
            Reranked list of (TextChunk, score) tuples
        """
        if not results or not self.rerankers:
            return results
        
        # Get individual reranker results
        all_reranked_results = []
        for reranker in self.rerankers:
            reranked = reranker.rerank(query, results, **kwargs)
            all_reranked_results.append(reranked)
        
        # Create a mapping of chunk ID to weighted scores
        chunk_scores = {}
        for i, reranked in enumerate(all_reranked_results):
            weight = self.weights[i]
            for chunk, score in reranked:
                if chunk.id not in chunk_scores:
                    chunk_scores[chunk.id] = {"chunk": chunk, "score": 0.0}
                chunk_scores[chunk.id]["score"] += score * weight
        
        # Normalize weights
        total_weight = sum(self.weights)
        if total_weight > 0:
            for chunk_id in chunk_scores:
                chunk_scores[chunk_id]["score"] /= total_weight
        
        # Convert back to list of tuples
        ensemble_results = [
            (data["chunk"], data["score"]) for data in chunk_scores.values()
        ]
        
        # Sort by combined scores
        ensemble_results.sort(key=lambda x: x[1], reverse=True)
        
        return ensemble_results


class Reranker:
    """Main reranker class that applies reranking strategies to retrieval results."""
    
    def __init__(self, config: Config):
        """Initialize the reranker with configuration.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.strategy = self._create_strategy()
    
    def _create_strategy(self) -> RerankerStrategy:
        """Create a reranking strategy based on configuration.
        
        Returns:
            An instance of the configured reranking strategy
            
        Raises:
            RetrievalError: If the strategy cannot be created
        """
        try:
            rerank_model = self.config.retrieval.rerank_model
            
            if rerank_model == "exact_match":
                return ExactMatchReranker(self.config)
            elif rerank_model == "length_normalized":
                return LengthNormalizedReranker(self.config)
            elif rerank_model == "metadata_boost":
                return MetadataBoostReranker(self.config)
            elif rerank_model == "ensemble":
                # Create an ensemble of all rerankers
                ensemble = EnsembleReranker(self.config)
                ensemble.add_reranker(ExactMatchReranker(self.config), 0.4)
                ensemble.add_reranker(LengthNormalizedReranker(self.config), 0.3)
                ensemble.add_reranker(MetadataBoostReranker(self.config), 0.3)
                return ensemble
            else:
                # Default to exact match reranker
                logger.warning(f"Unknown rerank model '{rerank_model}', using ExactMatchReranker")
                return ExactMatchReranker(self.config)
                
        except Exception as e:
            raise RetrievalError(f"Failed to create reranking strategy: {e}")
    
    def rerank(
        self,
        query: str,
        results: List[Tuple[TextChunk, float]],
        **kwargs
    ) -> List[Tuple[TextChunk, float]]:
        """Rerank retrieval results to improve relevance.
        
        Args:
            query: Original query text
            results: List of (TextChunk, score) tuples from the retriever
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            Reranked list of (TextChunk, score) tuples
            
        Raises:
            RetrievalError: If reranking fails
        """
        try:
            # Skip reranking if disabled or no results
            if not self.config.retrieval.enable_reranking or not results:
                return results
            
            # Apply reranking strategy
            reranked_results = self.strategy.rerank(query, results, **kwargs)
            
            # Limit to top_k if specified
            top_k = kwargs.get("top_k", self.config.retrieval.rerank_top_k)
            if top_k > 0 and len(reranked_results) > top_k:
                reranked_results = reranked_results[:top_k]
            
            logger.debug(f"Reranked {len(results)} results to {len(reranked_results)} results")
            return reranked_results
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Return original results on error
            return results
"""
Retrieval system for the unified knowledge base.

This module provides the core retrieval functionality for the knowledge base system,
including the base Retriever class and various retrieval strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Type, Union
import logging
import time

from ..core.config_fixed import Config
from ..core.types import TextChunk, RetrievalResult, SearchQuery
from ..core.exceptions import RetrievalError
from ..storage.base import BaseVectorStore
from .context_manager import ContextManager
from .cache import RetrievalCache

logger = logging.getLogger(__name__)


class RetrievalStrategy(ABC):
    """Base abstract class for retrieval strategies."""
    
    def __init__(self, config: Config):
        """Initialize the retrieval strategy with configuration.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    @abstractmethod
    async def retrieve(
        self,
        vector_store: BaseVectorStore,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Tuple[TextChunk, float]]:
        """Retrieve relevant chunks for a query.
        
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
        pass


class Retriever:
    """Retrieves relevant chunks for a query.
    
    This class provides a unified interface for retrieving relevant information
    from the knowledge base using different retrieval strategies.
    """
    
    def __init__(self, config: Config, vector_store: BaseVectorStore):
        """Initialize the retriever with configuration and vector store.
        
        Args:
            config: Configuration object
            vector_store: Vector store to search in
        """
        self.config = config
        self.vector_store = vector_store
        self.strategy = self._create_strategy()
        self.reranker = self._create_reranker()
        self.cache = RetrievalCache(config)
        self.context_manager = ContextManager(config)
    
    def _create_strategy(self) -> RetrievalStrategy:
        """Create a retrieval strategy based on configuration.
        
        Returns:
            An instance of the configured retrieval strategy
            
        Raises:
            RetrievalError: If the strategy cannot be created
        """
        strategy_name = self.config.retrieval.strategy
        try:
            if strategy_name == "semantic":
                from .strategies.semantic import SemanticStrategy
                return SemanticStrategy(self.config)
            elif strategy_name == "keyword":
                from .strategies.keyword import KeywordStrategy
                return KeywordStrategy(self.config)
            elif strategy_name == "hybrid":
                from .strategies.hybrid import HybridStrategy
                return HybridStrategy(self.config)
            else:
                raise RetrievalError(f"Unknown retrieval strategy: {strategy_name}")
        except ImportError as e:
            raise RetrievalError(f"Failed to import retrieval strategy '{strategy_name}': {e}")
        except Exception as e:
            raise RetrievalError(f"Failed to create retrieval strategy '{strategy_name}': {e}")
            
    def _create_reranker(self) -> Optional['Reranker']:
        """Create a reranker if enabled.
        
        Returns:
            An instance of the Reranker if enabled, None otherwise
        """
        if not self.config.retrieval.enable_reranking:
            return None
        try:
            from .reranker import Reranker
            return Reranker(self.config)
        except ImportError as e:
            logger.warning(f"Failed to import reranker: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to create reranker: {e}")
            return None
    
    async def retrieve(
        self,
        query: Union[str, SearchQuery],
        k: Optional[int] = None,
        filter: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        conversation_id: Optional[str] = None
    ) -> List[RetrievalResult]:
        """Retrieve relevant chunks for a query.
        
        Args:
            query: Query text or SearchQuery object
            k: Number of results to return (overrides config if provided)
            filter: Optional metadata filters to apply (overrides query filters if provided)
            use_cache: Whether to use the cache
            conversation_id: Optional ID of the conversation for context-aware retrieval
            
        Returns:
            List of RetrievalResult objects
            
        Raises:
            RetrievalError: If retrieval fails
        """
        # Convert string query to SearchQuery if needed
        if isinstance(query, str):
            search_query = SearchQuery(
                text=query,
                filters=filter or {},
                top_k=k or self.config.retrieval.top_k,
                min_score=self.config.retrieval.min_score
            )
        else:
            search_query = query
            # Override filters and top_k if provided as separate arguments
            if filter is not None:
                search_query.filters = filter
            if k is not None:
                search_query.top_k = k
        
        # Apply conversation context if provided
        original_query = search_query.text
        if conversation_id:
            # Add the query to the conversation
            turn = self.context_manager.add_query(conversation_id, original_query)
            
            # Enhance the query with conversation context
            enhanced_query = self.context_manager.enhance_query(conversation_id, original_query)
            search_query.text = enhanced_query
            
            if enhanced_query != original_query:
                logger.debug(f"Enhanced query: '{original_query}' -> '{enhanced_query}'")
        
        # Check cache if enabled
        if use_cache:
            cached_results = self.cache.get(search_query)
            if cached_results:
                # Update conversation with cached results if needed
                if conversation_id and turn:
                    self.context_manager.update_turn(
                        conversation_id,
                        turn.turn_id,
                        sources=cached_results
                    )
                
                return cached_results
        
        try:
            # Measure retrieval time
            start_time = time.time()
            
            # Retrieve chunks using the selected strategy
            results = await self.strategy.retrieve(
                self.vector_store,
                search_query.text,
                search_query.top_k,
                search_query.filters
            )
            
            # Apply reranking if enabled
            if self.reranker:
                results = self.reranker.rerank(search_query.text, results)
            
            # Filter by minimum score
            if search_query.min_score > 0:
                results = [(chunk, score) for chunk, score in results if score >= search_query.min_score]
            
            # Convert to RetrievalResult objects
            retrieval_results = []
            for i, (chunk, score) in enumerate(results):
                retrieval_results.append(RetrievalResult(
                    chunk=chunk,
                    score=score,
                    rank=i
                ))
            
            # Update cache if enabled
            if use_cache:
                self.cache.put(search_query, retrieval_results)
            
            # Update conversation with results if needed
            if conversation_id and turn:
                self.context_manager.update_turn(
                    conversation_id,
                    turn.turn_id,
                    sources=retrieval_results
                )
            
            # Log retrieval time
            retrieval_time = time.time() - start_time
            logger.debug(f"Retrieved {len(retrieval_results)} chunks in {retrieval_time:.3f}s")
            
            return retrieval_results
        
        except Exception as e:
            raise RetrievalError(f"Failed to retrieve chunks for query '{search_query.text}': {e}")
    
    def clear_cache(self) -> None:
        """Clear the retrieval cache."""
        self.cache.clear()
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        return self.cache.get_stats()
        
    def create_conversation(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new conversation for context-aware retrieval.
        
        Args:
            metadata: Optional metadata for the conversation
            
        Returns:
            ID of the newly created conversation
        """
        conversation = self.context_manager.create_conversation(metadata)
        return conversation.id
    
    def get_conversation_context(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get the conversation context for a given conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of conversation turns as dictionaries
        """
        turns, _ = self.context_manager.get_context(conversation_id)
        return [
            {
                "query": turn.query,
                "answer": turn.answer,
                "sources": [
                    {
                        "text": source.chunk.text,
                        "score": source.score,
                        "metadata": source.chunk.metadata
                    }
                    for source in turn.sources
                ],
                "timestamp": turn.timestamp.isoformat(),
                "turn_id": turn.turn_id
            }
            for turn in turns
        ]
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if the conversation was deleted, False if not found
        """
        return self.context_manager.delete_conversation(conversation_id)
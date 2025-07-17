"""Main retriever implementation."""

import logging
from typing import List, Optional
from ..core.config import RetrievalConfig
from ..core.types import SearchQuery, RetrievalResult, Chunk
from ..storage.vector_store import VectorStore
from ..processing.embedder import Embedder

logger = logging.getLogger(__name__)


class Retriever:
    """
    Main retriever that handles semantic and hybrid search.
    """
    
    def __init__(self, vector_store: VectorStore, config: RetrievalConfig):
        """Initialize retriever with vector store and configuration."""
        self.vector_store = vector_store
        self.config = config
        
        # We'll need an embedder to convert queries to vectors
        from ..core.config import EmbeddingConfig
        embedding_config = EmbeddingConfig()  # Use default config
        self.embedder = Embedder(embedding_config)
        
        logger.info(f"Retriever initialized with strategy: {config.strategy}")
    
    async def retrieve(self, query: SearchQuery) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: Search query with parameters
            
        Returns:
            List of retrieval results ranked by relevance
        """
        try:
            logger.debug(f"Retrieving for query: {query.text[:100]}...")
            
            if self.config.strategy == "semantic":
                return await self._semantic_retrieve(query)
            elif self.config.strategy == "keyword":
                return await self._keyword_retrieve(query)
            elif self.config.strategy == "hybrid":
                return await self._hybrid_retrieve(query)
            else:
                logger.warning(f"Unknown retrieval strategy: {self.config.strategy}, using semantic")
                return await self._semantic_retrieve(query)
                
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    async def _semantic_retrieve(self, query: SearchQuery) -> List[RetrievalResult]:
        """Semantic retrieval using vector similarity."""
        # Generate query embedding
        if not self.embedder.is_initialized:
            await self.embedder.initialize()
        
        query_vector = await self.embedder.embed_text(query.text)
        
        # Search vector store
        search_results = await self.vector_store.search_similar(
            query_vector=query_vector,
            top_k=query.top_k,
            filters=query.filters,
            min_score=query.min_score
        )
        
        # Convert to retrieval results
        results = []
        for i, result in enumerate(search_results):
            chunk = result["chunk"]
            score = result["score"]
            
            retrieval_result = RetrievalResult(
                chunk=chunk,
                score=score,
                rank=i + 1
            )
            results.append(retrieval_result)
        
        logger.debug(f"Semantic retrieval found {len(results)} results")
        return results
    
    async def _keyword_retrieve(self, query: SearchQuery) -> List[RetrievalResult]:
        """Keyword-based retrieval (simple text matching)."""
        # For now, we'll use semantic retrieval as fallback
        # In a full implementation, this would use BM25 or similar
        logger.debug("Keyword retrieval not fully implemented, using semantic fallback")
        return await self._semantic_retrieve(query)
    
    async def _hybrid_retrieve(self, query: SearchQuery) -> List[RetrievalResult]:
        """Hybrid retrieval combining semantic and keyword approaches."""
        # Get semantic results
        semantic_results = await self._semantic_retrieve(query)
        
        # For now, just return semantic results
        # In a full implementation, this would combine with keyword results
        # using the configured weights
        logger.debug(f"Hybrid retrieval returning {len(semantic_results)} semantic results")
        return semantic_results
    
    def _merge_results(
        self, 
        semantic_results: List[RetrievalResult], 
        keyword_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Merge semantic and keyword results using configured weights."""
        # Create a map of chunk_id to results
        result_map = {}
        
        # Add semantic results
        for result in semantic_results:
            chunk_id = result.chunk.id
            result_map[chunk_id] = {
                'chunk': result.chunk,
                'semantic_score': result.score,
                'keyword_score': 0.0,
                'rank': result.rank
            }
        
        # Add keyword results
        for result in keyword_results:
            chunk_id = result.chunk.id
            if chunk_id in result_map:
                result_map[chunk_id]['keyword_score'] = result.score
            else:
                result_map[chunk_id] = {
                    'chunk': result.chunk,
                    'semantic_score': 0.0,
                    'keyword_score': result.score,
                    'rank': result.rank
                }
        
        # Calculate combined scores
        merged_results = []
        for chunk_id, data in result_map.items():
            combined_score = (
                data['semantic_score'] * self.config.semantic_weight +
                data['keyword_score'] * self.config.keyword_weight
            )
            
            merged_results.append(RetrievalResult(
                chunk=data['chunk'],
                score=combined_score,
                rank=0  # Will be set after sorting
            ))
        
        # Sort by combined score and update ranks
        merged_results.sort(key=lambda x: x.score, reverse=True)
        for i, result in enumerate(merged_results):
            result.rank = i + 1
        
        return merged_results
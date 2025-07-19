"""
Unit tests for the retrieval system.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from src.knowledge_base.core.config_fixed import Config
from src.knowledge_base.core.types import TextChunk, RetrievalResult, SearchQuery
from src.knowledge_base.retrieval.retriever import Retriever, RetrievalStrategy
from src.knowledge_base.retrieval.strategies.semantic import SemanticStrategy
from src.knowledge_base.retrieval.strategies.keyword import KeywordStrategy
from src.knowledge_base.retrieval.strategies.hybrid import HybridStrategy


class TestRetriever:
    """Test the Retriever class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = Config()
        config.retrieval.strategy = "semantic"
        config.retrieval.top_k = 3
        config.retrieval.min_score = 0.5
        config.retrieval.cache_enabled = True
        config.retrieval.cache_ttl = 60
        return config
    
    @pytest.fixture
    def vector_store(self):
        """Create a mock vector store."""
        mock_store = AsyncMock()
        
        # Create test chunks
        chunks = [
            TextChunk(id=f"chunk{i}", text=f"Test chunk {i}", document_id=f"doc{i}")
            for i in range(5)
        ]
        
        # Mock similarity_search
        async def mock_similarity_search(query, k=5, filter=None, embedding=None):
            return [(chunks[i], 0.9 - i * 0.1) for i in range(min(k, len(chunks)))]
        
        # Mock keyword_search
        async def mock_keyword_search(query, k=5, filter=None):
            return [(chunks[i], 0.8 - i * 0.1) for i in range(min(k, len(chunks)))]
        
        mock_store.similarity_search = mock_similarity_search
        mock_store.keyword_search = mock_keyword_search
        return mock_store
    
    @pytest.mark.asyncio
    async def test_retriever_initialization(self, config, vector_store):
        """Test that the retriever initializes correctly."""
        retriever = Retriever(config, vector_store)
        assert retriever.config == config
        assert retriever.vector_store == vector_store
        assert isinstance(retriever.strategy, SemanticStrategy)
    
    @pytest.mark.asyncio
    async def test_semantic_retrieval(self, config, vector_store):
        """Test semantic retrieval."""
        config.retrieval.strategy = "semantic"
        retriever = Retriever(config, vector_store)
        
        results = await retriever.retrieve("test query", k=3)
        
        assert len(results) == 3
        assert all(isinstance(r, RetrievalResult) for r in results)
        assert results[0].score > results[1].score > results[2].score
    
    @pytest.mark.asyncio
    async def test_keyword_retrieval(self, config, vector_store):
        """Test keyword retrieval."""
        config.retrieval.strategy = "keyword"
        retriever = Retriever(config, vector_store)
        
        results = await retriever.retrieve("test query", k=3)
        
        assert len(results) == 3
        assert all(isinstance(r, RetrievalResult) for r in results)
        assert results[0].score > results[1].score > results[2].score
    
    @pytest.mark.asyncio
    async def test_hybrid_retrieval(self, config, vector_store):
        """Test hybrid retrieval."""
        config.retrieval.strategy = "hybrid"
        config.retrieval.semantic_weight = 0.7
        config.retrieval.keyword_weight = 0.3
        retriever = Retriever(config, vector_store)
        
        results = await retriever.retrieve("test query", k=3)
        
        assert len(results) == 3
        assert all(isinstance(r, RetrievalResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_retrieval_with_filters(self, config, vector_store):
        """Test retrieval with filters."""
        retriever = Retriever(config, vector_store)
        
        filters = {"category": "test"}
        results = await retriever.retrieve("test query", filter=filters)
        
        # Check that the filter was passed to the vector store
        vector_store.similarity_search.assert_awaited_with(
            query="test query",
            k=3,
            filter=filters,
            embedding=None
        )
    
    @pytest.mark.asyncio
    async def test_retrieval_with_search_query(self, config, vector_store):
        """Test retrieval with SearchQuery object."""
        retriever = Retriever(config, vector_store)
        
        query = SearchQuery(
            text="test query",
            filters={"category": "test"},
            top_k=2,
            min_score=0.6
        )
        
        results = await retriever.retrieve(query)
        
        # Check that the query parameters were passed to the vector store
        vector_store.similarity_search.assert_awaited_with(
            query="test query",
            k=2,
            filter={"category": "test"},
            embedding=None
        )
    
    @pytest.mark.asyncio
    async def test_retrieval_caching(self, config, vector_store):
        """Test that retrieval results are cached."""
        retriever = Retriever(config, vector_store)
        
        # First call should hit the vector store
        results1 = await retriever.retrieve("test query")
        assert vector_store.similarity_search.call_count == 1
        
        # Second call with the same query should use the cache
        results2 = await retriever.retrieve("test query")
        assert vector_store.similarity_search.call_count == 1
        
        # Call with different query should hit the vector store again
        results3 = await retriever.retrieve("different query")
        assert vector_store.similarity_search.call_count == 2
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, config, vector_store):
        """Test clearing the cache."""
        retriever = Retriever(config, vector_store)
        
        # First call should hit the vector store
        await retriever.retrieve("test query")
        assert vector_store.similarity_search.call_count == 1
        
        # Clear the cache
        retriever.clear_cache()
        
        # Next call should hit the vector store again
        await retriever.retrieve("test query")
        assert vector_store.similarity_search.call_count == 2
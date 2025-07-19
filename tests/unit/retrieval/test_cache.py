"""
Unit tests for the retrieval cache.
"""

import pytest
import time
from unittest.mock import MagicMock

from src.knowledge_base.core.config_fixed import Config
from src.knowledge_base.core.types import RetrievalResult, TextChunk, SearchQuery
from src.knowledge_base.retrieval.cache import RetrievalCache, LRUCache


class TestLRUCache:
    """Test the LRUCache class."""
    
    def test_lru_cache_basic(self):
        """Test basic LRU cache operations."""
        cache = LRUCache[str](3)
        
        # Add items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Check items
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert len(cache) == 3
        
        # Add one more item (should evict key1)
        cache.put("key4", "value4")
        
        # Check eviction
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
        assert len(cache) == 3
    
    def test_lru_cache_update(self):
        """Test LRU cache update behavior."""
        cache = LRUCache[str](3)
        
        # Add items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Access key1 (makes it most recently used)
        assert cache.get("key1") == "value1"
        
        # Add one more item (should evict key2)
        cache.put("key4", "value4")
        
        # Check eviction
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_lru_cache_remove(self):
        """Test LRU cache remove operation."""
        cache = LRUCache[str](3)
        
        # Add items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Remove item
        assert cache.remove("key1") is True
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        
        # Remove non-existent item
        assert cache.remove("key3") is False
    
    def test_lru_cache_clear(self):
        """Test LRU cache clear operation."""
        cache = LRUCache[str](3)
        
        # Add items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Clear cache
        cache.clear()
        
        # Check items
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert len(cache) == 0


class TestRetrievalCache:
    """Test the RetrievalCache class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = Config()
        config.retrieval.cache_enabled = True
        config.retrieval.cache_ttl = 60
        config.retrieval.cache_size = 10
        return config
    
    @pytest.fixture
    def retrieval_results(self):
        """Create test retrieval results."""
        chunks = [
            TextChunk(id=f"chunk{i}", text=f"Test chunk {i}", document_id=f"doc{i}")
            for i in range(3)
        ]
        
        return [
            RetrievalResult(chunk=chunks[0], score=0.9, rank=0),
            RetrievalResult(chunk=chunks[1], score=0.8, rank=1),
            RetrievalResult(chunk=chunks[2], score=0.7, rank=2)
        ]
    
    def test_cache_initialization(self, config):
        """Test cache initialization."""
        cache = RetrievalCache(config)
        
        assert cache.enabled is True
        assert cache.ttl == 60
        assert cache.cache.capacity == 10
    
    def test_cache_disabled(self, config, retrieval_results):
        """Test cache when disabled."""
        config.retrieval.cache_enabled = False
        cache = RetrievalCache(config)
        
        # Put and get should do nothing
        cache.put("test query", retrieval_results)
        assert cache.get("test query") is None
        
        # Stats should show disabled
        stats = cache.get_stats()
        assert stats["enabled"] is False
    
    def test_cache_basic(self, config, retrieval_results):
        """Test basic cache operations."""
        cache = RetrievalCache(config)
        
        # Initially empty
        assert cache.get("test query") is None
        
        # Add an item
        cache.put("test query", retrieval_results)
        
        # Get the item
        cached_results = cache.get("test query")
        assert cached_results is not None
        assert len(cached_results) == 3
        assert cached_results[0].score == 0.9
        
        # Check stats
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
    
    def test_cache_with_search_query(self, config, retrieval_results):
        """Test cache with SearchQuery objects."""
        cache = RetrievalCache(config)
        
        # Create a search query
        query = SearchQuery(
            text="test query",
            filters={"category": "test"},
            top_k=5
        )
        
        # Add an item
        cache.put(query, retrieval_results)
        
        # Get with the same query
        cached_results = cache.get(query)
        assert cached_results is not None
        
        # Get with a different query
        different_query = SearchQuery(
            text="test query",
            filters={"category": "different"},
            top_k=5
        )
        assert cache.get(different_query) is None
    
    def test_cache_expiration(self, config, retrieval_results):
        """Test cache entry expiration."""
        # Set a short TTL for testing
        config.retrieval.cache_ttl = 0.1
        cache = RetrievalCache(config)
        
        # Add an item
        cache.put("test query", retrieval_results)
        
        # Get the item immediately
        assert cache.get("test query") is not None
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Item should be expired
        assert cache.get("test query") is None
        
        # Check stats
        stats = cache.get_stats()
        assert stats["evictions"] == 1
    
    def test_cache_clear(self, config, retrieval_results):
        """Test clearing the cache."""
        cache = RetrievalCache(config)
        
        # Add items
        cache.put("query1", retrieval_results)
        cache.put("query2", retrieval_results)
        
        # Clear the cache
        cache.clear()
        
        # Items should be gone
        assert cache.get("query1") is None
        assert cache.get("query2") is None
    
    def test_cache_invalidation(self, config, retrieval_results):
        """Test cache invalidation."""
        cache = RetrievalCache(config)
        
        # Add items
        cache.put("query1", retrieval_results)
        cache.put("query2", retrieval_results)
        
        # Invalidate specific query
        cache.invalidate("query1")
        
        # Both should be gone (current implementation clears all)
        assert cache.get("query1") is None
        assert cache.get("query2") is None
    
    def test_cache_size_limit(self, config, retrieval_results):
        """Test cache size limit."""
        # Set a small cache size
        config.retrieval.cache_size = 2
        cache = RetrievalCache(config)
        
        # Add items
        cache.put("query1", retrieval_results)
        cache.put("query2", retrieval_results)
        
        # Both should be in cache
        assert cache.get("query1") is not None
        assert cache.get("query2") is not None
        
        # Add one more item
        cache.put("query3", retrieval_results)
        
        # query1 should be evicted (LRU)
        assert cache.get("query1") is None
        assert cache.get("query2") is not None
        assert cache.get("query3") is not None
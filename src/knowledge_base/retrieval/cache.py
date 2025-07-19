"""
Cache implementation for the retrieval system.

This module provides caching mechanisms for retrieval results to improve
performance by avoiding redundant queries to the vector store.
"""

import time
import logging
from typing import Dict, Any, Optional, List, Tuple, Generic, TypeVar, Union
import threading
from collections import OrderedDict
import hashlib
import json

from ..core.config_fixed import Config
from ..core.types import RetrievalResult, SearchQuery

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LRUCache(Generic[T]):
    """
    Least Recently Used (LRU) cache implementation.
    
    This cache automatically evicts the least recently used items when it reaches
    its capacity limit.
    """
    
    def __init__(self, capacity: int):
        """Initialize the LRU cache with a specified capacity.
        
        Args:
            capacity: Maximum number of items to store in the cache
        """
        self.capacity = max(1, capacity)
        self.cache = OrderedDict()
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[T]:
        """Get an item from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached item if found, None otherwise
        """
        with self.lock:
            if key in self.cache:
                # Move the item to the end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            return None
    
    def put(self, key: str, value: T) -> None:
        """Add an item to the cache.
        
        Args:
            key: Cache key
            value: Item to cache
        """
        with self.lock:
            if key in self.cache:
                # Remove the existing item
                self.cache.pop(key)
            elif len(self.cache) >= self.capacity:
                # Remove the least recently used item (first item)
                self.cache.popitem(last=False)
            # Add the new item
            self.cache[key] = value
    
    def remove(self, key: str) -> bool:
        """Remove an item from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the item was removed, False if not found
        """
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        with self.lock:
            self.cache.clear()
    
    def __len__(self) -> int:
        """Get the number of items in the cache."""
        return len(self.cache)
    
    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        return key in self.cache


class RetrievalCache:
    """
    Cache for retrieval results.
    
    This class provides caching mechanisms for retrieval results with:
    - Time-based invalidation (TTL)
    - Size-based eviction (LRU)
    - Query-based invalidation
    """
    
    def __init__(self, config: Config):
        """Initialize the retrieval cache.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.enabled = config.retrieval.cache_enabled
        self.ttl = config.retrieval.cache_ttl
        
        # Default to 1000 items if not specified
        cache_size = getattr(config.retrieval, 'cache_size', 1000)
        self.cache = LRUCache[Dict[str, Any]](cache_size)
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        logger.debug(f"Initialized retrieval cache (enabled={self.enabled}, ttl={self.ttl}s, size={cache_size})")
    
    def _generate_key(self, query: Union[str, SearchQuery], filters: Optional[Dict[str, Any]] = None, k: Optional[int] = None) -> str:
        """Generate a cache key for a query.
        
        Args:
            query: Query text or SearchQuery object
            filters: Optional metadata filters
            k: Number of results to return
            
        Returns:
            A unique cache key
        """
        if isinstance(query, SearchQuery):
            query_text = query.text
            filters = query.filters
            k = query.top_k
        else:
            query_text = query
        
        # Create a dictionary of all parameters that affect the query result
        key_dict = {
            "query": query_text,
            "filters": filters or {},
            "k": k or self.config.retrieval.top_k
        }
        
        # Convert to a stable JSON string and hash it
        key_json = json.dumps(key_dict, sort_keys=True)
        return hashlib.md5(key_json.encode()).hexdigest()
    
    def get(self, query: Union[str, SearchQuery], filters: Optional[Dict[str, Any]] = None, k: Optional[int] = None) -> Optional[List[RetrievalResult]]:
        """Get cached retrieval results for a query.
        
        Args:
            query: Query text or SearchQuery object
            filters: Optional metadata filters
            k: Number of results to return
            
        Returns:
            Cached retrieval results if found and valid, None otherwise
        """
        if not self.enabled:
            return None
        
        key = self._generate_key(query, filters, k)
        cache_entry = self.cache.get(key)
        
        if cache_entry is None:
            self.misses += 1
            return None
        
        # Check if the cache entry is still valid
        if time.time() - cache_entry["timestamp"] > self.ttl:
            # Entry has expired
            self.cache.remove(key)
            self.evictions += 1
            return None
        
        self.hits += 1
        logger.debug(f"Cache hit for query: {query if isinstance(query, str) else query.text}")
        return cache_entry["results"]
    
    def put(self, query: Union[str, SearchQuery], results: List[RetrievalResult], filters: Optional[Dict[str, Any]] = None, k: Optional[int] = None) -> None:
        """Cache retrieval results for a query.
        
        Args:
            query: Query text or SearchQuery object
            results: Retrieval results to cache
            filters: Optional metadata filters
            k: Number of results to return
        """
        if not self.enabled:
            return
        
        key = self._generate_key(query, filters, k)
        cache_entry = {
            "results": results,
            "timestamp": time.time()
        }
        
        self.cache.put(key, cache_entry)
        logger.debug(f"Cached results for query: {query if isinstance(query, str) else query.text}")
    
    def invalidate(self, query: Optional[Union[str, SearchQuery]] = None, filters: Optional[Dict[str, Any]] = None) -> None:
        """Invalidate cache entries matching a query pattern.
        
        Args:
            query: Optional query text or SearchQuery object to invalidate
            filters: Optional metadata filters to invalidate
        """
        if not self.enabled:
            return
        
        if query is None and filters is None:
            # Invalidate all entries
            self.clear()
            return
        
        # For selective invalidation, we would need to iterate through all keys
        # This is not efficient with the current implementation, so we'll just clear the cache
        # A more sophisticated implementation would use a different data structure
        # that allows for pattern-based key lookup
        logger.warning("Selective cache invalidation not implemented, clearing entire cache")
        self.clear()
    
    def clear(self) -> None:
        """Clear all cached results."""
        if not self.enabled:
            return
        
        self.cache.clear()
        logger.debug("Cleared retrieval cache")
    
    def clean_expired(self) -> int:
        """Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        if not self.enabled:
            return 0
        
        # This is not efficient with the current implementation
        # A more sophisticated implementation would use a data structure
        # that allows for efficient expiration checks
        logger.warning("Explicit expired entry cleaning not implemented")
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "enabled": self.enabled,
            "size": len(self.cache),
            "capacity": self.cache.capacity,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions
        }
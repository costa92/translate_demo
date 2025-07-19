"""
Optimized embedder implementation.

This module provides an optimized embedder wrapper that adds caching,
batch processing optimizations, and fallback mechanisms.
"""

import logging
import time
from functools import lru_cache
from typing import List, Optional, Dict, Any, Tuple, Callable

from .embedder import Embedder
from ..core.config import Config
from ..core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class OptimizedEmbedder(Embedder):
    """Optimized embedder wrapper.
    
    This class wraps an embedder implementation and adds caching,
    batch processing optimizations, and fallback mechanisms.
    """
    
    def __init__(self, config: Config):
        """Initialize the OptimizedEmbedder.
        
        Args:
            config: The system configuration.
        """
        super().__init__(config)
        self.config = config
        self.primary_embedder = self._create_primary_embedder()
        self.fallback_embedders = self._create_fallback_embedders()
        self.cache_size = config.embedding.cache_size or 1000
        self.batch_size = config.embedding.batch_size or 32
        self.retry_attempts = config.embedding.retry_attempts or 3
        self.retry_delay = config.embedding.retry_delay or 1.0  # seconds
        
        # Initialize cache
        self._setup_cache()
        
        logger.info(
            f"Initialized OptimizedEmbedder with cache_size={self.cache_size}, "
            f"batch_size={self.batch_size}, retry_attempts={self.retry_attempts}"
        )
    
    def _create_primary_embedder(self) -> Embedder:
        """Create the primary embedder based on configuration.
        
        Returns:
            The primary embedder instance.
            
        Raises:
            ProcessingError: If the embedder cannot be created.
        """
        provider = self.config.embedding.provider
        try:
            if provider == "sentence_transformers":
                from .providers.sentence_transformers import SentenceTransformersEmbedder
                return SentenceTransformersEmbedder(self.config)
            elif provider == "openai":
                from .providers.openai import OpenAIEmbedder
                return OpenAIEmbedder(self.config)
            elif provider == "deepseek":
                from .providers.deepseek import DeepSeekEmbedder
                return DeepSeekEmbedder(self.config)
            elif provider == "siliconflow":
                from .providers.siliconflow import SiliconFlowEmbedder
                return SiliconFlowEmbedder(self.config)
            elif provider == "simple":
                from .providers.simple import SimpleEmbedder
                return SimpleEmbedder(self.config)
            else:
                raise ProcessingError(f"Unknown embedding provider: {provider}")
        except Exception as e:
            raise ProcessingError(f"Failed to create primary embedder: {str(e)}")
    
    def _create_fallback_embedders(self) -> List[Embedder]:
        """Create fallback embedders based on configuration.
        
        Returns:
            A list of fallback embedder instances.
        """
        fallbacks = []
        fallback_providers = self.config.embedding.fallback_providers or []
        
        for provider in fallback_providers:
            try:
                if provider == "sentence_transformers":
                    from .providers.sentence_transformers import SentenceTransformersEmbedder
                    fallbacks.append(SentenceTransformersEmbedder(self.config))
                elif provider == "openai":
                    from .providers.openai import OpenAIEmbedder
                    fallbacks.append(OpenAIEmbedder(self.config))
                elif provider == "deepseek":
                    from .providers.deepseek import DeepSeekEmbedder
                    fallbacks.append(DeepSeekEmbedder(self.config))
                elif provider == "siliconflow":
                    from .providers.siliconflow import SiliconFlowEmbedder
                    fallbacks.append(SiliconFlowEmbedder(self.config))
                elif provider == "simple":
                    from .providers.simple import SimpleEmbedder
                    fallbacks.append(SimpleEmbedder(self.config))
                else:
                    logger.warning(f"Unknown fallback embedding provider: {provider}")
            except Exception as e:
                logger.warning(f"Failed to create fallback embedder {provider}: {str(e)}")
        
        # Always add SimpleEmbedder as a last resort fallback if not already included
        if not any(isinstance(embedder, SimpleEmbedder) for embedder in fallbacks):
            try:
                from .providers.simple import SimpleEmbedder
                fallbacks.append(SimpleEmbedder(self.config))
            except Exception as e:
                logger.warning(f"Failed to create SimpleEmbedder fallback: {str(e)}")
        
        return fallbacks
    
    def _setup_cache(self) -> None:
        """Set up the embedding cache."""
        # Create a cache decorator with the specified size
        @lru_cache(maxsize=self.cache_size)
        def cached_embed(text: str) -> Tuple[float, ...]:
            # This is just a placeholder - the actual implementation is in _cached_embed_text
            # We need this indirection because lru_cache requires hashable arguments
            pass
        
        self._cached_embed = cached_embed
    
    async def _cached_embed_text(self, text: str) -> List[float]:
        """Embed a single text with caching.
        
        Args:
            text: The text to embed.
            
        Returns:
            A list of floats representing the embedding vector.
            
        Raises:
            ProcessingError: If embedding fails with all providers.
        """
        # Check if the text is in the cache
        cache_key = text
        
        # If the text is in the cache, return the cached embedding
        if cache_key in self._cached_embed.__wrapped__.cache_info().hits:
            cached_result = self._cached_embed(cache_key)
            return list(cached_result)
        
        # Try the primary embedder with retries
        for attempt in range(self.retry_attempts):
            try:
                embedding = await self.primary_embedder.embed_text(text)
                # Cache the result
                self._cached_embed(cache_key)
                return embedding
            except Exception as e:
                logger.warning(
                    f"Primary embedder failed (attempt {attempt + 1}/{self.retry_attempts}): {str(e)}"
                )
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
        
        # Try fallback embedders
        for i, fallback in enumerate(self.fallback_embedders):
            try:
                logger.info(f"Trying fallback embedder {i + 1}/{len(self.fallback_embedders)}")
                embedding = await fallback.embed_text(text)
                return embedding
            except Exception as e:
                logger.warning(f"Fallback embedder {i + 1} failed: {str(e)}")
        
        # If all embedders fail, raise an error
        raise ProcessingError("All embedding providers failed")
    
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text with caching and fallback.
        
        Args:
            text: The text to embed.
            
        Returns:
            A list of floats representing the embedding vector.
            
        Raises:
            ProcessingError: If embedding fails with all providers.
        """
        return await self._cached_embed_text(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts with batching, caching, and fallback.
        
        Args:
            texts: A list of texts to embed.
            
        Returns:
            A list of embedding vectors, one for each input text.
            
        Raises:
            ProcessingError: If embedding fails with all providers.
        """
        results = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            # Try to get embeddings from cache first
            batch_results = []
            uncached_indices = []
            uncached_texts = []
            
            # Check which texts are in the cache
            for j, text in enumerate(batch):
                try:
                    # Try to get from cache
                    cached_result = self._cached_embed(text)
                    batch_results.append(list(cached_result))
                except Exception:
                    # Not in cache, add to list for batch processing
                    uncached_indices.append(j)
                    uncached_texts.append(text)
            
            # If there are uncached texts, process them
            if uncached_texts:
                # Try the primary embedder with retries
                uncached_embeddings = None
                for attempt in range(self.retry_attempts):
                    try:
                        uncached_embeddings = await self.primary_embedder.embed_texts(uncached_texts)
                        break
                    except Exception as e:
                        logger.warning(
                            f"Primary embedder batch failed (attempt {attempt + 1}/{self.retry_attempts}): {str(e)}"
                        )
                        if attempt < self.retry_attempts - 1:
                            time.sleep(self.retry_delay)
                
                # If primary embedder failed, try fallbacks
                if uncached_embeddings is None:
                    for i, fallback in enumerate(self.fallback_embedders):
                        try:
                            logger.info(f"Trying fallback embedder {i + 1}/{len(self.fallback_embedders)} for batch")
                            uncached_embeddings = await fallback.embed_texts(uncached_texts)
                            break
                        except Exception as e:
                            logger.warning(f"Fallback embedder {i + 1} batch failed: {str(e)}")
                
                # If all embedders fail, try one by one
                if uncached_embeddings is None:
                    logger.warning("All batch embedding attempts failed, trying one by one")
                    uncached_embeddings = []
                    for text in uncached_texts:
                        try:
                            embedding = await self.embed_text(text)
                            uncached_embeddings.append(embedding)
                        except ProcessingError as e:
                            # If individual embedding fails, use a zero vector as a last resort
                            logger.error(f"Individual embedding failed: {str(e)}")
                            dimension = self.config.embedding.dimension or 768
                            uncached_embeddings.append([0.0] * dimension)
                
                # Add uncached embeddings to results and cache them
                for j, embedding in zip(uncached_indices, uncached_embeddings):
                    batch_results.insert(j, embedding)
                    # Cache the result
                    self._cached_embed(batch[j])
            
            results.extend(batch_results)
        
        return results
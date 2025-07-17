"""Text embedding implementation."""

import asyncio
import logging
from typing import List, Optional
from ..core.config import EmbeddingConfig
from ..core.exceptions import EmbeddingError
from .providers.sentence_transformers import SentenceTransformersEmbedder

logger = logging.getLogger(__name__)


class Embedder:
    """
    Text embedder that converts text to vector embeddings.
    Supports multiple embedding providers.
    """
    
    def __init__(self, config: EmbeddingConfig):
        """Initialize embedder with configuration."""
        self.config = config
        self._provider = None
        self._initialized = False
        
        logger.info(f"Embedder initialized with provider: {config.provider}")
    
    async def initialize(self) -> None:
        """Initialize the embedding provider."""
        if self._initialized:
            return
        
        try:
            logger.info(f"Initializing embedding provider: {self.config.provider}")
            
            if self.config.provider == "sentence_transformers":
                self._provider = SentenceTransformersEmbedder(self.config)
            elif self.config.provider == "openai":
                from .providers.openai import OpenAIEmbedder
                self._provider = OpenAIEmbedder(self.config)
            elif self.config.provider == "huggingface":
                from .providers.huggingface import HuggingFaceEmbedder
                self._provider = HuggingFaceEmbedder(self.config)
            elif self.config.provider == "siliconflow":
                from .providers.siliconflow import SiliconFlowEmbedder
                self._provider = SiliconFlowEmbedder(self.config)
            elif self.config.provider == "deepseek":
                from .providers.deepseek import DeepSeekEmbedder
                self._provider = DeepSeekEmbedder(self.config)
            else:
                raise EmbeddingError(f"Unsupported embedding provider: {self.config.provider}")
            
            await self._provider.initialize()
            self._initialized = True
            
            logger.info(f"Embedding provider initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding provider: {e}")
            raise EmbeddingError(f"Embedding provider initialization failed: {e}")
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if not self._initialized:
            await self.initialize()
        
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.config.dimensions
        
        try:
            return await self._provider.embed_text(text.strip())
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise EmbeddingError(f"Text embedding failed: {e}", text_length=len(text))
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self._initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        # Filter out empty texts but keep track of positions
        filtered_texts = []
        text_indices = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                filtered_texts.append(text.strip())
                text_indices.append(i)
        
        if not filtered_texts:
            # Return zero vectors for all texts
            return [[0.0] * self.config.dimensions] * len(texts)
        
        try:
            # Get embeddings for non-empty texts
            embeddings = await self._provider.embed_batch(filtered_texts)
            
            # Create result list with zero vectors for empty texts
            result = []
            embedding_idx = 0
            
            for i in range(len(texts)):
                if i in text_indices:
                    result.append(embeddings[embedding_idx])
                    embedding_idx += 1
                else:
                    result.append([0.0] * self.config.dimensions)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            raise EmbeddingError(f"Batch embedding failed: {e}")
    
    async def close(self) -> None:
        """Close the embedder and cleanup resources."""
        if self._provider:
            await self._provider.close()
        
        self._initialized = False
        logger.info("Embedder closed")
    
    @property
    def is_initialized(self) -> bool:
        """Check if the embedder is initialized."""
        return self._initialized
    
    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.config.dimensions
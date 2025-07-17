"""Sentence Transformers embedding provider."""

import asyncio
import logging
from typing import List
from ...core.config import EmbeddingConfig
from ...core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class SentenceTransformersEmbedder:
    """
    Sentence Transformers embedding provider.
    Falls back to simple embedding if sentence-transformers is not available.
    """
    
    def __init__(self, config: EmbeddingConfig):
        """Initialize sentence transformers embedder."""
        self.config = config
        self._model = None
        self._initialized = False
        self._use_fallback = False
        
        logger.info(f"SentenceTransformersEmbedder initialized with model: {config.model}")
    
    async def initialize(self) -> None:
        """Initialize the sentence transformers model."""
        if self._initialized:
            return
        
        try:
            # Try to import and load sentence transformers
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading sentence transformers model: {self.config.model}")
            
            # Load model in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(
                None, 
                lambda: SentenceTransformer(self.config.model, device=self.config.device)
            )
            
            # Update dimensions from model
            self.config.dimensions = self._model.get_sentence_embedding_dimension()
            
            logger.info(f"Sentence transformers model loaded successfully, dimensions: {self.config.dimensions}")
            
        except ImportError:
            logger.warning("sentence-transformers not available, using fallback embedder")
            self._use_fallback = True
            self._init_fallback()
        except Exception as e:
            logger.warning(f"Failed to load sentence transformers model: {e}, using fallback")
            self._use_fallback = True
            self._init_fallback()
        
        self._initialized = True
    
    def _init_fallback(self) -> None:
        """Initialize fallback simple embedder."""
        from .simple import SimpleEmbedder
        self._model = SimpleEmbedder(self.config.dimensions)
        logger.info(f"Fallback embedder initialized with dimensions: {self.config.dimensions}")
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not self._initialized:
            await self.initialize()
        
        if not text or not text.strip():
            return [0.0] * self.config.dimensions
        
        try:
            if self._use_fallback:
                return self._model.embed_text(text)
            else:
                # Use sentence transformers
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(
                    None,
                    lambda: self._model.encode([text], convert_to_tensor=False)[0]
                )
                return embedding.tolist()
                
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise EmbeddingError(f"Text embedding failed: {e}")
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self._initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        try:
            if self._use_fallback:
                return [self._model.embed_text(text) for text in texts]
            else:
                # Use sentence transformers batch processing
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(
                    None,
                    lambda: self._model.encode(texts, convert_to_tensor=False, batch_size=self.config.batch_size)
                )
                return [emb.tolist() for emb in embeddings]
                
        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            raise EmbeddingError(f"Batch embedding failed: {e}")
    
    async def close(self) -> None:
        """Close the embedder and cleanup resources."""
        self._model = None
        self._initialized = False
        logger.info("SentenceTransformersEmbedder closed")
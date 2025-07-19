"""
Sentence Transformers embedder implementation.

This module provides an embedder implementation using the sentence-transformers library.
"""

import logging
from typing import List, Optional

from ..embedder import Embedder
from ...core.config import Config
from ...core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class SentenceTransformersEmbedder(Embedder):
    """Embedder implementation using sentence-transformers.
    
    This class provides text embedding capabilities using the sentence-transformers library,
    which supports a wide range of embedding models.
    """
    
    def __init__(self, config: Config):
        """Initialize the SentenceTransformersEmbedder.
        
        Args:
            config: The system configuration.
            
        Raises:
            ProcessingError: If the sentence-transformers library cannot be imported or
                the model cannot be loaded.
        """
        super().__init__(config)
        self.model_name = config.embedding.model_name or "all-MiniLM-L6-v2"
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the sentence-transformers model.
        
        Raises:
            ProcessingError: If the sentence-transformers library cannot be imported or
                the model cannot be loaded.
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded sentence-transformers model: {self.model_name}")
        except ImportError:
            raise ProcessingError(
                "Could not import sentence-transformers. "
                "Please install it with 'pip install sentence-transformers'."
            )
        except Exception as e:
            raise ProcessingError(f"Failed to load sentence-transformers model: {str(e)}")
    
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text.
        
        Args:
            text: The text to embed.
            
        Returns:
            A list of floats representing the embedding vector.
            
        Raises:
            ProcessingError: If embedding fails.
        """
        try:
            # Convert to list to ensure serialization compatibility
            return self.model.encode(text).tolist()
        except Exception as e:
            raise ProcessingError(f"Failed to embed text: {str(e)}")
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts.
        
        Args:
            texts: A list of texts to embed.
            
        Returns:
            A list of embedding vectors, one for each input text.
            
        Raises:
            ProcessingError: If embedding fails.
        """
        try:
            # Convert to list to ensure serialization compatibility
            return self.model.encode(texts).tolist()
        except Exception as e:
            raise ProcessingError(f"Failed to embed texts: {str(e)}")
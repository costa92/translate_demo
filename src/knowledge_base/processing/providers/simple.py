"""
Simple embedder implementation.

This module provides a simple embedder implementation for testing and development.
"""

import hashlib
import logging
from typing import List, Optional

from ..embedder import Embedder
from ...core.config import Config
from ...core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class SimpleEmbedder(Embedder):
    """Simple embedder implementation for testing and development.
    
    This class provides a basic embedding capability that doesn't require
    external dependencies. It's not meant for production use but is useful
    for testing and development.
    """
    
    def __init__(self, config: Config):
        """Initialize the SimpleEmbedder.
        
        Args:
            config: The system configuration.
        """
        super().__init__(config)
        self.dimension = config.embedding.simple_dimension or 128
        logger.info(f"Initialized SimpleEmbedder with dimension: {self.dimension}")
    
    def _hash_text(self, text: str) -> List[float]:
        """Create a deterministic embedding from text using hashing.
        
        Args:
            text: The text to embed.
            
        Returns:
            A list of floats representing the embedding vector.
        """
        # Create a deterministic hash of the text
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert hash bytes to a list of floats in the range [-1, 1]
        embedding = []
        for i in range(self.dimension):
            # Use modulo to cycle through the hash bytes if needed
            byte_val = hash_bytes[i % len(hash_bytes)]
            # Convert byte (0-255) to float (-1 to 1)
            float_val = (byte_val / 127.5) - 1.0
            embedding.append(float_val)
        
        # Normalize the embedding to unit length
        magnitude = sum(x**2 for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text.
        
        Args:
            text: The text to embed.
            
        Returns:
            A list of floats representing the embedding vector.
        """
        return self._hash_text(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts.
        
        Args:
            texts: A list of texts to embed.
            
        Returns:
            A list of embedding vectors, one for each input text.
        """
        return [self._hash_text(text) for text in texts]
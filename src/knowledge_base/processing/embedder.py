"""
Embedder module for the knowledge base system.

This module provides the base interface for text embedders and utility functions.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..core.config import Config
from ..core.types import TextChunk


class Embedder(ABC):
    """Base interface for text embedders.
    
    This abstract class defines the interface that all embedder implementations must follow.
    It provides methods for embedding single texts, batches of texts, and text chunks.
    """
    
    def __init__(self, config: Config):
        """Initialize the embedder with configuration.
        
        Args:
            config: The system configuration.
        """
        self.config = config
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text.
        
        Args:
            text: The text to embed.
            
        Returns:
            A list of floats representing the embedding vector.
        """
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts.
        
        Args:
            texts: A list of texts to embed.
            
        Returns:
            A list of embedding vectors, one for each input text.
        """
        pass
    
    async def embed_chunks(self, chunks: List[TextChunk]) -> None:
        """Embed text chunks in-place.
        
        This method embeds the text of each chunk and updates the embedding field.
        
        Args:
            chunks: A list of text chunks to embed.
        """
        texts = [chunk.text for chunk in chunks]
        embeddings = await self.embed_texts(texts)
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
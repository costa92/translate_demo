"""
DeepSeek embedder implementation.

This module provides an embedder implementation using the DeepSeek API.
"""

import logging
import os
from typing import List, Optional, Dict, Any

from ..embedder import Embedder
from ...core.config import Config
from ...core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class DeepSeekEmbedder(Embedder):
    """Embedder implementation using DeepSeek API.
    
    This class provides text embedding capabilities using DeepSeek's embedding models.
    """
    
    def __init__(self, config: Config):
        """Initialize the DeepSeekEmbedder.
        
        Args:
            config: The system configuration.
            
        Raises:
            ProcessingError: If the DeepSeek library cannot be imported or
                the API key is not set.
        """
        super().__init__(config)
        self.model_name = config.embedding.deepseek_model_name or "deepseek-embedding"
        self.api_key = config.embedding.deepseek_api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.api_base = config.embedding.deepseek_api_base or "https://api.deepseek.com/v1"
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the DeepSeek client.
        
        Raises:
            ProcessingError: If the DeepSeek library cannot be imported or
                the API key is not set.
        """
        try:
            import deepseek
            
            if not self.api_key:
                raise ProcessingError(
                    "DeepSeek API key not found. Please set it in the configuration or "
                    "as the DEEPSEEK_API_KEY environment variable."
                )
            
            self.client = deepseek.Client(
                api_key=self.api_key,
                base_url=self.api_base
            )
            logger.info(f"Initialized DeepSeek client with model: {self.model_name}")
        except ImportError:
            raise ProcessingError(
                "Could not import deepseek. Please install it with 'pip install deepseek'."
            )
        except Exception as e:
            raise ProcessingError(f"Failed to initialize DeepSeek client: {str(e)}")
    
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
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise ProcessingError(f"Failed to embed text with DeepSeek: {str(e)}")
    
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
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            # Sort by index to ensure order is preserved
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]
        except Exception as e:
            raise ProcessingError(f"Failed to embed texts with DeepSeek: {str(e)}")
"""
Text chunking implementation for the unified knowledge base system.

This module provides the base Chunker interface and various chunking strategies.
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any, Type

from ..core.config import Config, ChunkingConfig
from ..core.types import Document, TextChunk
from ..core.exceptions import ProcessingError
from .strategies.base import BaseChunker

logger = logging.getLogger(__name__)


# For backward compatibility
Chunker = TextChunker

class TextChunker:
    """
    Chunker class that provides an interface for text chunking operations.
    It delegates the actual chunking to specific strategy implementations.
    """
    
    # Registry of available chunking strategies
    _strategies: Dict[str, Type[BaseChunker]] = {}
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[BaseChunker]) -> None:
        """
        Register a chunking strategy.
        
        Args:
            name: Name of the strategy
            strategy_class: Strategy class implementation
        """
        cls._strategies[name] = strategy_class
        logger.debug(f"Registered chunking strategy: {name}")
    
    @classmethod
    def get_strategy(cls, name: str) -> Type[BaseChunker]:
        """
        Get a chunking strategy by name.
        
        Args:
            name: Name of the strategy
            
        Returns:
            Strategy class
            
        Raises:
            ProcessingError: If strategy is not found
        """
        if name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ProcessingError(
                f"Chunking strategy '{name}' not found. Available strategies: {available}"
            )
        return cls._strategies[name]
    
    @classmethod
    def list_strategies(cls) -> List[str]:
        """
        List all available chunking strategies.
        
        Returns:
            List of strategy names
        """
        return list(cls._strategies.keys())
    
    def __init__(self, config: Config):
        """
        Initialize chunker with configuration.
        
        Args:
            config: System configuration
        """
        self.config = config
        self._strategy = self._create_strategy()
        logger.info(f"Chunker initialized with strategy: {config.strategy}")
    
    def _create_strategy(self) -> BaseChunker:
        """
        Create a chunking strategy based on configuration.
        
        Returns:
            Chunking strategy instance
        """
        strategy_name = self.config.strategy
        
        try:
            # Import strategies and register them
            from .strategies import register_strategies
            register_strategies()
            
            # Get strategy class
            strategy_class = self.get_strategy(strategy_name)
            
            # Create strategy instance
            return strategy_class(self.config)
            
        except ImportError as e:
            logger.warning(f"Failed to import chunking strategy: {e}")
            # Fall back to default strategy
            from .strategies.recursive import RecursiveChunker
            logger.warning(f"Using fallback RecursiveChunker instead of {strategy_name}")
            return RecursiveChunker(self.config.chunking)
    
    def chunk_text(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into chunks using the configured strategy.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of tuples (chunk_text, start_index, end_index)
        """
        return self._strategy.chunk_text(text)
    
    def chunk_document(self, document: Document) -> List[TextChunk]:
        """
        Chunk a document into text chunks.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of text chunks
        """
        return self._strategy.chunk_document(document)
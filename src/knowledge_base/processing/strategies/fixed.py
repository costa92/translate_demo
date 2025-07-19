"""
Fixed-length chunking strategy implementation.
"""

import logging
from typing import List, Tuple

from ...core.config import ChunkingConfig
from .base import BaseChunker

logger = logging.getLogger(__name__)


class FixedLengthChunker(BaseChunker):
    """
    Fixed-length chunking strategy that splits text into chunks of a fixed size.
    """
    
    def __init__(self, config: ChunkingConfig):
        """Initialize fixed-length chunker with configuration."""
        super().__init__(config)
        logger.debug(f"FixedLengthChunker initialized with chunk_size={config.chunk_size}, "
                    f"chunk_overlap={config.chunk_overlap}")
    
    def chunk_text(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into fixed-size chunks with overlap.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of tuples (chunk_text, start_index, end_index)
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        chunks = []
        start = 0
        
        while start < len(text):
            # Calculate end position
            end = min(start + self.config.chunk_size, len(text))
            
            # If we're not at the beginning and not at the end, try to find a better split point
            if start > 0 and end < len(text) and self.config.respect_sentence_boundary:
                # Look for a good split point (space, period, etc.)
                better_end = self._find_better_split_point(text, end)
                if better_end > 0:
                    end = better_end
            
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunks.append((chunk_text.strip(), start, end))
            
            # Move start position with overlap
            if self.config.chunk_overlap >= end - start:
                # Avoid infinite loop if overlap is too large
                start = end
            else:
                start = end - self.config.chunk_overlap
        
        return chunks
    
    def _find_better_split_point(self, text: str, position: int) -> int:
        """
        Find a better split point near the given position.
        Looks for sentence endings or spaces to avoid splitting in the middle of words or sentences.
        
        Args:
            text: Text to analyze
            position: Target position
            
        Returns:
            Adjusted position for better splitting
        """
        # Define the window to look for better split points
        window = min(50, self.config.chunk_size // 10)
        
        # First, try to find sentence endings
        for i in range(position, max(0, position - window), -1):
            if i < len(text) and text[i-1:i+1] in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                return i + 1
        
        # If no sentence ending found, try to find a space
        for i in range(position, max(0, position - window), -1):
            if i < len(text) and text[i] == ' ':
                return i + 1
        
        # If no good split point found, return the original position
        return position


# Registration will be done in __init__.py
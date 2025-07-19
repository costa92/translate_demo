"""
Recursive chunking strategy implementation.
"""

import logging
from typing import List, Tuple

from ...core.config import ChunkingConfig
from .base import BaseChunker

logger = logging.getLogger(__name__)


class RecursiveChunker(BaseChunker):
    """
    Recursive chunking strategy that tries different separators.
    This is the most flexible approach for chunking text.
    """
    
    def __init__(self, config: ChunkingConfig):
        """Initialize recursive chunker with configuration."""
        super().__init__(config)
        logger.debug(f"RecursiveChunker initialized with chunk_size={config.chunk_size}, "
                    f"chunk_overlap={config.chunk_overlap}")
    
    def chunk_text(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into chunks using recursive chunking.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of tuples (chunk_text, start_index, end_index)
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        chunks = []
        
        def _split_text(text: str, start_offset: int = 0) -> None:
            """
            Recursively split text using different separators.
            
            Args:
                text: Text to split
                start_offset: Starting position in the original text
            """
            if len(text) <= self.config.chunk_size:
                if text.strip():
                    chunks.append((text.strip(), start_offset, start_offset + len(text)))
                return
            
            # Try each separator in order
            for separator in self.config.separators:
                if separator in text:
                    parts = text.split(separator)
                    
                    current_chunk = ""
                    current_start = start_offset
                    
                    for i, part in enumerate(parts):
                        # Add separator back (except for last part)
                        if i > 0:
                            part = separator + part
                        
                        if len(current_chunk + part) <= self.config.chunk_size:
                            current_chunk += part
                        else:
                            # Save current chunk if not empty
                            if current_chunk.strip():
                                chunks.append((
                                    current_chunk.strip(),
                                    current_start,
                                    current_start + len(current_chunk)
                                ))
                            
                            # Start new chunk with overlap
                            if current_chunk and self.config.chunk_overlap > 0:
                                overlap_text = current_chunk[-self.config.chunk_overlap:]
                                current_chunk = overlap_text + part
                                current_start = current_start + len(current_chunk) - len(overlap_text) - len(part)
                            else:
                                current_chunk = part
                                current_start = start_offset + len(text) - len(separator.join(parts[i:]))
                    
                    # Add final chunk
                    if current_chunk.strip():
                        chunks.append((
                            current_chunk.strip(),
                            current_start,
                            current_start + len(current_chunk)
                        ))
                    return
            
            # If no separator worked, force split
            mid = self.config.chunk_size
            chunks.append((text[:mid].strip(), start_offset, start_offset + mid))
            
            # Continue with overlap
            if self.config.chunk_overlap > 0:
                overlap_start = max(0, mid - self.config.chunk_overlap)
                remaining = text[overlap_start:]
                _split_text(remaining, start_offset + overlap_start)
            else:
                remaining = text[mid:]
                _split_text(remaining, start_offset + mid)
        
        _split_text(text)
        return chunks


# Register the strategy will be done in __init__.py
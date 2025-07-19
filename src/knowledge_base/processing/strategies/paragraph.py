"""
Paragraph-based chunking strategy implementation.
"""

import logging
from typing import List, Tuple

from ...core.config import ChunkingConfig
from .base import BaseChunker

logger = logging.getLogger(__name__)


class ParagraphChunker(BaseChunker):
    """
    Paragraph-based chunking strategy that splits text by paragraphs.
    """
    
    def __init__(self, config: ChunkingConfig):
        """Initialize paragraph chunker with configuration."""
        super().__init__(config)
        logger.debug(f"ParagraphChunker initialized with chunk_size={config.chunk_size}, "
                    f"chunk_overlap={config.chunk_overlap}")
    
    def chunk_text(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into chunks by paragraphs.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of tuples (chunk_text, start_index, end_index)
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        
        # Split text into paragraphs (double newlines)
        paragraph_splits = []
        start = 0
        
        # Find all paragraph boundaries
        for i in range(len(text) - 1):
            if text[i:i+2] == '\n\n':
                paragraph_splits.append((start, i + 2))
                start = i + 2
        
        # Add the last paragraph
        if start < len(text):
            paragraph_splits.append((start, len(text)))
        
        # Create paragraphs with positions
        paragraphs = []
        for start, end in paragraph_splits:
            paragraph = text[start:end].strip()
            if paragraph:
                paragraphs.append((paragraph, start, end))
        
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for paragraph, start, end in paragraphs:
            # Check if adding this paragraph would exceed the chunk size
            separator = '\n\n' if current_chunk else ''
            if len(current_chunk + separator + paragraph) <= self.config.chunk_size:
                if not current_chunk:
                    current_start = start
                else:
                    current_chunk += separator
                current_chunk += paragraph
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append((current_chunk, current_start, current_start + len(current_chunk)))
                
                # Start new chunk
                if len(paragraph) > self.config.chunk_size:
                    # If a single paragraph is too large, we need to split it further
                    # Use a recursive approach for this paragraph
                    from .recursive import RecursiveChunker
                    recursive_chunker = RecursiveChunker(self.config)
                    sub_chunks = recursive_chunker.chunk_text(paragraph)
                    for sub_chunk, sub_start, sub_end in sub_chunks:
                        # Adjust positions to be relative to the original text
                        chunks.append((sub_chunk, start + sub_start, start + sub_end))
                else:
                    current_chunk = paragraph
                    current_start = start
        
        # Add final chunk
        if current_chunk:
            chunks.append((current_chunk, current_start, current_start + len(current_chunk)))
        
        return chunks


# Registration will be done in __init__.py
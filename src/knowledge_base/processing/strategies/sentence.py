"""
Sentence-based chunking strategy implementation.
"""

import re
import logging
from typing import List, Tuple

from ...core.config import ChunkingConfig
from .base import BaseChunker

logger = logging.getLogger(__name__)


class SentenceChunker(BaseChunker):
    """
    Sentence-based chunking strategy that splits text by sentences.
    """
    
    def __init__(self, config: ChunkingConfig):
        """Initialize sentence chunker with configuration."""
        super().__init__(config)
        
        # Compile regex patterns for sentence splitting
        self._sentence_patterns = [
            re.compile(r'[.!?]+\s+'),  # English sentence endings
            re.compile(r'[。！？]+\s*'),  # Chinese sentence endings
        ]
        
        logger.debug(f"SentenceChunker initialized with chunk_size={config.chunk_size}, "
                    f"chunk_overlap={config.chunk_overlap}")
    
    def chunk_text(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into chunks by sentences.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of tuples (chunk_text, start_index, end_index)
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for sentence, start, end in sentences:
            if len(current_chunk + sentence) <= self.config.chunk_size:
                if not current_chunk:
                    current_start = start
                current_chunk += sentence
            else:
                # Save current chunk
                if current_chunk.strip():
                    chunks.append((current_chunk.strip(), current_start, current_start + len(current_chunk)))
                
                # Start new chunk with potential overlap
                if self.config.chunk_overlap > 0 and current_chunk:
                    # Find a good overlap point (try to include complete sentences)
                    overlap_text = self._find_sentence_overlap(current_chunk)
                    current_chunk = overlap_text + sentence
                    current_start = end - len(sentence) - len(overlap_text)
                else:
                    current_chunk = sentence
                    current_start = start
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append((current_chunk.strip(), current_start, current_start + len(current_chunk)))
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into sentences with position tracking.
        
        Args:
            text: Text to split
            
        Returns:
            List of tuples (sentence, start_index, end_index)
        """
        sentences = []
        
        # Try each sentence pattern
        for pattern in self._sentence_patterns:
            matches = list(pattern.finditer(text))
            if matches:
                last_end = 0
                
                for match in matches:
                    sentence_end = match.end()
                    sentence = text[last_end:sentence_end]
                    
                    if sentence.strip():
                        sentences.append((sentence, last_end, sentence_end))
                    
                    last_end = sentence_end
                
                # Add remaining text
                if last_end < len(text):
                    remaining = text[last_end:]
                    if remaining.strip():
                        sentences.append((remaining, last_end, len(text)))
                
                break
        
        # If no sentence patterns matched, return whole text
        if not sentences and text.strip():
            sentences.append((text, 0, len(text)))
        
        return sentences
    
    def _find_sentence_overlap(self, text: str) -> str:
        """
        Find a good overlap point that respects sentence boundaries.
        
        Args:
            text: Text to find overlap in
            
        Returns:
            Overlap text
        """
        if len(text) <= self.config.chunk_overlap:
            return text
        
        # Start from the desired overlap point
        overlap_start = len(text) - self.config.chunk_overlap
        
        # Try to find a sentence boundary near the overlap point
        for pattern in self._sentence_patterns:
            # Look for sentence endings in the vicinity of the overlap point
            search_area = text[max(0, overlap_start - 100):overlap_start + 100]
            matches = list(pattern.finditer(search_area))
            
            if matches:
                # Find the closest match to the overlap point
                closest_match = min(matches, key=lambda m: abs(overlap_start - (m.start() + max(0, overlap_start - 100))))
                adjusted_start = max(0, overlap_start - 100) + closest_match.end()
                
                # If the adjusted start is too far from the desired overlap, use the original
                if abs(adjusted_start - overlap_start) > self.config.chunk_overlap / 2:
                    return text[overlap_start:]
                
                return text[adjusted_start:]
        
        # If no good sentence boundary found, use the original overlap point
        return text[overlap_start:]


# Registration will be done in __init__.py
"""Text chunking implementation."""

import re
import logging
from typing import List, Tuple
from ..core.config import ChunkingConfig

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Text chunker that splits documents into smaller, manageable chunks.
    Supports multiple chunking strategies.
    """
    
    def __init__(self, config: ChunkingConfig):
        """Initialize text chunker with configuration."""
        self.config = config
        
        # Compile regex patterns for sentence splitting
        self._sentence_patterns = [
            re.compile(r'[.!?]+\s+'),  # English sentence endings
            re.compile(r'[。！？]+\s*'),  # Chinese sentence endings
        ]
        
        logger.info(f"TextChunker initialized with strategy: {config.strategy}")
    
    def chunk_text(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into chunks.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of tuples (chunk_text, start_index, end_index)
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        
        if self.config.strategy == "recursive":
            return self._recursive_chunk(text)
        elif self.config.strategy == "sentence":
            return self._sentence_chunk(text)
        elif self.config.strategy == "paragraph":
            return self._paragraph_chunk(text)
        elif self.config.strategy == "fixed":
            return self._fixed_chunk(text)
        else:
            logger.warning(f"Unknown chunking strategy: {self.config.strategy}, using recursive")
            return self._recursive_chunk(text)
    
    def _recursive_chunk(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Recursive chunking that tries different separators.
        This is the most flexible approach.
        """
        chunks = []
        
        def _split_text(text: str, start_offset: int = 0) -> None:
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
    
    def _sentence_chunk(self, text: str) -> List[Tuple[str, int, int]]:
        """Chunk text by sentences."""
        # Split into sentences
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for sentence, start, end in sentences:
            if len(current_chunk + sentence) <= self.config.chunk_size:
                current_chunk += sentence
            else:
                # Save current chunk
                if current_chunk.strip():
                    chunks.append((current_chunk.strip(), current_start, current_start + len(current_chunk)))
                
                # Start new chunk with potential overlap
                if self.config.chunk_overlap > 0 and current_chunk:
                    overlap = current_chunk[-self.config.chunk_overlap:]
                    current_chunk = overlap + sentence
                    current_start = end - len(sentence) - len(overlap)
                else:
                    current_chunk = sentence
                    current_start = start
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append((current_chunk.strip(), current_start, current_start + len(current_chunk)))
        
        return chunks
    
    def _paragraph_chunk(self, text: str) -> List[Tuple[str, int, int]]:
        """Chunk text by paragraphs."""
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            if len(current_chunk + '\n\n' + paragraph) <= self.config.chunk_size:
                if current_chunk:
                    current_chunk += '\n\n' + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append((current_chunk, current_start, current_start + len(current_chunk)))
                
                # Start new chunk
                current_chunk = paragraph
                current_start = text.find(paragraph, current_start + len(current_chunk) if current_chunk else 0)
        
        # Add final chunk
        if current_chunk:
            chunks.append((current_chunk, current_start, current_start + len(current_chunk)))
        
        return chunks
    
    def _fixed_chunk(self, text: str) -> List[Tuple[str, int, int]]:
        """Fixed-size chunking with overlap."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.config.chunk_size, len(text))
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunks.append((chunk_text.strip(), start, end))
            
            # Move start position with overlap
            start = end - self.config.chunk_overlap
            if start >= end:  # Prevent infinite loop
                break
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        """Split text into sentences with position tracking."""
        sentences = []
        current_pos = 0
        
        # Try each sentence pattern
        for pattern in self._sentence_patterns:
            matches = list(pattern.finditer(text))
            if matches:
                last_end = 0
                
                for match in matches:
                    sentence_end = match.end()
                    sentence = text[last_end:sentence_end].strip()
                    
                    if sentence:
                        sentences.append((sentence, last_end, sentence_end))
                    
                    last_end = sentence_end
                
                # Add remaining text
                if last_end < len(text):
                    remaining = text[last_end:].strip()
                    if remaining:
                        sentences.append((remaining, last_end, len(text)))
                
                break
        
        # If no sentence patterns matched, return whole text
        if not sentences and text.strip():
            sentences.append((text.strip(), 0, len(text)))
        
        return sentences
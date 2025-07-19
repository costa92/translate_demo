"""
Base classes for document processing strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple

from ...core.config import ChunkingConfig
from ...core.types import Document, TextChunk


class BaseChunker(ABC):
    """
    Base interface for text chunking strategies.
    """
    
    def __init__(self, config: ChunkingConfig):
        """Initialize chunker with configuration."""
        self.config = config
    
    @abstractmethod
    def chunk_text(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into chunks.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of tuples (chunk_text, start_index, end_index)
        """
        pass
    
    def chunk_document(self, document: Document) -> List[TextChunk]:
        """
        Chunk a document into text chunks.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of text chunks
        """
        text_chunks = self.chunk_text(document.content)
        
        chunks = []
        for i, (text, start_idx, end_idx) in enumerate(text_chunks):
            chunk_id = f"{document.id}_chunk_{i}"
            
            chunk = TextChunk(
                id=chunk_id,
                text=text,
                document_id=document.id,
                start_index=start_idx,
                end_index=end_idx,
                metadata={
                    **document.metadata,
                    "chunk_index": i,
                    "chunk_count": len(text_chunks),
                    "document_type": document.type.value,
                    "source": document.source
                }
            )
            chunks.append(chunk)
        
        return chunks
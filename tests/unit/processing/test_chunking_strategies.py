"""
Tests for the chunking strategies in the processing module.
"""

import pytest
from typing import Dict, Any

from src.knowledge_base.core.types import Document, DocumentType
from src.knowledge_base.processing.chunker import Chunker
from src.knowledge_base.processing.strategies.recursive import RecursiveChunker
from src.knowledge_base.processing.strategies.sentence import SentenceChunker
from src.knowledge_base.processing.strategies.paragraph import ParagraphChunker
from src.knowledge_base.processing.strategies.fixed import FixedLengthChunker


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Create a test configuration."""
    return {
        "chunking": {
            "strategy": "recursive",
            "chunk_size": 100,
            "chunk_overlap": 20,
            "separators": ["\n\n", "\n", " ", ""]
        }
    }


@pytest.fixture
def test_document() -> Document:
    """Create a test document."""
    return Document(
        id="test_doc",
        content="""This is a test document with multiple paragraphs.

This is the second paragraph with some content.
This is still part of the second paragraph.

This is the third paragraph.
It has multiple sentences.
And continues for a while.

This is the final paragraph of the document.""",
        type=DocumentType.TEXT,
        metadata={"source": "test"}
    )


@pytest.fixture
def long_document() -> Document:
    """Create a longer test document."""
    # Create a document with repeated content to ensure it's long enough
    content = "This is a sentence. " * 100
    return Document(
        id="long_doc",
        content=content,
        type=DocumentType.TEXT,
        metadata={"source": "test"}
    )


class TestRecursiveChunker:
    """Tests for the RecursiveChunker class."""
    
    def test_initialization(self, test_config):
        """Test that the chunker initializes correctly."""
        chunker = RecursiveChunker(test_config)
        
        assert chunker.chunk_size == test_config["chunking"]["chunk_size"]
        assert chunker.chunk_overlap == test_config["chunking"]["chunk_overlap"]
        assert chunker.separators == test_config["chunking"]["separators"]
    
    def test_chunk_document(self, test_config, test_document):
        """Test chunking a document."""
        chunker = RecursiveChunker(test_config)
        
        chunks = chunker.chunk(test_document)
        
        # Verify chunks were created
        assert len(chunks) > 0
        
        # Verify chunk properties
        for chunk in chunks:
            assert chunk.document_id == test_document.id
            assert chunk.id.startswith(test_document.id)
            assert len(chunk.text) <= test_config["chunking"]["chunk_size"] + 10  # Allow small margin for edge cases
            assert chunk.metadata["source"] == test_document.metadata["source"]
            assert "chunk_index" in chunk.metadata
    
    def test_chunk_overlap(self, test_config, long_document):
        """Test that chunks have proper overlap."""
        chunker = RecursiveChunker(test_config)
        
        chunks = chunker.chunk(long_document)
        
        # Verify multiple chunks were created
        assert len(chunks) > 1
        
        # Check for overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i].text
            next_chunk = chunks[i + 1].text
            
            # The end of the current chunk should match the beginning of the next chunk
            overlap_size = min(test_config["chunking"]["chunk_overlap"], len(current_chunk), len(next_chunk))
            if overlap_size > 0:
                assert current_chunk[-overlap_size:] == next_chunk[:overlap_size] or \
                       current_chunk[-overlap_size:].strip() == next_chunk[:overlap_size].strip()


class TestSentenceChunker:
    """Tests for the SentenceChunker class."""
    
    def test_initialization(self, test_config):
        """Test that the chunker initializes correctly."""
        chunker = SentenceChunker(test_config)
        
        assert chunker.chunk_size == test_config["chunking"]["chunk_size"]
        assert chunker.chunk_overlap == test_config["chunking"]["chunk_overlap"]
    
    def test_chunk_document(self, test_config, test_document):
        """Test chunking a document by sentences."""
        chunker = SentenceChunker(test_config)
        
        chunks = chunker.chunk(test_document)
        
        # Verify chunks were created
        assert len(chunks) > 0
        
        # Verify chunk properties
        for chunk in chunks:
            assert chunk.document_id == test_document.id
            assert chunk.id.startswith(test_document.id)
            assert chunk.metadata["source"] == test_document.metadata["source"]
            assert "chunk_index" in chunk.metadata
        
        # Verify sentences are preserved
        all_text = " ".join([chunk.text for chunk in chunks])
        for sentence in [
            "This is a test document with multiple paragraphs.",
            "This is the second paragraph with some content.",
            "This is the third paragraph.",
            "It has multiple sentences.",
            "This is the final paragraph of the document."
        ]:
            assert sentence in all_text


class TestParagraphChunker:
    """Tests for the ParagraphChunker class."""
    
    def test_initialization(self, test_config):
        """Test that the chunker initializes correctly."""
        chunker = ParagraphChunker(test_config)
        
        assert chunker.max_paragraph_length == test_config["chunking"]["chunk_size"]
    
    def test_chunk_document(self, test_config, test_document):
        """Test chunking a document by paragraphs."""
        chunker = ParagraphChunker(test_config)
        
        chunks = chunker.chunk(test_document)
        
        # Verify chunks were created
        assert len(chunks) == 4  # 4 paragraphs in the test document
        
        # Verify chunk properties
        for chunk in chunks:
            assert chunk.document_id == test_document.id
            assert chunk.id.startswith(test_document.id)
            assert chunk.metadata["source"] == test_document.metadata["source"]
            assert "chunk_index" in chunk.metadata
        
        # Verify paragraphs are preserved
        assert "This is a test document with multiple paragraphs." in chunks[0].text
        assert "This is the second paragraph with some content." in chunks[1].text
        assert "This is the third paragraph." in chunks[2].text
        assert "This is the final paragraph of the document." in chunks[3].text


class TestFixedLengthChunker:
    """Tests for the FixedLengthChunker class."""
    
    def test_initialization(self, test_config):
        """Test that the chunker initializes correctly."""
        chunker = FixedLengthChunker(test_config)
        
        assert chunker.chunk_size == test_config["chunking"]["chunk_size"]
        assert chunker.chunk_overlap == test_config["chunking"]["chunk_overlap"]
    
    def test_chunk_document(self, test_config, long_document):
        """Test chunking a document with fixed length."""
        chunker = FixedLengthChunker(test_config)
        
        chunks = chunker.chunk(long_document)
        
        # Verify chunks were created
        assert len(chunks) > 1
        
        # Verify chunk properties
        for chunk in chunks:
            assert chunk.document_id == long_document.id
            assert chunk.id.startswith(long_document.id)
            assert len(chunk.text) <= test_config["chunking"]["chunk_size"]
            assert chunk.metadata["source"] == long_document.metadata["source"]
            assert "chunk_index" in chunk.metadata
    
    def test_chunk_overlap(self, test_config, long_document):
        """Test that chunks have proper overlap."""
        chunker = FixedLengthChunker(test_config)
        
        chunks = chunker.chunk(long_document)
        
        # Verify multiple chunks were created
        assert len(chunks) > 1
        
        # Check for overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i].text
            next_chunk = chunks[i + 1].text
            
            # The end of the current chunk should match the beginning of the next chunk
            overlap_size = min(test_config["chunking"]["chunk_overlap"], len(current_chunk), len(next_chunk))
            if overlap_size > 0:
                assert current_chunk[-overlap_size:] == next_chunk[:overlap_size]
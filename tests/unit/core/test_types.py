"""
Unit tests for the core type definitions.
"""

import pytest
from datetime import datetime
from src.knowledge_base.core.types import (
    DocumentType, ProcessingStatus, Document, TextChunk, 
    RetrievalResult, QueryResult, AddResult, SearchQuery,
    EmbeddingResult, ChunkingResult, ProcessingResult, GenerationResult
)


def test_document_type_enum():
    """Test the DocumentType enum."""
    assert DocumentType.TEXT.value == "text"
    assert DocumentType.PDF.value == "pdf"
    assert DocumentType.MARKDOWN.value == "markdown"
    assert DocumentType.URL.value == "url"
    assert DocumentType.UNKNOWN.value == "unknown"


def test_processing_status_enum():
    """Test the ProcessingStatus enum."""
    assert ProcessingStatus.PENDING.value == "pending"
    assert ProcessingStatus.PROCESSING.value == "processing"
    assert ProcessingStatus.COMPLETED.value == "completed"
    assert ProcessingStatus.FAILED.value == "failed"


def test_document_creation():
    """Test Document creation and properties."""
    doc = Document(
        id="doc1",
        content="This is a test document",
        type=DocumentType.TEXT,
        metadata={"author": "Test User", "tags": ["test", "document"]},
        source="test.txt"
    )
    
    assert doc.id == "doc1"
    assert doc.content == "This is a test document"
    assert doc.type == DocumentType.TEXT
    assert doc.metadata["author"] == "Test User"
    assert "tags" in doc.metadata
    assert doc.source == "test.txt"
    assert isinstance(doc.created_at, datetime)


def test_document_string_type_conversion():
    """Test Document creation with string type."""
    doc = Document(
        id="doc1",
        content="This is a test document",
        type="pdf",
        metadata={"author": "Test User"}
    )
    
    assert doc.type == DocumentType.PDF
    
    # Test with invalid type
    doc = Document(
        id="doc2",
        content="This is another test document",
        type="invalid_type"
    )
    
    assert doc.type == DocumentType.UNKNOWN


def test_text_chunk_creation():
    """Test TextChunk creation and properties."""
    chunk = TextChunk(
        id="chunk1",
        text="This is a test chunk",
        document_id="doc1",
        metadata={"position": 1},
        embedding=[0.1, 0.2, 0.3],
        start_index=0,
        end_index=19
    )
    
    assert chunk.id == "chunk1"
    assert chunk.text == "This is a test chunk"
    assert chunk.document_id == "doc1"
    assert chunk.metadata["position"] == 1
    assert chunk.embedding == [0.1, 0.2, 0.3]
    assert chunk.start_index == 0
    assert chunk.end_index == 19
    assert chunk.length == 20


def test_retrieval_result_creation():
    """Test RetrievalResult creation and properties."""
    chunk = TextChunk(
        id="chunk1",
        text="This is a test chunk",
        document_id="doc1",
        metadata={"position": 1}
    )
    
    result = RetrievalResult(
        chunk=chunk,
        score=0.85,
        rank=1
    )
    
    assert result.chunk == chunk
    assert result.score == 0.85
    assert result.rank == 1
    assert result.text == "This is a test chunk"
    assert result.metadata["position"] == 1


def test_query_result_creation():
    """Test QueryResult creation and properties."""
    chunk1 = TextChunk(
        id="chunk1",
        text="This is the first test chunk",
        document_id="doc1"
    )
    
    chunk2 = TextChunk(
        id="chunk2",
        text="This is the second test chunk",
        document_id="doc1"
    )
    
    source1 = RetrievalResult(chunk=chunk1, score=0.9, rank=1)
    source2 = RetrievalResult(chunk=chunk2, score=0.8, rank=2)
    
    result = QueryResult(
        query="test query",
        answer="This is the answer",
        sources=[source1, source2],
        confidence=0.85,
        processing_time=0.25,
        metadata={"model": "test-model"}
    )
    
    assert result.query == "test query"
    assert result.answer == "This is the answer"
    assert len(result.sources) == 2
    assert result.sources[0].score == 0.9
    assert result.confidence == 0.85
    assert result.processing_time == 0.25
    assert result.metadata["model"] == "test-model"
    assert result.source_count == 2
    assert len(result.chunks) == 2
    assert result.chunks[0].id == "chunk1"


def test_add_result_creation():
    """Test AddResult creation and properties."""
    result = AddResult(
        document_id="doc1",
        status=ProcessingStatus.COMPLETED,
        chunk_ids=["chunk1", "chunk2", "chunk3"],
        processing_time=0.5,
        metadata={"source": "test"}
    )
    
    assert result.document_id == "doc1"
    assert result.status == ProcessingStatus.COMPLETED
    assert len(result.chunk_ids) == 3
    assert result.chunks_created == 3
    assert result.processing_time == 0.5
    assert result.metadata["source"] == "test"
    assert result.success is True
    
    # Test with failed status
    failed_result = AddResult(
        document_id="doc2",
        status=ProcessingStatus.FAILED,
        error_message="Processing failed"
    )
    
    assert failed_result.success is False
    assert failed_result.error_message == "Processing failed"


def test_search_query_creation():
    """Test SearchQuery creation."""
    query = SearchQuery(
        text="test query",
        filters={"category": "test"},
        top_k=10,
        min_score=0.5,
        include_metadata=True
    )
    
    assert query.text == "test query"
    assert query.filters["category"] == "test"
    assert query.top_k == 10
    assert query.min_score == 0.5
    assert query.include_metadata is True


def test_embedding_result_creation():
    """Test EmbeddingResult creation and properties."""
    result = EmbeddingResult(
        text="test text",
        embedding=[0.1, 0.2, 0.3, 0.4],
        model="test-model"
    )
    
    assert result.text == "test text"
    assert result.embedding == [0.1, 0.2, 0.3, 0.4]
    assert result.model == "test-model"
    assert result.dimensions == 4


def test_chunking_result_creation():
    """Test ChunkingResult creation."""
    chunk1 = TextChunk(id="chunk1", text="First chunk", document_id="doc1")
    chunk2 = TextChunk(id="chunk2", text="Second chunk", document_id="doc1")
    
    result = ChunkingResult(
        document_id="doc1",
        chunks=[chunk1, chunk2],
        metadata={"strategy": "paragraph"}
    )
    
    assert result.document_id == "doc1"
    assert len(result.chunks) == 2
    assert result.metadata["strategy"] == "paragraph"


def test_processing_result_creation():
    """Test ProcessingResult creation."""
    chunk1 = TextChunk(id="chunk1", text="First chunk", document_id="doc1")
    chunk2 = TextChunk(id="chunk2", text="Second chunk", document_id="doc1")
    
    chunking_result = ChunkingResult(
        document_id="doc1",
        chunks=[chunk1, chunk2]
    )
    
    embedding_result1 = EmbeddingResult(
        text="First chunk",
        embedding=[0.1, 0.2, 0.3]
    )
    
    embedding_result2 = EmbeddingResult(
        text="Second chunk",
        embedding=[0.4, 0.5, 0.6]
    )
    
    result = ProcessingResult(
        document_id="doc1",
        chunking_result=chunking_result,
        embedding_results=[embedding_result1, embedding_result2],
        metadata={"processing_time": 0.5}
    )
    
    assert result.document_id == "doc1"
    assert result.chunking_result == chunking_result
    assert len(result.embedding_results) == 2
    assert result.metadata["processing_time"] == 0.5


def test_generation_result_creation():
    """Test GenerationResult creation."""
    result = GenerationResult(
        prompt="Generate a response",
        content="This is the generated response",
        metadata={"model": "test-model", "temperature": 0.7}
    )
    
    assert result.prompt == "Generate a response"
    assert result.content == "This is the generated response"
    assert result.metadata["model"] == "test-model"
    assert result.metadata["temperature"] == 0.7
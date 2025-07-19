"""
Integration tests for metadata extraction.

This module tests the integration between document processing and metadata extraction.
"""

import pytest
import asyncio
from typing import Dict, Any, List

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import Document
from src.knowledge_base.processing.processor import DocumentProcessor
from src.knowledge_base.processing.metadata_extractor import MetadataExtractor


@pytest.fixture
def processing_config():
    """Create a configuration for processing testing."""
    config_dict = {
        "system": {
            "debug": True,
            "log_level": "DEBUG"
        },
        "chunking": {
            "strategy": "recursive",
            "chunk_size": 100,
            "chunk_overlap": 20,
            "separators": ["\n\n", "\n", " ", ""]
        },
        "embedding": {
            "provider": "sentence_transformers",
            "model_name": "all-MiniLM-L6-v2",
            "cache_enabled": True
        },
        "processing": {
            "extract_metadata": True,
            "metadata_fields": ["title", "summary", "keywords", "language"],
            "use_llm_for_metadata": False
        }
    }
    return Config.from_dict(config_dict)


@pytest.fixture
def document_processor(processing_config):
    """Create a document processor for testing."""
    return DocumentProcessor(processing_config)


@pytest.fixture
def metadata_extractor(processing_config):
    """Create a metadata extractor for testing."""
    return MetadataExtractor(processing_config)


@pytest.fixture
def test_documents():
    """Create test documents with different content types."""
    return [
        Document(
            id="doc1",
            content="# Python Programming Guide\n\nPython is a high-level, interpreted programming language. "
                   "It was created by Guido van Rossum and first released in 1991. "
                   "Python's design philosophy emphasizes code readability with its "
                   "notable use of significant whitespace.",
            type="markdown",
            metadata={"source": "test"}
        ),
        Document(
            id="doc2",
            content="JavaScript Tutorial\n\nJavaScript is a programming language that conforms to the ECMAScript specification. "
                   "JavaScript is high-level, often just-in-time compiled, and multi-paradigm. "
                   "It has curly-bracket syntax, dynamic typing, prototype-based object-orientation, "
                   "and first-class functions.",
            type="text",
            metadata={"source": "test"}
        ),
        Document(
            id="doc3",
            content="<html><head><title>Machine Learning Overview</title></head><body>"
                   "<h1>Machine Learning</h1><p>Machine learning is a subset of artificial intelligence that provides systems "
                   "the ability to automatically learn and improve from experience without being "
                   "explicitly programmed. Machine learning focuses on the development of computer "
                   "programs that can access data and use it to learn for themselves.</p></body></html>",
            type="html",
            metadata={"source": "test"}
        )
    ]


@pytest.mark.asyncio
async def test_metadata_extraction_during_processing(document_processor, test_documents):
    """Test that metadata is properly extracted during document processing."""
    for document in test_documents:
        # Process the document
        chunks = await document_processor.process_document(document)
        
        # Check that chunks were created
        assert len(chunks) > 0, f"Document {document.id} should produce at least one chunk"
        
        # Check that each chunk has metadata
        for chunk in chunks:
            assert "source" in chunk.metadata, "Chunk should inherit source metadata"
            assert chunk.metadata["source"] == "test"
            
            # Check document-specific metadata
            assert "document_id" in chunk.metadata, "Chunk should have document_id metadata"
            assert chunk.metadata["document_id"] == document.id
            
            # Check chunk-specific metadata
            assert "chunk_index" in chunk.metadata, "Chunk should have chunk_index metadata"
            assert isinstance(chunk.metadata["chunk_index"], int)
            
            # Check content type metadata
            assert "content_type" in chunk.metadata, "Chunk should have content_type metadata"
            assert chunk.metadata["content_type"] == document.type


@pytest.mark.asyncio
async def test_standalone_metadata_extraction(metadata_extractor, test_documents):
    """Test standalone metadata extraction functionality."""
    for document in test_documents:
        # Extract metadata
        metadata = await metadata_extractor.extract_metadata(document)
        
        # Check basic metadata
        assert "content_type" in metadata, "Metadata should include content_type"
        assert metadata["content_type"] == document.type
        
        # Check document-specific metadata based on content type
        if document.type == "markdown":
            assert "title" in metadata, "Markdown document should have title metadata"
            assert "Python" in metadata["title"], "Title should be extracted from markdown heading"
            
        elif document.type == "html":
            assert "title" in metadata, "HTML document should have title metadata"
            assert "Machine Learning" in metadata["title"], "Title should be extracted from HTML title tag"
            
        # Check for extracted keywords
        if "keywords" in metadata:
            if document.id == "doc1":
                assert "Python" in metadata["keywords"], "Keywords should include 'Python'"
            elif document.id == "doc2":
                assert "JavaScript" in metadata["keywords"], "Keywords should include 'JavaScript'"
            elif document.id == "doc3":
                assert "Machine Learning" in metadata["keywords"] or "AI" in metadata["keywords"], \
                    "Keywords should include 'Machine Learning' or 'AI'"


@pytest.mark.asyncio
async def test_metadata_based_filtering(document_processor, test_documents):
    """Test that extracted metadata can be used for filtering."""
    processed_chunks = []
    
    # Process all documents
    for document in test_documents:
        chunks = await document_processor.process_document(document)
        processed_chunks.extend(chunks)
    
    # Filter chunks by content type
    markdown_chunks = [chunk for chunk in processed_chunks if chunk.metadata.get("content_type") == "markdown"]
    html_chunks = [chunk for chunk in processed_chunks if chunk.metadata.get("content_type") == "html"]
    text_chunks = [chunk for chunk in processed_chunks if chunk.metadata.get("content_type") == "text"]
    
    # Check filtering results
    assert len(markdown_chunks) > 0, "Should have markdown chunks"
    assert len(html_chunks) > 0, "Should have HTML chunks"
    assert len(text_chunks) > 0, "Should have text chunks"
    
    # Check document-specific filtering
    doc1_chunks = [chunk for chunk in processed_chunks if chunk.metadata.get("document_id") == "doc1"]
    doc2_chunks = [chunk for chunk in processed_chunks if chunk.metadata.get("document_id") == "doc2"]
    doc3_chunks = [chunk for chunk in processed_chunks if chunk.metadata.get("document_id") == "doc3"]
    
    assert len(doc1_chunks) > 0, "Should have chunks from document 1"
    assert len(doc2_chunks) > 0, "Should have chunks from document 2"
    assert len(doc3_chunks) > 0, "Should have chunks from document 3"
    
    # Verify content type matches document type
    assert all(chunk.metadata.get("content_type") == "markdown" for chunk in doc1_chunks)
    assert all(chunk.metadata.get("content_type") == "text" for chunk in doc2_chunks)
    assert all(chunk.metadata.get("content_type") == "html" for chunk in doc3_chunks)


@pytest.mark.asyncio
async def test_metadata_enrichment(processing_config, document_processor, test_documents):
    """Test metadata enrichment during processing."""
    # Enable LLM-based metadata extraction
    processing_config.processing.use_llm_for_metadata = True
    
    # Use a simple LLM provider for testing
    processing_config.generation.provider = "simple"
    
    for document in test_documents:
        # Process the document
        chunks = await document_processor.process_document(document)
        
        # Check that chunks were created
        assert len(chunks) > 0, f"Document {document.id} should produce at least one chunk"
        
        # Check for enriched metadata (may not be present in all testing environments)
        # This is a soft check since it depends on LLM availability
        for chunk in chunks:
            if "summary" in chunk.metadata:
                assert len(chunk.metadata["summary"]) > 0, "Summary should not be empty if present"
            
            if "keywords" in chunk.metadata:
                assert isinstance(chunk.metadata["keywords"], (list, str)), \
                    "Keywords should be a list or string if present"
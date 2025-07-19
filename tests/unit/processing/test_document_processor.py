"""
Unit tests for the document processor.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import Document, DocumentType, TextChunk
from src.knowledge_base.processing.processor import DocumentProcessor


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config()


@pytest.fixture
def processor(config):
    """Create a document processor with mocked components."""
    processor = DocumentProcessor(config)
    processor._chunker = MagicMock()
    processor._embedder = AsyncMock()
    processor._initialized = True
    return processor


class TestDocumentProcessor:
    """Tests for the DocumentProcessor class."""

    def test_init(self, config):
        """Test initialization."""
        processor = DocumentProcessor(config)
        assert processor.config == config
        assert not processor._initialized

    def test_detect_document_type_from_filename(self, processor):
        """Test document type detection from filename."""
        # Test various file extensions
        assert processor.detect_document_type("content", "document.txt") == DocumentType.TEXT
        assert processor.detect_document_type("content", "document.md") == DocumentType.MARKDOWN
        assert processor.detect_document_type("content", "document.html") == DocumentType.HTML
        assert processor.detect_document_type("content", "document.pdf") == DocumentType.PDF
        assert processor.detect_document_type("content", "document.docx") == DocumentType.DOCX
        assert processor.detect_document_type("content", "image.jpg") == DocumentType.IMAGE
        assert processor.detect_document_type("content", "audio.mp3") == DocumentType.AUDIO
        assert processor.detect_document_type("content", "video.mp4") == DocumentType.VIDEO
        assert processor.detect_document_type("content", "code.py") == DocumentType.CODE

    def test_detect_document_type_from_mime_type(self, processor):
        """Test document type detection from MIME type."""
        assert processor.detect_document_type("content", mime_type="text/plain") == DocumentType.TEXT
        assert processor.detect_document_type("content", mime_type="text/markdown") == DocumentType.MARKDOWN
        assert processor.detect_document_type("content", mime_type="text/html") == DocumentType.HTML
        assert processor.detect_document_type("content", mime_type="application/pdf") == DocumentType.PDF
        assert processor.detect_document_type("content", mime_type="application/msword") == DocumentType.DOCX
        assert processor.detect_document_type("content", mime_type="image/jpeg") == DocumentType.IMAGE
        assert processor.detect_document_type("content", mime_type="audio/mpeg") == DocumentType.AUDIO
        assert processor.detect_document_type("content", mime_type="video/mp4") == DocumentType.VIDEO
        assert processor.detect_document_type("content", mime_type="application/json") == DocumentType.CODE

    def test_detect_document_type_from_content(self, processor):
        """Test document type detection from content."""
        html_content = "<!DOCTYPE html><html><body>Test</body></html>"
        assert processor.detect_document_type(html_content) == DocumentType.HTML

        markdown_content = "# Heading\n\nThis is **markdown**."
        assert processor.detect_document_type(markdown_content) == DocumentType.MARKDOWN

        python_code = "import os\n\ndef main():\n    print('Hello')"
        assert processor.detect_document_type(python_code) == DocumentType.CODE

        plain_text = "This is just plain text."
        assert processor.detect_document_type(plain_text) == DocumentType.TEXT

    def test_markdown_to_text(self, processor):
        """Test Markdown to text conversion."""
        markdown = "# Heading\n\nThis is **bold** and *italic*.\n\n```python\nprint('code')\n```"
        text = processor._markdown_to_text(markdown)
        
        assert "# " not in text
        assert "**" not in text
        assert "*" not in text
        assert "```" not in text
        assert "Heading" in text
        assert "bold" in text
        assert "italic" in text

    def test_html_to_text(self, processor):
        """Test HTML to text conversion."""
        html = "<h1>Heading</h1><p>This is <strong>bold</strong> and <em>italic</em>.</p>"
        text = processor._html_to_text(html)
        
        assert "<" not in text
        assert ">" not in text
        assert "Heading" in text
        assert "bold" in text
        assert "italic" in text

    def test_html_to_markdown(self, processor):
        """Test HTML to Markdown conversion."""
        html = "<h1>Heading</h1><p>This is <strong>bold</strong> and <em>italic</em>.</p>"
        markdown = processor._html_to_markdown(html)
        
        assert "# Heading" in markdown
        assert "**bold**" in markdown
        assert "*italic*" in markdown

    def test_convert_document_format(self, processor):
        """Test document format conversion."""
        # Test Markdown to Text conversion
        markdown_doc = Document(
            id="doc1",
            content="# Heading\n\nThis is **markdown**.",
            type=DocumentType.MARKDOWN
        )
        text_doc = processor.convert_document_format(markdown_doc, DocumentType.TEXT)
        
        assert text_doc.id == markdown_doc.id
        assert text_doc.type == DocumentType.TEXT
        assert "# " not in text_doc.content
        assert "**" not in text_doc.content
        assert "Heading" in text_doc.content
        assert "markdown" in text_doc.content

        # Test HTML to Text conversion
        html_doc = Document(
            id="doc2",
            content="<h1>Heading</h1><p>This is HTML.</p>",
            type=DocumentType.HTML
        )
        text_doc = processor.convert_document_format(html_doc, DocumentType.TEXT)
        
        assert text_doc.id == html_doc.id
        assert text_doc.type == DocumentType.TEXT
        assert "<" not in text_doc.content
        assert ">" not in text_doc.content
        assert "Heading" in text_doc.content
        assert "This is HTML." in text_doc.content

    @pytest.mark.asyncio
    async def test_process_document(self, processor):
        """Test document processing."""
        # Setup mocks
        document = Document(
            id="test_doc",
            content="This is a test document.",
            type=DocumentType.TEXT
        )
        
        # Mock chunker to return some text chunks
        processor._chunker.chunk_text.return_value = [
            ("Chunk 1", 0, 7),
            ("Chunk 2", 8, 15)
        ]
        
        # Mock embedder to return embeddings
        processor._embedder.embed_batch.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        
        # Process document
        result = await processor.process_document(document)
        
        # Verify result
        assert result.document_id == document.id
        assert len(result.chunks) == 2
        assert result.chunks[0].text == "Chunk 1"
        assert result.chunks[0].document_id == document.id
        assert result.chunks[0].embedding == [0.1, 0.2, 0.3]
        assert result.chunks[1].text == "Chunk 2"
        assert result.chunks[1].document_id == document.id
        assert result.chunks[1].embedding == [0.4, 0.5, 0.6]
        
        # Verify chunker and embedder were called
        processor._chunker.chunk_text.assert_called_once_with(document.content)
        processor._embedder.embed_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_documents(self, processor):
        """Test processing multiple documents."""
        # Setup mocks
        documents = [
            Document(id="doc1", content="Document 1", type=DocumentType.TEXT),
            Document(id="doc2", content="Document 2", type=DocumentType.TEXT)
        ]
        
        # Mock process_document to return results
        async def mock_process_document(doc):
            chunk = TextChunk(
                id=f"{doc.id}_chunk_0",
                text=doc.content,
                document_id=doc.id,
                embedding=[0.1, 0.2, 0.3]
            )
            from src.knowledge_base.core.types import ChunkingResult
            return ChunkingResult(document_id=doc.id, chunks=[chunk])
        
        processor.process_document = AsyncMock(side_effect=mock_process_document)
        
        # Process documents
        results = await processor.process_documents(documents)
        
        # Verify results
        assert len(results) == 2
        assert results[0].document_id == "doc1"
        assert results[1].document_id == "doc2"
        assert len(results[0].chunks) == 1
        assert len(results[1].chunks) == 1
        assert results[0].chunks[0].text == "Document 1"
        assert results[1].chunks[0].text == "Document 2"
        
        # Verify process_document was called for each document
        assert processor.process_document.call_count == 2

    @pytest.mark.asyncio
    async def test_initialize(self, config):
        """Test initialization of processor components."""
        with patch("src.knowledge_base.processing.processor.TextChunker") as mock_chunker, \
             patch("src.knowledge_base.processing.processor.Embedder") as mock_embedder:
            
            # Setup mocks
            mock_embedder_instance = AsyncMock()
            mock_embedder.return_value = mock_embedder_instance
            
            # Create processor
            processor = DocumentProcessor(config)
            
            # Initialize
            await processor.initialize()
            
            # Verify components were initialized
            assert processor._initialized
            mock_chunker.assert_called_once_with(config.chunking)
            mock_embedder.assert_called_once_with(config.embedding)
            mock_embedder_instance.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, processor):
        """Test closing the processor."""
        await processor.close()
        
        # Verify embedder was closed
        processor._embedder.close.assert_called_once()
        assert not processor._initialized
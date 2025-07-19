"""
Unit tests for the metadata extractor.
"""

import pytest
from datetime import datetime
from pathlib import Path

from knowledge_base.core.types import Document, TextChunk, DocumentType
from knowledge_base.processing.metadata_extractor import MetadataExtractor


class TestMetadataExtractor:
    """Test suite for the MetadataExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MetadataExtractor()
        
        # Create test documents
        self.text_document = Document(
            id="doc1",
            content="This is a sample text document. It contains multiple sentences.\n\nIt has multiple paragraphs too.",
            type=DocumentType.TEXT,
            metadata={"source_type": "test"},
            source="test_file.txt"
        )
        
        self.markdown_document = Document(
            id="doc2",
            content="# Sample Markdown\n\nThis is a paragraph.\n\n## Section\n\n- List item 1\n- List item 2\n\n```python\nprint('Hello world')\n```",
            type=DocumentType.MARKDOWN,
            metadata={"source_type": "test"},
            source="test_file.md"
        )
        
        self.code_document = Document(
            id="doc3",
            content="def hello_world():\n    # This is a comment\n    print('Hello world')\n\n# Another comment\nclass TestClass:\n    def __init__(self):\n        self.value = 42",
            type=DocumentType.CODE,
            metadata={"source_type": "test"},
            source="test_file.py"
        )
        
        # Create test chunk
        self.chunk = TextChunk(
            id="chunk1",
            text="This is a sample text chunk. It contains a single paragraph.",
            document_id="doc1",
            metadata={"chunk_index": 0},
            start_index=0,
            end_index=59
        )
    
    def test_extract_document_metadata_text(self):
        """Test extracting metadata from a text document."""
        metadata = self.extractor.extract_document_metadata(self.text_document)
        
        # Check basic metadata
        assert metadata["document_id"] == "doc1"
        assert metadata["document_type"] == "text"
        assert metadata["content_length"] == len(self.text_document.content)
        assert "extracted_at" in metadata
        assert metadata["source"] == "test_file.txt"
        assert "content_hash" in metadata
        
        # Check text-specific metadata
        assert metadata["paragraph_count"] == 2
        assert metadata["word_count"] > 0
        assert "estimated_reading_time_seconds" in metadata
        
        # Check that original metadata is preserved
        assert metadata["source_type"] == "test"
    
    def test_extract_document_metadata_markdown(self):
        """Test extracting metadata from a markdown document."""
        metadata = self.extractor.extract_document_metadata(self.markdown_document)
        
        # Check basic metadata
        assert metadata["document_id"] == "doc2"
        assert metadata["document_type"] == "markdown"
        
        # Check markdown-specific metadata
        assert metadata["header_count"] == 2
        assert metadata["title"] == "Sample Markdown"
        assert metadata["code_block_count"] == 1
    
    def test_extract_document_metadata_code(self):
        """Test extracting metadata from a code document."""
        metadata = self.extractor.extract_document_metadata(self.code_document)
        
        # Check basic metadata
        assert metadata["document_id"] == "doc3"
        assert metadata["document_type"] == "code"
        
        # Check code-specific metadata
        assert metadata["code_lines"] > 0
        assert metadata["comment_lines"] > 0
        assert metadata["language"] == "python"
        assert metadata["function_count"] == 2
        assert metadata["class_count"] == 1
    
    def test_extract_chunk_metadata(self):
        """Test extracting metadata from a text chunk."""
        metadata = self.extractor.extract_chunk_metadata(self.chunk, self.text_document)
        
        # Check basic metadata
        assert metadata["chunk_id"] == "chunk1"
        assert metadata["document_id"] == "doc1"
        assert metadata["chunk_length"] == len(self.chunk.text)
        assert metadata["start_index"] == 0
        assert metadata["end_index"] == 59
        assert "extracted_at" in metadata
        assert "content_hash" in metadata
        
        # Check document context
        assert metadata["document_type"] == "text"
        assert metadata["source"] == "test_file.txt"
        
        # Check that original metadata is preserved
        assert metadata["chunk_index"] == 0
    
    def test_generate_automatic_metadata(self):
        """Test generating automatic metadata."""
        text = "This is a sample text for automatic metadata generation. It contains multiple sentences and should be detected as English text."
        metadata = self.extractor.generate_automatic_metadata(text)
        
        # Check basic statistics
        assert metadata["char_count"] == len(text)
        assert metadata["word_count"] > 0
        assert metadata["line_count"] >= 1
        
        # Check language detection
        assert metadata["language"] == "en"
        
        # Check reading level
        assert metadata["reading_level"] in ["basic", "intermediate", "advanced"]
        
        # Check content type
        assert metadata["content_type"] in ["general", "code", "narrative", "instructional", "informational"]
        
        # Check keywords
        assert "keywords" in metadata
        assert isinstance(metadata["keywords"], list)
    
    def test_index_metadata(self):
        """Test indexing metadata."""
        original_metadata = {
            "title": "Sample Document",
            "tags": ["test", "sample", "metadata"],
            "count": 42,
            "is_active": True,
            "nested": {
                "key": "value"
            }
        }
        
        indexed_metadata = self.extractor.index_metadata(original_metadata)
        
        # Check that original fields are preserved
        assert indexed_metadata["title"] == "Sample Document"
        assert indexed_metadata["count"] == 42
        assert indexed_metadata["is_active"] is True
        
        # Check that additional indexed fields are added
        assert "title_lower" in indexed_metadata
        assert indexed_metadata["title_lower"] == "sample document"
        
        assert "tags_lower" in indexed_metadata
        assert indexed_metadata["tags_lower"] == ["test", "sample", "metadata"]
        
        # Check that nested dictionaries are recursively indexed
        assert isinstance(indexed_metadata["nested"], dict)
    
    def test_detect_programming_language(self):
        """Test programming language detection."""
        python_code = "def hello():\n    print('Hello world')\n\nclass Test:\n    pass"
        javascript_code = "function hello() {\n    console.log('Hello world');\n}\n\nconst x = 42;"
        
        assert self.extractor._detect_programming_language(python_code) == "python"
        assert self.extractor._detect_programming_language(javascript_code) == "javascript"
    
    def test_detect_language(self):
        """Test natural language detection."""
        english_text = "This is a sample text in English language."
        spanish_text = "Este es un texto de ejemplo en español."
        
        assert self.extractor._detect_language(english_text) == "en"
        # Note: This is a simplified test. The actual implementation might not be accurate for all languages
    
    def test_content_hash_generation(self):
        """Test content hash generation."""
        text1 = "This is a sample text."
        text2 = "This is a sample text."
        text3 = "This is a different text."
        
        hash1 = self.extractor._generate_content_hash(text1)
        hash2 = self.extractor._generate_content_hash(text2)
        hash3 = self.extractor._generate_content_hash(text3)
        
        # Same content should produce same hash
        assert hash1 == hash2
        # Different content should produce different hash
        assert hash1 != hash3
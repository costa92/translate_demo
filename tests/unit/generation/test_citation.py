"""
Tests for the citation module.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import TextChunk, RetrievalResult
from src.knowledge_base.generation.citation import (
    Citation, ReferenceTracker, CitationGenerator, SourceAttributor
)


class TestCitation:
    """Tests for the Citation class."""
    
    def test_from_retrieval_result(self):
        """Test creating a citation from a retrieval result."""
        # Create a mock chunk
        chunk = TextChunk(
            id="chunk1",
            text="This is a test chunk with enough text to test the snippet creation functionality in the Citation class.",
            document_id="doc1",
            metadata={"title": "Test Document", "author": "Test Author"}
        )
        
        # Create a retrieval result
        result = RetrievalResult(chunk=chunk, score=0.95, rank=1)
        
        # Create a citation from the retrieval result
        citation = Citation.from_retrieval_result(result)
        
        # Check the citation
        assert citation.chunk_id == "chunk1"
        assert citation.document_id == "doc1"
        assert citation.text_snippet.startswith("This is a test chunk")
        assert citation.text_snippet.endswith("...")
        assert len(citation.text_snippet) <= 103  # 100 chars + "..."
        assert citation.relevance_score == 0.95
        assert citation.metadata == {"title": "Test Document", "author": "Test Author"}


class TestReferenceTracker:
    """Tests for the ReferenceTracker class."""
    
    def test_add_citation(self):
        """Test adding a citation to the tracker."""
        # Create a tracker
        tracker = ReferenceTracker()
        
        # Create a citation
        citation = Citation(
            chunk_id="chunk1",
            document_id="doc1",
            text_snippet="This is a test chunk",
            relevance_score=0.95
        )
        
        # Add the citation
        marker = tracker.add_citation(citation)
        
        # Check the marker and tracker state
        assert marker == "[1]"
        assert len(tracker.citations) == 1
        assert tracker.citations[0] == citation
        assert tracker.citation_map[marker] == citation
        assert tracker.next_citation_id == 2
        
        # Add another citation
        citation2 = Citation(
            chunk_id="chunk2",
            document_id="doc1",
            text_snippet="This is another test chunk",
            relevance_score=0.85
        )
        
        marker2 = tracker.add_citation(citation2)
        
        # Check the marker and tracker state
        assert marker2 == "[2]"
        assert len(tracker.citations) == 2
        assert tracker.citations[1] == citation2
        assert tracker.citation_map[marker2] == citation2
        assert tracker.next_citation_id == 3
    
    def test_get_citation(self):
        """Test getting a citation by marker."""
        # Create a tracker
        tracker = ReferenceTracker()
        
        # Create and add citations
        citation1 = Citation(
            chunk_id="chunk1",
            document_id="doc1",
            text_snippet="This is a test chunk",
            relevance_score=0.95
        )
        
        citation2 = Citation(
            chunk_id="chunk2",
            document_id="doc1",
            text_snippet="This is another test chunk",
            relevance_score=0.85
        )
        
        marker1 = tracker.add_citation(citation1)
        marker2 = tracker.add_citation(citation2)
        
        # Get citations by marker
        assert tracker.get_citation(marker1) == citation1
        assert tracker.get_citation(marker2) == citation2
        assert tracker.get_citation("[3]") is None
    
    def test_get_all_citations(self):
        """Test getting all citations."""
        # Create a tracker
        tracker = ReferenceTracker()
        
        # Create and add citations
        citation1 = Citation(
            chunk_id="chunk1",
            document_id="doc1",
            text_snippet="This is a test chunk",
            relevance_score=0.95
        )
        
        citation2 = Citation(
            chunk_id="chunk2",
            document_id="doc1",
            text_snippet="This is another test chunk",
            relevance_score=0.85
        )
        
        tracker.add_citation(citation1)
        tracker.add_citation(citation2)
        
        # Get all citations
        citations = tracker.get_all_citations()
        assert len(citations) == 2
        assert citations[0] == citation1
        assert citations[1] == citation2
        
        # Check that it's a copy
        citations.append("test")
        assert len(tracker.citations) == 2


class TestCitationGenerator:
    """Tests for the CitationGenerator class."""
    
    def test_generate_citations(self):
        """Test generating citations for sources."""
        # Create a mock config
        config = MagicMock()
        config.generation.citation_style = "numbered"
        
        # Create a generator
        generator = CitationGenerator(config)
        
        # Create mock chunks and retrieval results
        chunk1 = TextChunk(
            id="chunk1",
            text="This is test chunk 1",
            document_id="doc1",
            metadata={"title": "Document 1", "author": "Author 1"}
        )
        
        chunk2 = TextChunk(
            id="chunk2",
            text="This is test chunk 2",
            document_id="doc2",
            metadata={"title": "Document 2", "author": "Author 2"}
        )
        
        sources = [
            RetrievalResult(chunk=chunk1, score=0.95, rank=1),
            RetrievalResult(chunk=chunk2, score=0.85, rank=2)
        ]
        
        # Generate citations
        tracker = generator.generate_citations(sources)
        
        # Check the tracker
        assert len(tracker.citations) == 2
        assert tracker.citations[0].chunk_id == "chunk1"
        assert tracker.citations[1].chunk_id == "chunk2"
    
    def test_format_citation_text(self):
        """Test formatting citation text."""
        # Create a mock config
        config = MagicMock()
        
        # Create a generator
        generator = CitationGenerator(config)
        
        # Test document citation
        citation = Citation(
            chunk_id="chunk1",
            document_id="doc1",
            text_snippet="This is a test chunk",
            metadata={
                "title": "Test Document",
                "author": "Test Author",
                "date": "2023-01-01"
            }
        )
        
        text = generator.format_citation_text(citation)
        assert "Test Author" in text
        assert "2023-01-01" in text
        assert "Test Document" in text
        
        # Test webpage citation
        citation = Citation(
            chunk_id="chunk2",
            document_id="doc2",
            text_snippet="This is a test chunk",
            metadata={
                "title": "Test Webpage",
                "author": "Web Author",
                "date": "2023-01-02",
                "source_type": "webpage",
                "url": "https://example.com"
            }
        )
        
        text = generator.format_citation_text(citation)
        assert "Web Author" in text
        assert "2023-01-02" in text
        assert "Test Webpage" in text
        assert "https://example.com" in text
        
        # Test book citation
        citation = Citation(
            chunk_id="chunk3",
            document_id="doc3",
            text_snippet="This is a test chunk",
            metadata={
                "title": "Test Book",
                "author": "Book Author",
                "date": "2023-01-03",
                "source_type": "book",
                "publisher": "Test Publisher"
            }
        )
        
        text = generator.format_citation_text(citation)
        assert "Book Author" in text
        assert "2023-01-03" in text
        assert "Test Book" in text
        assert "Test Publisher" in text
        
        # Test article citation
        citation = Citation(
            chunk_id="chunk4",
            document_id="doc4",
            text_snippet="This is a test chunk",
            metadata={
                "title": "Test Article",
                "author": "Article Author",
                "date": "2023-01-04",
                "source_type": "article",
                "journal": "Test Journal",
                "volume": "10",
                "issue": "2",
                "pages": "123-145"
            }
        )
        
        text = generator.format_citation_text(citation)
        assert "Article Author" in text
        assert "2023-01-04" in text
        assert "Test Article" in text
        assert "Test Journal" in text
        assert "10" in text
        assert "2" in text
        assert "123-145" in text
    
    def test_format_references_section(self):
        """Test formatting a references section."""
        # Create a mock config
        config = MagicMock()
        config.generation.citation_style = "numbered"
        
        # Create a generator
        generator = CitationGenerator(config)
        
        # Create a tracker with citations
        tracker = ReferenceTracker()
        
        citation1 = Citation(
            chunk_id="chunk1",
            document_id="doc1",
            text_snippet="This is a test chunk",
            metadata={
                "title": "Test Document 1",
                "author": "Author 1",
                "date": "2023-01-01"
            }
        )
        
        citation2 = Citation(
            chunk_id="chunk2",
            document_id="doc2",
            text_snippet="This is another test chunk",
            metadata={
                "title": "Test Document 2",
                "author": "Author 2",
                "date": "2023-01-02"
            }
        )
        
        tracker.add_citation(citation1)
        tracker.add_citation(citation2)
        
        # Format references section
        section = generator.format_references_section(tracker)
        
        # Check the section
        assert "## References" in section
        assert "1. Author 1" in section
        assert "2. Author 2" in section
        assert "Test Document 1" in section
        assert "Test Document 2" in section
        
        # Test with bullet style
        # Create a new generator with bullet style
        bullet_config = MagicMock()
        bullet_config.generation.citation_style = "bullet"
        bullet_generator = CitationGenerator(bullet_config)
        
        bullet_section = bullet_generator.format_references_section(tracker)
        assert "- Author 1" in bullet_section
        assert "- Author 2" in bullet_section
        
        # Test with empty tracker
        empty_tracker = ReferenceTracker()
        empty_section = generator.format_references_section(empty_tracker)
        assert empty_section == ""


class TestSourceAttributor:
    """Tests for the SourceAttributor class."""
    
    def test_attribute_sources(self):
        """Test attributing sources in an answer."""
        # Create a mock config
        config = MagicMock()
        config.generation.citation_style = "numbered"
        config.generation.include_references_section = True
        
        # Create an attributor
        attributor = SourceAttributor(config)
        
        # Create mock chunks and retrieval results
        chunk1 = TextChunk(
            id="chunk1",
            text="This is test chunk 1",
            document_id="doc1",
            metadata={"title": "Document 1", "author": "Author 1", "date": "2023-01-01"}
        )
        
        chunk2 = TextChunk(
            id="chunk2",
            text="This is test chunk 2",
            document_id="doc2",
            metadata={"title": "Document 2", "author": "Author 2", "date": "2023-01-02"}
        )
        
        sources = [
            RetrievalResult(chunk=chunk1, score=0.95, rank=1),
            RetrievalResult(chunk=chunk2, score=0.85, rank=2)
        ]
        
        # Test answer
        answer = "This is a test answer. It has multiple sentences. This is the third sentence. This is the fourth sentence."
        
        # Attribute sources
        attributed_answer, references_section = attributor.attribute_sources(answer, sources)
        
        # Check the attributed answer
        assert "[1]" in attributed_answer or "[2]" in attributed_answer
        
        # Check the references section
        assert "## References" in references_section
        assert "1. Author 1" in references_section
        assert "2. Author 2" in references_section
        
        # Test with no sources
        attributed_answer, references_section = attributor.attribute_sources(answer, [])
        assert attributed_answer == answer
        assert references_section == ""
    
    def test_create_attributed_result(self):
        """Test creating a query result with attributed sources."""
        # Create a mock config
        config = MagicMock()
        config.generation.citation_style = "numbered"
        config.generation.include_references_section = True
        
        # Create an attributor
        attributor = SourceAttributor(config)
        
        # Create mock chunks and retrieval results
        chunk1 = TextChunk(
            id="chunk1",
            text="This is test chunk 1",
            document_id="doc1",
            metadata={"title": "Document 1", "author": "Author 1", "date": "2023-01-01"}
        )
        
        chunk2 = TextChunk(
            id="chunk2",
            text="This is test chunk 2",
            document_id="doc2",
            metadata={"title": "Document 2", "author": "Author 2", "date": "2023-01-02"}
        )
        
        sources = [
            RetrievalResult(chunk=chunk1, score=0.95, rank=1),
            RetrievalResult(chunk=chunk2, score=0.85, rank=2)
        ]
        
        # Test query and answer
        query = "Test query"
        answer = "This is a test answer. It has multiple sentences. This is the third sentence. This is the fourth sentence."
        
        # Create attributed result
        result = attributor.create_attributed_result(query, answer, sources)
        
        # Check the result
        assert result.query == query
        assert "[1]" in result.answer or "[2]" in result.answer
        assert "## References" in result.answer
        assert result.sources == sources
        assert result.metadata["has_citations"] is True
        assert result.metadata["citation_count"] == 2
"""
Source citation utilities for the knowledge base system.

This module provides functionality for generating citations, tracking references,
and attributing sources in generated content.
"""

from typing import Dict, List, Optional, Tuple, Any
import re
from dataclasses import dataclass, field
from datetime import datetime

from ..core.config import Config
from ..core.types import TextChunk, RetrievalResult, QueryResult


@dataclass
class Citation:
    """Represents a citation to a source.
    
    Attributes:
        chunk_id: ID of the cited text chunk
        document_id: ID of the document containing the chunk
        text_snippet: Short snippet of the cited text
        relevance_score: Relevance score of the chunk to the query
        metadata: Additional information about the citation
    """
    chunk_id: str
    document_id: str
    text_snippet: str
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_retrieval_result(cls, result: RetrievalResult) -> "Citation":
        """Create a citation from a retrieval result.
        
        Args:
            result: The retrieval result to create a citation from
            
        Returns:
            A new Citation object
        """
        # Extract a short snippet (first 100 characters)
        snippet = result.chunk.text[:100] + ("..." if len(result.chunk.text) > 100 else "")
        
        return cls(
            chunk_id=result.chunk.id,
            document_id=result.chunk.document_id,
            text_snippet=snippet,
            relevance_score=result.score,
            metadata=result.chunk.metadata.copy()
        )


@dataclass
class ReferenceTracker:
    """Tracks references to sources in generated content.
    
    Attributes:
        citations: List of citations
        citation_map: Mapping from citation markers to citations
        next_citation_id: Counter for generating citation IDs
    """
    citations: List[Citation] = field(default_factory=list)
    citation_map: Dict[str, Citation] = field(default_factory=dict)
    next_citation_id: int = 1
    
    def add_citation(self, citation: Citation) -> str:
        """Add a citation and return a citation marker.
        
        Args:
            citation: The citation to add
            
        Returns:
            A citation marker (e.g., "[1]")
        """
        citation_id = str(self.next_citation_id)
        marker = f"[{citation_id}]"
        
        self.citations.append(citation)
        self.citation_map[marker] = citation
        self.next_citation_id += 1
        
        return marker
    
    def get_citation(self, marker: str) -> Optional[Citation]:
        """Get a citation by its marker.
        
        Args:
            marker: The citation marker
            
        Returns:
            The corresponding Citation object, or None if not found
        """
        return self.citation_map.get(marker)
    
    def get_all_citations(self) -> List[Citation]:
        """Get all citations in order.
        
        Returns:
            List of all citations
        """
        return self.citations.copy()


class CitationGenerator:
    """Generates citations for sources used in answers."""
    
    def __init__(self, config: Config):
        """Initialize the citation generator.
        
        Args:
            config: The system configuration
        """
        self.config = config
        self.citation_style = getattr(config.generation, "citation_style", "numbered")
    
    def generate_citations(self, sources: List[RetrievalResult]) -> ReferenceTracker:
        """Generate citations for a list of sources.
        
        Args:
            sources: List of retrieval results
            
        Returns:
            A ReferenceTracker containing the citations
        """
        tracker = ReferenceTracker()
        
        for source in sources:
            citation = Citation.from_retrieval_result(source)
            tracker.add_citation(citation)
            
        return tracker
    
    def format_citation_text(self, citation: Citation) -> str:
        """Format a citation as text.
        
        Args:
            citation: The citation to format
            
        Returns:
            Formatted citation text
        """
        # Extract metadata for citation
        title = citation.metadata.get("title", "Untitled")
        author = citation.metadata.get("author", "Unknown")
        date = citation.metadata.get("date")
        if not date and "created_at" in citation.metadata:
            date = citation.metadata["created_at"]
        if isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")
        elif not date:
            date = "n.d."  # No date
            
        source_type = citation.metadata.get("source_type", "document")
        url = citation.metadata.get("url", "")
        
        # Format based on source type
        if source_type == "webpage" or url:
            return f"{author}. ({date}). {title}. Retrieved from {url}"
        elif source_type == "book":
            publisher = citation.metadata.get("publisher", "Unknown Publisher")
            return f"{author}. ({date}). {title}. {publisher}."
        elif source_type == "article":
            journal = citation.metadata.get("journal", "Unknown Journal")
            volume = citation.metadata.get("volume", "")
            issue = citation.metadata.get("issue", "")
            pages = citation.metadata.get("pages", "")
            
            vol_info = f", {volume}" if volume else ""
            issue_info = f"({issue})" if issue else ""
            page_info = f", {pages}" if pages else ""
            
            return f"{author}. ({date}). {title}. {journal}{vol_info}{issue_info}{page_info}."
        else:
            # Default format for documents
            return f"{author}. ({date}). {title}."
    
    def format_references_section(self, tracker: ReferenceTracker) -> str:
        """Format a references section from a reference tracker.
        
        Args:
            tracker: The reference tracker containing citations
            
        Returns:
            Formatted references section
        """
        if not tracker.citations:
            return ""
            
        references = ["## References"]
        
        for i, citation in enumerate(tracker.citations, 1):
            citation_text = self.format_citation_text(citation)
            if self.citation_style == "numbered":
                references.append(f"{i}. {citation_text}")
            elif self.citation_style == "bullet":
                references.append(f"- {citation_text}")
            else:
                # Default to numbered if style is unknown
                references.append(f"{i}. {citation_text}")
                
        return "\n\n".join(references)


class SourceAttributor:
    """Attributes sources in generated content."""
    
    def __init__(self, config: Config):
        """Initialize the source attributor.
        
        Args:
            config: The system configuration
        """
        self.config = config
        self.citation_generator = CitationGenerator(config)
        self.citation_style = getattr(config.generation, "citation_style", "numbered")
        self.include_references_section = getattr(config.generation, "include_references_section", True)
    
    def attribute_sources(self, answer: str, sources: List[RetrievalResult]) -> Tuple[str, str]:
        """Attribute sources in an answer.
        
        Args:
            answer: The generated answer
            sources: The sources used to generate the answer
            
        Returns:
            Tuple of (attributed_answer, references_section)
        """
        # Generate citations
        tracker = self.citation_generator.generate_citations(sources)
        
        # If no sources, return the original answer
        if not tracker.citations:
            return answer, ""
        
        # Format references section
        references_section = self.citation_generator.format_references_section(tracker)
        
        # For simple implementation, just append citation markers to sentences
        # A more sophisticated implementation would analyze which parts of the answer
        # came from which sources and insert citations accordingly
        attributed_answer = self._add_citation_markers(answer, len(tracker.citations))
        
        return attributed_answer, references_section
    
    def _add_citation_markers(self, text: str, num_citations: int) -> str:
        """Add citation markers to text.
        
        This is a simple implementation that adds citation markers to sentences.
        A more sophisticated implementation would analyze which parts of the text
        came from which sources.
        
        Args:
            text: The text to add citation markers to
            num_citations: The number of available citations
            
        Returns:
            Text with citation markers added
        """
        if num_citations == 0:
            return text
            
        # Split into sentences (simple approach)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Add citations to some sentences
        # For this simple implementation, we'll add citations to every third sentence
        # and cycle through the available citations
        for i in range(2, len(sentences), 3):
            citation_idx = (i // 3) % num_citations
            citation_marker = f" [{citation_idx + 1}]"
            sentences[i] = sentences[i] + citation_marker
            
        return " ".join(sentences)
    
    def create_attributed_result(self, query: str, answer: str, sources: List[RetrievalResult]) -> QueryResult:
        """Create a query result with attributed sources.
        
        Args:
            query: The original query
            answer: The generated answer
            sources: The sources used to generate the answer
            
        Returns:
            QueryResult with attributed answer and references
        """
        attributed_answer, references_section = self.attribute_sources(answer, sources)
        
        # Combine answer and references if configured to include references section
        final_answer = attributed_answer
        if self.include_references_section and references_section:
            final_answer = f"{attributed_answer}\n\n{references_section}"
            
        # Create query result
        from ..core.types import QueryResult
        result = QueryResult(
            query=query,
            answer=final_answer,
            sources=sources,
            metadata={"has_citations": True, "citation_count": len(sources)}
        )
        
        return result
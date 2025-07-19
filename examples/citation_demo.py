"""
Demo script for the citation functionality.

This script demonstrates how to use the citation functionality
to generate answers with source citations.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import TextChunk, RetrievalResult, QueryResult
from src.knowledge_base.generation.generator import Generator
from src.knowledge_base.generation.citation import SourceAttributor


async def main():
    """Run the citation demo."""
    print("Citation Demo")
    print("=" * 50)
    
    # Create a simple configuration
    config = Config()
    
    # Set citation-related configuration
    config.generation.provider = "simple"  # Use the simple provider for demo
    config.generation.citation_style = "numbered"
    config.generation.include_references_section = True
    config.generation.include_citations = True
    config.generation.validate = False  # Disable validation for the demo
    
    # Create a generator
    generator = Generator(config)
    
    # Create some sample chunks
    chunks = [
        TextChunk(
            id="chunk1",
            text="The Earth is the third planet from the Sun and the only astronomical object known to harbor life. "
                 "About 29.2% of Earth's surface is land consisting of continents and islands.",
            document_id="doc1",
            metadata={
                "title": "Earth Facts",
                "author": "Science Encyclopedia",
                "date": "2022-05-15",
                "source_type": "article"
            }
        ),
        TextChunk(
            id="chunk2",
            text="The Earth's atmosphere consists of 78% nitrogen, 21% oxygen, and 1% other gases including argon, "
                 "carbon dioxide, and water vapor.",
            document_id="doc2",
            metadata={
                "title": "Atmospheric Composition",
                "author": "Environmental Science Journal",
                "date": "2023-01-10",
                "source_type": "article",
                "journal": "Environmental Science",
                "volume": "45",
                "issue": "2"
            }
        ),
        TextChunk(
            id="chunk3",
            text="Climate change is a long-term change in the average weather patterns that have come to define Earth's "
                 "local, regional and global climates. These changes have a broad range of observed effects.",
            document_id="doc3",
            metadata={
                "title": "Climate Change Overview",
                "author": "Climate Research Institute",
                "date": "2023-03-22",
                "source_type": "webpage",
                "url": "https://example.com/climate-change"
            }
        )
    ]
    
    # Create a query
    query = "Tell me about Earth and its atmosphere."
    
    print(f"Query: {query}")
    print("-" * 50)
    
    # Generate an answer without citations
    print("Generating answer without citations...")
    answer_without_citations = await generator.generate(
        query=query,
        chunks=chunks,
        include_citations=False
    )
    
    print("\nAnswer without citations:")
    print(answer_without_citations)
    print("-" * 50)
    
    # Generate an answer with citations
    print("Generating answer with citations...")
    result_with_citations = await generator.generate(
        query=query,
        chunks=chunks,
        include_citations=True
    )
    
    print("\nAnswer with citations:")
    print(result_with_citations.answer)
    print("-" * 50)
    
    # Demonstrate direct use of SourceAttributor
    print("Demonstrating direct use of SourceAttributor...")
    
    # Create a source attributor
    source_attributor = SourceAttributor(config)
    
    # Create some retrieval results
    sources = [
        RetrievalResult(chunk=chunks[0], score=0.95, rank=1),
        RetrievalResult(chunk=chunks[1], score=0.90, rank=2),
        RetrievalResult(chunk=chunks[2], score=0.80, rank=3)
    ]
    
    # Create a sample answer
    sample_answer = (
        "Earth is the third planet from the Sun and the only place known to support life. "
        "The Earth's atmosphere is composed primarily of nitrogen (78%) and oxygen (21%), "
        "with trace amounts of other gases. "
        "Climate change is affecting Earth's weather patterns with various observable effects."
    )
    
    # Attribute sources
    attributed_answer, references_section = source_attributor.attribute_sources(sample_answer, sources)
    
    print("\nSample answer with attributed sources:")
    print(attributed_answer)
    print("\nReferences section:")
    print(references_section)
    print("-" * 50)
    
    # Create a query result with attributed sources
    result = source_attributor.create_attributed_result(query, sample_answer, sources)
    
    print("\nQuery result with attributed sources:")
    print(f"Query: {result.query}")
    print(f"Answer: {result.answer}")
    print(f"Metadata: {result.metadata}")
    print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
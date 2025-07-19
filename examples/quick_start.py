#!/usr/bin/env python
"""
Quick start example for the Unified Knowledge Base System.

This example demonstrates how to initialize the knowledge base,
add documents, and query the knowledge base.
"""

from src.knowledge_base import KnowledgeBase
from src.knowledge_base.core.config import Config


def main():
    """Run the quick start example."""
    # Initialize the knowledge base with default configuration
    config = Config()
    kb = KnowledgeBase(config)
    
    print("Unified Knowledge Base System - Quick Start Example")
    print("==================================================")
    
    # Add a document
    print("\n1. Adding a document...")
    document_text = """
    # Unified Knowledge Base System
    
    The Unified Knowledge Base System is a comprehensive knowledge management solution
    that combines document storage, processing, retrieval, and generation capabilities
    in a cohesive platform. It supports multiple storage backends, flexible document
    processing, advanced retrieval, and high-quality generation.
    
    ## Key Features
    
    - Multiple storage backends (in-memory, Notion, vector databases)
    - Flexible document processing with various chunking strategies
    - Advanced retrieval with semantic, keyword, and hybrid search
    - High-quality generation with multiple LLM providers
    - Multi-agent architecture for specialized knowledge tasks
    """
    
    result = kb.add_document(
        content=document_text,
        metadata={
            "title": "Unified Knowledge Base System Overview",
            "format": "markdown",
            "source": "documentation"
        }
    )
    
    print(f"Document added with ID: {result.document_id}")
    print(f"Created {len(result.chunk_ids)} chunks")
    
    # Query the knowledge base
    print("\n2. Querying the knowledge base...")
    query_result = kb.query("What are the key features of the system?")
    
    print(f"\nAnswer: {query_result.answer}")
    print("\nSources:")
    for i, chunk in enumerate(query_result.chunks):
        print(f"  {i+1}. {chunk.text[:100]}...")
    
    # Add another document
    print("\n3. Adding another document...")
    another_document = """
    # Storage Backends
    
    The Unified Knowledge Base System supports multiple storage backends:
    
    1. In-memory storage for development and testing
    2. Notion for team collaboration
    3. Vector databases (Chroma, Pinecone, Weaviate) for efficient similarity search
    4. Cloud storage options (OSS, Google Drive) for production use
    
    Each storage backend implements the BaseVectorStore interface, ensuring
    consistent behavior regardless of the backend used.
    """
    
    result = kb.add_document(
        content=another_document,
        metadata={
            "title": "Storage Backends",
            "format": "markdown",
            "source": "documentation"
        }
    )
    
    print(f"Document added with ID: {result.document_id}")
    print(f"Created {len(result.chunk_ids)} chunks")
    
    # Query with metadata filter
    print("\n4. Querying with metadata filter...")
    query_result = kb.query(
        "What storage backends are supported?",
        metadata_filter={"source": "documentation"}
    )
    
    print(f"\nAnswer: {query_result.answer}")
    print("\nSources:")
    for i, chunk in enumerate(query_result.chunks):
        print(f"  {i+1}. {chunk.text[:100]}...")
    
    # Clean up (optional)
    print("\n5. Cleaning up...")
    kb.clear()
    print("Knowledge base cleared")


if __name__ == "__main__":
    main()
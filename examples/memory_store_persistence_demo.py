"""
Demo script for MemoryVectorStore with persistence.

This script demonstrates how to use the MemoryVectorStore with persistence options.
It shows how to:
1. Create and configure a MemoryVectorStore with persistence enabled
2. Add documents and chunks
3. Save data to disk
4. Load data from disk
5. Perform searches
"""

import asyncio
import os
import shutil
import uuid
from typing import List, Dict, Any

from src.knowledge_base.core.types import Chunk, Document, DocumentType
from src.knowledge_base.storage.providers.memory import MemoryVectorStore


async def create_test_chunks() -> List[Chunk]:
    """Create test chunks for demonstration."""
    return [
        Chunk(
            id=f"chunk_{uuid.uuid4()}",
            document_id="doc1",
            text="Python is a high-level, interpreted programming language known for its readability and simplicity.",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"source": "programming_languages", "topic": "python"}
        ),
        Chunk(
            id=f"chunk_{uuid.uuid4()}",
            document_id="doc1",
            text="Python supports multiple programming paradigms, including procedural, object-oriented, and functional programming.",
            embedding=[0.15, 0.25, 0.35, 0.45, 0.55],
            metadata={"source": "programming_languages", "topic": "python"}
        ),
        Chunk(
            id=f"chunk_{uuid.uuid4()}",
            document_id="doc2",
            text="JavaScript is a high-level, interpreted programming language that conforms to the ECMAScript specification.",
            embedding=[0.2, 0.3, 0.4, 0.5, 0.6],
            metadata={"source": "programming_languages", "topic": "javascript"}
        ),
        Chunk(
            id=f"chunk_{uuid.uuid4()}",
            document_id="doc2",
            text="JavaScript is used for web development, often for client-side scripting to create dynamic web pages.",
            embedding=[0.25, 0.35, 0.45, 0.55, 0.65],
            metadata={"source": "programming_languages", "topic": "javascript"}
        ),
        Chunk(
            id=f"chunk_{uuid.uuid4()}",
            document_id="doc3",
            text="Machine learning is a subset of artificial intelligence that provides systems the ability to learn and improve from experience.",
            embedding=[0.3, 0.4, 0.5, 0.6, 0.7],
            metadata={"source": "ai_topics", "topic": "machine_learning"}
        )
    ]


async def main():
    """Run the demo."""
    print("MemoryVectorStore Persistence Demo")
    print("==================================")
    
    # Define persistence directory
    persistence_path = "./demo_kb_storage"
    
    # Clean up any existing data
    if os.path.exists(persistence_path):
        print(f"Cleaning up existing data in {persistence_path}")
        shutil.rmtree(persistence_path)
    
    # Create configuration
    config = {
        "max_chunks": 10000,
        "persistence_enabled": True,
        "persistence_path": persistence_path,
        "auto_save": True,
        "auto_save_interval": 60  # Save every 60 seconds
    }
    
    print("\n1. Creating and initializing MemoryVectorStore with persistence")
    store = MemoryVectorStore(config)
    await store.initialize()
    
    # Get initial stats
    stats = await store.get_stats()
    print(f"Initial stats: {stats}")
    
    print("\n2. Adding test chunks")
    chunks = await create_test_chunks()
    success = await store.add_chunks(chunks)
    print(f"Added {len(chunks)} chunks: {success}")
    
    # Get updated stats
    stats = await store.get_stats()
    print(f"Updated stats: {stats}")
    
    print("\n3. Manually saving data to disk")
    await store.save()
    print(f"Data saved to {persistence_path}")
    
    print("\n4. Performing search")
    # Search for chunks about Python
    query_vector = [0.1, 0.2, 0.3, 0.4, 0.5]  # Similar to Python chunks
    results = await store.search_similar(query_vector, top_k=2)
    print(f"Search results: {len(results)} chunks found")
    for i, result in enumerate(results):
        print(f"  Result {i+1}: {result['chunk'].text[:50]}... (score: {result['score']:.4f})")
    
    print("\n5. Performing filtered search")
    # Search for chunks about JavaScript
    results = await store.search_similar(
        query_vector,
        top_k=2,
        filters={"topic": "javascript"}
    )
    print(f"Filtered search results: {len(results)} chunks found")
    for i, result in enumerate(results):
        print(f"  Result {i+1}: {result['chunk'].text[:50]}... (score: {result['score']:.4f})")
    
    print("\n6. Closing store")
    await store.close()
    
    print("\n7. Creating new store and loading data")
    new_store = MemoryVectorStore(config)
    await new_store.initialize()
    
    # Get stats after loading
    stats = await new_store.get_stats()
    print(f"Stats after loading: {stats}")
    
    print("\n8. Verifying data was loaded correctly")
    # Search again
    results = await new_store.search_similar(query_vector, top_k=2)
    print(f"Search results after loading: {len(results)} chunks found")
    for i, result in enumerate(results):
        print(f"  Result {i+1}: {result['chunk'].text[:50]}... (score: {result['score']:.4f})")
    
    print("\n9. Cleaning up")
    await new_store.clear()
    await new_store.close()
    
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
"""
Scalability tests for the knowledge base system.

These tests evaluate how the system scales with increasing data and load.
"""

import pytest
import asyncio
import time
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any

from src.knowledge_base.core.knowledge_base import KnowledgeBase
from src.knowledge_base.core.types import Document


@pytest.mark.asyncio
async def test_document_scaling(perf_config, generate_documents, timer):
    """Test how performance scales with increasing document count."""
    kb = KnowledgeBase(perf_config)
    await kb.initialize()
    
    # Test with increasing document counts
    doc_counts = [10, 50, 100, 200, 500]
    add_times = []
    query_times = []
    
    for count in doc_counts:
        # Generate and add documents
        documents = generate_documents(count, 500)
        
        # Measure addition time
        timer.start()
        for doc in documents:
            await kb.add_document(doc)
        timer.stop()
        add_time = timer.elapsed
        add_times.append(add_time)
        
        # Measure query time
        query = "test query for scalability evaluation"
        timer.start()
        await kb.query(query)
        timer.stop()
        query_time = timer.elapsed
        query_times.append(query_time)
        
        print(f"\nDocument count: {count}")
        print(f"  Addition time: {add_time:.2f} seconds ({add_time/count:.4f} seconds per document)")
        print(f"  Query time: {query_time:.4f} seconds")
        
        # Clear KB for next test
        await kb.clear()
    
    # Log scaling metrics
    print("\nScaling with document count:")
    for i, count in enumerate(doc_counts):
        print(f"Documents: {count}, Add time: {add_times[i]:.2f}s, Query time: {query_times[i]:.4f}s")


@pytest.mark.asyncio
async def test_chunk_scaling(perf_config, timer):
    """Test how performance scales with increasing chunk count per document."""
    kb = KnowledgeBase(perf_config)
    await kb.initialize()
    
    # Create documents with increasing size to generate more chunks
    # Adjust chunk size to control number of chunks
    chunk_configs = [
        {"chunk_size": 1000, "doc_size": 5000},    # ~5 chunks
        {"chunk_size": 500, "doc_size": 5000},     # ~10 chunks
        {"chunk_size": 200, "doc_size": 5000},     # ~25 chunks
        {"chunk_size": 100, "doc_size": 5000},     # ~50 chunks
        {"chunk_size": 50, "doc_size": 5000},      # ~100 chunks
    ]
    
    results = []
    
    for config in chunk_configs:
        # Update chunking configuration
        perf_config.chunking.chunk_size = config["chunk_size"]
        kb = KnowledgeBase(perf_config)
        await kb.initialize()
        
        # Create document
        content = ' '.join(['test'] * (config["doc_size"] // 5))
        doc = Document(
            id=f"chunk_test_{config['chunk_size']}",
            content=content,
            type="text",
            metadata={"chunk_size": config["chunk_size"]}
        )
        
        # Add document and measure time
        timer.start()
        result = await kb.add_document(doc)
        timer.stop()
        add_time = timer.elapsed
        
        # Query and measure time
        timer.start()
        await kb.query("test query")
        timer.stop()
        query_time = timer.elapsed
        
        chunk_count = len(result.chunk_ids)
        results.append({
            "chunk_size": config["chunk_size"],
            "chunk_count": chunk_count,
            "add_time": add_time,
            "query_time": query_time
        })
        
        print(f"\nChunk size: {config['chunk_size']}, Chunks created: {chunk_count}")
        print(f"  Addition time: {add_time:.4f} seconds")
        print(f"  Query time: {query_time:.4f} seconds")
    
    # Log scaling metrics
    print("\nScaling with chunk count:")
    for r in results:
        print(f"Chunks: {r['chunk_count']}, Add time: {r['add_time']:.4f}s, Query time: {r['query_time']:.4f}s")


@pytest.mark.asyncio
async def test_concurrent_user_scaling(perf_config, generate_documents, generate_queries, timer):
    """Test how performance scales with increasing concurrent users."""
    kb = KnowledgeBase(perf_config)
    await kb.initialize()
    
    # Add initial documents
    initial_docs = generate_documents(100, 500)
    for doc in initial_docs:
        await kb.add_document(doc)
    
    # Test with increasing concurrent users
    user_counts = [1, 5, 10, 25, 50, 100]
    query_times = []
    
    for user_count in user_counts:
        # Generate queries for each user
        queries = generate_queries(user_count)
        
        # Execute queries concurrently
        timer.start()
        tasks = [kb.query(q) for q in queries]
        results = await asyncio.gather(*tasks)
        timer.stop()
        
        total_time = timer.elapsed
        query_times.append(total_time)
        
        print(f"\nConcurrent users: {user_count}")
        print(f"  Total time: {total_time:.2f} seconds")
        print(f"  Average time per user: {total_time/user_count:.4f} seconds")
    
    # Log scaling metrics
    print("\nScaling with concurrent users:")
    for i, count in enumerate(user_counts):
        print(f"Users: {count}, Total time: {query_times[i]:.2f}s, Avg time: {query_times[i]/count:.4f}s")


@pytest.mark.asyncio
async def test_embedding_dimension_scaling(perf_config, generate_documents, timer):
    """Test how performance scales with different embedding dimensions."""
    # This is a simulated test since we can't easily change embedding dimensions
    # in real models without changing the model itself
    
    from src.knowledge_base.storage.providers.memory import MemoryVectorStore
    from src.knowledge_base.core.types import TextChunk
    import random
    
    # Test with different embedding dimensions
    dimensions = [32, 64, 128, 256, 512, 768]
    add_times = []
    query_times = []
    
    for dim in dimensions:
        # Create a memory vector store
        vector_store = MemoryVectorStore(perf_config)
        await vector_store.initialize()
        
        # Generate chunks with embeddings of the specified dimension
        chunks = []
        for i in range(100):
            chunk = TextChunk(
                id=f"chunk_{i}",
                text=f"This is test chunk {i}",
                document_id=f"doc_{i//5}",
                metadata={"index": i},
                embedding=[random.random() for _ in range(dim)]
            )
            chunks.append(chunk)
        
        # Add chunks to vector store
        timer.start()
        for chunk in chunks:
            await vector_store.add_texts(
                [chunk.text], 
                [chunk.metadata], 
                [chunk.id], 
                [chunk.embedding]
            )
        timer.stop()
        add_time = timer.elapsed
        add_times.append(add_time)
        
        # Query vector store
        query_embedding = [random.random() for _ in range(dim)]
        timer.start()
        for _ in range(10):  # Run 10 queries
            await vector_store.similarity_search("test", embedding=query_embedding)
        timer.stop()
        query_time = timer.elapsed
        query_times.append(query_time)
        
        print(f"\nEmbedding dimension: {dim}")
        print(f"  Addition time: {add_time:.4f} seconds")
        print(f"  Query time (10 queries): {query_time:.4f} seconds")
    
    # Log scaling metrics
    print("\nScaling with embedding dimensions:")
    for i, dim in enumerate(dimensions):
        print(f"Dimension: {dim}, Add time: {add_times[i]:.4f}s, Query time: {query_times[i]:.4f}s")
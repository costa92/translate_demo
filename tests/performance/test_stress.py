"""
Stress tests for the knowledge base system.

These tests evaluate the system's performance under extreme conditions.
"""

import pytest
import asyncio
import time
import random
from typing import List, Dict, Any

from src.knowledge_base.core.knowledge_base import KnowledgeBase
from src.knowledge_base.core.types import Document


@pytest.mark.asyncio
async def test_large_document_handling(perf_config, timer):
    """Test handling very large documents."""
    kb = KnowledgeBase(perf_config)
    await kb.initialize()
    
    # Create documents of increasing size
    sizes = [10_000, 50_000, 100_000, 500_000]
    results = {}
    
    for size in sizes:
        # Generate a large document
        content = ' '.join(['test'] * (size // 5))  # Approximately 'size' characters
        doc = Document(
            id=f"large_doc_{size}",
            content=content,
            type="text",
            metadata={"size": size}
        )
        
        # Process document
        timer.start()
        result = await kb.add_document(doc)
        timer.stop()
        
        results[size] = {
            "time": timer.elapsed,
            "chunks": len(result.chunk_ids) if result.success else 0
        }
    
    # Log performance metrics
    print("\nLarge document processing performance:")
    for size, data in results.items():
        print(f"Document size {size}: {data['time']:.2f} seconds, {data['chunks']} chunks")


@pytest.mark.asyncio
async def test_high_concurrency(perf_config, generate_documents, generate_queries, timer):
    """Test system under high concurrency."""
    kb = KnowledgeBase(perf_config)
    await kb.initialize()
    
    # Add initial documents
    initial_docs = generate_documents(50, 500)
    for doc in initial_docs:
        await kb.add_document(doc)
    
    # Generate a large number of concurrent operations
    num_operations = 100
    operations = []
    
    # Mix of different operations
    additional_docs = generate_documents(num_operations // 2, 500)
    queries = generate_queries(num_operations // 2)
    
    for i in range(num_operations // 2):
        operations.append(("add", additional_docs[i]))
        operations.append(("query", queries[i]))
    
    random.shuffle(operations)  # Randomize operation order
    
    # Execute all operations concurrently
    timer.start()
    tasks = []
    for op_type, data in operations:
        if op_type == "add":
            tasks.append(kb.add_document(data))
        else:  # query
            tasks.append(kb.query(data))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    timer.stop()
    
    # Count successful operations
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    
    # Log performance metrics
    print(f"\nExecuted {num_operations} concurrent operations in {timer.elapsed:.2f} seconds")
    print(f"Success rate: {success_count}/{num_operations} ({success_count/num_operations*100:.1f}%)")
    print(f"Average time per operation: {timer.elapsed / num_operations:.4f} seconds")
    
    # Count errors by type
    error_counts = {}
    for r in results:
        if isinstance(r, Exception):
            error_type = type(r).__name__
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
    
    if error_counts:
        print("Errors encountered:")
        for error_type, count in error_counts.items():
            print(f"  {error_type}: {count}")


@pytest.mark.asyncio
async def test_memory_usage(perf_config, generate_documents, timer):
    """Test memory usage with a large number of documents."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    kb = KnowledgeBase(perf_config)
    await kb.initialize()
    
    # Record initial memory usage
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Add documents in batches and monitor memory
    batch_size = 50
    num_batches = 10
    memory_usage = [initial_memory]
    
    for i in range(num_batches):
        documents = generate_documents(batch_size, 1000)
        
        timer.start()
        for doc in documents:
            await kb.add_document(doc)
        timer.stop()
        
        # Record memory after batch
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage.append(current_memory)
        
        print(f"\nBatch {i+1}: Added {batch_size} documents in {timer.elapsed:.2f} seconds")
        print(f"Current memory usage: {current_memory:.2f} MB (change: {current_memory - memory_usage[-2]:.2f} MB)")
    
    # Log overall memory metrics
    print(f"\nInitial memory usage: {initial_memory:.2f} MB")
    print(f"Final memory usage: {memory_usage[-1]:.2f} MB")
    print(f"Total increase: {memory_usage[-1] - initial_memory:.2f} MB")
    print(f"Average increase per document: {(memory_usage[-1] - initial_memory) / (batch_size * num_batches):.4f} MB")


@pytest.mark.asyncio
async def test_error_recovery(perf_config, generate_documents, generate_queries, timer):
    """Test system recovery after errors."""
    from unittest.mock import patch
    import random
    
    kb = KnowledgeBase(perf_config)
    await kb.initialize()
    
    # Add initial documents
    initial_docs = generate_documents(30, 500)
    for doc in initial_docs:
        await kb.add_document(doc)
    
    # Create a function that sometimes fails
    original_similarity_search = kb._vector_store.similarity_search
    
    async def failing_similarity_search(*args, **kwargs):
        # Fail 30% of the time
        if random.random() < 0.3:
            raise Exception("Simulated failure in similarity search")
        return await original_similarity_search(*args, **kwargs)
    
    # Patch the similarity search method to sometimes fail
    with patch.object(kb._vector_store, 'similarity_search', failing_similarity_search):
        # Run multiple queries and measure success rate
        queries = generate_queries(50)
        
        timer.start()
        tasks = [kb.query(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        timer.stop()
        
        # Count successful queries
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        
        # Log performance metrics
        print(f"\nExecuted 50 queries with simulated failures in {timer.elapsed:.2f} seconds")
        print(f"Success rate: {success_count}/50 ({success_count/50*100:.1f}%)")
        print(f"Average time per query: {timer.elapsed / 50:.4f} seconds")
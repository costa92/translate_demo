"""
Load tests for the knowledge base system.

These tests evaluate the system's performance under normal to heavy load conditions.
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any

from src.knowledge_base.core.knowledge_base import KnowledgeBase
from src.knowledge_base.core.types import Document


@pytest.mark.asyncio
async def test_concurrent_document_addition(perf_config, generate_documents, timer):
    """Test adding multiple documents concurrently."""
    kb = KnowledgeBase(perf_config)
    await kb.initialize()
    
    # Generate 50 documents
    documents = generate_documents(50, 500)
    
    # Add documents concurrently
    timer.start()
    tasks = [kb.add_document(doc) for doc in documents]
    results = await asyncio.gather(*tasks)
    timer.stop()
    
    # Verify results
    assert len(results) == 50
    assert all(result.success for result in results)
    
    # Log performance metrics
    print(f"\nAdded 50 documents concurrently in {timer.elapsed:.2f} seconds")
    print(f"Average time per document: {timer.elapsed / 50:.4f} seconds")


@pytest.mark.asyncio
async def test_concurrent_queries(populated_kb, generate_queries, timer):
    """Test executing multiple queries concurrently."""
    kb = populated_kb
    
    # Generate 20 queries
    queries = generate_queries(20)
    
    # Execute queries concurrently
    timer.start()
    tasks = [kb.query(q) for q in queries]
    results = await asyncio.gather(*tasks)
    timer.stop()
    
    # Verify results
    assert len(results) == 20
    
    # Log performance metrics
    print(f"\nExecuted 20 concurrent queries in {timer.elapsed:.2f} seconds")
    print(f"Average time per query: {timer.elapsed / 20:.4f} seconds")


@pytest.mark.asyncio
async def test_mixed_workload(perf_config, generate_documents, generate_queries, timer):
    """Test a mixed workload of additions and queries."""
    kb = KnowledgeBase(perf_config)
    await kb.initialize()
    
    # Add initial documents
    initial_docs = generate_documents(30, 500)
    for doc in initial_docs:
        await kb.add_document(doc)
    
    # Generate additional documents and queries
    additional_docs = generate_documents(20, 500)
    queries = generate_queries(30)
    
    # Mix document additions and queries
    timer.start()
    tasks = []
    for i in range(20):
        tasks.append(kb.add_document(additional_docs[i]))
        tasks.append(kb.query(queries[i]))
        if i < 10:
            tasks.append(kb.query(queries[i+20]))
    
    results = await asyncio.gather(*tasks)
    timer.stop()
    
    # Log performance metrics
    print(f"\nExecuted mixed workload (20 additions + 30 queries) in {timer.elapsed:.2f} seconds")
    print(f"Average time per operation: {timer.elapsed / 50:.4f} seconds")


@pytest.mark.asyncio
async def test_batch_document_processing(perf_config, generate_documents, timer):
    """Test processing documents in batches."""
    kb = KnowledgeBase(perf_config)
    await kb.initialize()
    
    # Generate documents in different batch sizes
    batch_sizes = [1, 5, 10, 20, 50]
    results = {}
    
    for batch_size in batch_sizes:
        documents = generate_documents(batch_size, 1000)
        
        # Process batch
        timer.start()
        for doc in documents:
            await kb.add_document(doc)
        timer.stop()
        
        results[batch_size] = timer.elapsed
        
        # Clear KB for next test
        await kb.clear()
    
    # Log performance metrics
    print("\nBatch document processing performance:")
    for batch_size, elapsed in results.items():
        print(f"Batch size {batch_size}: {elapsed:.4f} seconds total, {elapsed/batch_size:.4f} seconds per document")


@pytest.mark.asyncio
async def test_retrieval_performance_by_k(populated_kb, timer):
    """Test retrieval performance with different k values."""
    kb = populated_kb
    query = "test query for performance evaluation"
    
    k_values = [1, 5, 10, 20, 50]
    results = {}
    
    for k in k_values:
        timer.start()
        result = await kb.query(query, k=k)
        timer.stop()
        
        results[k] = timer.elapsed
    
    # Log performance metrics
    print("\nRetrieval performance by k value:")
    for k, elapsed in results.items():
        print(f"k={k}: {elapsed:.4f} seconds")
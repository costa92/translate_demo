"""
Integration tests for the RAG pipeline.

This module tests the end-to-end functionality of the Retrieval-Augmented Generation pipeline.
"""

import pytest
import asyncio
from typing import List, Dict, Any

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import Document, TextChunk
from src.knowledge_base.storage.vector_store import VectorStore
from src.knowledge_base.processing.processor import DocumentProcessor
from src.knowledge_base.retrieval.retriever import Retriever
from src.knowledge_base.generation.generator import Generator


@pytest.fixture
def rag_config():
    """Create a configuration for RAG pipeline testing."""
    config_dict = {
        "system": {
            "debug": True,
            "log_level": "DEBUG"
        },
        "storage": {
            "provider": "memory",
            "max_chunks": 1000,
            "persistence_enabled": False
        },
        "embedding": {
            "provider": "sentence_transformers",
            "model_name": "all-MiniLM-L6-v2",
            "cache_enabled": True
        },
        "chunking": {
            "strategy": "recursive",
            "chunk_size": 100,
            "chunk_overlap": 20,
            "separators": ["\n\n", "\n", " ", ""]
        },
        "retrieval": {
            "strategy": "semantic",
            "top_k": 3,
            "reranking_enabled": True
        },
        "generation": {
            "provider": "simple",
            "model_name": "test-model",
            "temperature": 0.7,
            "max_tokens": 500,
            "stream": False,
            "include_citations": True
        }
    }
    return Config.from_dict(config_dict)


@pytest.fixture
async def vector_store(rag_config):
    """Create and initialize a vector store for testing."""
    store = VectorStore.create(rag_config)
    await store.initialize()
    yield store
    await store.clear()
    await store.close()


@pytest.fixture
def document_processor(rag_config):
    """Create a document processor for testing."""
    return DocumentProcessor(rag_config)


@pytest.fixture
async def retriever(rag_config, vector_store):
    """Create a retriever for testing."""
    return Retriever(rag_config, vector_store)


@pytest.fixture
def generator(rag_config):
    """Create a generator for testing."""
    return Generator(rag_config)


@pytest.fixture
def test_documents():
    """Create test documents for the RAG pipeline."""
    return [
        Document(
            id="doc1",
            content="Python is a high-level, interpreted programming language. "
                   "It was created by Guido van Rossum and first released in 1991. "
                   "Python's design philosophy emphasizes code readability with its "
                   "notable use of significant whitespace.",
            type="text",
            metadata={"source": "test", "topic": "programming"}
        ),
        Document(
            id="doc2",
            content="JavaScript is a programming language that conforms to the ECMAScript specification. "
                   "JavaScript is high-level, often just-in-time compiled, and multi-paradigm. "
                   "It has curly-bracket syntax, dynamic typing, prototype-based object-orientation, "
                   "and first-class functions.",
            type="text",
            metadata={"source": "test", "topic": "programming"}
        ),
        Document(
            id="doc3",
            content="Machine learning is a subset of artificial intelligence that provides systems "
                   "the ability to automatically learn and improve from experience without being "
                   "explicitly programmed. Machine learning focuses on the development of computer "
                   "programs that can access data and use it to learn for themselves.",
            type="text",
            metadata={"source": "test", "topic": "ai"}
        )
    ]


@pytest.mark.asyncio
async def test_rag_pipeline_end_to_end(
    rag_config, 
    vector_store, 
    document_processor, 
    retriever, 
    generator, 
    test_documents
):
    """Test the complete RAG pipeline from document ingestion to answer generation."""
    # Process and store documents
    for document in test_documents:
        chunks = await document_processor.process_document(document)
        assert len(chunks) > 0, f"Document {document.id} should produce at least one chunk"
        
        # Store chunks in vector store
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_metadatas = [chunk.metadata for chunk in chunks]
        chunk_ids = [chunk.id for chunk in chunks]
        chunk_embeddings = [chunk.embedding for chunk in chunks]
        
        stored_ids = await vector_store.add_texts(
            texts=chunk_texts,
            metadatas=chunk_metadatas,
            ids=chunk_ids,
            embeddings=chunk_embeddings
        )
        
        assert len(stored_ids) == len(chunks), "All chunks should be stored"
    
    # Test retrieval
    query = "What is Python programming language?"
    retrieved_results = await retriever.retrieve(query, k=2)
    
    assert len(retrieved_results) > 0, "Should retrieve at least one chunk"
    assert any("Python" in result.chunk.text for result in retrieved_results), "Should retrieve chunks about Python"
    
    # Test generation
    chunks = [result.chunk for result in retrieved_results]
    answer = await generator.generate(query, chunks)
    
    assert answer is not None, "Should generate an answer"
    assert len(answer.answer) > 0, "Answer should not be empty"
    assert "Python" in answer.answer, "Answer should mention Python"
    
    # Test with different query
    query = "What is machine learning?"
    retrieved_results = await retriever.retrieve(query, k=2)
    
    assert len(retrieved_results) > 0, "Should retrieve at least one chunk"
    assert any("machine learning" in result.chunk.text.lower() for result in retrieved_results), \
        "Should retrieve chunks about machine learning"
    
    # Test generation with different query
    chunks = [result.chunk for result in retrieved_results]
    answer = await generator.generate(query, chunks)
    
    assert answer is not None, "Should generate an answer"
    assert len(answer.answer) > 0, "Answer should not be empty"
    assert "machine learning" in answer.answer.lower() or "ai" in answer.answer.lower(), \
        "Answer should mention machine learning or AI"


@pytest.mark.asyncio
async def test_rag_pipeline_with_filters(
    rag_config, 
    vector_store, 
    document_processor, 
    retriever, 
    generator, 
    test_documents
):
    """Test the RAG pipeline with metadata filters."""
    # Process and store documents
    for document in test_documents:
        chunks = await document_processor.process_document(document)
        
        # Store chunks in vector store
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_metadatas = [chunk.metadata for chunk in chunks]
        chunk_ids = [chunk.id for chunk in chunks]
        chunk_embeddings = [chunk.embedding for chunk in chunks]
        
        await vector_store.add_texts(
            texts=chunk_texts,
            metadatas=chunk_metadatas,
            ids=chunk_ids,
            embeddings=chunk_embeddings
        )
    
    # Test retrieval with filter
    query = "What is a programming language?"
    filter_dict = {"topic": "programming"}
    retrieved_results = await retriever.retrieve(query, k=3, filter=filter_dict)
    
    assert len(retrieved_results) > 0, "Should retrieve at least one chunk"
    assert all(result.chunk.metadata.get("topic") == "programming" for result in retrieved_results), \
        "All retrieved chunks should have topic=programming"
    
    # Test with different filter
    query = "What is artificial intelligence?"
    filter_dict = {"topic": "ai"}
    retrieved_results = await retriever.retrieve(query, k=3, filter=filter_dict)
    
    assert len(retrieved_results) > 0, "Should retrieve at least one chunk"
    assert all(result.chunk.metadata.get("topic") == "ai" for result in retrieved_results), \
        "All retrieved chunks should have topic=ai"


@pytest.mark.asyncio
async def test_rag_pipeline_streaming(
    rag_config, 
    vector_store, 
    document_processor, 
    retriever, 
    test_documents
):
    """Test the RAG pipeline with streaming generation."""
    # Modify config for streaming
    rag_config.generation.stream = True
    
    # Create generator with streaming enabled
    generator = Generator(rag_config)
    
    # Process and store documents
    for document in test_documents:
        chunks = await document_processor.process_document(document)
        
        # Store chunks in vector store
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_metadatas = [chunk.metadata for chunk in chunks]
        chunk_ids = [chunk.id for chunk in chunks]
        chunk_embeddings = [chunk.embedding for chunk in chunks]
        
        await vector_store.add_texts(
            texts=chunk_texts,
            metadatas=chunk_metadatas,
            ids=chunk_ids,
            embeddings=chunk_embeddings
        )
    
    # Test retrieval
    query = "What is Python programming language?"
    retrieved_results = await retriever.retrieve(query, k=2)
    
    assert len(retrieved_results) > 0, "Should retrieve at least one chunk"
    
    # Test streaming generation
    chunks = [result.chunk for result in retrieved_results]
    stream = await generator.generate(query, chunks)
    
    # Collect streaming output
    collected_text = ""
    async for text_chunk in stream:
        assert isinstance(text_chunk, str), "Stream should yield string chunks"
        collected_text += text_chunk
    
    assert len(collected_text) > 0, "Streamed answer should not be empty"
    assert "Python" in collected_text, "Answer should mention Python"
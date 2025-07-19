"""
Test configuration and fixtures for performance tests.
"""

import os
import time
import pytest
import asyncio
import random
import string
from typing import Dict, Any, List, Callable

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import Document, TextChunk
from src.knowledge_base.storage.base import BaseVectorStore
from src.knowledge_base.storage.providers.memory import MemoryVectorStore
from src.knowledge_base.processing.processor import DocumentProcessor
from src.knowledge_base.retrieval.retriever import Retriever
from src.knowledge_base.generation.generator import Generator
from src.knowledge_base.core.knowledge_base import KnowledgeBase


@pytest.fixture
def performance_config() -> Dict[str, Any]:
    """Create a configuration optimized for performance testing."""
    return {
        "system": {
            "debug": False,
            "log_level": "WARNING"
        },
        "storage": {
            "provider": "memory",
            "max_chunks": 10000,
            "persistence_enabled": False
        },
        "embedding": {
            "provider": "sentence_transformers",
            "model_name": "all-MiniLM-L6-v2",
            "cache_enabled": True,
            "batch_size": 32
        },
        "chunking": {
            "strategy": "recursive",
            "chunk_size": 100,
            "chunk_overlap": 20,
            "separators": ["\n\n", "\n", " ", ""]
        },
        "retrieval": {
            "strategy": "semantic",
            "top_k": 5,
            "reranking_enabled": False
        },
        "generation": {
            "provider": "simple",
            "model_name": "test-model",
            "temperature": 0.7,
            "max_tokens": 500,
            "stream": False
        },
        "api": {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": False,
            "cors_origins": ["*"],
            "rate_limit": {
                "enabled": True,
                "requests_per_minute": 100
            }
        }
    }


@pytest.fixture
def perf_config(performance_config) -> Config:
    """Create a Config object for performance testing."""
    return Config.from_dict(performance_config)


@pytest.fixture
def generate_documents() -> Callable[[int, int], List[Document]]:
    """Create a function to generate test documents."""
    def _generate_documents(count: int, content_length: int = 1000) -> List[Document]:
        documents = []
        for i in range(count):
            # Generate random content
            content = ''.join(random.choices(
                string.ascii_letters + string.digits + ' \n', 
                k=content_length
            ))
            
            doc = Document(
                id=f"doc_{i}",
                content=content,
                type="text",
                metadata={"source": "performance_test", "index": i}
            )
            documents.append(doc)
        return documents
    
    return _generate_documents


@pytest.fixture
def generate_queries() -> Callable[[int], List[str]]:
    """Create a function to generate test queries."""
    def _generate_queries(count: int) -> List[str]:
        queries = []
        for i in range(count):
            # Generate random queries
            query_length = random.randint(5, 20)
            query = ' '.join(''.join(random.choices(
                string.ascii_lowercase, 
                k=random.randint(3, 10)
            )) for _ in range(query_length))
            
            queries.append(query)
        return queries
    
    return _generate_queries


@pytest.fixture
async def populated_kb(perf_config, generate_documents) -> KnowledgeBase:
    """Create a knowledge base populated with test documents."""
    kb = KnowledgeBase(perf_config)
    await kb.initialize()
    
    # Add 100 documents with 1000 characters each
    documents = generate_documents(100, 1000)
    for doc in documents:
        await kb.add_document(doc)
    
    return kb


@pytest.fixture
def timer():
    """Create a simple timer for measuring execution time."""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
            return self
        
        def stop(self):
            self.end_time = time.time()
            return self
        
        @property
        def elapsed(self):
            if self.start_time is None:
                return 0
            end = self.end_time if self.end_time is not None else time.time()
            return end - self.start_time
    
    return Timer()
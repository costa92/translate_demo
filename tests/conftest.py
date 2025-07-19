"""
Test configuration and common fixtures.

This module provides configuration and fixtures for all tests.
"""

import os
import pytest
from unittest.mock import MagicMock
from typing import Dict, Any

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import Document, TextChunk


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Create a test configuration dictionary."""
    return {
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
            "strategy": "hybrid",
            "top_k": 5,
            "reranking_enabled": True
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
            "debug": True,
            "cors_origins": ["*"]
        }
    }


@pytest.fixture
def mock_config(test_config) -> Config:
    """Create a mock Config object."""
    return Config.from_dict(test_config)


@pytest.fixture
def test_document() -> Document:
    """Create a test document."""
    return Document(
        id="test_doc",
        content="This is a test document with some content for testing purposes.",
        type="text",
        metadata={"source": "test", "author": "tester"}
    )


@pytest.fixture
def test_chunks() -> list[TextChunk]:
    """Create test text chunks."""
    return [
        TextChunk(
            id="chunk1",
            text="This is the first test chunk.",
            document_id="test_doc",
            metadata={"source": "test", "chunk_index": 0},
            embedding=[0.1, 0.2, 0.3, 0.4]
        ),
        TextChunk(
            id="chunk2",
            text="This is the second test chunk.",
            document_id="test_doc",
            metadata={"source": "test", "chunk_index": 1},
            embedding=[0.2, 0.3, 0.4, 0.5]
        ),
        TextChunk(
            id="chunk3",
            text="This is a chunk from another document.",
            document_id="other_doc",
            metadata={"source": "other", "chunk_index": 0},
            embedding=[0.3, 0.4, 0.5, 0.6]
        )
    ]


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for tests."""
    return tmp_path
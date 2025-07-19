"""
End-to-end tests for complete workflows in the unified knowledge base system.

This module tests complete workflows from document ingestion to querying.
"""

import pytest
import asyncio
import os
from typing import Dict, Any, List

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import Document
from src.knowledge_base.api.server import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def e2e_config():
    """Create a configuration for end-to-end testing."""
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
        },
        "agents": {
            "specialized_agents": {
                "collection": True,
                "processing": True,
                "storage": True,
                "retrieval": True,
                "maintenance": True,
                "rag": True
            }
        },
        "api": {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": True,
            "cors_origins": ["*"],
            "auth_enabled": False,
            "rate_limit_enabled": False,
            "docs_enabled": True
        }
    }
    return Config.from_dict(config_dict)


@pytest.fixture
def api_client(e2e_config):
    """Create a test client for the API."""
    app = create_app(e2e_config)
    
    # Start the orchestrator
    loop = asyncio.get_event_loop()
    from src.knowledge_base.api.server import _orchestrator
    loop.run_until_complete(_orchestrator.start())
    
    client = TestClient(app)
    yield client
    
    # Stop the orchestrator
    loop.run_until_complete(_orchestrator.stop())


@pytest.fixture
def test_documents():
    """Create test documents for end-to-end testing."""
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
async def test_complete_workflow(api_client, test_documents):
    """Test a complete workflow from document ingestion to querying."""
    # 1. Add documents through the API
    for document in test_documents:
        response = api_client.post(
            "/knowledge/documents",
            json={
                "id": document.id,
                "content": document.content,
                "type": document.type,
                "metadata": document.metadata
            }
        )
        assert response.status_code == 200, f"Failed to add document: {response.text}"
        result = response.json()
        assert result["status"] == "success", f"Document addition failed: {result}"
        assert "document_id" in result["result"], "Response should contain document_id"
    
    # 2. Query the knowledge base
    query = "What is Python programming language?"
    response = api_client.post(
        "/query",
        json={"query": query}
    )
    assert response.status_code == 200, f"Query failed: {response.text}"
    result = response.json()
    assert result["status"] == "success", f"Query failed: {result}"
    assert "answer" in result["result"], "Response should contain an answer"
    assert "Python" in result["result"]["answer"], "Answer should mention Python"
    
    # 3. Query with filter
    query = "What is a programming language?"
    response = api_client.post(
        "/query",
        json={
            "query": query,
            "filter": {"topic": "programming"}
        }
    )
    assert response.status_code == 200, f"Filtered query failed: {response.text}"
    result = response.json()
    assert result["status"] == "success", f"Filtered query failed: {result}"
    assert "answer" in result["result"], "Response should contain an answer"
    
    # 4. Get document by ID
    doc_id = test_documents[0].id
    response = api_client.get(f"/knowledge/documents/{doc_id}")
    assert response.status_code == 200, f"Get document failed: {response.text}"
    result = response.json()
    assert result["status"] == "success", f"Get document failed: {result}"
    assert result["result"]["id"] == doc_id, "Retrieved document should have correct ID"
    
    # 5. List all documents
    response = api_client.get("/knowledge/documents")
    assert response.status_code == 200, f"List documents failed: {response.text}"
    result = response.json()
    assert result["status"] == "success", f"List documents failed: {result}"
    assert len(result["result"]["documents"]) == len(test_documents), "Should list all documents"
    
    # 6. Delete a document
    doc_id = test_documents[0].id
    response = api_client.delete(f"/knowledge/documents/{doc_id}")
    assert response.status_code == 200, f"Delete document failed: {response.text}"
    result = response.json()
    assert result["status"] == "success", f"Delete document failed: {result}"
    
    # 7. Verify document was deleted
    response = api_client.get("/knowledge/documents")
    assert response.status_code == 200, f"List documents failed: {response.text}"
    result = response.json()
    assert len(result["result"]["documents"]) == len(test_documents) - 1, "Document should be deleted"
    
    # 8. Check health endpoint
    response = api_client.get("/health")
    assert response.status_code == 200, f"Health check failed: {response.text}"
    assert response.json()["status"] == "ok", "Health check should return ok status"
"""
Integration tests for the API endpoints.

This module tests the integration between API endpoints and the underlying system.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
import json
from typing import Dict, Any, List

from src.knowledge_base.core.config import Config
from src.knowledge_base.api.server import create_app, get_orchestrator, get_config
from src.knowledge_base.agents.orchestrator import OrchestratorAgent
from src.knowledge_base.core.types import Document


@pytest.fixture
def api_config():
    """Create a configuration for API testing."""
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
        "api": {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": True,
            "cors_origins": ["*"],
            "auth_enabled": False
        },
        "agents": {
            "enabled": True,
            "orchestrator": {
                "max_retries": 3,
                "timeout": 30
            }
        }
    }
    return Config.from_dict(config_dict)


@pytest.fixture
async def orchestrator(api_config):
    """Create and initialize an orchestrator agent for testing."""
    orchestrator = OrchestratorAgent(api_config)
    await orchestrator.start()
    yield orchestrator
    await orchestrator.stop()


@pytest.fixture
def app(api_config, orchestrator):
    """Create a FastAPI application for testing."""
    app = create_app(api_config)
    
    # Override dependency injection
    app.dependency_overrides[get_config] = lambda: api_config
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def test_document():
    """Create a test document for API testing."""
    return {
        "content": "This is a test document for API integration testing. "
                  "It contains information about knowledge base systems and RAG pipelines.",
        "type": "text",
        "metadata": {
            "source": "api_test",
            "author": "tester",
            "topic": "knowledge_base"
        }
    }


@pytest.mark.asyncio
async def test_document_lifecycle(client, test_document):
    """Test the complete document lifecycle through API endpoints."""
    # Add a document
    response = client.post("/api/documents", json=test_document)
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "document_id" in result
    assert "chunk_ids" in result
    assert len(result["chunk_ids"]) > 0
    
    document_id = result["document_id"]
    
    # Get the document
    response = client.get(f"/api/documents/{document_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == document_id
    assert result["content"] == test_document["content"]
    assert result["type"] == test_document["type"]
    assert result["metadata"] == test_document["metadata"]
    
    # Query using the document
    query = "What is this document about?"
    response = client.post(
        "/api/query",
        json={"query": query, "filter": {"source": "api_test"}}
    )
    assert response.status_code == 200
    result = response.json()
    assert "answer" in result
    assert len(result["answer"]) > 0
    assert "chunks" in result
    assert len(result["chunks"]) > 0
    
    # Delete the document
    response = client.delete(f"/api/documents/{document_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    
    # Verify document is deleted
    response = client.get(f"/api/documents/{document_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_batch_operations(client):
    """Test batch operations through API endpoints."""
    # Create multiple test documents
    test_documents = [
        {
            "content": f"This is test document {i} for batch operations testing.",
            "type": "text",
            "metadata": {
                "source": "batch_test",
                "index": i,
                "topic": "knowledge_base"
            }
        }
        for i in range(3)
    ]
    
    # Add documents in batch
    response = client.post("/api/documents/batch", json={"documents": test_documents})
    assert response.status_code == 200
    result = response.json()
    assert "results" in result
    assert len(result["results"]) == 3
    assert all(r["success"] for r in result["results"])
    
    document_ids = [r["document_id"] for r in result["results"]]
    
    # Query with batch filter
    response = client.post(
        "/api/query",
        json={"query": "What are these documents about?", "filter": {"source": "batch_test"}}
    )
    assert response.status_code == 200
    result = response.json()
    assert "answer" in result
    assert len(result["answer"]) > 0
    assert "chunks" in result
    assert len(result["chunks"]) > 0
    
    # Delete documents in batch
    response = client.post("/api/documents/batch/delete", json={"document_ids": document_ids})
    assert response.status_code == 200
    result = response.json()
    assert "results" in result
    assert len(result["results"]) == 3
    assert all(r["success"] for r in result["results"])


@pytest.mark.asyncio
async def test_streaming_response(client, test_document):
    """Test streaming response through API endpoints."""
    # Add a document
    response = client.post("/api/documents", json=test_document)
    assert response.status_code == 200
    result = response.json()
    document_id = result["document_id"]
    
    # Test WebSocket connection
    # Note: TestClient doesn't support WebSocket testing directly
    # This is a placeholder for actual WebSocket testing
    
    # Clean up
    response = client.delete(f"/api/documents/{document_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_and_admin_endpoints(client):
    """Test health check and admin endpoints."""
    # Health check
    response = client.get("/health")
    assert response.status_code == 200
    result = response.json()
    assert "status" in result
    assert result["status"] == "healthy"
    
    # System info
    response = client.get("/api/admin/system")
    assert response.status_code == 200
    result = response.json()
    assert "version" in result
    assert "uptime" in result
    assert "components" in result
    
    # Storage stats
    response = client.get("/api/admin/storage/stats")
    assert response.status_code == 200
    result = response.json()
    assert "document_count" in result
    assert "chunk_count" in result
    assert "provider" in result


@pytest.mark.asyncio
async def test_error_handling(client):
    """Test error handling in API endpoints."""
    # Invalid document format
    response = client.post(
        "/api/documents",
        json={"invalid": "document"}  # Missing required fields
    )
    assert response.status_code == 422
    
    # Non-existent document
    response = client.get("/api/documents/non_existent_id")
    assert response.status_code == 404
    
    # Invalid query
    response = client.post(
        "/api/query",
        json={"filter": {"source": "test"}}  # Missing query field
    )
    assert response.status_code == 422
    
    # Invalid filter
    response = client.post(
        "/api/query",
        json={"query": "Test query", "filter": "invalid_filter"}  # Filter should be a dict
    )
    assert response.status_code == 422
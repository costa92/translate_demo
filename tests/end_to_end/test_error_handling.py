"""
End-to-end tests for error handling in the unified knowledge base system.

This module tests how the system handles various error conditions.
"""

import pytest
import asyncio
import json
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


@pytest.mark.asyncio
async def test_invalid_document_format(api_client):
    """Test error handling for invalid document format."""
    # Missing required fields
    invalid_doc = {
        "content": "This is a test document."
        # Missing id and type
    }
    
    response = api_client.post("/knowledge/documents", json=invalid_doc)
    assert response.status_code == 400, "Should return 400 for invalid document format"
    result = response.json()
    assert "error" in result, "Response should contain error message"
    
    # Invalid document type
    invalid_doc = {
        "id": "test_doc",
        "content": "This is a test document.",
        "type": "invalid_type",  # Invalid type
        "metadata": {}
    }
    
    response = api_client.post("/knowledge/documents", json=invalid_doc)
    assert response.status_code == 400, "Should return 400 for invalid document type"
    result = response.json()
    assert "error" in result, "Response should contain error message"


@pytest.mark.asyncio
async def test_document_not_found(api_client):
    """Test error handling for document not found."""
    # Try to get a non-existent document
    response = api_client.get("/knowledge/documents/non_existent_doc")
    assert response.status_code == 404, "Should return 404 for non-existent document"
    result = response.json()
    assert "error" in result, "Response should contain error message"
    
    # Try to update a non-existent document
    update_doc = {
        "id": "non_existent_doc",
        "content": "Updated content",
        "type": "text",
        "metadata": {}
    }
    
    response = api_client.put("/knowledge/documents/non_existent_doc", json=update_doc)
    assert response.status_code == 404, "Should return 404 for updating non-existent document"
    result = response.json()
    assert "error" in result, "Response should contain error message"
    
    # Try to delete a non-existent document
    response = api_client.delete("/knowledge/documents/non_existent_doc")
    assert response.status_code == 404, "Should return 404 for deleting non-existent document"
    result = response.json()
    assert "error" in result, "Response should contain error message"


@pytest.mark.asyncio
async def test_invalid_query_format(api_client):
    """Test error handling for invalid query format."""
    # Empty query
    invalid_query = {
        "query": ""
    }
    
    response = api_client.post("/query", json=invalid_query)
    assert response.status_code == 400, "Should return 400 for empty query"
    result = response.json()
    assert "error" in result, "Response should contain error message"
    
    # Invalid filter format
    invalid_query = {
        "query": "Test query",
        "filter": "not_a_dict"  # Filter should be a dict
    }
    
    response = api_client.post("/query", json=invalid_query)
    assert response.status_code == 400, "Should return 400 for invalid filter format"
    result = response.json()
    assert "error" in result, "Response should contain error message"


@pytest.mark.asyncio
async def test_empty_knowledge_base(api_client):
    """Test querying an empty knowledge base."""
    # Query without adding any documents
    response = api_client.post("/query", json={"query": "Test query"})
    assert response.status_code == 200, "Should handle query on empty knowledge base"
    result = response.json()
    assert result["status"] == "success", "Should return success status"
    assert "answer" in result["result"], "Should return an answer"
    # The answer should indicate no relevant information was found
    assert "no relevant information" in result["result"]["answer"].lower() or \
           "no information" in result["result"]["answer"].lower() or \
           "couldn't find" in result["result"]["answer"].lower(), \
           "Answer should indicate no information was found"


@pytest.mark.asyncio
async def test_invalid_document_update(api_client):
    """Test error handling for invalid document update."""
    # First add a document
    doc = {
        "id": "test_doc",
        "content": "This is a test document.",
        "type": "text",
        "metadata": {}
    }
    
    response = api_client.post("/knowledge/documents", json=doc)
    assert response.status_code == 200, "Failed to add document"
    
    # Try to update with mismatched ID
    update_doc = {
        "id": "different_id",  # Different from the URL parameter
        "content": "Updated content",
        "type": "text",
        "metadata": {}
    }
    
    response = api_client.put(f"/knowledge/documents/{doc['id']}", json=update_doc)
    assert response.status_code == 400, "Should return 400 for mismatched document ID"
    result = response.json()
    assert "error" in result, "Response should contain error message"


@pytest.mark.asyncio
async def test_invalid_api_endpoints(api_client):
    """Test error handling for invalid API endpoints."""
    # Non-existent endpoint
    response = api_client.get("/non_existent_endpoint")
    assert response.status_code == 404, "Should return 404 for non-existent endpoint"
    
    # Invalid HTTP method
    response = api_client.put("/query", json={"query": "Test query"})
    assert response.status_code == 405, "Should return 405 for invalid HTTP method"


@pytest.mark.asyncio
async def test_concurrent_document_operations(api_client):
    """Test error handling for concurrent document operations."""
    # Add multiple documents with the same ID
    doc = {
        "id": "concurrent_doc",
        "content": "This is a test document.",
        "type": "text",
        "metadata": {}
    }
    
    # First addition should succeed
    response = api_client.post("/knowledge/documents", json=doc)
    assert response.status_code == 200, "Failed to add first document"
    
    # Second addition with same ID should fail or update
    doc["content"] = "This is a different document with the same ID."
    response = api_client.post("/knowledge/documents", json=doc)
    
    # Either it should fail with 400 (if system prevents duplicates)
    # or it should succeed with 200 (if system updates existing documents)
    assert response.status_code in [200, 400], "Should handle duplicate document ID appropriately"
    
    # If it succeeded, verify the content was updated
    if response.status_code == 200:
        response = api_client.get(f"/knowledge/documents/{doc['id']}")
        assert response.status_code == 200, "Failed to retrieve document"
        result = response.json()
        assert "different document" in result["result"]["content"], "Document content should be updated"
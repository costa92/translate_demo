"""
End-to-end tests for user scenarios in the unified knowledge base system.

This module tests common user scenarios and workflows.
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
async def test_knowledge_base_creation_scenario(api_client):
    """Test the scenario of creating and populating a knowledge base."""
    # 1. Add a document about Python
    python_doc = {
        "id": "python_doc",
        "content": "Python is a high-level, interpreted programming language. "
                 "It was created by Guido van Rossum and first released in 1991. "
                 "Python's design philosophy emphasizes code readability with its "
                 "notable use of significant whitespace.",
        "type": "text",
        "metadata": {"source": "test", "topic": "programming", "language": "Python"}
    }
    
    response = api_client.post("/knowledge/documents", json=python_doc)
    assert response.status_code == 200, f"Failed to add Python document: {response.text}"
    
    # 2. Add a document about JavaScript
    js_doc = {
        "id": "js_doc",
        "content": "JavaScript is a programming language that conforms to the ECMAScript specification. "
                 "JavaScript is high-level, often just-in-time compiled, and multi-paradigm. "
                 "It has curly-bracket syntax, dynamic typing, prototype-based object-orientation, "
                 "and first-class functions.",
        "type": "text",
        "metadata": {"source": "test", "topic": "programming", "language": "JavaScript"}
    }
    
    response = api_client.post("/knowledge/documents", json=js_doc)
    assert response.status_code == 200, f"Failed to add JavaScript document: {response.text}"
    
    # 3. Add a document about Machine Learning
    ml_doc = {
        "id": "ml_doc",
        "content": "Machine learning is a subset of artificial intelligence that provides systems "
                 "the ability to automatically learn and improve from experience without being "
                 "explicitly programmed. Machine learning focuses on the development of computer "
                 "programs that can access data and use it to learn for themselves.",
        "type": "text",
        "metadata": {"source": "test", "topic": "ai", "field": "machine learning"}
    }
    
    response = api_client.post("/knowledge/documents", json=ml_doc)
    assert response.status_code == 200, f"Failed to add ML document: {response.text}"
    
    # 4. Query about Python
    response = api_client.post("/query", json={"query": "Tell me about Python"})
    assert response.status_code == 200, f"Query failed: {response.text}"
    result = response.json()
    assert "Python" in result["result"]["answer"], "Answer should mention Python"
    
    # 5. Query about programming languages with filter
    response = api_client.post(
        "/query", 
        json={
            "query": "What programming language has curly braces?",
            "filter": {"topic": "programming"}
        }
    )
    assert response.status_code == 200, f"Filtered query failed: {response.text}"
    result = response.json()
    assert "JavaScript" in result["result"]["answer"], "Answer should mention JavaScript"
    
    # 6. Query about AI
    response = api_client.post("/query", json={"query": "Explain machine learning"})
    assert response.status_code == 200, f"Query failed: {response.text}"
    result = response.json()
    assert "machine learning" in result["result"]["answer"].lower(), "Answer should mention machine learning"


@pytest.mark.asyncio
async def test_document_management_scenario(api_client):
    """Test the scenario of managing documents in the knowledge base."""
    # 1. Add a document
    doc = {
        "id": "test_doc",
        "content": "This is a test document for document management scenario.",
        "type": "text",
        "metadata": {"source": "test", "category": "test_docs"}
    }
    
    response = api_client.post("/knowledge/documents", json=doc)
    assert response.status_code == 200, f"Failed to add document: {response.text}"
    
    # 2. Retrieve the document
    response = api_client.get(f"/knowledge/documents/{doc['id']}")
    assert response.status_code == 200, f"Failed to retrieve document: {response.text}"
    result = response.json()
    assert result["result"]["id"] == doc["id"], "Retrieved document should have correct ID"
    
    # 3. Update the document
    updated_doc = {
        "id": doc["id"],
        "content": "This is an updated test document.",
        "type": "text",
        "metadata": {"source": "test", "category": "test_docs", "status": "updated"}
    }
    
    response = api_client.put(f"/knowledge/documents/{doc['id']}", json=updated_doc)
    assert response.status_code == 200, f"Failed to update document: {response.text}"
    
    # 4. Verify the update
    response = api_client.get(f"/knowledge/documents/{doc['id']}")
    assert response.status_code == 200, f"Failed to retrieve updated document: {response.text}"
    result = response.json()
    assert "updated" in result["result"]["content"], "Document content should be updated"
    assert result["result"]["metadata"]["status"] == "updated", "Document metadata should be updated"
    
    # 5. List documents with filter
    response = api_client.get("/knowledge/documents", params={"category": "test_docs"})
    assert response.status_code == 200, f"Failed to list documents with filter: {response.text}"
    result = response.json()
    assert len(result["result"]["documents"]) > 0, "Should find documents with filter"
    
    # 6. Delete the document
    response = api_client.delete(f"/knowledge/documents/{doc['id']}")
    assert response.status_code == 200, f"Failed to delete document: {response.text}"
    
    # 7. Verify deletion
    response = api_client.get(f"/knowledge/documents/{doc['id']}")
    assert response.status_code == 404, "Document should be deleted"


@pytest.mark.asyncio
async def test_multi_turn_conversation_scenario(api_client):
    """Test a multi-turn conversation scenario with context maintenance."""
    # 1. Add documents about different programming languages
    languages = [
        {
            "id": "python_doc",
            "content": "Python is a high-level, interpreted programming language created by Guido van Rossum. "
                     "It's known for its readability and simplicity.",
            "type": "text",
            "metadata": {"topic": "programming", "language": "Python"}
        },
        {
            "id": "js_doc",
            "content": "JavaScript is a scripting language that enables interactive web pages. "
                     "It was created by Brendan Eich at Netscape.",
            "type": "text",
            "metadata": {"topic": "programming", "language": "JavaScript"}
        },
        {
            "id": "java_doc",
            "content": "Java is a class-based, object-oriented programming language developed by Sun Microsystems. "
                     "It's designed to have as few implementation dependencies as possible.",
            "type": "text",
            "metadata": {"topic": "programming", "language": "Java"}
        }
    ]
    
    for doc in languages:
        response = api_client.post("/knowledge/documents", json=doc)
        assert response.status_code == 200, f"Failed to add document: {response.text}"
    
    # 2. Start a conversation about Python
    conversation_id = "test_conversation"
    response = api_client.post(
        "/query", 
        json={
            "query": "Tell me about Python",
            "conversation_id": conversation_id
        }
    )
    assert response.status_code == 200, f"Query failed: {response.text}"
    result = response.json()
    assert "Python" in result["result"]["answer"], "Answer should mention Python"
    
    # 3. Follow-up question about its creator
    response = api_client.post(
        "/query", 
        json={
            "query": "Who created it?",
            "conversation_id": conversation_id
        }
    )
    assert response.status_code == 200, f"Follow-up query failed: {response.text}"
    result = response.json()
    assert "Guido" in result["result"]["answer"], "Answer should mention Guido van Rossum"
    
    # 4. Switch topic to JavaScript
    response = api_client.post(
        "/query", 
        json={
            "query": "Now tell me about JavaScript",
            "conversation_id": conversation_id
        }
    )
    assert response.status_code == 200, f"Topic switch query failed: {response.text}"
    result = response.json()
    assert "JavaScript" in result["result"]["answer"], "Answer should mention JavaScript"
    
    # 5. Follow-up question about JavaScript's creator
    response = api_client.post(
        "/query", 
        json={
            "query": "Who created this language?",
            "conversation_id": conversation_id
        }
    )
    assert response.status_code == 200, f"Follow-up query failed: {response.text}"
    result = response.json()
    assert "Brendan" in result["result"]["answer"] or "Eich" in result["result"]["answer"], \
        "Answer should mention Brendan Eich"
    
    # 6. Compare the languages
    response = api_client.post(
        "/query", 
        json={
            "query": "Compare these programming languages",
            "conversation_id": conversation_id
        }
    )
    assert response.status_code == 200, f"Comparison query failed: {response.text}"
    result = response.json()
    assert "Python" in result["result"]["answer"] and "JavaScript" in result["result"]["answer"], \
        "Answer should mention both Python and JavaScript"
"""
Tests for the API server.

This module contains tests for the FastAPI application server.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.knowledge_base.api.server import create_app, get_orchestrator, get_config
from src.knowledge_base.core.config import Config
from src.knowledge_base.agents.orchestrator import OrchestratorAgent


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = MagicMock(spec=Config)
    config.api.cors_origins = ["http://localhost:3000"]
    config.api.port = 8000
    config.api.host = "0.0.0.0"
    config.api.debug = True
    return config


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator agent."""
    orchestrator = MagicMock(spec=OrchestratorAgent)
    
    # Mock receive_request method
    async def mock_receive_request(source, request_type, payload):
        if request_type == "query":
            return {
                "answer": "Test answer",
                "chunks": [
                    {"id": "1", "text": "Test chunk 1", "document_id": "doc1", "metadata": {}},
                    {"id": "2", "text": "Test chunk 2", "document_id": "doc1", "metadata": {}}
                ]
            }
        elif request_type == "add_document":
            return {"document_id": "doc1", "chunk_ids": ["1", "2"], "success": True}
        elif request_type == "delete_document":
            return {"success": True}
        elif request_type == "health":
            return {"status": "healthy", "components": {"storage": "ok", "processing": "ok"}}
        return {"status": "success"}
    
    orchestrator.receive_request = mock_receive_request
    return orchestrator


@pytest.fixture
def app(mock_config, mock_orchestrator):
    """Create a FastAPI application for testing."""
    # Override dependency injection
    app = create_app(mock_config)
    app.dependency_overrides[get_config] = lambda: mock_config
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestAPIServer:
    """Tests for the API server."""
    
    def test_create_app(self, mock_config):
        """Test creating the FastAPI application."""
        app = create_app(mock_config)
        
        assert isinstance(app, FastAPI)
        assert app.title == "Knowledge Base API"
    
    def test_health_endpoint(self, client, mock_orchestrator):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_query_endpoint(self, client, mock_orchestrator):
        """Test the query endpoint."""
        response = client.post(
            "/api/query",
            json={"query": "Test query", "filter": {"source": "test"}}
        )
        
        assert response.status_code == 200
        assert "answer" in response.json()
        assert "chunks" in response.json()
    
    def test_add_document_endpoint(self, client, mock_orchestrator):
        """Test the add document endpoint."""
        response = client.post(
            "/api/documents",
            json={
                "content": "Test document content",
                "type": "text",
                "metadata": {"source": "test"}
            }
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "document_id" in response.json()
        assert "chunk_ids" in response.json()
    
    def test_delete_document_endpoint(self, client, mock_orchestrator):
        """Test the delete document endpoint."""
        response = client.delete("/api/documents/doc1")
        
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_api_documentation(self, client):
        """Test the API documentation endpoint."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_schema(self, client):
        """Test the OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        
        schema = response.json()
        assert "paths" in schema
        assert "/api/query" in schema["paths"]
        assert "/api/documents" in schema["paths"]
    
    def test_cors_headers(self, client):
        """Test CORS headers."""
        response = client.options(
            "/api/query",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"}
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    
    def test_error_handling(self, client, mock_orchestrator):
        """Test error handling."""
        # Mock orchestrator to raise an exception
        async def mock_error(*args, **kwargs):
            raise ValueError("Test error")
        
        mock_orchestrator.receive_request = mock_error
        
        response = client.post(
            "/api/query",
            json={"query": "Test query"}
        )
        
        assert response.status_code == 500
        assert "error" in response.json()
    
    def test_validation_error(self, client):
        """Test validation error handling."""
        response = client.post(
            "/api/query",
            json={}  # Missing required field 'query'
        )
        
        assert response.status_code == 422
        assert "detail" in response.json()
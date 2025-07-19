"""
Tests for the API middleware components.

This module contains tests for authentication, logging, and rate limiting middleware.
"""

import pytest
import time
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from src.knowledge_base.api.middleware.auth import AuthMiddleware, verify_api_key
from src.knowledge_base.api.middleware.logging import LoggingMiddleware
from src.knowledge_base.api.middleware.rate_limit import RateLimitMiddleware
from src.knowledge_base.api.auth.store import APIKeyStore


@pytest.fixture
def mock_api_key_store():
    """Create a mock API key store."""
    store = MagicMock(spec=APIKeyStore)
    store.verify_key = MagicMock(return_value=True)
    return store


@pytest.fixture
def auth_app(mock_api_key_store):
    """Create a FastAPI application with auth middleware for testing."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, api_key_store=mock_api_key_store)
    
    @app.get("/protected")
    async def protected_route():
        return {"status": "success"}
    
    @app.get("/public", include_in_schema=False)
    async def public_route():
        return {"status": "success"}
    
    return app


@pytest.fixture
def logging_app():
    """Create a FastAPI application with logging middleware for testing."""
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)
    
    @app.get("/test")
    async def test_route():
        return {"status": "success"}
    
    return app


@pytest.fixture
def rate_limit_app():
    """Create a FastAPI application with rate limiting middleware for testing."""
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        rate_limit=2,  # 2 requests per second
        window_size=1  # 1 second window
    )
    
    @app.get("/test")
    async def test_route():
        return {"status": "success"}
    
    return app


class TestAuthMiddleware:
    """Tests for the authentication middleware."""
    
    def test_protected_route_with_valid_key(self, auth_app, mock_api_key_store):
        """Test accessing a protected route with a valid API key."""
        client = TestClient(auth_app)
        
        response = client.get(
            "/protected",
            headers={"X-API-Key": "valid_key"}
        )
        
        assert response.status_code == 200
        mock_api_key_store.verify_key.assert_called_once_with("valid_key")
    
    def test_protected_route_without_key(self, auth_app):
        """Test accessing a protected route without an API key."""
        client = TestClient(auth_app)
        
        response = client.get("/protected")
        
        assert response.status_code == 401
        assert "API key required" in response.json()["detail"]
    
    def test_protected_route_with_invalid_key(self, auth_app, mock_api_key_store):
        """Test accessing a protected route with an invalid API key."""
        mock_api_key_store.verify_key.return_value = False
        client = TestClient(auth_app)
        
        response = client.get(
            "/protected",
            headers={"X-API-Key": "invalid_key"}
        )
        
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]
    
    def test_public_route(self, auth_app):
        """Test accessing a public route without an API key."""
        client = TestClient(auth_app)
        
        response = client.get("/public")
        
        assert response.status_code == 200
    
    def test_verify_api_key_dependency(self, mock_api_key_store):
        """Test the verify_api_key dependency."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_route(api_key: str = Depends(verify_api_key)):
            return {"api_key": api_key}
        
        app.dependency_overrides[APIKeyStore] = lambda: mock_api_key_store
        
        client = TestClient(app)
        
        response = client.get(
            "/test",
            headers={"X-API-Key": "test_key"}
        )
        
        assert response.status_code == 200
        assert response.json()["api_key"] == "test_key"


class TestLoggingMiddleware:
    """Tests for the logging middleware."""
    
    @patch("src.knowledge_base.api.middleware.logging.logger")
    def test_successful_request_logging(self, mock_logger, logging_app):
        """Test logging of successful requests."""
        client = TestClient(logging_app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        mock_logger.info.assert_called()
    
    @patch("src.knowledge_base.api.middleware.logging.logger")
    def test_error_request_logging(self, mock_logger, logging_app):
        """Test logging of error requests."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/error")
        async def error_route():
            raise HTTPException(status_code=500, detail="Test error")
        
        client = TestClient(app)
        
        response = client.get("/error")
        
        assert response.status_code == 500
        mock_logger.error.assert_called()
    
    @patch("src.knowledge_base.api.middleware.logging.logger")
    def test_request_id_generation(self, mock_logger, logging_app):
        """Test that a request ID is generated and included in logs."""
        client = TestClient(logging_app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        
        # Check that the request ID was included in the log
        log_call_args = mock_logger.info.call_args[0][0]
        assert "request_id" in log_call_args


class TestRateLimitMiddleware:
    """Tests for the rate limiting middleware."""
    
    def test_rate_limit_not_exceeded(self, rate_limit_app):
        """Test requests within the rate limit."""
        client = TestClient(rate_limit_app)
        
        # Make requests within the rate limit
        response1 = client.get("/test")
        response2 = client.get("/test")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    def test_rate_limit_exceeded(self, rate_limit_app):
        """Test requests exceeding the rate limit."""
        client = TestClient(rate_limit_app)
        
        # Make requests exceeding the rate limit
        response1 = client.get("/test")
        response2 = client.get("/test")
        response3 = client.get("/test")  # This should exceed the rate limit
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 429
        assert "Rate limit exceeded" in response3.json()["detail"]
    
    def test_rate_limit_reset(self, rate_limit_app):
        """Test that the rate limit resets after the window period."""
        client = TestClient(rate_limit_app)
        
        # Make requests to reach the rate limit
        response1 = client.get("/test")
        response2 = client.get("/test")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Wait for the rate limit window to reset
        time.sleep(1.1)  # Slightly more than the window size
        
        # Make another request after the window reset
        response3 = client.get("/test")
        
        assert response3.status_code == 200
    
    def test_different_clients(self, rate_limit_app):
        """Test that rate limits are applied per client."""
        client1 = TestClient(rate_limit_app)
        client2 = TestClient(rate_limit_app)
        
        # Make requests from client1
        response1 = client1.get("/test", headers={"X-Forwarded-For": "1.1.1.1"})
        response2 = client1.get("/test", headers={"X-Forwarded-For": "1.1.1.1"})
        
        # Make requests from client2
        response3 = client2.get("/test", headers={"X-Forwarded-For": "2.2.2.2"})
        response4 = client2.get("/test", headers={"X-Forwarded-For": "2.2.2.2"})
        
        # All requests should succeed because they're from different clients
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        assert response4.status_code == 200
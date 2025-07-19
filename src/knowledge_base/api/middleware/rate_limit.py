"""
Rate limiting middleware for the knowledge base API.

This middleware implements rate limiting for API requests.
"""

import time
import logging
from typing import Callable, Dict, List, Tuple
from collections import defaultdict

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.knowledge_base.core.config import Config

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting."""
    
    def __init__(self, app, config: Config):
        """Initialize the middleware.
        
        Args:
            app: The FastAPI application.
            config: The configuration instance.
        """
        super().__init__(app)
        self.config = config
        self.request_counts: Dict[str, List[float]] = defaultdict(list)
        self.public_paths: List[str] = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process a request and apply rate limiting.
        
        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.
            
        Returns:
            The response.
        """
        # Skip rate limiting for public paths
        if any(request.url.path.startswith(path) for path in self.public_paths):
            return await call_next(request)
        
        # Skip rate limiting if disabled
        if not self.config.api.rate_limit_enabled:
            return await call_next(request)
        
        # Get client identifier (IP address or API key)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_id):
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get a unique identifier for the client.
        
        Args:
            request: The incoming request.
            
        Returns:
            A unique client identifier.
        """
        # Use API key if available
        if self.config.api.auth_enabled and self.config.api.auth_provider == "api_key":
            api_key = request.headers.get(self.config.api.api_key_header)
            if api_key:
                return f"api_key:{api_key}"
        
        # Fall back to IP address
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if a client has exceeded the rate limit.
        
        Args:
            client_id: The client identifier.
            
        Returns:
            True if the client is within the rate limit, False otherwise.
        """
        current_time = time.time()
        time_window = self.config.api.rate_limit_period
        max_requests = self.config.api.rate_limit_requests
        
        # Get the client's request timestamps
        timestamps = self.request_counts[client_id]
        
        # Remove timestamps outside the current window
        timestamps = [ts for ts in timestamps if current_time - ts < time_window]
        
        # Check if the client has exceeded the rate limit
        if len(timestamps) >= max_requests:
            return False
        
        # Add the current timestamp
        timestamps.append(current_time)
        self.request_counts[client_id] = timestamps
        
        return True
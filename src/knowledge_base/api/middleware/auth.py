"""
Authentication middleware for the knowledge base API.

This middleware handles API authentication.
"""

import logging
from typing import Callable, Optional, Dict, List

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import AuthenticationError
from src.knowledge_base.api.auth.store import AuthStore
from src.knowledge_base.api.models.auth import Permission

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API authentication."""
    
    def __init__(self, app, config: Config):
        """Initialize the middleware.
        
        Args:
            app: The FastAPI application.
            config: The configuration instance.
        """
        super().__init__(app)
        self.config = config
        self.auth_store = AuthStore(config)
        self.public_paths: List[str] = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        # Path-permission mapping for authorization
        self.path_permissions: Dict[str, Permission] = {
            # Knowledge management endpoints
            "/knowledge": Permission.KNOWLEDGE_READ,
            "/knowledge/add": Permission.KNOWLEDGE_WRITE,
            "/knowledge/update": Permission.KNOWLEDGE_WRITE,
            "/knowledge/delete": Permission.KNOWLEDGE_DELETE,
            
            # Query endpoints
            "/query": Permission.QUERY_BASIC,
            "/query/stream": Permission.QUERY_BASIC,
            "/query/batch": Permission.QUERY_ADVANCED,
            
            # Admin endpoints
            "/admin/health": Permission.ADMIN_READ,
            "/admin/status": Permission.ADMIN_READ,
            "/admin/maintenance": Permission.ADMIN_WRITE,
            "/admin/config": Permission.ADMIN_READ,
            "/admin/metrics": Permission.ADMIN_READ,
            "/admin/logs": Permission.ADMIN_READ,
            "/admin/backup": Permission.ADMIN_SYSTEM,
            "/admin/restore": Permission.ADMIN_SYSTEM,
            "/admin/restart": Permission.ADMIN_SYSTEM,
            
            # User management endpoints
            "/admin/users": Permission.USER_READ,
            "/admin/users/create": Permission.USER_WRITE,
            "/admin/users/update": Permission.USER_WRITE,
            "/admin/users/delete": Permission.USER_DELETE,
            "/admin/api-keys": Permission.USER_READ,
            "/admin/api-keys/create": Permission.USER_WRITE,
            "/admin/api-keys/update": Permission.USER_WRITE,
            "/admin/api-keys/delete": Permission.USER_DELETE,
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process a request and authenticate.
        
        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.
            
        Returns:
            The response.
        """
        # Skip authentication for public paths
        if any(request.url.path.startswith(path) for path in self.public_paths):
            return await call_next(request)
        
        # Skip authentication if disabled
        if not self.config.api.auth_enabled:
            return await call_next(request)
        
        # Authenticate based on the configured provider
        if self.config.api.auth_provider == "api_key":
            api_key = request.headers.get(self.config.api.api_key_header)
            if not api_key:
                logger.warning(f"Missing API key: {request.method} {request.url.path}")
                raise HTTPException(status_code=401, detail="API key required")
            
            # Authenticate API key
            user = self.auth_store.authenticate_api_key(api_key)
            if not user:
                logger.warning(f"Invalid API key: {request.method} {request.url.path}")
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            # Add user to request state
            request.state.user = user
            request.state.user_id = user.id
            
            # Check authorization for the endpoint
            if not self._check_authorization(request, user):
                logger.warning(f"Unauthorized access attempt: {request.method} {request.url.path} by user {user.username}")
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Other authentication providers can be added here
        
        return await call_next(request)
    
    def _check_authorization(self, request: Request, user) -> bool:
        """Check if the user is authorized to access the endpoint.
        
        Args:
            request: The request.
            user: The authenticated user.
            
        Returns:
            True if the user is authorized, False otherwise.
        """
        # Find the most specific path match
        path = request.url.path
        required_permission = None
        
        # Check exact path match
        if path in self.path_permissions:
            required_permission = self.path_permissions[path]
        else:
            # Check prefix matches
            for prefix, permission in self.path_permissions.items():
                if path.startswith(prefix):
                    required_permission = permission
                    break
        
        # If no permission is required, allow access
        if required_permission is None:
            return True
        
        # Check if user has the required permission
        return user.has_permission(required_permission)
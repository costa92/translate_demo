"""
API server for the unified knowledge base system.

This module provides a FastAPI application for the knowledge base system.
"""

import logging
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from src.knowledge_base.core.logging_config import configure_logging
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import KnowledgeBaseError

# Import dependencies
from .dependencies import (
    initialize_dependencies,
    get_config,
    get_orchestrator,
    get_websocket_manager,
    get_monitoring
)

# Import middleware
from .middleware.logging import LoggingMiddleware
from .middleware.auth import AuthMiddleware
from .middleware.rate_limit import RateLimitMiddleware

logger = logging.getLogger(__name__)


async def exception_handler(request: Request, exc: KnowledgeBaseError) -> JSONResponse:
    """Handle knowledge base exceptions.
    
    Args:
        request: The request that caused the exception.
        exc: The exception that was raised.
        
    Returns:
        A JSON response with the error details.
    """
    error_type = type(exc).__name__
    status_code = 500
    
    # Map exception types to status codes
    if error_type == "ConfigurationError":
        status_code = 400
    elif error_type == "ValidationError":
        status_code = 400
    elif error_type == "NotFoundError":
        status_code = 404
    elif error_type == "AuthenticationError":
        status_code = 401
    elif error_type == "AuthorizationError":
        status_code = 403
    elif error_type == "RateLimitError":
        status_code = 429
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": str(exc),
            "error_type": error_type,
            "status_code": status_code
        }
    )


def create_app(config: Config) -> FastAPI:
    """Create a FastAPI application.
    
    Args:
        config: The configuration instance.
        
    Returns:
        A FastAPI application.
    """
    # Initialize dependencies
    initialize_dependencies(config)
    
    # Create FastAPI app
    app = FastAPI(
        title="Knowledge Base API",
        description="""
        # Unified Knowledge Base System API
        
        This API provides access to the Unified Knowledge Base System, allowing you to:
        
        - Add, update, and retrieve documents
        - Query the knowledge base with natural language
        - Manage users and API keys
        - Monitor system health and performance
        - Perform administrative tasks
        
        ## Authentication
        
        Most endpoints require authentication using either:
        - API key (via `X-API-Key` header)
        - Bearer token (via `Authorization` header)
        
        ## WebSocket Support
        
        Real-time communication is available through WebSocket at `/ws/{client_id}`.
        
        ## Rate Limiting
        
        API requests are subject to rate limiting based on your account tier.
        """,
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json" if config.api.docs_enabled else None,
        terms_of_service="https://example.com/terms/",
        contact={
            "name": "API Support",
            "url": "https://example.com/support",
            "email": "support@example.com",
        },
        license_info={
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=config.api.cors_allow_credentials,
        allow_methods=config.api.cors_allow_methods,
        allow_headers=config.api.cors_allow_headers,
    )
    
    # Add custom middleware
    app.add_middleware(LoggingMiddleware, config=config)
    
    # Add authentication middleware if enabled
    if config.api.auth_enabled:
        app.add_middleware(AuthMiddleware, config=config)
    
    # Add rate limiting middleware if enabled
    if config.api.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware, config=config)
    
    # Add exception handlers
    app.add_exception_handler(KnowledgeBaseError, exception_handler)
    
    # Dependencies are already initialized
    
    # Import routes after dependencies are initialized
    from .routes.knowledge import router as knowledge_router
    from .routes.query import router as query_router
    from .routes.admin import router as admin_router
    from .routes.users import router as users_router
    from .routes.monitoring import router as monitoring_router
    
    # Configure logging
    configure_logging(config)
    
    # Include routers
    app.include_router(knowledge_router)
    app.include_router(query_router)
    app.include_router(admin_router)
    app.include_router(users_router)
    app.include_router(monitoring_router)
    
    # Mount static documentation files
    if config.api.docs_enabled:
        import os
        docs_dir = os.path.join(os.path.dirname(__file__), "docs")
        if os.path.exists(docs_dir):
            app.mount("/api-docs", StaticFiles(directory=docs_dir), name="api-docs")
    
    # Custom documentation endpoints
    if config.api.docs_enabled:
        @app.get("/docs", include_in_schema=False)
        async def custom_swagger_ui_html():
            return get_swagger_ui_html(
                openapi_url="/openapi.json",
                title="Knowledge Base API Documentation",
                swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
                swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
                swagger_ui_parameters={
                    "persistAuthorization": True,
                    "displayRequestDuration": True,
                    "tryItOutEnabled": True,
                    "filter": True,
                    "deepLinking": True
                }
            )

        @app.get("/redoc", include_in_schema=False)
        async def custom_redoc_html():
            return get_redoc_html(
                openapi_url="/openapi.json",
                title="Knowledge Base API Documentation",
                redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            )
            
        @app.get("/api-docs", include_in_schema=False)
        async def api_docs_redirect():
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/api-docs/interactive.html")
            
        # Custom OpenAPI schema with enhanced documentation
        def custom_openapi():
            if app.openapi_schema:
                return app.openapi_schema
                
            openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
                terms_of_service=app.terms_of_service,
                contact=app.contact,
                license_info=app.license_info,
            )
            
            # Add security schemes
            openapi_schema["components"]["securitySchemes"] = {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key authentication"
                },
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT Bearer token authentication"
                }
            }
            
            # Apply security globally
            openapi_schema["security"] = [
                {"ApiKeyAuth": []},
                {"BearerAuth": []}
            ]
            
            # Add WebSocket documentation
            openapi_schema["components"]["schemas"]["WebSocketMessage"] = {
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "Unique identifier for the request"
                    },
                    "request_type": {
                        "type": "string",
                        "description": "Type of request (query, subscribe, unsubscribe, etc.)"
                    },
                    "payload": {
                        "type": "object",
                        "description": "Request payload"
                    }
                }
            }
            
            # Add WebSocket path
            openapi_schema["paths"]["/ws/{client_id}"] = {
                "get": {
                    "summary": "WebSocket endpoint",
                    "description": "Connect to the WebSocket API for real-time communication",
                    "operationId": "websocket_endpoint",
                    "tags": ["WebSocket"],
                    "parameters": [
                        {
                            "name": "client_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Client identifier"
                        }
                    ]
                }
            }
            
            app.openapi_schema = openapi_schema
            return app.openapi_schema
            
        app.openapi = custom_openapi
    
    # Add startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        """Initialize components on startup."""
        logger.info("Starting Knowledge Base API server")
        orchestrator = get_orchestrator()
        await orchestrator.start()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown."""
        logger.info("Shutting down Knowledge Base API server")
        # Cancel WebSocket notification task if running
        websocket_manager = get_websocket_manager()
        if websocket_manager and hasattr(websocket_manager, "notification_task") and websocket_manager.notification_task:
            websocket_manager.notification_task.cancel()
        orchestrator = get_orchestrator()
        await orchestrator.stop()
    
    # Add health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok"}
    
    # Add WebSocket endpoint
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        """WebSocket endpoint for real-time communication.
        
        Args:
            websocket: The WebSocket connection.
            client_id: The client identifier.
        """
        await _websocket_manager.handle_client(websocket, client_id)
    
    return app


def run_app(config: Optional[Config] = None) -> None:
    """Run the FastAPI application with uvicorn.
    
    Args:
        config: The configuration instance. If not provided, a default configuration will be used.
    """
    import uvicorn
    
    if config is None:
        config = Config()
    
    app = create_app(config)
    
    uvicorn.run(
        app,
        host=config.api.host,
        port=config.api.port,
        log_level=config.system.log_level.lower()
    )
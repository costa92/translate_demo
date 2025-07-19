"""
Logging middleware for the knowledge base API.

This middleware logs API requests and responses, including audit logging.
"""

import time
import logging
import json
import os
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from pathlib import Path

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.knowledge_base.core.config import Config

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("audit")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API requests and responses."""
    
    def __init__(self, app, config: Config = None):
        """Initialize the middleware.
        
        Args:
            app: The FastAPI application.
            config: The configuration instance.
        """
        super().__init__(app)
        self.config = config
        self.audit_log_enabled = True
        self.audit_log_dir = Path(os.environ.get("KB_AUDIT_LOG_DIR", "./.kb_audit"))
        
        # Create audit log directory if it doesn't exist
        if self.audit_log_enabled:
            self.audit_log_dir.mkdir(exist_ok=True, parents=True)
            
            # Configure audit logger
            audit_handler = logging.FileHandler(
                self.audit_log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
            )
            audit_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            audit_logger.addHandler(audit_handler)
            audit_logger.setLevel(logging.INFO)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process a request and log details.
        
        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.
            
        Returns:
            The response.
        """
        start_time = time.time()
        request_id = f"{int(start_time * 1000)}"
        
        # Extract user information if available
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "user", None)
        if username:
            username = getattr(username, "username", None)
        
        # Log request details
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"Client: {request.client.host if request.client else 'unknown'} "
            f"User: {username or 'anonymous'} "
            f"ID: {request_id}"
        )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Log response details
            process_time = time.time() - start_time
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.3f}s "
                f"ID: {request_id}"
            )
            
            # Create audit log entry
            if self.audit_log_enabled:
                self._create_audit_log(
                    request=request,
                    response=response,
                    user_id=user_id,
                    username=username,
                    request_id=request_id,
                    process_time=process_time,
                    error=None
                )
            
            return response
        except Exception as e:
            # Log exceptions
            process_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} "
                f"Exception: {str(e)} "
                f"Time: {process_time:.3f}s "
                f"ID: {request_id}"
            )
            
            # Create audit log entry for error
            if self.audit_log_enabled:
                self._create_audit_log(
                    request=request,
                    response=None,
                    user_id=user_id,
                    username=username,
                    request_id=request_id,
                    process_time=process_time,
                    error=str(e)
                )
            
            raise
    
    def _create_audit_log(
        self,
        request: Request,
        response: Optional[Response],
        user_id: Optional[str],
        username: Optional[str],
        request_id: str,
        process_time: float,
        error: Optional[str]
    ) -> None:
        """Create an audit log entry.
        
        Args:
            request: The request.
            response: The response.
            user_id: The user ID.
            username: The username.
            request_id: The request ID.
            process_time: The processing time.
            error: The error message, if any.
        """
        try:
            # Create audit log entry
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
                "user_id": user_id,
                "username": username or "anonymous",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "status_code": response.status_code if response else None,
                "process_time": process_time,
                "error": error
            }
            
            # Log audit entry
            audit_logger.info(json.dumps(audit_entry))
            
            # Write to daily audit log file
            if self.config and getattr(self.config.api, "detailed_audit_log", False):
                log_file = self.audit_log_dir / f"detailed_{datetime.now().strftime('%Y%m%d')}.jsonl"
                with open(log_file, "a") as f:
                    f.write(json.dumps(audit_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
"""
Exception definitions for the unified knowledge base system.

This module provides a comprehensive exception hierarchy for the knowledge base system,
with specific exception types for each module and error handling utilities.
"""
from typing import Dict, Any, Optional, List, Callable, Type, Union
import traceback
import logging
import sys

logger = logging.getLogger(__name__)


class KnowledgeBaseError(Exception):
    """Base exception for all knowledge base errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for API responses."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


# Configuration Exceptions

class ConfigurationError(KnowledgeBaseError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, config_key: str = None, config_value: Any = None):
        details = {"config_key": config_key}
        if config_value is not None:
            details["config_value"] = str(config_value)
        super().__init__(message, "CONFIG_ERROR", details)
        self.config_key = config_key
        self.config_value = config_value


class MissingConfigurationError(ConfigurationError):
    """Exception raised when a required configuration is missing."""
    
    def __init__(self, config_key: str):
        super().__init__(f"Missing required configuration: {config_key}", config_key)


class InvalidConfigurationError(ConfigurationError):
    """Exception raised when a configuration value is invalid."""
    
    def __init__(self, config_key: str, config_value: Any, reason: str = None):
        message = f"Invalid configuration value for {config_key}: {config_value}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, config_key, config_value)
        self.reason = reason


# Storage Exceptions

class StorageError(KnowledgeBaseError):
    """Base exception for storage errors."""
    
    def __init__(self, message: str, operation: str = None, provider: str = None):
        details = {}
        if operation:
            details["operation"] = operation
        if provider:
            details["provider"] = provider
        super().__init__(message, "STORAGE_ERROR", details)
        self.operation = operation
        self.provider = provider


class DocumentNotFoundError(StorageError):
    """Exception raised when a document is not found."""
    
    def __init__(self, document_id: str, provider: str = None):
        super().__init__(
            f"Document not found: {document_id}", 
            operation="retrieve", 
            provider=provider
        )
        self.document_id = document_id


class ChunkNotFoundError(StorageError):
    """Exception raised when a chunk is not found."""
    
    def __init__(self, chunk_id: str, provider: str = None):
        super().__init__(
            f"Chunk not found: {chunk_id}", 
            operation="retrieve", 
            provider=provider
        )
        self.chunk_id = chunk_id


class StorageConnectionError(StorageError):
    """Exception raised when there's an error connecting to the storage."""
    
    def __init__(self, provider: str, reason: str = None):
        message = f"Failed to connect to storage provider: {provider}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, operation="connect", provider=provider)
        self.reason = reason


class StorageOperationError(StorageError):
    """Exception raised when a storage operation fails."""
    
    def __init__(self, operation: str, provider: str = None, reason: str = None):
        message = f"Storage operation failed: {operation}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, operation=operation, provider=provider)
        self.reason = reason


class StorageQuotaExceededError(StorageError):
    """Exception raised when storage quota is exceeded."""
    
    def __init__(self, provider: str = None, limit: str = None):
        details = {"provider": provider}
        if limit:
            details["limit"] = limit
        super().__init__(
            f"Storage quota exceeded for provider: {provider}", 
            operation="add", 
            provider=provider
        )
        self.limit = limit


# Processing Exceptions

class ProcessingError(KnowledgeBaseError):
    """Base exception for document processing errors."""
    
    def __init__(self, message: str, document_id: str = None, stage: str = None):
        details = {}
        if document_id:
            details["document_id"] = document_id
        if stage:
            details["stage"] = stage
        super().__init__(message, "PROCESSING_ERROR", details)
        self.document_id = document_id
        self.stage = stage


class DocumentTypeError(ProcessingError):
    """Exception raised when a document type is not supported."""
    
    def __init__(self, document_type: str, document_id: str = None):
        super().__init__(
            f"Unsupported document type: {document_type}", 
            document_id=document_id, 
            stage="type_detection"
        )
        self.document_type = document_type


class ChunkingError(ProcessingError):
    """Exception raised when chunking fails."""
    
    def __init__(self, reason: str, document_id: str = None, strategy: str = None):
        details = {
            "document_id": document_id,
            "strategy": strategy
        }
        super().__init__(
            f"Chunking failed: {reason}", 
            document_id=document_id, 
            stage="chunking"
        )
        self.reason = reason
        self.strategy = strategy


class EmbeddingError(ProcessingError):
    """Exception raised when embedding generation fails."""
    
    def __init__(self, reason: str, model: str = None, text_length: int = None):
        details = {}
        if model:
            details["model"] = model
        if text_length:
            details["text_length"] = text_length
        super().__init__(f"Embedding failed: {reason}", stage="embedding")
        self.reason = reason
        self.model = model
        self.text_length = text_length


class MetadataExtractionError(ProcessingError):
    """Exception raised when metadata extraction fails."""
    
    def __init__(self, reason: str, document_id: str = None):
        super().__init__(
            f"Metadata extraction failed: {reason}", 
            document_id=document_id, 
            stage="metadata_extraction"
        )
        self.reason = reason


# Retrieval Exceptions

class RetrievalError(KnowledgeBaseError):
    """Base exception for retrieval errors."""
    
    def __init__(self, message: str, query: str = None, strategy: str = None):
        details = {}
        if query:
            details["query"] = query
        if strategy:
            details["strategy"] = strategy
        super().__init__(message, "RETRIEVAL_ERROR", details)
        self.query = query
        self.strategy = strategy


class EmptyQueryError(RetrievalError):
    """Exception raised when a query is empty."""
    
    def __init__(self):
        super().__init__("Query cannot be empty", query="")


class NoResultsFoundError(RetrievalError):
    """Exception raised when no results are found for a query."""
    
    def __init__(self, query: str, strategy: str = None):
        super().__init__(f"No results found for query: {query}", query=query, strategy=strategy)


class InvalidFilterError(RetrievalError):
    """Exception raised when a filter is invalid."""
    
    def __init__(self, filter_expr: str, reason: str = None):
        message = f"Invalid filter expression: {filter_expr}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)
        self.filter_expr = filter_expr
        self.reason = reason


class RetrievalTimeoutError(RetrievalError):
    """Exception raised when retrieval times out."""
    
    def __init__(self, query: str, timeout_seconds: float, strategy: str = None):
        super().__init__(
            f"Retrieval timed out after {timeout_seconds} seconds", 
            query=query, 
            strategy=strategy
        )
        self.timeout_seconds = timeout_seconds


# Generation Exceptions

class GenerationError(KnowledgeBaseError):
    """Base exception for generation errors."""
    
    def __init__(self, message: str, provider: str = None, model: str = None):
        details = {}
        if provider:
            details["provider"] = provider
        if model:
            details["model"] = model
        super().__init__(message, "GENERATION_ERROR", details)
        self.provider = provider
        self.model = model


class PromptTooLongError(GenerationError):
    """Exception raised when a prompt is too long."""
    
    def __init__(self, prompt_length: int, max_length: int, provider: str = None, model: str = None):
        super().__init__(
            f"Prompt too long: {prompt_length} tokens (max: {max_length})", 
            provider=provider, 
            model=model
        )
        self.prompt_length = prompt_length
        self.max_length = max_length


class GenerationTimeoutError(GenerationError):
    """Exception raised when generation times out."""
    
    def __init__(self, timeout_seconds: float, provider: str = None, model: str = None):
        super().__init__(
            f"Generation timed out after {timeout_seconds} seconds", 
            provider=provider, 
            model=model
        )
        self.timeout_seconds = timeout_seconds


class ContentFilterError(GenerationError):
    """Exception raised when content is filtered by the provider."""
    
    def __init__(self, reason: str, provider: str = None, model: str = None):
        super().__init__(
            f"Content filtered: {reason}", 
            provider=provider, 
            model=model
        )
        self.reason = reason


class ProviderQuotaExceededError(GenerationError):
    """Exception raised when provider quota is exceeded."""
    
    def __init__(self, provider: str, limit: str = None):
        message = f"Provider quota exceeded: {provider}"
        if limit:
            message += f" (limit: {limit})"
        super().__init__(message, provider=provider)
        self.limit = limit


# Agent Exceptions

class AgentError(KnowledgeBaseError):
    """Base exception for agent errors."""
    
    def __init__(self, message: str, agent_id: str = None, task_id: str = None):
        details = {}
        if agent_id:
            details["agent_id"] = agent_id
        if task_id:
            details["task_id"] = task_id
        super().__init__(message, "AGENT_ERROR", details)
        self.agent_id = agent_id
        self.task_id = task_id


class AgentNotFoundError(AgentError):
    """Exception raised when an agent is not found."""
    
    def __init__(self, agent_id: str):
        super().__init__(f"Agent not found: {agent_id}", agent_id=agent_id)


class AgentCommunicationError(AgentError):
    """Exception raised when agent communication fails."""
    
    def __init__(self, source_agent: str, target_agent: str, reason: str = None):
        message = f"Communication failed between {source_agent} and {target_agent}"
        if reason:
            message += f": {reason}"
        super().__init__(message, agent_id=source_agent)
        self.source_agent = source_agent
        self.target_agent = target_agent
        self.reason = reason


class AgentTaskError(AgentError):
    """Exception raised when an agent task fails."""
    
    def __init__(self, task_id: str, agent_id: str = None, reason: str = None):
        message = f"Task failed: {task_id}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, agent_id=agent_id, task_id=task_id)
        self.reason = reason


# API Exceptions

class APIError(KnowledgeBaseError):
    """Base exception for API errors."""
    
    def __init__(self, message: str, status_code: int = 500, endpoint: str = None):
        details = {"status_code": status_code}
        if endpoint:
            details["endpoint"] = endpoint
        super().__init__(message, "API_ERROR", details)
        self.status_code = status_code
        self.endpoint = endpoint


class AuthenticationError(APIError):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", endpoint: str = None):
        super().__init__(message, status_code=401, endpoint=endpoint)


class AuthorizationError(APIError):
    """Exception raised for authorization errors."""
    
    def __init__(self, message: str = "Not authorized", resource: str = None, endpoint: str = None):
        details = {"endpoint": endpoint}
        if resource:
            details["resource"] = resource
        super().__init__(message, status_code=403, endpoint=endpoint)
        self.resource = resource


class RateLimitError(APIError):
    """Exception raised for rate limit errors."""
    
    def __init__(self, limit: int = None, reset_time: str = None, endpoint: str = None):
        details = {"endpoint": endpoint}
        if limit:
            details["limit"] = limit
        if reset_time:
            details["reset_time"] = reset_time
        super().__init__("Rate limit exceeded", status_code=429, endpoint=endpoint)
        self.limit = limit
        self.reset_time = reset_time


class ValidationError(APIError):
    """Exception raised for input validation errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None, endpoint: str = None):
        details = {"endpoint": endpoint}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, status_code=400, endpoint=endpoint)
        self.field = field
        self.value = value


# Provider Exceptions

class ProviderError(KnowledgeBaseError):
    """Base exception for provider errors."""
    
    def __init__(self, message: str, provider_type: str = None, provider_name: str = None):
        details = {}
        if provider_type:
            details["provider_type"] = provider_type
        if provider_name:
            details["provider_name"] = provider_name
        super().__init__(message, "PROVIDER_ERROR", details)
        self.provider_type = provider_type
        self.provider_name = provider_name


class ProviderNotFoundError(ProviderError):
    """Exception raised when a provider is not found."""
    
    def __init__(self, provider_type: str, provider_name: str):
        super().__init__(
            f"Provider not found: {provider_name} ({provider_type})", 
            provider_type=provider_type, 
            provider_name=provider_name
        )


class ProviderInitializationError(ProviderError):
    """Exception raised when a provider fails to initialize."""
    
    def __init__(self, provider_type: str, provider_name: str, reason: str = None):
        message = f"Failed to initialize provider: {provider_name} ({provider_type})"
        if reason:
            message += f" - {reason}"
        super().__init__(message, provider_type=provider_type, provider_name=provider_name)
        self.reason = reason


class StrategyNotFoundError(ProviderError):
    """Exception raised when a strategy is not found."""
    
    def __init__(self, strategy_type: str, strategy_name: str):
        super().__init__(
            f"Strategy not found: {strategy_name} ({strategy_type})", 
            provider_type=strategy_type, 
            provider_name=strategy_name
        )
        self.strategy_type = strategy_type
        self.strategy_name = strategy_name


# Error handling utilities

def format_exception(exc: Exception) -> str:
    """Format an exception with traceback for logging."""
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


def safe_execute(func: Callable, *args, default_value: Any = None, 
                error_handler: Callable[[Exception], Any] = None, 
                **kwargs) -> Any:
    """
    Execute a function safely, catching and handling exceptions.
    
    Args:
        func: The function to execute
        *args: Arguments to pass to the function
        default_value: Value to return if an exception occurs
        error_handler: Function to handle the exception
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function or the default value if an exception occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            return error_handler(e)
        logger.error(f"Error executing {func.__name__}: {str(e)}")
        logger.debug(format_exception(e))
        return default_value


async def safe_execute_async(func: Callable, *args, default_value: Any = None,
                           error_handler: Callable[[Exception], Any] = None,
                           **kwargs) -> Any:
    """
    Execute an async function safely, catching and handling exceptions.
    
    Args:
        func: The async function to execute
        *args: Arguments to pass to the function
        default_value: Value to return if an exception occurs
        error_handler: Function to handle the exception
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function or the default value if an exception occurs
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            return error_handler(e)
        logger.error(f"Error executing {func.__name__}: {str(e)}")
        logger.debug(format_exception(e))
        return default_value


def with_fallback(primary_func: Callable, fallback_func: Callable, 
                 error_types: List[Type[Exception]] = None) -> Callable:
    """
    Create a function that falls back to another function if the primary one fails.
    
    Args:
        primary_func: The primary function to execute
        fallback_func: The fallback function to execute if the primary one fails
        error_types: List of exception types to catch. If None, catches all exceptions.
        
    Returns:
        A function that executes the primary function and falls back to the fallback function
    """
    error_types = error_types or [Exception]
    
    def wrapper(*args, **kwargs):
        try:
            return primary_func(*args, **kwargs)
        except tuple(error_types) as e:
            logger.warning(f"Primary function {primary_func.__name__} failed: {str(e)}. "
                          f"Falling back to {fallback_func.__name__}.")
            return fallback_func(*args, **kwargs)
    
    return wrapper


async def with_fallback_async(primary_func: Callable, fallback_func: Callable,
                            error_types: List[Type[Exception]] = None) -> Callable:
    """
    Create an async function that falls back to another function if the primary one fails.
    
    Args:
        primary_func: The primary async function to execute
        fallback_func: The fallback async function to execute if the primary one fails
        error_types: List of exception types to catch. If None, catches all exceptions.
        
    Returns:
        An async function that executes the primary function and falls back to the fallback function
    """
    error_types = error_types or [Exception]
    
    async def wrapper(*args, **kwargs):
        try:
            return await primary_func(*args, **kwargs)
        except tuple(error_types) as e:
            logger.warning(f"Primary function {primary_func.__name__} failed: {str(e)}. "
                          f"Falling back to {fallback_func.__name__}.")
            return await fallback_func(*args, **kwargs)
    
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, 
         backoff_factor: float = 2.0,
         error_types: List[Type[Exception]] = None) -> Callable:
    """
    Decorator to retry a function if it fails.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff_factor: Factor to increase delay by after each attempt
        error_types: List of exception types to catch. If None, catches all exceptions.
        
    Returns:
        A decorator that retries the function
    """
    import time
    error_types = error_types or [Exception]
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except tuple(error_types) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                                      f"Retrying in {current_delay:.2f} seconds.")
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"All {max_attempts} attempts failed. Last error: {str(e)}")
            
            raise last_exception
        
        return wrapper
    
    return decorator


def retry_async(max_attempts: int = 3, delay: float = 1.0,
                    backoff_factor: float = 2.0,
                    error_types: List[Type[Exception]] = None) -> Callable:
    """
    Decorator to retry an async function if it fails.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff_factor: Factor to increase delay by after each attempt
        error_types: List of exception types to catch. If None, catches all exceptions.
        
    Returns:
        A decorator that retries the async function
    """
    import asyncio
    error_types = error_types or [Exception]
    
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except tuple(error_types) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                                      f"Retrying in {current_delay:.2f} seconds.")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"All {max_attempts} attempts failed. Last error: {str(e)}")
            
            raise last_exception
        
        return wrapper
    
    return decorator


def setup_exception_handler(app=None):
    """
    Set up global exception handling for the application.
    
    If app is provided, sets up FastAPI exception handlers.
    Otherwise, sets up a global exception hook.
    
    Args:
        app: FastAPI application instance (optional)
    """
    if app:
        from fastapi import Request
        from fastapi.responses import JSONResponse
        
        @app.exception_handler(KnowledgeBaseError)
        async def knowledge_base_exception_handler(request: Request, exc: KnowledgeBaseError):
            status_code = 500
            
            if isinstance(exc, ValidationError):
                status_code = 400
            elif isinstance(exc, AuthenticationError):
                status_code = 401
            elif isinstance(exc, AuthorizationError):
                status_code = 403
            elif isinstance(exc, DocumentNotFoundError) or isinstance(exc, ChunkNotFoundError):
                status_code = 404
            elif isinstance(exc, RateLimitError):
                status_code = 429
            
            return JSONResponse(
                status_code=getattr(exc, 'status_code', status_code),
                content=exc.to_dict()
            )
        
        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled exception: {str(exc)}")
            logger.debug(format_exception(exc))
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "error_code": "INTERNAL_ERROR",
                    "details": {"type": type(exc).__name__}
                }
            )
    else:
        def global_exception_hook(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # Don't capture keyboard interrupt
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        sys.excepthook = global_exception_hook
"""
Tests for the exception handling system.
"""
import pytest
import sys
import logging
from unittest.mock import MagicMock, patch

from src.knowledge_base.core.exceptions import (
    # Base exception
    KnowledgeBaseError,
    
    # Configuration exceptions
    ConfigurationError, MissingConfigurationError, InvalidConfigurationError,
    
    # Storage exceptions
    StorageError, DocumentNotFoundError, ChunkNotFoundError, 
    StorageConnectionError, StorageOperationError, StorageQuotaExceededError,
    
    # Processing exceptions
    ProcessingError, DocumentTypeError, ChunkingError, 
    EmbeddingError, MetadataExtractionError,
    
    # Retrieval exceptions
    RetrievalError, EmptyQueryError, NoResultsFoundError, 
    InvalidFilterError, RetrievalTimeoutError,
    
    # Generation exceptions
    GenerationError, PromptTooLongError, GenerationTimeoutError, 
    ContentFilterError, ProviderQuotaExceededError,
    
    # Agent exceptions
    AgentError, AgentNotFoundError, AgentCommunicationError, AgentTaskError,
    
    # API exceptions
    APIError, AuthenticationError, AuthorizationError, 
    RateLimitError, ValidationError,
    
    # Provider exceptions
    ProviderError, ProviderNotFoundError, ProviderInitializationError, StrategyNotFoundError,
    
    # Utility functions
    format_exception, safe_execute, safe_execute_async, 
    with_fallback, with_fallback_async, retry, retry_async, setup_exception_handler
)


class TestBaseExceptions:
    """Tests for the base exception classes."""
    
    def test_knowledge_base_error(self):
        """Test the KnowledgeBaseError class."""
        error = KnowledgeBaseError("Test error", "TEST_ERROR", {"detail": "test"})
        assert str(error) == "[TEST_ERROR] Test error"
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"detail": "test"}
        
        # Test to_dict method
        error_dict = error.to_dict()
        assert error_dict["error"] == "Test error"
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["details"] == {"detail": "test"}
        
        # Test default values
        error = KnowledgeBaseError("Test error")
        assert error.error_code == "UNKNOWN_ERROR"
        assert error.details == {}


class TestConfigurationExceptions:
    """Tests for configuration exceptions."""
    
    def test_configuration_error(self):
        """Test the ConfigurationError class."""
        error = ConfigurationError("Invalid config", "api.key", "invalid-key")
        assert isinstance(error, KnowledgeBaseError)
        assert error.config_key == "api.key"
        assert error.config_value == "invalid-key"
        # The string representation includes the error code and message, not necessarily the config key
        assert "CONFIG_ERROR" in str(error)
        assert "Invalid config" in str(error)
        
    def test_missing_configuration_error(self):
        """Test the MissingConfigurationError class."""
        error = MissingConfigurationError("api.key")
        assert isinstance(error, ConfigurationError)
        assert error.config_key == "api.key"
        assert "Missing required configuration" in str(error)
        
    def test_invalid_configuration_error(self):
        """Test the InvalidConfigurationError class."""
        error = InvalidConfigurationError("max_tokens", -1, "must be positive")
        assert isinstance(error, ConfigurationError)
        assert error.config_key == "max_tokens"
        assert error.config_value == -1
        assert error.reason == "must be positive"
        assert "must be positive" in str(error)


class TestStorageExceptions:
    """Tests for storage exceptions."""
    
    def test_storage_error(self):
        """Test the StorageError class."""
        error = StorageError("Storage error", "write", "memory")
        assert isinstance(error, KnowledgeBaseError)
        assert error.operation == "write"
        assert error.provider == "memory"
        
    def test_document_not_found_error(self):
        """Test the DocumentNotFoundError class."""
        error = DocumentNotFoundError("doc123", "notion")
        assert isinstance(error, StorageError)
        assert error.document_id == "doc123"
        assert error.provider == "notion"
        assert error.operation == "retrieve"
        assert "Document not found" in str(error)
        
    def test_chunk_not_found_error(self):
        """Test the ChunkNotFoundError class."""
        error = ChunkNotFoundError("chunk123", "memory")
        assert isinstance(error, StorageError)
        assert error.chunk_id == "chunk123"
        assert error.provider == "memory"
        assert error.operation == "retrieve"
        assert "Chunk not found" in str(error)
        
    def test_storage_connection_error(self):
        """Test the StorageConnectionError class."""
        error = StorageConnectionError("notion", "API key invalid")
        assert isinstance(error, StorageError)
        assert error.provider == "notion"
        assert error.reason == "API key invalid"
        assert error.operation == "connect"
        assert "Failed to connect" in str(error)
        
    def test_storage_operation_error(self):
        """Test the StorageOperationError class."""
        error = StorageOperationError("delete", "chroma", "database locked")
        assert isinstance(error, StorageError)
        assert error.operation == "delete"
        assert error.provider == "chroma"
        assert error.reason == "database locked"
        assert "Storage operation failed" in str(error)
        
    def test_storage_quota_exceeded_error(self):
        """Test the StorageQuotaExceededError class."""
        error = StorageQuotaExceededError("pinecone", "1GB")
        assert isinstance(error, StorageError)
        assert error.provider == "pinecone"
        assert error.limit == "1GB"
        assert error.operation == "add"
        assert "Storage quota exceeded" in str(error)


class TestProcessingExceptions:
    """Tests for processing exceptions."""
    
    def test_processing_error(self):
        """Test the ProcessingError class."""
        error = ProcessingError("Processing error", "doc123", "chunking")
        assert isinstance(error, KnowledgeBaseError)
        assert error.document_id == "doc123"
        assert error.stage == "chunking"
        
    def test_document_type_error(self):
        """Test the DocumentTypeError class."""
        error = DocumentTypeError("video/mp4", "doc123")
        assert isinstance(error, ProcessingError)
        assert error.document_type == "video/mp4"
        assert error.document_id == "doc123"
        assert error.stage == "type_detection"
        assert "Unsupported document type" in str(error)
        
    def test_chunking_error(self):
        """Test the ChunkingError class."""
        error = ChunkingError("Invalid chunk size", "doc123", "recursive")
        assert isinstance(error, ProcessingError)
        assert error.reason == "Invalid chunk size"
        assert error.document_id == "doc123"
        assert error.strategy == "recursive"
        assert error.stage == "chunking"
        assert "Chunking failed" in str(error)
        
    def test_embedding_error(self):
        """Test the EmbeddingError class."""
        error = EmbeddingError("API error", "openai", 1000)
        assert isinstance(error, ProcessingError)
        assert error.reason == "API error"
        assert error.model == "openai"
        assert error.text_length == 1000
        assert error.stage == "embedding"
        assert "Embedding failed" in str(error)
        
    def test_metadata_extraction_error(self):
        """Test the MetadataExtractionError class."""
        error = MetadataExtractionError("Invalid metadata format", "doc123")
        assert isinstance(error, ProcessingError)
        assert error.reason == "Invalid metadata format"
        assert error.document_id == "doc123"
        assert error.stage == "metadata_extraction"
        assert "Metadata extraction failed" in str(error)


class TestRetrievalExceptions:
    """Tests for retrieval exceptions."""
    
    def test_retrieval_error(self):
        """Test the RetrievalError class."""
        error = RetrievalError("Retrieval error", "what is AI?", "semantic")
        assert isinstance(error, KnowledgeBaseError)
        assert error.query == "what is AI?"
        assert error.strategy == "semantic"
        
    def test_empty_query_error(self):
        """Test the EmptyQueryError class."""
        error = EmptyQueryError()
        assert isinstance(error, RetrievalError)
        assert error.query == ""
        assert "Query cannot be empty" in str(error)
        
    def test_no_results_found_error(self):
        """Test the NoResultsFoundError class."""
        error = NoResultsFoundError("quantum computing", "hybrid")
        assert isinstance(error, RetrievalError)
        assert error.query == "quantum computing"
        assert error.strategy == "hybrid"
        assert "No results found" in str(error)
        
    def test_invalid_filter_error(self):
        """Test the InvalidFilterError class."""
        error = InvalidFilterError("date > 2023", "Invalid operator")
        assert isinstance(error, RetrievalError)
        assert error.filter_expr == "date > 2023"
        assert error.reason == "Invalid operator"
        assert "Invalid filter expression" in str(error)
        
    def test_retrieval_timeout_error(self):
        """Test the RetrievalTimeoutError class."""
        error = RetrievalTimeoutError("complex query", 30.0, "semantic")
        assert isinstance(error, RetrievalError)
        assert error.query == "complex query"
        assert error.timeout_seconds == 30.0
        assert error.strategy == "semantic"
        assert "Retrieval timed out" in str(error)


class TestGenerationExceptions:
    """Tests for generation exceptions."""
    
    def test_generation_error(self):
        """Test the GenerationError class."""
        error = GenerationError("Generation error", "openai", "gpt-4")
        assert isinstance(error, KnowledgeBaseError)
        assert error.provider == "openai"
        assert error.model == "gpt-4"
        
    def test_prompt_too_long_error(self):
        """Test the PromptTooLongError class."""
        error = PromptTooLongError(5000, 4096, "openai", "gpt-4")
        assert isinstance(error, GenerationError)
        assert error.prompt_length == 5000
        assert error.max_length == 4096
        assert error.provider == "openai"
        assert error.model == "gpt-4"
        assert "Prompt too long" in str(error)
        
    def test_generation_timeout_error(self):
        """Test the GenerationTimeoutError class."""
        error = GenerationTimeoutError(60.0, "anthropic", "claude-2")
        assert isinstance(error, GenerationError)
        assert error.timeout_seconds == 60.0
        assert error.provider == "anthropic"
        assert error.model == "claude-2"
        assert "Generation timed out" in str(error)
        
    def test_content_filter_error(self):
        """Test the ContentFilterError class."""
        error = ContentFilterError("Harmful content detected", "openai", "gpt-4")
        assert isinstance(error, GenerationError)
        assert error.reason == "Harmful content detected"
        assert error.provider == "openai"
        assert error.model == "gpt-4"
        assert "Content filtered" in str(error)
        
    def test_provider_quota_exceeded_error(self):
        """Test the ProviderQuotaExceededError class."""
        error = ProviderQuotaExceededError("openai", "100 requests/min")
        assert isinstance(error, GenerationError)
        assert error.provider == "openai"
        assert error.limit == "100 requests/min"
        assert "Provider quota exceeded" in str(error)


class TestAgentExceptions:
    """Tests for agent exceptions."""
    
    def test_agent_error(self):
        """Test the AgentError class."""
        error = AgentError("Agent error", "retrieval_agent", "task123")
        assert isinstance(error, KnowledgeBaseError)
        assert error.agent_id == "retrieval_agent"
        assert error.task_id == "task123"
        
    def test_agent_not_found_error(self):
        """Test the AgentNotFoundError class."""
        error = AgentNotFoundError("unknown_agent")
        assert isinstance(error, AgentError)
        assert error.agent_id == "unknown_agent"
        assert "Agent not found" in str(error)
        
    def test_agent_communication_error(self):
        """Test the AgentCommunicationError class."""
        error = AgentCommunicationError("orchestrator", "retrieval", "timeout")
        assert isinstance(error, AgentError)
        assert error.source_agent == "orchestrator"
        assert error.target_agent == "retrieval"
        assert error.reason == "timeout"
        assert "Communication failed" in str(error)
        
    def test_agent_task_error(self):
        """Test the AgentTaskError class."""
        error = AgentTaskError("process_document", "processing_agent", "invalid input")
        assert isinstance(error, AgentError)
        assert error.task_id == "process_document"
        assert error.agent_id == "processing_agent"
        assert error.reason == "invalid input"
        assert "Task failed" in str(error)


class TestAPIExceptions:
    """Tests for API exceptions."""
    
    def test_api_error(self):
        """Test the APIError class."""
        error = APIError("API error", 400, "/api/query")
        assert isinstance(error, KnowledgeBaseError)
        assert error.status_code == 400
        assert error.endpoint == "/api/query"
        
    def test_authentication_error(self):
        """Test the AuthenticationError class."""
        error = AuthenticationError("Invalid API key", "/api/documents")
        assert isinstance(error, APIError)
        assert error.status_code == 401
        assert error.endpoint == "/api/documents"
        # Check for the actual message used in the constructor
        assert "Invalid API key" in str(error)
        
    def test_authorization_error(self):
        """Test the AuthorizationError class."""
        error = AuthorizationError("Insufficient permissions", "documents", "/api/documents")
        assert isinstance(error, APIError)
        assert error.status_code == 403
        assert error.endpoint == "/api/documents"
        assert error.resource == "documents"
        # Check for the actual message used in the constructor
        assert "Insufficient permissions" in str(error)
        
    def test_rate_limit_error(self):
        """Test the RateLimitError class."""
        error = RateLimitError(100, "2023-01-01T12:00:00Z", "/api/query")
        assert isinstance(error, APIError)
        assert error.status_code == 429
        assert error.endpoint == "/api/query"
        assert error.limit == 100
        assert error.reset_time == "2023-01-01T12:00:00Z"
        assert "Rate limit exceeded" in str(error)
        
    def test_validation_error(self):
        """Test the ValidationError class."""
        error = ValidationError("Invalid value", "query", "", "/api/query")
        assert isinstance(error, APIError)
        assert error.status_code == 400
        assert error.endpoint == "/api/query"
        assert error.field == "query"
        assert error.value == ""
        assert "Invalid value" in str(error)


class TestProviderExceptions:
    """Tests for provider exceptions."""
    
    def test_provider_error(self):
        """Test the ProviderError class."""
        error = ProviderError("Provider error", "embedding", "sentence_transformers")
        assert isinstance(error, KnowledgeBaseError)
        assert error.provider_type == "embedding"
        assert error.provider_name == "sentence_transformers"
        
    def test_provider_not_found_error(self):
        """Test the ProviderNotFoundError class."""
        error = ProviderNotFoundError("storage", "unknown")
        assert isinstance(error, ProviderError)
        assert error.provider_type == "storage"
        assert error.provider_name == "unknown"
        assert "Provider not found" in str(error)
        
    def test_provider_initialization_error(self):
        """Test the ProviderInitializationError class."""
        error = ProviderInitializationError("embedding", "openai", "Invalid API key")
        assert isinstance(error, ProviderError)
        assert error.provider_type == "embedding"
        assert error.provider_name == "openai"
        assert error.reason == "Invalid API key"
        assert "Failed to initialize provider" in str(error)
        
    def test_strategy_not_found_error(self):
        """Test the StrategyNotFoundError class."""
        error = StrategyNotFoundError("retrieval", "unknown")
        assert isinstance(error, ProviderError)
        assert error.strategy_type == "retrieval"
        assert error.strategy_name == "unknown"
        assert "Strategy not found" in str(error)


class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_format_exception(self):
        """Test the format_exception function."""
        try:
            1 / 0
        except Exception as e:
            result = format_exception(e)
            assert "ZeroDivisionError" in result
            assert "division by zero" in result
    
    def test_safe_execute(self):
        """Test the safe_execute function."""
        def success_func():
            return "success"
            
        def error_func():
            raise ValueError("test error")
            
        def error_handler(e):
            return f"handled: {str(e)}"
        
        # Test successful execution
        assert safe_execute(success_func) == "success"
        
        # Test with error and default value
        assert safe_execute(error_func, default_value="default") == "default"
        
        # Test with error handler
        assert safe_execute(error_func, error_handler=error_handler) == "handled: test error"
    
    @pytest.mark.asyncio
    async def test_safe_execute_async(self):
        """Test the safe_execute_async function."""
        async def success_func():
            return "success"
            
        async def error_func():
            raise ValueError("test error")
            
        def error_handler(e):
            return f"handled: {str(e)}"
        
        # Test successful execution
        assert await safe_execute_async(success_func) == "success"
        
        # Test with error and default value
        assert await safe_execute_async(error_func, default_value="default") == "default"
        
        # Test with error handler
        assert await safe_execute_async(error_func, error_handler=error_handler) == "handled: test error"
    
    def test_with_fallback(self):
        """Test the with_fallback function."""
        def primary_func():
            raise ValueError("primary error")
            
        def fallback_func():
            return "fallback"
        
        # Create a function with fallback
        func = with_fallback(primary_func, fallback_func)
        
        # Test fallback
        assert func() == "fallback"
        
        # Test with specific error types
        func = with_fallback(primary_func, fallback_func, [TypeError])
        
        # Should raise ValueError since we're only catching TypeError
        with pytest.raises(ValueError):
            func()
    
    @pytest.mark.asyncio
    async def test_with_fallback_async(self):
        """Test the with_fallback_async function."""
        async def primary_func():
            raise ValueError("primary error")
            
        async def fallback_func():
            return "fallback"
        
        # Create an async function with fallback
        func = await with_fallback_async(primary_func, fallback_func)
        
        # Test fallback
        assert await func() == "fallback"
        
        # Test with specific error types
        func = await with_fallback_async(primary_func, fallback_func, [TypeError])
        
        # Should raise ValueError since we're only catching TypeError
        with pytest.raises(ValueError):
            await func()
    
    def test_retry(self):
        """Test the retry decorator."""
        mock = MagicMock()
        mock.side_effect = [ValueError("error"), ValueError("error"), "success"]
        
        @retry(max_attempts=3, delay=0.01)
        def test_func():
            return mock()
        
        # Should succeed on the third attempt
        assert test_func() == "success"
        assert mock.call_count == 3
        
        # Reset mock
        mock.reset_mock()
        mock.side_effect = [ValueError("error"), ValueError("error"), ValueError("error")]
        
        # Should raise after all attempts fail
        with pytest.raises(ValueError):
            test_func()
        
        assert mock.call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_async(self):
        """Test the retry_async decorator."""
        mock = MagicMock()
        mock.side_effect = [ValueError("error"), ValueError("error"), "success"]
        
        # Apply the decorator to an async function
        @retry_async(max_attempts=3, delay=0.01)
        async def test_func():
            return mock()
        
        # Should succeed on the third attempt
        assert await test_func() == "success"
        assert mock.call_count == 3
        
        # Reset mock
        mock.reset_mock()
        mock.side_effect = [ValueError("error"), ValueError("error"), ValueError("error")]
        
        # Should raise after all attempts fail
        with pytest.raises(ValueError):
            await test_func()
        
        assert mock.call_count == 3
    
    def test_setup_exception_handler_global(self):
        """Test the setup_exception_handler function for global handling."""
        original_hook = sys.excepthook
        
        try:
            # Set up global exception handler
            setup_exception_handler()
            
            # Check that sys.excepthook has been changed
            assert sys.excepthook != original_hook
            
            # Test that KeyboardInterrupt is not caught
            with patch.object(sys, '__excepthook__') as mock_excepthook:
                sys.excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
                mock_excepthook.assert_called_once()
        finally:
            # Restore original excepthook
            sys.excepthook = original_hook
    
    def test_setup_exception_handler_fastapi(self):
        """Test the setup_exception_handler function for FastAPI."""
        # Create a mock FastAPI app
        mock_app = MagicMock()
        
        # Set up exception handlers
        setup_exception_handler(mock_app)
        
        # Check that exception handlers were registered
        assert mock_app.exception_handler.call_count == 2
        
        # Check that the correct exception types were registered
        mock_app.exception_handler.assert_any_call(KnowledgeBaseError)
        mock_app.exception_handler.assert_any_call(Exception)
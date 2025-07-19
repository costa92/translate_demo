"""
Tests for the knowledge processing agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_base.agents.knowledge_processing_agent import KnowledgeProcessingAgent
from src.knowledge_base.agents.message import AgentMessage
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import Document, DocumentType, TextChunk, ChunkingResult


@pytest.fixture
def config():
    """Create a test configuration."""
    config = Config()
    # Add processing-specific configuration
    config.processing = MagicMock()
    config.processing.batch_size = 5
    config.processing.max_concurrent_tasks = 3
    return config


@pytest.fixture
def agent(config):
    """Create a test knowledge processing agent."""
    agent = KnowledgeProcessingAgent(config)
    agent.dispatch_message = AsyncMock()
    agent.processor = MagicMock()
    agent.processor.process_document = AsyncMock()
    agent.processor.process_documents = AsyncMock()
    return agent


@pytest.fixture
def document():
    """Create a test document."""
    return Document(
        id="test_doc_1",
        content="This is a test document content.",
        type=DocumentType.TEXT,
        metadata={"source": "test"},
        source="test"
    )


@pytest.fixture
def chunking_result(document):
    """Create a test chunking result."""
    chunk = TextChunk(
        id="test_chunk_1",
        text="This is a test document content.",
        document_id=document.id,
        metadata={"chunk_index": 0},
        embedding=[0.1, 0.2, 0.3]
    )
    return ChunkingResult(
        document_id=document.id,
        chunks=[chunk],
        metadata={"chunk_count": 1}
    )


@pytest.fixture
def task_message():
    """Create a test task message."""
    return AgentMessage(
        source="orchestrator",
        destination="processing_agent",
        message_type="task",
        payload={
            "task_id": "test_task",
            "task": "process_document",
            "params": {
                "document": {
                    "id": "test_doc_1",
                    "content": "This is a test document content.",
                    "type": "text",
                    "metadata": {"source": "test"},
                    "source": "test"
                }
            }
        }
    )


class TestKnowledgeProcessingAgent:
    """Tests for the KnowledgeProcessingAgent class."""
    
    async def test_initialization(self, config):
        """Test agent initialization."""
        agent = KnowledgeProcessingAgent(config)
        assert agent.agent_id == "processing_agent"
        assert "task" in agent.message_handlers
        assert agent.batch_size == 5
        assert agent.max_concurrent_tasks == 3
    
    async def test_start(self, agent):
        """Test starting the agent."""
        # Mock the processor initialize method
        agent.processor.initialize = AsyncMock()
        
        # Start the agent
        await agent.start()
        
        # Check that processor was initialized
        agent.processor.initialize.assert_called_once()
    
    async def test_stop(self, agent):
        """Test stopping the agent."""
        # Mock the processor close method
        agent.processor.close = AsyncMock()
        
        # Stop the agent
        await agent.stop()
        
        # Check that processor was closed
        agent.processor.close.assert_called_once()
    
    async def test_process_message(self, agent, task_message):
        """Test processing a message."""
        # Mock the handle_task method
        agent.handle_task = AsyncMock()
        
        # Process a task message
        response = await agent.process_message(task_message)
        
        # Check that handle_task was called
        agent.handle_task.assert_called_once_with(task_message)
        
        # Check the response
        assert response.message_type == "task_response"
        assert response.payload["status"] == "processing"
    
    async def test_handle_task_process_document(self, agent, task_message, chunking_result):
        """Test handling a process_document task."""
        # Set up the mock processor to return a chunking result
        agent.processor.process_document.return_value = chunking_result
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that processor was called with the document
        agent.processor.process_document.assert_called_once()
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["document_id"] == "test_doc_1"
        assert completion_message.payload["result"]["chunk_count"] == 1
    
    async def test_handle_task_process_documents(self, agent, chunking_result):
        """Test handling a process_documents task."""
        # Create a task message for processing multiple documents
        task_message = AgentMessage(
            source="orchestrator",
            destination="processing_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "process_documents",
                "params": {
                    "documents": [
                        {
                            "id": "test_doc_1",
                            "content": "This is test document 1.",
                            "type": "text"
                        },
                        {
                            "id": "test_doc_2",
                            "content": "This is test document 2.",
                            "type": "text"
                        }
                    ]
                }
            }
        )
        
        # Mock the _process_batch method
        agent._process_batch = AsyncMock(return_value=[chunking_result, chunking_result])
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that _process_batch was called
        agent._process_batch.assert_called_once()
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["documents_processed"] == 2
        assert completion_message.payload["result"]["chunks_created"] == 2
    
    async def test_handle_task_missing_params(self, agent):
        """Test handling a task with missing parameters."""
        # Create a message with missing parameters
        message = AgentMessage(
            source="orchestrator",
            destination="processing_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "process_document",
                "params": {}
            }
        )
        
        # Handle the task
        await agent.handle_task(message)
        
        # Check that an error message was dispatched
        agent.dispatch_message.assert_called_once()
        error_message = agent.dispatch_message.call_args[0][0]
        assert error_message.message_type == "task_error"
        assert "Missing document parameter" in error_message.payload["error"]
    
    async def test_handle_task_unsupported_task(self, agent):
        """Test handling an unsupported task."""
        # Create a message with an unsupported task
        message = AgentMessage(
            source="orchestrator",
            destination="processing_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "unsupported_task",
                "params": {}
            }
        )
        
        # Handle the task
        await agent.handle_task(message)
        
        # Check that an error message was dispatched
        agent.dispatch_message.assert_called_once()
        error_message = agent.dispatch_message.call_args[0][0]
        assert error_message.message_type == "task_error"
        assert "Unsupported task" in error_message.payload["error"]
    
    async def test_process_batch(self, agent, document, chunking_result):
        """Test batch processing of documents."""
        # Mock the processor to return a chunking result
        agent.processor.process_document.return_value = chunking_result
        
        # Process a batch of documents
        results = await agent._process_batch([document, document])
        
        # Check that processor was called for each document
        assert agent.processor.process_document.call_count == 2
        
        # Check the results
        assert len(results) == 2
        assert all(r == chunking_result for r in results)
    
    async def test_chunk_to_dict(self, agent):
        """Test converting a chunk to a dictionary."""
        # Create a test chunk
        chunk = TextChunk(
            id="test_chunk",
            text="Test text",
            document_id="test_doc",
            metadata={"key": "value"},
            embedding=[0.1, 0.2, 0.3],
            start_index=0,
            end_index=9
        )
        
        # Convert to dictionary
        chunk_dict = agent._chunk_to_dict(chunk)
        
        # Check the dictionary
        assert chunk_dict["id"] == "test_chunk"
        assert chunk_dict["text"] == "Test text"
        assert chunk_dict["document_id"] == "test_doc"
        assert chunk_dict["metadata"] == {"key": "value"}
        assert chunk_dict["embedding"] == [0.1, 0.2, 0.3]
        assert chunk_dict["start_index"] == 0
        assert chunk_dict["end_index"] == 9
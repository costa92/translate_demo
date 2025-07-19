"""
Tests for the knowledge storage agent.
"""

import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_base.agents.knowledge_storage_agent import KnowledgeStorageAgent
from src.knowledge_base.agents.message import AgentMessage
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import TextChunk


@pytest.fixture
def config():
    """Create a test configuration."""
    config = Config()
    # Add storage-specific configuration
    config.storage = MagicMock()
    config.storage.provider = "memory"
    config.storage.batch_size = 50
    config.storage.auto_backup = False
    config.storage.backup_dir = "test_backups"
    return config


@pytest.fixture
def agent(config):
    """Create a test knowledge storage agent."""
    agent = KnowledgeStorageAgent(config)
    agent.dispatch_message = AsyncMock()
    agent.vector_store = MagicMock()
    agent.vector_store.add_chunks = AsyncMock()
    agent.vector_store.get_chunks = AsyncMock()
    agent.vector_store.delete_document = AsyncMock()
    agent.vector_store.get_stats = AsyncMock()
    return agent


@pytest.fixture
def chunks():
    """Create test chunks."""
    return [
        TextChunk(
            id=f"chunk_{i}",
            text=f"This is test chunk {i}",
            document_id="test_doc",
            metadata={"index": i},
            embedding=[0.1, 0.2, 0.3]
        )
        for i in range(3)
    ]


@pytest.fixture
def task_message():
    """Create a test task message."""
    return AgentMessage(
        source="orchestrator",
        destination="storage_agent",
        message_type="task",
        payload={
            "task_id": "test_task",
            "task": "store_chunks",
            "params": {
                "chunks": [
                    {
                        "id": "chunk_1",
                        "text": "This is test chunk 1",
                        "document_id": "test_doc",
                        "metadata": {"index": 1},
                        "embedding": [0.1, 0.2, 0.3]
                    }
                ]
            }
        }
    )


class TestKnowledgeStorageAgent:
    """Tests for the KnowledgeStorageAgent class."""
    
    async def test_initialization(self, config):
        """Test agent initialization."""
        agent = KnowledgeStorageAgent(config)
        assert agent.agent_id == "storage_agent"
        assert "task" in agent.message_handlers
        assert agent.batch_size == 50
        assert agent.auto_backup is False
        assert agent.backup_dir == "test_backups"
    
    async def test_start(self, agent):
        """Test starting the agent."""
        # Mock the vector store initialize method
        agent.vector_store.initialize = AsyncMock()
        
        # Start the agent
        await agent.start()
        
        # Check that vector store was initialized
        agent.vector_store.initialize.assert_called_once()
    
    async def test_stop(self, agent):
        """Test stopping the agent."""
        # Mock the vector store close method
        agent.vector_store.close = AsyncMock()
        
        # Stop the agent
        await agent.stop()
        
        # Check that vector store was closed
        agent.vector_store.close.assert_called_once()
    
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
    
    async def test_handle_task_store_chunks(self, agent, task_message):
        """Test handling a store_chunks task."""
        # Set up the mock vector store to return IDs
        agent.vector_store.add_chunks.return_value = ["chunk_1"]
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that vector store was called with the chunk
        agent.vector_store.add_chunks.assert_called_once()
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["chunks_stored"] == 1
    
    async def test_handle_task_retrieve_chunks(self, agent, chunks):
        """Test handling a retrieve_chunks task."""
        # Create a task message for retrieving chunks
        task_message = AgentMessage(
            source="orchestrator",
            destination="storage_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "retrieve_chunks",
                "params": {
                    "chunk_ids": ["chunk_0", "chunk_1", "chunk_2"]
                }
            }
        )
        
        # Set up the mock vector store to return chunks
        agent.vector_store.get_chunks.return_value = chunks
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that vector store was called with the chunk IDs
        agent.vector_store.get_chunks.assert_called_once_with(["chunk_0", "chunk_1", "chunk_2"])
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["chunks_retrieved"] == 3
    
    async def test_handle_task_delete_document(self, agent):
        """Test handling a delete_document task."""
        # Create a task message for deleting a document
        task_message = AgentMessage(
            source="orchestrator",
            destination="storage_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "delete_document",
                "params": {
                    "document_id": "test_doc"
                }
            }
        )
        
        # Set up the mock vector store to return success
        agent.vector_store.delete_document.return_value = True
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that vector store was called with the document ID
        agent.vector_store.delete_document.assert_called_once_with("test_doc")
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["success"] is True
    
    async def test_handle_task_get_stats(self, agent):
        """Test handling a get_stats task."""
        # Create a task message for getting stats
        task_message = AgentMessage(
            source="orchestrator",
            destination="storage_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "get_stats",
                "params": {}
            }
        )
        
        # Set up the mock vector store to return stats
        stats = {
            "total_chunks": 100,
            "total_documents": 10,
            "provider": "memory"
        }
        agent.vector_store.get_stats.return_value = stats
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that vector store was called
        agent.vector_store.get_stats.assert_called_once()
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"] == stats
    
    async def test_handle_task_missing_params(self, agent):
        """Test handling a task with missing parameters."""
        # Create a message with missing parameters
        message = AgentMessage(
            source="orchestrator",
            destination="storage_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "retrieve_chunks",
                "params": {}
            }
        )
        
        # Handle the task
        await agent.handle_task(message)
        
        # Check that an error message was dispatched
        agent.dispatch_message.assert_called_once()
        error_message = agent.dispatch_message.call_args[0][0]
        assert error_message.message_type == "task_error"
        assert "Missing chunk_ids parameter" in error_message.payload["error"]
    
    async def test_handle_task_unsupported_task(self, agent):
        """Test handling an unsupported task."""
        # Create a message with an unsupported task
        message = AgentMessage(
            source="orchestrator",
            destination="storage_agent",
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
    
    @patch("os.makedirs")
    @patch("json.dump")
    @patch("builtins.open")
    async def test_create_backup(self, mock_open, mock_json_dump, mock_makedirs, agent):
        """Test creating a backup."""
        # Set up the mock vector store to return stats
        stats = {
            "total_chunks": 100,
            "total_documents": 10,
            "provider": "memory"
        }
        agent.vector_store.get_stats.return_value = stats
        agent.vector_store.provider_name = "memory"
        
        # Create a backup
        backup_path = await agent._create_backup()
        
        # Check that the backup directory was created
        mock_makedirs.assert_called_once_with("test_backups", exist_ok=True)
        
        # Check that the backup file was written
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()
        
        # Check that the backup path is returned
        assert "test_backups" in backup_path
        assert "kb_backup_" in backup_path
    
    async def test_chunk_to_dict(self, agent, chunks):
        """Test converting a chunk to a dictionary."""
        # Convert a chunk to a dictionary
        chunk_dict = agent._chunk_to_dict(chunks[0])
        
        # Check the dictionary
        assert chunk_dict["id"] == "chunk_0"
        assert chunk_dict["text"] == "This is test chunk 0"
        assert chunk_dict["document_id"] == "test_doc"
        assert chunk_dict["metadata"] == {"index": 0}
        assert chunk_dict["embedding"] == [0.1, 0.2, 0.3]
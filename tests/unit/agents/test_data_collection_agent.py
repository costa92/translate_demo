"""
Tests for the data collection agent.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_base.agents.data_collection_agent import DataCollectionAgent
from src.knowledge_base.agents.message import AgentMessage
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import Document, DocumentType


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config()


@pytest.fixture
def agent(config):
    """Create a test data collection agent."""
    agent = DataCollectionAgent(config)
    agent.dispatch_message = AsyncMock()
    return agent


@pytest.fixture
def task_message():
    """Create a test task message."""
    return AgentMessage(
        source="orchestrator",
        destination="collection_agent",
        message_type="task",
        payload={
            "task_id": "test_task",
            "task": "collect",
            "params": {
                "source": "test_source",
                "source_type": "file",
                "options": {}
            }
        }
    )


class TestDataCollectionAgent:
    """Tests for the DataCollectionAgent class."""
    
    async def test_initialization(self, config):
        """Test agent initialization."""
        agent = DataCollectionAgent(config)
        assert agent.agent_id == "collection_agent"
        assert "task" in agent.message_handlers
        assert len(agent.supported_source_types) == 4
        assert len(agent.supported_extensions) > 0
    
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
    
    async def test_handle_task_missing_params(self, agent):
        """Test handling a task with missing parameters."""
        # Create a message with missing parameters
        message = AgentMessage(
            source="orchestrator",
            destination="collection_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "collect",
                "params": {}
            }
        )
        
        # Handle the task
        await agent.handle_task(message)
        
        # Check that an error message was dispatched
        agent.dispatch_message.assert_called_once()
        error_message = agent.dispatch_message.call_args[0][0]
        assert error_message.message_type == "task_error"
        assert "Missing source parameter" in error_message.payload["error"]
    
    async def test_handle_task_unsupported_task(self, agent):
        """Test handling an unsupported task."""
        # Create a message with an unsupported task
        message = AgentMessage(
            source="orchestrator",
            destination="collection_agent",
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
    
    async def test_detect_source_type(self, agent):
        """Test source type detection."""
        # Test URL detection
        assert agent._detect_source_type("http://example.com") == "url"
        assert agent._detect_source_type("https://example.com") == "url"
        
        # Test directory detection (mocked)
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_dir", return_value=True):
                assert agent._detect_source_type("/path/to/dir") == "directory"
        
        # Test file detection (mocked)
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_dir", return_value=False):
                assert agent._detect_source_type("/path/to/file.txt") == "file"
        
        # Test API detection
        assert agent._detect_source_type("my_api_endpoint") == "api"
    
    async def test_get_document_type(self, agent):
        """Test document type detection."""
        assert agent._get_document_type("file.txt") == DocumentType.TEXT
        assert agent._get_document_type("file.md") == DocumentType.MARKDOWN
        assert agent._get_document_type("file.pdf") == DocumentType.PDF
        assert agent._get_document_type("file.docx") == DocumentType.DOCX
        assert agent._get_document_type("file.html") == DocumentType.HTML
        assert agent._get_document_type("file.unknown") == DocumentType.TEXT
    
    async def test_collect_from_file(self, agent):
        """Test collecting from a file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as temp:
            temp.write("Test content")
            temp_path = temp.name
        
        try:
            # Collect from the file
            documents = await agent._collect_from_file(temp_path, {})
            
            # Check the result
            assert len(documents) == 1
            assert documents[0].content == "Test content"
            assert documents[0].type == DocumentType.TEXT
            assert documents[0].metadata["source"] == temp_path
            assert documents[0].metadata["source_type"] == "file"
        finally:
            # Clean up
            os.unlink(temp_path)
    
    async def test_collect_from_directory(self, agent):
        """Test collecting from a directory."""
        # Create a temporary directory with files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create text files
            for i in range(3):
                with open(os.path.join(temp_dir, f"file{i}.txt"), "w") as f:
                    f.write(f"Content {i}")
            
            # Create a subdirectory with files
            subdir = os.path.join(temp_dir, "subdir")
            os.mkdir(subdir)
            for i in range(2):
                with open(os.path.join(subdir, f"subfile{i}.txt"), "w") as f:
                    f.write(f"Subcontent {i}")
            
            # Test recursive collection
            documents = await agent._collect_from_directory(temp_dir, {"recursive": True})
            assert len(documents) == 5
            
            # Test non-recursive collection
            documents = await agent._collect_from_directory(temp_dir, {"recursive": False})
            assert len(documents) == 3
    
    @patch("urllib.request.urlopen")
    async def test_collect_from_url(self, mock_urlopen, agent):
        """Test collecting from a URL."""
        # Mock the URL response
        mock_response = MagicMock()
        mock_response.read.return_value = b"Test content"
        mock_response.info.return_value.get_content_type.return_value = "text/html"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        # Collect from the URL
        documents = await agent._collect_from_url("https://example.com", {})
        
        # Check the result
        assert len(documents) == 1
        assert documents[0].content == "Test content"
        assert documents[0].type == DocumentType.HTML
        assert documents[0].metadata["source"] == "https://example.com"
        assert documents[0].metadata["source_type"] == "url"
        assert documents[0].metadata["domain"] == "example.com"
    
    @patch("urllib.request.urlopen")
    async def test_collect_from_api(self, mock_urlopen, agent):
        """Test collecting from an API."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"key": "value"}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        # Collect from the API
        documents = await agent._collect_from_api(
            "https://api.example.com/data",
            {
                "method": "GET",
                "headers": {"Authorization": "Bearer token"},
                "params": {"param1": "value1"}
            }
        )
        
        # Check the result
        assert len(documents) == 1
        assert "key" in documents[0].content
        assert "value" in documents[0].content
        assert documents[0].type == DocumentType.TEXT
        assert documents[0].metadata["source"] == "https://api.example.com/data"
        assert documents[0].metadata["source_type"] == "api"
        assert documents[0].metadata["method"] == "GET"
        assert documents[0].metadata["domain"] == "api.example.com"
"""
Tests for the knowledge maintenance agent.
"""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_base.agents.knowledge_maintenance_agent import KnowledgeMaintenanceAgent
from src.knowledge_base.agents.message import AgentMessage
from src.knowledge_base.core.config import Config


@pytest.fixture
def config():
    """Create a test configuration."""
    config = Config()
    # Add maintenance-specific configuration
    config.maintenance = MagicMock()
    config.maintenance.scheduled_tasks = {
        "check_integrity": {
            "interval": 86400,  # Daily
            "enabled": True,
            "params": {}
        },
        "clean_outdated": {
            "interval": 604800,  # Weekly
            "enabled": False,
            "params": {"max_age_days": 90}
        }
    }
    return config


@pytest.fixture
def agent(config):
    """Create a test knowledge maintenance agent."""
    agent = KnowledgeMaintenanceAgent(config)
    agent.dispatch_message = AsyncMock()
    agent.vector_store = MagicMock()
    agent.vector_store.get_stats = AsyncMock()
    return agent


@pytest.fixture
def task_message():
    """Create a test task message."""
    return AgentMessage(
        source="orchestrator",
        destination="maintenance_agent",
        message_type="task",
        payload={
            "task_id": "test_task",
            "task": "check_integrity",
            "params": {}
        }
    )


class TestKnowledgeMaintenanceAgent:
    """Tests for the KnowledgeMaintenanceAgent class."""
    
    async def test_initialization(self, config):
        """Test agent initialization."""
        agent = KnowledgeMaintenanceAgent(config)
        assert agent.agent_id == "maintenance_agent"
        assert "task" in agent.message_handlers
        assert len(agent.scheduled_tasks) == 2
        assert "check_integrity" in agent.scheduled_tasks
        assert agent.scheduled_tasks["check_integrity"]["enabled"] is True
        assert "clean_outdated" in agent.scheduled_tasks
        assert agent.scheduled_tasks["clean_outdated"]["enabled"] is False
    
    async def test_start(self, agent):
        """Test starting the agent."""
        # Mock the vector store initialize method
        agent.vector_store.initialize = AsyncMock()
        
        # Start the agent
        with patch("asyncio.create_task") as mock_create_task:
            await agent.start()
            
            # Check that vector store was initialized
            agent.vector_store.initialize.assert_called_once()
            
            # Check that maintenance scheduler was started
            mock_create_task.assert_called_once()
    
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
    
    async def test_handle_task_check_integrity(self, agent, task_message):
        """Test handling a check_integrity task."""
        # Set up the mock vector store to return stats
        stats = {
            "initialized": True,
            "total_documents": 100,
            "total_chunks": 1000,
            "provider": "memory"
        }
        agent.vector_store.get_stats.return_value = stats
        
        # Mock the _run_maintenance_task method
        agent._run_maintenance_task = AsyncMock()
        agent._run_maintenance_task.return_value = {
            "status": "ok",
            "checks_passed": 3,
            "checks_failed": 0,
            "issues": [],
            "stats": stats
        }
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that _run_maintenance_task was called with the correct parameters
        agent._run_maintenance_task.assert_called_once_with("check_integrity", {})
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["status"] == "ok"
    
    async def test_handle_task_get_maintenance_history(self, agent):
        """Test handling a get_maintenance_history task."""
        # Add some history entries
        agent.maintenance_history = [
            {
                "task": "check_integrity",
                "timestamp": int(time.time()),
                "success": True,
                "duration": 0.5,
                "result": {"status": "ok"}
            },
            {
                "task": "optimize_storage",
                "timestamp": int(time.time()),
                "success": True,
                "duration": 1.2,
                "result": {"status": "optimized"}
            }
        ]
        
        # Create a task message for getting maintenance history
        task_message = AgentMessage(
            source="orchestrator",
            destination="maintenance_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "get_maintenance_history",
                "params": {"limit": 1}
            }
        )
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert len(completion_message.payload["result"]["history"]) == 1
        assert completion_message.payload["result"]["count"] == 1
    
    async def test_handle_task_get_scheduled_tasks(self, agent):
        """Test handling a get_scheduled_tasks task."""
        # Create a task message for getting scheduled tasks
        task_message = AgentMessage(
            source="orchestrator",
            destination="maintenance_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "get_scheduled_tasks",
                "params": {}
            }
        )
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert len(completion_message.payload["result"]["tasks"]) == 2
        assert "check_integrity" in completion_message.payload["result"]["tasks"]
        assert "clean_outdated" in completion_message.payload["result"]["tasks"]
    
    async def test_handle_task_update_scheduled_task(self, agent):
        """Test handling an update_scheduled_task task."""
        # Create a task message for updating a scheduled task
        task_message = AgentMessage(
            source="orchestrator",
            destination="maintenance_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "update_scheduled_task",
                "params": {
                    "task_name": "clean_outdated",
                    "enabled": True,
                    "interval": 259200  # 3 days
                }
            }
        )
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that the task was updated
        assert agent.scheduled_tasks["clean_outdated"]["enabled"] is True
        assert agent.scheduled_tasks["clean_outdated"]["interval"] == 259200
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["task_name"] == "clean_outdated"
        assert completion_message.payload["result"]["updated"] is True
    
    async def test_handle_task_missing_params(self, agent):
        """Test handling a task with missing parameters."""
        # Create a message with missing parameters
        message = AgentMessage(
            source="orchestrator",
            destination="maintenance_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "update_scheduled_task",
                "params": {}
            }
        )
        
        # Handle the task
        await agent.handle_task(message)
        
        # Check that an error message was dispatched
        agent.dispatch_message.assert_called_once()
        error_message = agent.dispatch_message.call_args[0][0]
        assert error_message.message_type == "task_error"
        assert "Missing task_name parameter" in error_message.payload["error"]
    
    async def test_handle_task_unsupported_task(self, agent):
        """Test handling an unsupported task."""
        # Create a message with an unsupported task
        message = AgentMessage(
            source="orchestrator",
            destination="maintenance_agent",
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
    
    async def test_run_maintenance_task(self, agent):
        """Test running a maintenance task."""
        # Mock the maintenance task methods
        agent._check_integrity = AsyncMock()
        agent._check_integrity.return_value = {"status": "ok"}
        
        # Run a maintenance task
        result = await agent._run_maintenance_task("check_integrity", {})
        
        # Check that the task method was called
        agent._check_integrity.assert_called_once_with({})
        
        # Check the result
        assert result["success"] is True
        assert result["status"] == "ok"
        assert "duration" in result
        
        # Check that the task was added to history
        assert len(agent.maintenance_history) == 1
        assert agent.maintenance_history[0]["task"] == "check_integrity"
        assert agent.maintenance_history[0]["success"] is True
    
    async def test_check_integrity(self, agent):
        """Test checking integrity."""
        # Set up the mock vector store to return stats
        stats = {
            "initialized": True,
            "total_documents": 100,
            "total_chunks": 1000,
            "provider": "memory"
        }
        agent.vector_store.get_stats.return_value = stats
        
        # Check integrity
        result = await agent._check_integrity({})
        
        # Check that vector store was called
        agent.vector_store.get_stats.assert_called_once()
        
        # Check the result
        assert result["status"] == "ok"
        assert result["checks_passed"] == 3
        assert result["checks_failed"] == 0
        assert len(result["issues"]) == 0
        assert result["stats"] == stats
    
    async def test_check_integrity_with_issues(self, agent):
        """Test checking integrity with issues."""
        # Set up the mock vector store to return stats with issues
        stats = {
            "initialized": True,
            "total_documents": 0,
            "total_chunks": 0,
            "provider": "memory"
        }
        agent.vector_store.get_stats.return_value = stats
        
        # Check integrity
        result = await agent._check_integrity({})
        
        # Check the result
        assert result["status"] == "issues"
        assert result["checks_passed"] == 1
        assert result["checks_failed"] == 2
        assert len(result["issues"]) == 2
        assert "No documents in the vector store" in result["issues"]
        assert "No chunks in the vector store" in result["issues"]
    
    def test_add_to_history(self, agent):
        """Test adding to maintenance history."""
        # Add a task to history
        agent._add_to_history("test_task", True, 1.5, {"status": "ok"})
        
        # Check that the task was added
        assert len(agent.maintenance_history) == 1
        assert agent.maintenance_history[0]["task"] == "test_task"
        assert agent.maintenance_history[0]["success"] is True
        assert agent.maintenance_history[0]["duration"] == 1.5
        assert agent.maintenance_history[0]["result"]["status"] == "ok"
        
        # Add more tasks to test trimming
        agent.max_history_size = 2
        agent._add_to_history("test_task_2", True, 2.0, {"status": "ok"})
        agent._add_to_history("test_task_3", True, 3.0, {"status": "ok"})
        
        # Check that history was trimmed
        assert len(agent.maintenance_history) == 2
        assert agent.maintenance_history[0]["task"] == "test_task_2"
        assert agent.maintenance_history[1]["task"] == "test_task_3"
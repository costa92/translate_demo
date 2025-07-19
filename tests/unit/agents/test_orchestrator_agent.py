"""
Tests for the orchestrator agent.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch

from src.knowledge_base.agents import (
    AgentMessage, 
    AgentSystem, 
    BaseAgent, 
    OrchestratorAgent
)
from src.knowledge_base.core.config import Config


class MockSpecializedAgent(BaseAgent):
    """Mock specialized agent for testing."""
    
    def __init__(self, config, agent_id):
        super().__init__(config, agent_id)
        self.received_tasks = []
        self.register_handler("task", self.handle_task)
    
    async def handle_task(self, message):
        """Handle task messages."""
        self.received_tasks.append(message)
        task_id = message.payload.get("task_id")
        task = message.payload.get("task")
        
        # Simulate task execution
        await asyncio.sleep(0.1)
        
        # Send task completion message
        response = AgentMessage(
            source=self.agent_id,
            destination="orchestrator",
            message_type="task_complete",
            payload={
                "task_id": task_id,
                "result": {"status": "success", "task": task}
            }
        )
        
        await self.dispatch_message(response)
    
    async def process_message(self, message):
        """Process a message."""
        return message.create_response({"result": "success"})


# Create a concrete implementation of BaseAgent for testing
class TestResponseAgent(BaseAgent):
    """Test agent for receiving responses."""
    
    async def process_message(self, message):
        """Process a message."""
        return message.create_response({"result": "success"})


@pytest.fixture
def config():
    """Create a test configuration."""
    config = Config()
    # Mock the agents configuration
    config.agents = MagicMock()
    config.agents.specialized_agents = {
        "retrieval": True,
        "rag": True,
        "processing": True,
        "storage": True,
        "collection": False,
        "maintenance": False
    }
    return config


@pytest.fixture
def agent_system(config):
    """Create a test agent system."""
    return AgentSystem(config)


@pytest.fixture
def orchestrator_agent(config, agent_system):
    """Create a test orchestrator agent."""
    # Mock the create_agent function
    with patch("src.knowledge_base.agents.orchestrator.create_agent") as mock_create:
        # Configure the mock to return specialized agents
        def create_mock_agent(agent_class, config, agent_id):
            return MockSpecializedAgent(config, agent_id)
        
        mock_create.side_effect = create_mock_agent
        
        # Create the orchestrator agent
        orchestrator = OrchestratorAgent(config)
        agent_system.register_agent(orchestrator)
        
        return orchestrator


@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator_agent, agent_system):
    """Test orchestrator agent initialization."""
    # Start the agent system
    await agent_system.start_all()
    
    try:
        # Check that specialized agents were initialized
        assert "retrieval" in orchestrator_agent.agents
        assert "rag" in orchestrator_agent.agents
        assert "processing" in orchestrator_agent.agents
        assert "storage" in orchestrator_agent.agents
        assert "collection" not in orchestrator_agent.agents
        assert "maintenance" not in orchestrator_agent.agents
    finally:
        # Stop the agent system
        await agent_system.stop_all()


@pytest.mark.asyncio
async def test_orchestrator_request_handling(orchestrator_agent, agent_system):
    """Test orchestrator request handling."""
    # Start the agent system
    await agent_system.start_all()
    
    try:
        # Create a query request
        request = AgentMessage(
            source="api",
            destination="orchestrator",
            message_type="api_request",
            payload={
                "request_type": "query",
                "query": "test query"
            }
        )
        
        # Create a mock response handler for testing
        response_future = asyncio.Future()
        task_future = asyncio.Future()
        
        # Track dispatched tasks
        dispatched_tasks = []
        
        async def mock_dispatch(message):
            if message.message_type == "api_request_response":
                response_future.set_result(message)
            elif message.message_type == "task":
                dispatched_tasks.append(message)
                if len(dispatched_tasks) == 1:  # First task
                    task_future.set_result(message)
        
        # Replace the dispatch_message method temporarily
        original_dispatch = orchestrator_agent.dispatch_message
        orchestrator_agent.dispatch_message = mock_dispatch
        
        # Send the request
        await orchestrator_agent.send_message(request)
        
        # Wait for the response with timeout
        response = await asyncio.wait_for(response_future, timeout=2.0)
        
        # Check the initial response
        assert response.message_type == "api_request_response"
        assert response.payload["status"] == "processing"
        
        # Wait for the first task to be dispatched
        task = await asyncio.wait_for(task_future, timeout=2.0)
        
        # Check that the task is for retrieval
        assert task.destination.startswith("retrieval")
        assert task.payload["task"] == "retrieve"
        
        # Restore the original dispatch method
        orchestrator_agent.dispatch_message = original_dispatch
    finally:
        # Stop the agent system
        await agent_system.stop_all()


@pytest.mark.asyncio
async def test_orchestrator_task_planning(orchestrator_agent, agent_system):
    """Test orchestrator task planning."""
    # Start the agent system
    await agent_system.start_all()
    
    try:
        # Test query request plan
        query_plan = await orchestrator_agent._create_task_plan("query", {"query": "test"})
        assert len(query_plan) == 2
        assert query_plan[0]["agent"] == "retrieval"
        assert query_plan[1]["agent"] == "rag"
        
        # Test add_document request plan
        add_doc_plan = await orchestrator_agent._create_task_plan("add_document", {"document": "test"})
        assert len(add_doc_plan) == 2
        assert add_doc_plan[0]["agent"] == "processing"
        assert add_doc_plan[1]["agent"] == "storage"
        
        # Test collect_data request plan
        collect_plan = await orchestrator_agent._create_task_plan("collect_data", {"source": "test"})
        assert len(collect_plan) == 3
        assert collect_plan[0]["agent"] == "collection"
        assert collect_plan[1]["agent"] == "processing"
        assert collect_plan[2]["agent"] == "storage"
        
        # Test maintenance request plan
        maintenance_plan = await orchestrator_agent._create_task_plan("maintenance", {"maintenance_task": "test"})
        assert len(maintenance_plan) == 1
        assert maintenance_plan[0]["agent"] == "maintenance"
    finally:
        # Stop the agent system
        await agent_system.stop_all()


@pytest.mark.asyncio
async def test_orchestrator_error_handling(orchestrator_agent, agent_system):
    """Test orchestrator error handling."""
    # Start the agent system
    await agent_system.start_all()
    
    try:
        # Create a request with an unsupported type
        request = AgentMessage(
            source="api",
            destination="orchestrator",
            message_type="request",
            payload={
                "request_type": "unsupported_type"
            }
        )
        
        # Create a mock response handler for testing
        error_future = asyncio.Future()
        
        async def mock_dispatch(message):
            if message.message_type == "request_error":
                error_future.set_result(message)
        
        # Replace the dispatch_message method temporarily
        original_dispatch = orchestrator_agent.dispatch_message
        orchestrator_agent.dispatch_message = mock_dispatch
        
        # Send the request directly to the orchestrator
        await orchestrator_agent.send_message(request)
        
        # Wait for error response with timeout
        error_response = await asyncio.wait_for(error_future, timeout=2.0)
        
        # Restore the original dispatch method
        orchestrator_agent.dispatch_message = original_dispatch
        
        # Check that an error response was generated
        assert error_response.message_type == "request_error"
        assert "error" in error_response.payload
        assert "Unsupported request type" in error_response.payload["error"]
    finally:
        # Stop the agent system
        await agent_system.stop_all()


@pytest.mark.asyncio
async def test_orchestrator_recovery(orchestrator_agent, agent_system):
    """Test orchestrator recovery mechanisms."""
    # Start the agent system
    await agent_system.start_all()
    
    try:
        # Create a mock task context with an error
        task_id = "test_task_id"
        orchestrator_agent.active_tasks[task_id] = {
            "request": AgentMessage(
                source="api",
                destination="orchestrator",
                message_type="request",
                payload={"request_type": "query", "query": "test"}
            ),
            "plan": [
                {
                    "agent": "retrieval",
                    "task": "retrieve",
                    "params": {"query": "test"}
                }
            ],
            "current_step": 0,
            "results": {},
            "errors": [],
            "status": "in_progress"
        }
        
        # Test connection error recovery
        recovery_success = await orchestrator_agent._attempt_recovery(
            task_id, "retrieval", "Connection timeout"
        )
        assert recovery_success is True
        
        # Test retrieval not found error recovery
        recovery_success = await orchestrator_agent._attempt_recovery(
            task_id, "retrieval", "Document not found"
        )
        assert recovery_success is True
        
        # Test RAG generation error recovery
        recovery_success = await orchestrator_agent._attempt_recovery(
            task_id, "rag", "Generation failed"
        )
        assert recovery_success is True
        
        # Test unrecoverable error
        recovery_success = await orchestrator_agent._attempt_recovery(
            task_id, "storage", "Critical error"
        )
        assert recovery_success is False
    finally:
        # Stop the agent system
        await agent_system.stop_all()


@pytest.mark.asyncio
async def test_orchestrator_result_aggregation(orchestrator_agent, agent_system):
    """Test orchestrator result aggregation."""
    # Start the agent system
    await agent_system.start_all()
    
    try:
        # Create a mock task context with results
        task_context = {
            "request": AgentMessage(
                source="api",
                destination="orchestrator",
                message_type="request",
                payload={"request_type": "query", "query": "test"}
            ),
            "results": {
                "retrieval": {
                    "chunks": [{"id": "1", "text": "test chunk"}]
                },
                "rag": {
                    "query": "test",
                    "answer": "test answer",
                    "chunks": [{"id": "1", "text": "test chunk"}]
                }
            },
            "errors": [],
            "status": "completed"
        }
        
        # Test query result aggregation
        aggregated = await orchestrator_agent._aggregate_results(task_context)
        assert aggregated == task_context["results"]["rag"]
        
        # Test add_document result aggregation
        task_context["request"].payload["request_type"] = "add_document"
        task_context["results"] = {
            "processing": {"document_id": "doc1", "chunks": ["chunk1", "chunk2"]},
            "storage": {"document_id": "doc1", "chunks_stored": 2}
        }
        
        aggregated = await orchestrator_agent._aggregate_results(task_context)
        assert aggregated == task_context["results"]["storage"]
        
        # Test collect_data result aggregation
        task_context["request"].payload["request_type"] = "collect_data"
        task_context["results"] = {
            "collection": {"documents_collected": 5},
            "processing": {"chunks_created": 10},
            "storage": {"chunks_stored": 10}
        }
        
        aggregated = await orchestrator_agent._aggregate_results(task_context)
        assert aggregated["collected"] == 5
        assert aggregated["processed"] == 10
        assert aggregated["stored"] == 10
        assert aggregated["status"] == "completed"
    finally:
        # Stop the agent system
        await agent_system.stop_all()
"""
Tests for the agent framework.
"""

import asyncio
import pytest

from src.knowledge_base.agents import (
    AgentMessage, 
    AgentSystem, 
    BaseAgent, 
    AgentRegistry, 
    register_agent
)
from src.knowledge_base.core.config import Config


class TestAgent(BaseAgent):
    """Test agent implementation."""
    
    def __init__(self, config, agent_id):
        super().__init__(config, agent_id)
        self.received_messages = []
        self.register_handler("test_message", self.handle_test_message)
    
    async def handle_test_message(self, message):
        self.received_messages.append(message)
        return await self.process_message(message)
    
    async def process_message(self, message):
        return message.create_response({"result": "success"})


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config()


@pytest.fixture
def agent_system(config):
    """Create a test agent system."""
    return AgentSystem(config)


@pytest.mark.asyncio
async def test_agent_message():
    """Test the AgentMessage class."""
    # Create a message
    message = AgentMessage(
        source="source_agent",
        destination="dest_agent",
        message_type="test_message",
        payload={"key": "value"}
    )
    
    # Check basic properties
    assert message.source == "source_agent"
    assert message.destination == "dest_agent"
    assert message.message_type == "test_message"
    assert message.payload == {"key": "value"}
    assert message.id is not None
    assert message.timestamp is not None
    assert message.parent_id is None
    
    # Test response creation
    response = message.create_response({"result": "success"})
    assert response.source == "dest_agent"
    assert response.destination == "source_agent"
    assert response.message_type == "test_message_response"
    assert response.payload == {"result": "success"}
    assert response.parent_id == message.id
    
    # Test error response creation
    error = message.create_error_response("Something went wrong")
    assert error.source == "dest_agent"
    assert error.destination == "source_agent"
    assert error.message_type == "test_message_error"
    assert error.payload == {"error": "Something went wrong", "details": {}}
    assert error.parent_id == message.id


@pytest.mark.asyncio
async def test_agent_system(config, agent_system):
    """Test the AgentSystem class."""
    # Create agents
    agent1 = TestAgent(config, "agent1")
    agent2 = TestAgent(config, "agent2")
    
    # Register agents
    agent_system.register_agent(agent1)
    agent_system.register_agent(agent2)
    
    # Start agents
    await agent_system.start_all()
    
    try:
        # Send a message
        message = AgentMessage(
            source="external",
            destination="agent1",
            message_type="test_message",
            payload={"key": "value"}
        )
        
        await agent_system.send_message(message)
        
        # Wait for message processing
        await asyncio.sleep(0.1)
        
        # Check that agent1 received the message
        assert len(agent1.received_messages) == 1
        assert agent1.received_messages[0].id == message.id
        
        # Check that agent2 did not receive the message
        assert len(agent2.received_messages) == 0
        
        # Test request-response
        response = await agent_system.request_response(
            AgentMessage(
                source="external",
                destination="agent1",
                message_type="test_message",
                payload={"key": "value"}
            )
        )
        
        assert response.message_type == "test_message_response"
        assert response.payload == {"result": "success"}
    finally:
        # Stop agents
        await agent_system.stop_all()


@pytest.mark.asyncio
async def test_agent_registry(config):
    """Test the AgentRegistry class."""
    # Create registry
    registry = AgentRegistry()
    
    # Register agent class
    registry.register("TestAgent", TestAgent)
    
    # Check registration
    assert "TestAgent" in registry.list()
    assert registry.get("TestAgent") == TestAgent
    
    # Create agent instance
    agent = registry.create("TestAgent", config, "test_agent")
    assert isinstance(agent, TestAgent)
    assert agent.agent_id == "test_agent"
    
    # Test global registry functions
    register_agent("GlobalTestAgent", TestAgent)
    from src.knowledge_base.agents import create_agent, get_registry
    
    assert "GlobalTestAgent" in get_registry().list()
    
    global_agent = create_agent("GlobalTestAgent", config, "global_test_agent")
    assert isinstance(global_agent, TestAgent)
    assert global_agent.agent_id == "global_test_agent"
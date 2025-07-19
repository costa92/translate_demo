"""
Tests for the knowledge retrieval agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_base.agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from src.knowledge_base.agents.message import AgentMessage
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import TextChunk, RetrievalResult


@pytest.fixture
def config():
    """Create a test configuration."""
    config = Config()
    # Add retrieval-specific configuration
    config.retrieval = MagicMock()
    config.retrieval.strategy = "semantic"
    config.retrieval.top_k = 5
    config.retrieval.min_score = 0.5
    config.retrieval.enable_reranking = False
    return config


@pytest.fixture
def agent(config):
    """Create a test knowledge retrieval agent."""
    agent = KnowledgeRetrievalAgent(config)
    agent.dispatch_message = AsyncMock()
    agent.vector_store = MagicMock()
    agent.retriever = MagicMock()
    return agent


@pytest.fixture
def retrieval_results():
    """Create test retrieval results."""
    results = []
    for i in range(3):
        chunk = TextChunk(
            id=f"chunk_{i}",
            text=f"This is test chunk {i}",
            document_id="test_doc",
            metadata={"index": i},
            embedding=[0.1, 0.2, 0.3]
        )
        result = RetrievalResult(
            chunk=chunk,
            score=0.8 - (i * 0.1),
            rank=i
        )
        results.append(result)
    return results


@pytest.fixture
def task_message():
    """Create a test task message."""
    return AgentMessage(
        source="orchestrator",
        destination="retrieval_agent",
        message_type="task",
        payload={
            "task_id": "test_task",
            "task": "retrieve",
            "params": {
                "query": "test query",
                "filter": {"category": "test"},
                "top_k": 3
            }
        }
    )


class TestKnowledgeRetrievalAgent:
    """Tests for the KnowledgeRetrievalAgent class."""
    
    async def test_initialization(self, config):
        """Test agent initialization."""
        agent = KnowledgeRetrievalAgent(config)
        assert agent.agent_id == "retrieval_agent"
        assert "task" in agent.message_handlers
        assert agent.active_conversations == {}
    
    async def test_start(self, agent):
        """Test starting the agent."""
        # Mock the vector store initialize method
        agent.vector_store.initialize = AsyncMock()
        
        # Create a mock retriever class
        with patch("src.knowledge_base.agents.knowledge_retrieval_agent.Retriever") as mock_retriever_class:
            # Start the agent
            await agent.start()
            
            # Check that vector store was initialized
            agent.vector_store.initialize.assert_called_once()
            
            # Check that retriever was created
            mock_retriever_class.assert_called_once()
    
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
    
    async def test_handle_task_retrieve(self, agent, task_message, retrieval_results):
        """Test handling a retrieve task."""
        # Set up the mock retriever to return results
        agent.retriever.retrieve.return_value = retrieval_results
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that retriever was called with the correct parameters
        agent.retriever.retrieve.assert_called_once()
        call_args = agent.retriever.retrieve.call_args[0][0]
        assert call_args.text == "test query"
        assert call_args.filters == {"category": "test"}
        assert call_args.top_k == 3
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["query"] == "test query"
        assert completion_message.payload["result"]["count"] == 3
        assert len(completion_message.payload["result"]["chunks"]) == 3
    
    async def test_handle_task_create_conversation(self, agent):
        """Test handling a create_conversation task."""
        # Create a task message for creating a conversation
        task_message = AgentMessage(
            source="orchestrator",
            destination="retrieval_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "create_conversation",
                "params": {
                    "metadata": {"user_id": "test_user"}
                }
            }
        )
        
        # Set up the mock retriever to return a conversation ID
        agent.retriever.create_conversation.return_value = "conv_123"
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that retriever was called with the correct parameters
        agent.retriever.create_conversation.assert_called_once_with({"user_id": "test_user"})
        
        # Check that the conversation was stored
        assert "conv_123" in agent.active_conversations
        assert agent.active_conversations["conv_123"] == {"user_id": "test_user"}
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["conversation_id"] == "conv_123"
    
    async def test_handle_task_get_conversation_context(self, agent):
        """Test handling a get_conversation_context task."""
        # Create a task message for getting conversation context
        task_message = AgentMessage(
            source="orchestrator",
            destination="retrieval_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "get_conversation_context",
                "params": {
                    "conversation_id": "conv_123"
                }
            }
        )
        
        # Set up the mock retriever to return context
        context = [
            {
                "query": "test query",
                "answer": "test answer",
                "sources": [],
                "timestamp": "2023-01-01T12:00:00",
                "turn_id": 1
            }
        ]
        agent.retriever.get_conversation_context.return_value = context
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that retriever was called with the correct parameters
        agent.retriever.get_conversation_context.assert_called_once_with("conv_123")
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["conversation_id"] == "conv_123"
        assert completion_message.payload["result"]["context"] == context
    
    async def test_handle_task_delete_conversation(self, agent):
        """Test handling a delete_conversation task."""
        # Add a conversation to active conversations
        agent.active_conversations["conv_123"] = {"user_id": "test_user"}
        
        # Create a task message for deleting a conversation
        task_message = AgentMessage(
            source="orchestrator",
            destination="retrieval_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "delete_conversation",
                "params": {
                    "conversation_id": "conv_123"
                }
            }
        )
        
        # Set up the mock retriever to return success
        agent.retriever.delete_conversation.return_value = True
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that retriever was called with the correct parameters
        agent.retriever.delete_conversation.assert_called_once_with("conv_123")
        
        # Check that the conversation was removed
        assert "conv_123" not in agent.active_conversations
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["conversation_id"] == "conv_123"
        assert completion_message.payload["result"]["success"] is True
    
    async def test_handle_task_clear_cache(self, agent):
        """Test handling a clear_cache task."""
        # Create a task message for clearing the cache
        task_message = AgentMessage(
            source="orchestrator",
            destination="retrieval_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "clear_cache",
                "params": {}
            }
        )
        
        # Set up the mock retriever
        agent.retriever.clear_cache = MagicMock()
        agent.retriever.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that retriever methods were called
        agent.retriever.clear_cache.assert_called_once()
        agent.retriever.get_cache_stats.assert_called_once()
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["success"] is True
        assert completion_message.payload["result"]["cache_stats"] == {"hits": 0, "misses": 0}
    
    async def test_handle_task_missing_params(self, agent):
        """Test handling a task with missing parameters."""
        # Create a message with missing parameters
        message = AgentMessage(
            source="orchestrator",
            destination="retrieval_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "retrieve",
                "params": {}
            }
        )
        
        # Handle the task
        await agent.handle_task(message)
        
        # Check that an error message was dispatched
        agent.dispatch_message.assert_called_once()
        error_message = agent.dispatch_message.call_args[0][0]
        assert error_message.message_type == "task_error"
        assert "Missing query parameter" in error_message.payload["error"]
    
    async def test_handle_task_unsupported_task(self, agent):
        """Test handling an unsupported task."""
        # Create a message with an unsupported task
        message = AgentMessage(
            source="orchestrator",
            destination="retrieval_agent",
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
    
    def test_format_retrieval_results(self, agent, retrieval_results):
        """Test formatting retrieval results."""
        # Format the results
        formatted_results = agent._format_retrieval_results(retrieval_results)
        
        # Check the formatted results
        assert len(formatted_results) == 3
        for i, result in enumerate(formatted_results):
            assert result["id"] == f"chunk_{i}"
            assert result["text"] == f"This is test chunk {i}"
            assert result["document_id"] == "test_doc"
            assert result["metadata"] == {"index": i}
            assert result["score"] == 0.8 - (i * 0.1)
            assert result["rank"] == i
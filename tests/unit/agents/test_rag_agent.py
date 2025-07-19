"""
Tests for the RAG agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_base.agents.rag_agent import RAGAgent
from src.knowledge_base.agents.message import AgentMessage
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import TextChunk, RetrievalResult, QueryResult, Citation


@pytest.fixture
def config():
    """Create a test configuration."""
    config = Config()
    # Add generation-specific configuration
    config.generation = MagicMock()
    config.generation.provider = "simple"
    config.generation.stream = False
    config.generation.validate = True
    config.generation.include_citations = True
    return config


@pytest.fixture
def agent(config):
    """Create a test RAG agent."""
    agent = RAGAgent(config)
    agent.dispatch_message = AsyncMock()
    agent.vector_store = MagicMock()
    agent.retriever = MagicMock()
    agent.generator = MagicMock()
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
def query_result(chunks):
    """Create a test query result."""
    sources = [
        RetrievalResult(chunk=chunk, score=0.8, rank=i)
        for i, chunk in enumerate(chunks)
    ]
    citations = [
        Citation(
            text="test chunk 0",
            chunk_id="chunk_0",
            document_id="test_doc",
            start=8,
            end=19
        )
    ]
    return QueryResult(
        query="test query",
        answer="The answer is in test chunk 0.",
        sources=sources,
        citations=citations
    )


@pytest.fixture
def task_message():
    """Create a test task message."""
    return AgentMessage(
        source="orchestrator",
        destination="rag_agent",
        message_type="task",
        payload={
            "task_id": "test_task",
            "task": "generate",
            "params": {
                "query": "test query",
                "stream": False
            }
        }
    )


class TestRAGAgent:
    """Tests for the RAGAgent class."""
    
    async def test_initialization(self, config):
        """Test agent initialization."""
        agent = RAGAgent(config)
        assert agent.agent_id == "rag_agent"
        assert "task" in agent.message_handlers
        assert agent.stream_chunk_size == 10
    
    async def test_start(self, agent):
        """Test starting the agent."""
        # Mock the vector store initialize method
        agent.vector_store.initialize = AsyncMock()
        
        # Create mock classes
        with patch("src.knowledge_base.agents.rag_agent.Retriever") as mock_retriever_class, \
             patch("src.knowledge_base.agents.rag_agent.Generator") as mock_generator_class:
            # Start the agent
            await agent.start()
            
            # Check that vector store was initialized
            agent.vector_store.initialize.assert_called_once()
            
            # Check that retriever and generator were created
            mock_retriever_class.assert_called_once()
            mock_generator_class.assert_called_once()
    
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
    
    async def test_handle_task_generate_with_chunks(self, agent, task_message, chunks, query_result):
        """Test handling a generate task with provided chunks."""
        # Add chunks to the task message
        task_message.payload["params"]["chunks"] = [
            {
                "id": chunk.id,
                "text": chunk.text,
                "document_id": chunk.document_id,
                "metadata": chunk.metadata,
                "embedding": chunk.embedding
            }
            for chunk in chunks
        ]
        
        # Set up the mock generator to return a query result
        agent.generator.generate = AsyncMock(return_value=query_result)
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that generator was called with the correct parameters
        agent.generator.generate.assert_called_once()
        call_args = agent.generator.generate.call_args[1]
        assert call_args["query"] == "test query"
        assert len(call_args["chunks"]) == 3
        assert call_args["stream"] is False
        assert call_args["validate"] is True
        assert call_args["include_citations"] is True
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["query"] == "test query"
        assert completion_message.payload["result"]["answer"] == "The answer is in test chunk 0."
        assert len(completion_message.payload["result"]["chunks"]) == 3
        assert len(completion_message.payload["result"]["citations"]) == 1
    
    async def test_handle_task_generate_with_retrieval(self, agent, task_message, chunks):
        """Test handling a generate task with retrieval results."""
        # Set up the mock retriever to return results
        retrieval_results = [
            RetrievalResult(chunk=chunk, score=0.8, rank=i)
            for i, chunk in enumerate(chunks)
        ]
        agent.retriever.retrieve = AsyncMock(return_value=retrieval_results)
        
        # Set up the mock generator to return a string
        agent.generator.generate = AsyncMock(return_value="The answer is in the chunks.")
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that retriever was called
        agent.retriever.retrieve.assert_called_once()
        
        # Check that generator was called with the correct parameters
        agent.generator.generate.assert_called_once()
        call_args = agent.generator.generate.call_args[1]
        assert call_args["query"] == "test query"
        assert len(call_args["chunks"]) == 3
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["query"] == "test query"
        assert completion_message.payload["result"]["answer"] == "The answer is in the chunks."
    
    async def test_handle_task_generate_no_chunks(self, agent, task_message):
        """Test handling a generate task with no chunks."""
        # Set up the mock retriever to return empty results
        agent.retriever.retrieve = AsyncMock(return_value=[])
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that retriever was called
        agent.retriever.retrieve.assert_called_once()
        
        # Check that generator was not called
        agent.generator.generate.assert_not_called()
        
        # Check that a completion message was dispatched
        agent.dispatch_message.assert_called_once()
        completion_message = agent.dispatch_message.call_args[0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["query"] == "test query"
        assert completion_message.payload["result"]["answer"] == "I don't have enough information to answer that question."
        assert completion_message.payload["result"]["chunks"] == []
    
    async def test_handle_task_generate_streaming(self, agent, task_message, chunks):
        """Test handling a streaming generate task."""
        # Set streaming to true
        task_message.payload["params"]["stream"] = True
        
        # Add chunks to the task message
        task_message.payload["params"]["chunks"] = [
            {
                "id": chunk.id,
                "text": chunk.text,
                "document_id": chunk.document_id,
                "metadata": chunk.metadata,
                "embedding": chunk.embedding
            }
            for chunk in chunks
        ]
        
        # Mock the _handle_streaming_generation method
        agent._handle_streaming_generation = AsyncMock()
        
        # Handle the task
        await agent.handle_task(task_message)
        
        # Check that _handle_streaming_generation was called
        agent._handle_streaming_generation.assert_called_once()
        call_args = agent._handle_streaming_generation.call_args[1]
        assert call_args["task_id"] == "test_task"
        assert call_args["query"] == "test query"
        assert len(call_args["chunks"]) == 3
        assert call_args["destination"] == "orchestrator"
    
    async def test_handle_task_missing_params(self, agent):
        """Test handling a task with missing parameters."""
        # Create a message with missing parameters
        message = AgentMessage(
            source="orchestrator",
            destination="rag_agent",
            message_type="task",
            payload={
                "task_id": "test_task",
                "task": "generate",
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
            destination="rag_agent",
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
    
    async def test_handle_streaming_generation(self, agent, chunks):
        """Test handling streaming generation."""
        # Create a mock async iterator for the stream
        async def mock_stream():
            yield "This "
            yield "is "
            yield "a "
            yield "test "
            yield "answer."
        
        # Set up the mock generator to return a stream
        agent.generator.generate = AsyncMock(return_value=mock_stream())
        
        # Handle streaming generation
        await agent._handle_streaming_generation(
            task_id="test_task",
            query="test query",
            chunks=chunks,
            destination="orchestrator"
        )
        
        # Check that generator was called with the correct parameters
        agent.generator.generate.assert_called_once()
        call_args = agent.generator.generate.call_args[1]
        assert call_args["query"] == "test query"
        assert call_args["chunks"] == chunks
        assert call_args["stream"] is True
        
        # Check that messages were dispatched
        assert agent.dispatch_message.call_count >= 4
        
        # Check the start message
        start_message = agent.dispatch_message.call_args_list[0][0][0]
        assert start_message.message_type == "stream_start"
        assert start_message.payload["task_id"] == "test_task"
        assert start_message.payload["query"] == "test query"
        
        # Check the end message (second to last call)
        end_message = agent.dispatch_message.call_args_list[-2][0][0]
        assert end_message.message_type == "stream_end"
        assert end_message.payload["task_id"] == "test_task"
        assert end_message.payload["status"] == "completed"
        
        # Check the completion message (last call)
        completion_message = agent.dispatch_message.call_args_list[-1][0][0]
        assert completion_message.message_type == "task_complete"
        assert completion_message.payload["task_id"] == "test_task"
        assert completion_message.payload["result"]["query"] == "test query"
        assert completion_message.payload["result"]["status"] == "streamed"
    
    def test_chunk_to_dict(self, agent, chunks):
        """Test converting a chunk to a dictionary."""
        # Convert a chunk to a dictionary
        chunk_dict = agent._chunk_to_dict(chunks[0])
        
        # Check the dictionary
        assert chunk_dict["id"] == "chunk_0"
        assert chunk_dict["text"] == "This is test chunk 0"
        assert chunk_dict["document_id"] == "test_doc"
        assert chunk_dict["metadata"] == {"index": 0}
        assert chunk_dict["embedding"] == [0.1, 0.2, 0.3]
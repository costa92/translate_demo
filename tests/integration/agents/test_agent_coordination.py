"""
Integration tests for agent coordination.

This module tests the coordination between different agents in the system.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import MagicMock

from src.knowledge_base.core.config import Config
from src.knowledge_base.agents.orchestrator import OrchestratorAgent
from src.knowledge_base.agents.data_collection_agent import DataCollectionAgent
from src.knowledge_base.agents.knowledge_processing_agent import KnowledgeProcessingAgent
from src.knowledge_base.agents.knowledge_storage_agent import KnowledgeStorageAgent
from src.knowledge_base.agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from src.knowledge_base.agents.rag_agent import RAGAgent
from src.knowledge_base.agents.message import AgentMessage
from src.knowledge_base.core.types import Document, TextChunk


@pytest.fixture
def agent_config():
    """Create a configuration for agent testing."""
    config_dict = {
        "system": {
            "debug": True,
            "log_level": "DEBUG"
        },
        "storage": {
            "provider": "memory",
            "max_chunks": 1000,
            "persistence_enabled": False
        },
        "embedding": {
            "provider": "sentence_transformers",
            "model_name": "all-MiniLM-L6-v2",
            "cache_enabled": True
        },
        "chunking": {
            "strategy": "recursive",
            "chunk_size": 100,
            "chunk_overlap": 20,
            "separators": ["\n\n", "\n", " ", ""]
        },
        "retrieval": {
            "strategy": "semantic",
            "top_k": 3,
            "reranking_enabled": True
        },
        "generation": {
            "provider": "simple",
            "model_name": "test-model",
            "temperature": 0.7,
            "max_tokens": 500,
            "stream": False,
            "include_citations": True
        },
        "agents": {
            "enabled": True,
            "orchestrator": {
                "max_retries": 3,
                "timeout": 30
            }
        }
    }
    return Config.from_dict(config_dict)


@pytest.fixture
async def orchestrator(agent_config):
    """Create and initialize an orchestrator agent for testing."""
    orchestrator = OrchestratorAgent(agent_config)
    await orchestrator.start()
    yield orchestrator
    await orchestrator.stop()


@pytest.fixture
def test_document():
    """Create a test document for agent testing."""
    return Document(
        id="test_doc",
        content="This is a test document for agent coordination testing. "
                "It contains information about knowledge base systems and RAG pipelines.",
        type="text",
        metadata={
            "source": "agent_test",
            "author": "tester",
            "topic": "knowledge_base"
        }
    )


@pytest.mark.asyncio
async def test_agent_initialization(agent_config):
    """Test that all agents can be initialized properly."""
    # Create all agents
    orchestrator = OrchestratorAgent(agent_config)
    data_collection = DataCollectionAgent(agent_config)
    knowledge_processing = KnowledgeProcessingAgent(agent_config)
    knowledge_storage = KnowledgeStorageAgent(agent_config)
    knowledge_retrieval = KnowledgeRetrievalAgent(agent_config)
    rag = RAGAgent(agent_config)
    
    # Start all agents
    await orchestrator.start()
    await data_collection.start()
    await knowledge_processing.start()
    await knowledge_storage.start()
    await knowledge_retrieval.start()
    await rag.start()
    
    # Verify agent IDs
    assert orchestrator.agent_id == "orchestrator"
    assert data_collection.agent_id == "data_collection_agent"
    assert knowledge_processing.agent_id == "knowledge_processing_agent"
    assert knowledge_storage.agent_id == "knowledge_storage_agent"
    assert knowledge_retrieval.agent_id == "knowledge_retrieval_agent"
    assert rag.agent_id == "rag_agent"
    
    # Stop all agents
    await rag.stop()
    await knowledge_retrieval.stop()
    await knowledge_storage.stop()
    await knowledge_processing.stop()
    await data_collection.stop()
    await orchestrator.stop()


@pytest.mark.asyncio
async def test_orchestrator_agent_registry(agent_config):
    """Test that the orchestrator can register and manage other agents."""
    orchestrator = OrchestratorAgent(agent_config)
    await orchestrator.start()
    
    # Check that all required agents are registered
    assert "data_collection_agent" in orchestrator.agents
    assert "knowledge_processing_agent" in orchestrator.agents
    assert "knowledge_storage_agent" in orchestrator.agents
    assert "knowledge_retrieval_agent" in orchestrator.agents
    assert "knowledge_maintenance_agent" in orchestrator.agents
    assert "rag_agent" in orchestrator.agents
    
    # Check that agents are of the correct type
    assert isinstance(orchestrator.agents["data_collection_agent"], DataCollectionAgent)
    assert isinstance(orchestrator.agents["knowledge_processing_agent"], KnowledgeProcessingAgent)
    assert isinstance(orchestrator.agents["knowledge_storage_agent"], KnowledgeStorageAgent)
    assert isinstance(orchestrator.agents["knowledge_retrieval_agent"], KnowledgeRetrievalAgent)
    assert isinstance(orchestrator.agents["rag_agent"], RAGAgent)
    
    await orchestrator.stop()


@pytest.mark.asyncio
async def test_document_processing_workflow(orchestrator, test_document):
    """Test the document processing workflow across multiple agents."""
    # Create a request to add a document
    result = await orchestrator.receive_request(
        source="test",
        request_type="add_document",
        payload={
            "document": {
                "id": test_document.id,
                "content": test_document.content,
                "type": test_document.type,
                "metadata": test_document.metadata
            }
        }
    )
    
    # Check the result
    assert "success" in result
    assert result["success"] is True
    assert "document_id" in result
    assert result["document_id"] == test_document.id
    assert "chunk_ids" in result
    assert len(result["chunk_ids"]) > 0
    
    # Verify the document was processed by querying for it
    query_result = await orchestrator.receive_request(
        source="test",
        request_type="query",
        payload={
            "query": "What is this document about?",
            "filter": {"source": "agent_test"}
        }
    )
    
    # Check the query result
    assert "answer" in query_result
    assert len(query_result["answer"]) > 0
    assert "chunks" in query_result
    assert len(query_result["chunks"]) > 0
    
    # Clean up
    delete_result = await orchestrator.receive_request(
        source="test",
        request_type="delete_document",
        payload={
            "document_id": test_document.id
        }
    )
    
    assert "success" in delete_result
    assert delete_result["success"] is True


@pytest.mark.asyncio
async def test_message_routing(orchestrator):
    """Test message routing between agents."""
    # Create a test message
    message = AgentMessage(
        source="test",
        destination="orchestrator",
        message_type="task",
        payload={
            "task_id": "test_task",
            "task": "echo",
            "params": {
                "message": "Hello, agents!"
            }
        }
    )
    
    # Process the message
    response = await orchestrator.process_message(message)
    
    # Check the response
    assert response.source == "orchestrator"
    assert response.destination == "test"
    assert response.message_type == "task_response"
    assert "status" in response.payload
    assert response.payload["status"] == "received"
    assert "task_id" in response.payload
    assert response.payload["task_id"] == "test_task"


@pytest.mark.asyncio
async def test_error_handling_and_recovery(orchestrator):
    """Test error handling and recovery mechanisms between agents."""
    # Create a message that will cause an error
    message = AgentMessage(
        source="test",
        destination="orchestrator",
        message_type="task",
        payload={
            "task_id": "error_task",
            "task": "process_document",
            "params": {
                # Missing required document parameter
            }
        }
    )
    
    # Process the message
    response = await orchestrator.process_message(message)
    
    # Check the response indicates an error
    assert response.message_type == "task_error"
    assert "error" in response.payload
    assert response.payload["task_id"] == "error_task"
    
    # Test recovery by sending a valid message after an error
    valid_message = AgentMessage(
        source="test",
        destination="orchestrator",
        message_type="task",
        payload={
            "task_id": "valid_task",
            "task": "health_check",
            "params": {}
        }
    )
    
    # Process the valid message
    response = await orchestrator.process_message(valid_message)
    
    # Check the response is successful
    assert response.message_type == "task_response"
    assert "status" in response.payload
    assert response.payload["status"] == "healthy"


@pytest.mark.asyncio
async def test_parallel_task_processing(orchestrator):
    """Test that multiple tasks can be processed in parallel."""
    # Create multiple tasks
    tasks = []
    for i in range(5):
        tasks.append(
            orchestrator.receive_request(
                source="test",
                request_type="health_check",
                payload={}
            )
        )
    
    # Process tasks in parallel
    results = await asyncio.gather(*tasks)
    
    # Check all results
    for result in results:
        assert "status" in result
        assert result["status"] == "healthy"


@pytest.mark.asyncio
async def test_rag_workflow(orchestrator, test_document):
    """Test the complete RAG workflow across multiple agents."""
    # Add a document
    add_result = await orchestrator.receive_request(
        source="test",
        request_type="add_document",
        payload={
            "document": {
                "id": test_document.id,
                "content": test_document.content,
                "type": test_document.type,
                "metadata": test_document.metadata
            }
        }
    )
    
    assert add_result["success"] is True
    
    # Perform a query
    query_result = await orchestrator.receive_request(
        source="test",
        request_type="query",
        payload={
            "query": "What is this document about?",
            "filter": {"source": "agent_test"}
        }
    )
    
    # Check the query result
    assert "answer" in query_result
    assert len(query_result["answer"]) > 0
    assert "chunks" in query_result
    assert len(query_result["chunks"]) > 0
    
    # Test streaming query
    stream_result = await orchestrator.receive_request(
        source="test",
        request_type="query",
        payload={
            "query": "Summarize this document",
            "filter": {"source": "agent_test"},
            "stream": True
        }
    )
    
    # For streaming, we expect a status indicating streaming has started
    assert "status" in stream_result
    assert stream_result["status"] == "streaming"
    
    # Clean up
    delete_result = await orchestrator.receive_request(
        source="test",
        request_type="delete_document",
        payload={
            "document_id": test_document.id
        }
    )
    
    assert delete_result["success"] is True
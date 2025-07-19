"""
Tests for the WebSocket handler.

This module contains tests for the WebSocket handler functionality.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import WebSocket, WebSocketDisconnect
from src.knowledge_base.api.websocket.handler import WebSocketManager
from src.knowledge_base.core.config import Config
from src.knowledge_base.agents.orchestrator import OrchestratorAgent
from src.knowledge_base.agents.message import AgentMessage


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.sent_messages = []
        self.closed = False
        
    async def accept(self):
        """Accept the connection."""
        pass
        
    async def send_json(self, data):
        """Send JSON data."""
        self.sent_messages.append(data)
        
    async def receive_json(self):
        """Receive JSON data."""
        if self.closed:
            raise WebSocketDisconnect()
        return {"request_id": "test", "request_type": "query", "payload": {"query": "test query"}}
        
    def close(self):
        """Close the connection."""
        self.closed = True


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = MagicMock(spec=Config)
    return config


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator agent."""
    orchestrator = AsyncMock(spec=OrchestratorAgent)
    
    # Mock receive_request method
    async def mock_receive_request(source, request_type, payload):
        if request_type == "retrieve":
            return {
                "chunks": [
                    {"id": "1", "text": "Test chunk 1", "document_id": "doc1", "metadata": {}},
                    {"id": "2", "text": "Test chunk 2", "document_id": "doc1", "metadata": {}}
                ]
            }
        return {"status": "success", "result": "Test result"}
    
    orchestrator.receive_request = mock_receive_request
    
    # Mock receive_request_stream method
    async def mock_receive_request_stream(source, request_type, payload):
        yield "Chunk 1"
        yield "Chunk 2"
        yield "Chunk 3"
    
    orchestrator.receive_request_stream = mock_receive_request_stream
    
    return orchestrator


@pytest.fixture
def websocket_manager(mock_config, mock_orchestrator):
    """Create a WebSocket manager for testing."""
    return WebSocketManager(mock_config, mock_orchestrator)


@pytest.mark.asyncio
async def test_connect(websocket_manager):
    """Test WebSocket connection."""
    websocket = MockWebSocket()
    client_id = "test_client"
    
    await websocket_manager.connect(websocket, client_id)
    
    assert client_id in websocket_manager.active_connections
    assert websocket_manager.active_connections[client_id] == websocket


@pytest.mark.asyncio
async def test_disconnect(websocket_manager):
    """Test WebSocket disconnection."""
    websocket = MockWebSocket()
    client_id = "test_client"
    
    await websocket_manager.connect(websocket, client_id)
    websocket_manager.disconnect(client_id)
    
    assert client_id not in websocket_manager.active_connections


@pytest.mark.asyncio
async def test_send_message(websocket_manager):
    """Test sending a message to a client."""
    websocket = MockWebSocket()
    client_id = "test_client"
    message = {"type": "test", "data": "test_data"}
    
    await websocket_manager.connect(websocket, client_id)
    await websocket_manager.send_message(client_id, message)
    
    assert message in websocket.sent_messages


@pytest.mark.asyncio
async def test_broadcast(websocket_manager):
    """Test broadcasting a message to all clients."""
    websocket1 = MockWebSocket()
    websocket2 = MockWebSocket()
    client_id1 = "test_client1"
    client_id2 = "test_client2"
    message = {"type": "test", "data": "test_data"}
    
    await websocket_manager.connect(websocket1, client_id1)
    await websocket_manager.connect(websocket2, client_id2)
    await websocket_manager.broadcast(message)
    
    assert message in websocket1.sent_messages
    assert message in websocket2.sent_messages


@pytest.mark.asyncio
async def test_handle_streaming_query(websocket_manager):
    """Test handling a streaming query."""
    websocket = MockWebSocket()
    client_id = "test_client"
    request_id = "test_request"
    payload = {"query": "test query", "stream": True}
    
    await websocket_manager.connect(websocket, client_id)
    await websocket_manager._handle_streaming_query(client_id, request_id, payload)
    
    # Check that chunks response was sent
    assert any(msg.get("type") == "chunks" for msg in websocket.sent_messages)
    
    # Check that chunks were sent
    chunk_messages = [msg for msg in websocket.sent_messages if msg.get("type") == "chunk"]
    assert len(chunk_messages) == 3
    
    # Check that complete message was sent
    assert any(msg.get("type") == "complete" for msg in websocket.sent_messages)


@pytest.mark.asyncio
async def test_subscribe_unsubscribe(websocket_manager):
    """Test subscribing and unsubscribing to topics."""
    websocket = MockWebSocket()
    client_id = "test_client"
    topic = "test_topic"
    
    await websocket_manager.connect(websocket, client_id)
    
    # Test subscribe
    await websocket_manager.subscribe(client_id, topic)
    assert client_id in websocket_manager.subscriptions
    assert topic in websocket_manager.subscriptions[client_id]
    
    # Check subscription confirmation
    subscription_messages = [msg for msg in websocket.sent_messages if msg.get("type") == "subscription"]
    assert len(subscription_messages) == 1
    assert subscription_messages[0]["status"] == "subscribed"
    assert subscription_messages[0]["topic"] == topic
    
    # Test unsubscribe
    await websocket_manager.unsubscribe(client_id, topic)
    assert topic not in websocket_manager.subscriptions[client_id]
    
    # Check unsubscription confirmation
    unsubscription_messages = [
        msg for msg in websocket.sent_messages 
        if msg.get("type") == "subscription" and msg.get("status") == "unsubscribed"
    ]
    assert len(unsubscription_messages) == 1
    assert unsubscription_messages[0]["topic"] == topic


@pytest.mark.asyncio
async def test_notify_topic(websocket_manager):
    """Test notifying subscribers of a topic."""
    websocket1 = MockWebSocket()
    websocket2 = MockWebSocket()
    client_id1 = "test_client1"
    client_id2 = "test_client2"
    topic = "test_topic"
    data = {"message": "test notification"}
    
    await websocket_manager.connect(websocket1, client_id1)
    await websocket_manager.connect(websocket2, client_id2)
    
    # Subscribe client1 to the topic
    await websocket_manager.subscribe(client_id1, topic)
    
    # Clear sent messages
    websocket1.sent_messages = []
    websocket2.sent_messages = []
    
    # Notify the topic
    await websocket_manager.notify_topic(topic, data)
    
    # Check that client1 received the notification
    notifications = [msg for msg in websocket1.sent_messages if msg.get("type") == "notification"]
    assert len(notifications) == 1
    assert notifications[0]["topic"] == topic
    assert notifications[0]["data"] == data
    
    # Check that client2 did not receive the notification
    assert not any(msg.get("type") == "notification" for msg in websocket2.sent_messages)


@pytest.mark.asyncio
async def test_process_client_message_query(websocket_manager):
    """Test processing a query message from a client."""
    websocket = MockWebSocket()
    client_id = "test_client"
    data = {
        "request_id": "test_request",
        "request_type": "query",
        "payload": {"query": "test query"}
    }
    
    await websocket_manager.connect(websocket, client_id)
    await websocket_manager._process_client_message(client_id, data)
    
    # Check that acknowledgment was sent
    ack_messages = [msg for msg in websocket.sent_messages if msg.get("type") == "ack"]
    assert len(ack_messages) == 1
    
    # Check that response was sent
    response_messages = [msg for msg in websocket.sent_messages if msg.get("type") == "response"]
    assert len(response_messages) == 1


@pytest.mark.asyncio
async def test_process_client_message_subscribe(websocket_manager):
    """Test processing a subscription message from a client."""
    websocket = MockWebSocket()
    client_id = "test_client"
    topic = "test_topic"
    data = {
        "request_id": "test_request",
        "request_type": "subscribe",
        "payload": {"topic": topic}
    }
    
    await websocket_manager.connect(websocket, client_id)
    await websocket_manager._process_client_message(client_id, data)
    
    # Check that client was subscribed
    assert client_id in websocket_manager.subscriptions
    assert topic in websocket_manager.subscriptions[client_id]
    
    # Check that subscription confirmation was sent
    subscription_messages = [msg for msg in websocket.sent_messages if msg.get("type") == "subscription"]
    assert len(subscription_messages) == 1
    assert subscription_messages[0]["status"] == "subscribed"
    assert subscription_messages[0]["topic"] == topic


@pytest.mark.asyncio
async def test_handle_client(websocket_manager):
    """Test handling a client connection."""
    websocket = MockWebSocket()
    client_id = "test_client"
    
    # Mock the _process_client_message method
    websocket_manager._process_client_message = AsyncMock()
    
    # Create a task for handle_client
    task = asyncio.create_task(websocket_manager.handle_client(websocket, client_id))
    
    # Wait a bit for the connection to be established
    await asyncio.sleep(0.1)
    
    # Check that the client is connected
    assert client_id in websocket_manager.active_connections
    
    # Simulate a disconnection
    websocket.closed = True
    
    # Wait for the task to complete
    await asyncio.sleep(0.1)
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    # Check that the client was disconnected
    assert client_id not in websocket_manager.active_connections
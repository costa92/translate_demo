"""
Tests for the agent communication module.
"""

import asyncio
import pytest
from typing import Dict, Any, List

from src.knowledge_base.agents.communication import (
    EventBus, MessageBroker, StreamingChannel, 
    AgentCommunication, EventType, get_agent_communication
)
from src.knowledge_base.agents.message import AgentMessage


@pytest.fixture
def event_bus():
    """Create an event bus for testing."""
    return EventBus()


@pytest.fixture
def message_broker():
    """Create a message broker for testing."""
    return MessageBroker()


@pytest.fixture
def streaming_channel():
    """Create a streaming channel for testing."""
    return StreamingChannel("test_channel")


@pytest.fixture
def agent_communication():
    """Create an agent communication instance for testing."""
    return AgentCommunication()


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe(event_bus):
    """Test publishing and subscribing to events."""
    received_events = []
    
    def event_handler(event):
        received_events.append(event)
    
    # Subscribe to an event
    event_bus.subscribe(EventType.DOCUMENT_ADDED, event_handler)
    
    # Publish an event
    event_data = {"document_id": "123", "title": "Test Document"}
    await event_bus.publish(EventType.DOCUMENT_ADDED, event_data)
    
    # Check that the event was received
    assert len(received_events) == 1
    assert received_events[0]["type"] == EventType.DOCUMENT_ADDED.value
    assert received_events[0]["data"] == event_data
    
    # Unsubscribe and publish again
    event_bus.unsubscribe(EventType.DOCUMENT_ADDED, event_handler)
    await event_bus.publish(EventType.DOCUMENT_ADDED, {"document_id": "456"})
    
    # Check that no new event was received
    assert len(received_events) == 1


@pytest.mark.asyncio
async def test_event_bus_history(event_bus):
    """Test event history functionality."""
    # Publish some events
    await event_bus.publish(EventType.DOCUMENT_ADDED, {"document_id": "123"})
    await event_bus.publish(EventType.DOCUMENT_UPDATED, {"document_id": "123"})
    await event_bus.publish(EventType.DOCUMENT_ADDED, {"document_id": "456"})
    
    # Get all history
    history = event_bus.get_history()
    assert len(history) == 3
    
    # Get filtered history
    added_history = event_bus.get_history(EventType.DOCUMENT_ADDED)
    assert len(added_history) == 2
    assert all(event["type"] == EventType.DOCUMENT_ADDED.value for event in added_history)


@pytest.mark.asyncio
async def test_message_broker_topic(message_broker):
    """Test publishing and subscribing to topics."""
    # Subscribe to a topic
    queue = await message_broker.subscribe_to_topic("test_topic")
    
    # Create a message
    message = AgentMessage(
        source="test_agent",
        destination="*",
        message_type="test_message",
        payload={"key": "value"}
    )
    
    # Publish to the topic
    await message_broker.publish_to_topic("test_topic", message)
    
    # Check that the message was received
    received_message = await asyncio.wait_for(queue.get(), timeout=1.0)
    queue.task_done()
    
    assert received_message.source == "test_agent"
    assert received_message.message_type == "test_message"
    assert received_message.payload == {"key": "value"}
    
    # Unsubscribe and publish again
    message_broker.unsubscribe_from_topic("test_topic", queue)
    
    # Create a new message
    message2 = AgentMessage(
        source="test_agent",
        destination="*",
        message_type="test_message2",
        payload={"key2": "value2"}
    )
    
    # This should not raise an exception even though there are no subscribers
    await message_broker.publish_to_topic("test_topic", message2)


@pytest.mark.asyncio
async def test_message_broker_queue(message_broker):
    """Test sending and receiving from named queues."""
    # Create a message
    message = AgentMessage(
        source="test_agent",
        destination="test_queue",
        message_type="test_message",
        payload={"key": "value"}
    )
    
    # Send to a queue
    await message_broker.send_to_queue("test_queue", message)
    
    # Receive from the queue
    received_message = await message_broker.receive_from_queue("test_queue")
    
    assert received_message.source == "test_agent"
    assert received_message.message_type == "test_message"
    assert received_message.payload == {"key": "value"}


@pytest.mark.asyncio
async def test_streaming_channel(streaming_channel):
    """Test streaming data through a channel."""
    # Send some data
    await streaming_channel.send("item1")
    await streaming_channel.send("item2")
    await streaming_channel.send("item3")
    
    # Receive the data
    received_items = []
    async for item in streaming_channel.receive():
        received_items.append(item)
        if len(received_items) == 3:
            break
    
    assert received_items == ["item1", "item2", "item3"]
    
    # Close the channel
    streaming_channel.close()


@pytest.mark.asyncio
async def test_agent_communication_integration(agent_communication):
    """Test integration of all communication components."""
    # Set up event handler
    events_received = []
    
    def event_handler(event):
        events_received.append(event)
    
    # Subscribe to events
    agent_communication.event_bus.subscribe(EventType.DOCUMENT_ADDED, event_handler)
    agent_communication.event_bus.subscribe(EventType.SYSTEM_ERROR, event_handler)
    
    # Subscribe to a topic
    topic_queue = await agent_communication.message_broker.subscribe_to_topic("test_topic")
    
    # Create a streaming channel
    channel = agent_communication.get_or_create_channel("test_channel")
    
    # Send data through all channels
    await agent_communication.event_bus.publish(
        EventType.DOCUMENT_ADDED, 
        {"document_id": "123"}
    )
    
    message = AgentMessage(
        source="test_agent",
        destination="*",
        message_type="test_message",
        payload={"key": "value"}
    )
    
    await agent_communication.message_broker.publish_to_topic("test_topic", message)
    await channel.send("streaming_data")
    
    # Check event was received
    assert len(events_received) == 1
    assert events_received[0]["type"] == EventType.DOCUMENT_ADDED.value
    
    # Check topic message was received
    topic_message = await asyncio.wait_for(topic_queue.get(), timeout=1.0)
    topic_queue.task_done()
    assert topic_message.source == "test_agent"
    
    # Check streaming data
    received_stream_data = []
    async for item in channel.receive():
        received_stream_data.append(item)
        break
    
    assert received_stream_data == ["streaming_data"]
    
    # Test broadcast
    broadcast_queue = await agent_communication.message_broker.subscribe_to_topic("broadcast")
    
    await agent_communication.broadcast_message(message)
    
    broadcast_message = await asyncio.wait_for(broadcast_queue.get(), timeout=1.0)
    broadcast_queue.task_done()
    
    assert broadcast_message.destination == "*"
    
    # Test notify all
    await agent_communication.notify_all(
        EventType.SYSTEM_ERROR,
        {"error": "Test error"}
    )
    
    # Should have received both an event and a broadcast message
    assert len(events_received) == 2
    
    system_message = await asyncio.wait_for(broadcast_queue.get(), timeout=1.0)
    broadcast_queue.task_done()
    
    assert system_message.message_type == "event_system_error"
    
    # Clean up
    agent_communication.event_bus.unsubscribe(EventType.DOCUMENT_ADDED, event_handler)
    agent_communication.event_bus.unsubscribe(EventType.SYSTEM_ERROR, event_handler)
    agent_communication.message_broker.unsubscribe_from_topic("test_topic", topic_queue)
    agent_communication.message_broker.unsubscribe_from_topic("broadcast", broadcast_queue)
    agent_communication.close_channel("test_channel")


def test_get_agent_communication():
    """Test the global agent communication instance."""
    comm1 = get_agent_communication()
    comm2 = get_agent_communication()
    
    # Should be the same instance
    assert comm1 is comm2
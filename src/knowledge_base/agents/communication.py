"""
Agent communication module for the knowledge base system.

This module provides utilities for message passing, asynchronous communication,
and event-based notifications between agents.
"""

import asyncio
import logging
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union, AsyncIterator

from knowledge_base.core.exceptions import AgentError
from .message import AgentMessage

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for the event bus."""
    DOCUMENT_ADDED = "document_added"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"
    QUERY_EXECUTED = "query_executed"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    SYSTEM_ERROR = "system_error"
    MAINTENANCE_COMPLETED = "maintenance_completed"
    CUSTOM_EVENT = "custom_event"


class EventBus:
    """Event bus for publishing and subscribing to events.

    The event bus allows agents to communicate through an event-based
    publish-subscribe pattern, enabling loose coupling between components.
    """

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._max_history = 100

    def subscribe(self, event_type: Union[str, EventType], callback: Callable) -> None:
        """Subscribe to an event type.

        Args:
            event_type: The event type to subscribe to.
            callback: The callback function to call when the event occurs.
        """
        if isinstance(event_type, EventType):
            event_type = event_type.value

        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()

        self._subscribers[event_type].add(callback)
        logger.debug(f"Subscribed to event type: {event_type}")

    def unsubscribe(self, event_type: Union[str, EventType], callback: Callable) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: The event type to unsubscribe from.
            callback: The callback function to remove.
        """
        if isinstance(event_type, EventType):
            event_type = event_type.value

        if event_type in self._subscribers:
            self._subscribers[event_type].discard(callback)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
            logger.debug(f"Unsubscribed from event type: {event_type}")

    async def publish(self, event_type: Union[str, EventType], data: Dict[str, Any]) -> None:
        """Publish an event.

        Args:
            event_type: The type of event to publish.
            data: The event data.
        """
        if isinstance(event_type, EventType):
            event_type = event_type.value

        event = {
            "type": event_type,
            "data": data
        }

        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Notify subscribers
        if event_type in self._subscribers:
            tasks = []
            for callback in self._subscribers[event_type]:
                try:
                    result = callback(event)
                    if asyncio.iscoroutine(result):
                        tasks.append(asyncio.create_task(result))
                except Exception as e:
                    logger.error(f"Error in event subscriber for {event_type}: {e}")

            # Wait for all async callbacks to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"Published event: {event_type}")

    def get_history(self, event_type: Optional[Union[str, EventType]] = None) -> List[Dict[str, Any]]:
        """Get event history.

        Args:
            event_type: Optional event type to filter by.

        Returns:
            A list of historical events.
        """
        if event_type is None:
            return self._event_history.copy()

        if isinstance(event_type, EventType):
            event_type = event_type.value

        return [event for event in self._event_history if event["type"] == event_type]


class MessageBroker:
    """Message broker for asynchronous communication between agents.

    The message broker provides a reliable way for agents to exchange
    messages asynchronously, with support for topics and queues.
    """

    def __init__(self):
        """Initialize the message broker."""
        self._topics: Dict[str, Set[asyncio.Queue]] = {}
        self._queues: Dict[str, asyncio.Queue] = {}
        self._running = True

    async def publish_to_topic(self, topic: str, message: AgentMessage) -> None:
        """Publish a message to a topic.

        Messages published to a topic are delivered to all subscribers.

        Args:
            topic: The topic to publish to.
            message: The message to publish.
        """
        if not self._running:
            raise AgentError("Message broker is not running")

        if topic not in self._topics:
            return

        # Deliver to all subscribers
        for queue in self._topics[topic]:
            await queue.put(message)

        logger.debug(f"Published message to topic: {topic}")

    async def subscribe_to_topic(self, topic: str) -> asyncio.Queue:
        """Subscribe to a topic.

        Args:
            topic: The topic to subscribe to.

        Returns:
            A queue that will receive messages published to the topic.
        """
        if not self._running:
            raise AgentError("Message broker is not running")

        if topic not in self._topics:
            self._topics[topic] = set()

        # Create a queue for this subscription
        queue = asyncio.Queue()
        self._topics[topic].add(queue)

        logger.debug(f"Subscribed to topic: {topic}")
        return queue

    def unsubscribe_from_topic(self, topic: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from a topic.

        Args:
            topic: The topic to unsubscribe from.
            queue: The queue to remove.
        """
        if topic in self._topics:
            self._topics[topic].discard(queue)
            if not self._topics[topic]:
                del self._topics[topic]
            logger.debug(f"Unsubscribed from topic: {topic}")

    async def send_to_queue(self, queue_name: str, message: AgentMessage) -> None:
        """Send a message to a named queue.

        Messages sent to a queue are delivered to a single consumer.

        Args:
            queue_name: The name of the queue.
            message: The message to send.
        """
        if not self._running:
            raise AgentError("Message broker is not running")

        if queue_name not in self._queues:
            self._queues[queue_name] = asyncio.Queue()

        await self._queues[queue_name].put(message)
        logger.debug(f"Sent message to queue: {queue_name}")

    async def receive_from_queue(self, queue_name: str) -> AgentMessage:
        """Receive a message from a named queue.

        Args:
            queue_name: The name of the queue.

        Returns:
            The next message from the queue.
        """
        if not self._running:
            raise AgentError("Message broker is not running")

        if queue_name not in self._queues:
            self._queues[queue_name] = asyncio.Queue()

        message = await self._queues[queue_name].get()
        self._queues[queue_name].task_done()
        return message

    def stop(self) -> None:
        """Stop the message broker."""
        self._running = False
        logger.info("Message broker stopped")


class StreamingChannel:
    """Channel for streaming data between agents.

    This class provides a way for agents to stream data to each other,
    which is useful for large data transfers or real-time updates.
    """

    def __init__(self, channel_id: str, buffer_size: int = 100):
        """Initialize the streaming channel.

        Args:
            channel_id: Unique identifier for this channel.
            buffer_size: Maximum number of items to buffer.
        """
        self.channel_id = channel_id
        self.buffer_size = buffer_size
        self._queue = asyncio.Queue(maxsize=buffer_size)
        self._closed = False
        self._consumers: Set[asyncio.Queue] = set()

    async def send(self, data: Any) -> None:
        """Send data to the channel.

        Args:
            data: The data to send.

        Raises:
            AgentError: If the channel is closed.
        """
        if self._closed:
            raise AgentError(f"Channel {self.channel_id} is closed")

        # Send to all consumers
        if self._consumers:
            for consumer_queue in self._consumers:
                await consumer_queue.put(data)
        else:
            # Buffer if no consumers
            try:
                await asyncio.wait_for(self._queue.put(data), timeout=1.0)
            except asyncio.TimeoutError:
                # If buffer is full, remove oldest item
                if self._queue.full():
                    try:
                        self._queue.get_nowait()
                        self._queue.task_done()
                    except asyncio.QueueEmpty:
                        pass
                await self._queue.put(data)

    async def receive(self) -> AsyncIterator[Any]:
        """Receive data from the channel as an async iterator.

        Yields:
            Data items from the channel.
        """
        # Create a queue for this consumer
        consumer_queue = asyncio.Queue()
        self._consumers.add(consumer_queue)

        try:
            # First yield any buffered items
            while not self._queue.empty():
                try:
                    item = self._queue.get_nowait()
                    self._queue.task_done()
                    yield item
                except asyncio.QueueEmpty:
                    break

            # Then yield new items as they arrive
            while not self._closed:
                try:
                    item = await consumer_queue.get()
                    consumer_queue.task_done()
                    yield item
                except asyncio.CancelledError:
                    break
        finally:
            self._consumers.discard(consumer_queue)

    def close(self) -> None:
        """Close the channel."""
        self._closed = True


class AgentCommunication:
    """Agent communication utilities.

    This class provides a unified interface for agent communication,
    combining the event bus, message broker, and streaming channels.
    """

    def __init__(self):
        """Initialize the agent communication utilities."""
        self.event_bus = EventBus()
        self.message_broker = MessageBroker()
        self._channels: Dict[str, StreamingChannel] = {}

    def get_or_create_channel(self, channel_id: str, buffer_size: int = 100) -> StreamingChannel:
        """Get or create a streaming channel.

        Args:
            channel_id: The channel identifier.
            buffer_size: Maximum number of items to buffer.

        Returns:
            The streaming channel.
        """
        if channel_id not in self._channels:
            self._channels[channel_id] = StreamingChannel(channel_id, buffer_size)
        return self._channels[channel_id]

    def close_channel(self, channel_id: str) -> None:
        """Close a streaming channel.

        Args:
            channel_id: The channel identifier.
        """
        if channel_id in self._channels:
            self._channels[channel_id].close()
            del self._channels[channel_id]

    async def broadcast_message(self, message: AgentMessage) -> None:
        """Broadcast a message to all agents.

        This is a convenience method that sets the destination to "*"
        and publishes to a special broadcast topic.

        Args:
            message: The message to broadcast.
        """
        broadcast_message = AgentMessage(
            source=message.source,
            destination="*",
            message_type=message.message_type,
            payload=message.payload,
            id=message.id,
            timestamp=message.timestamp,
            parent_id=message.parent_id
        )

        await self.message_broker.publish_to_topic("broadcast", broadcast_message)

    async def notify_all(self, event_type: Union[str, EventType], data: Dict[str, Any]) -> None:
        """Notify all subscribers of an event.

        This is a convenience method that publishes an event and also
        broadcasts a message with the same content.

        Args:
            event_type: The type of event.
            data: The event data.
        """
        # Publish event
        await self.event_bus.publish(event_type, data)

        # Also broadcast as a message
        if isinstance(event_type, EventType):
            message_type = event_type.value
        else:
            message_type = event_type

        message = AgentMessage(
            source="system",
            destination="*",
            message_type=f"event_{message_type}",
            payload=data
        )

        await self.broadcast_message(message)


# Global instance
_agent_communication: Optional[AgentCommunication] = None


def get_agent_communication() -> AgentCommunication:
    """Get the global agent communication instance.

    Returns:
        The global agent communication instance.
    """
    global _agent_communication
    if _agent_communication is None:
        _agent_communication = AgentCommunication()
    return _agent_communication
"""
Base agent module for the knowledge base system.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import AgentError

from .message import AgentMessage
from .communication import get_agent_communication, EventType

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base interface for all agents.
    
    This abstract class defines the common interface and functionality
    for all agents in the knowledge base system.
    """
    
    def __init__(self, config: Config, agent_id: str):
        """Initialize the agent.
        
        Args:
            config: The system configuration.
            agent_id: Unique identifier for this agent.
        """
        self.config = config
        self.agent_id = agent_id
        self.message_handlers: Dict[str, Callable[[AgentMessage], Any]] = {}
        self.subscriptions: Set[str] = set()
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._topic_queues: Dict[str, asyncio.Queue] = {}
        self._event_handlers: Dict[str, Callable] = {}
    
    def register_handler(self, message_type: str, handler: Callable[[AgentMessage], Any]) -> None:
        """Register a handler for a specific message type.
        
        Args:
            message_type: The type of message to handle.
            handler: The handler function.
        """
        self.message_handlers[message_type] = handler
        
    def subscribe(self, message_type: str) -> None:
        """Subscribe to a specific message type.
        
        Args:
            message_type: The type of message to subscribe to.
        """
        self.subscriptions.add(message_type)
    
    def unsubscribe(self, message_type: str) -> None:
        """Unsubscribe from a specific message type.
        
        Args:
            message_type: The type of message to unsubscribe from.
        """
        self.subscriptions.discard(message_type)
        
    async def subscribe_to_topic(self, topic: str) -> None:
        """Subscribe to a message broker topic.
        
        Args:
            topic: The topic to subscribe to.
        """
        comm = get_agent_communication()
        queue = await comm.message_broker.subscribe_to_topic(topic)
        self._topic_queues[topic] = queue
        
        # Start a task to process messages from this topic
        asyncio.create_task(self._process_topic_messages(topic, queue))
        
    def unsubscribe_from_topic(self, topic: str) -> None:
        """Unsubscribe from a message broker topic.
        
        Args:
            topic: The topic to unsubscribe from.
        """
        if topic in self._topic_queues:
            comm = get_agent_communication()
            comm.message_broker.unsubscribe_from_topic(topic, self._topic_queues[topic])
            del self._topic_queues[topic]
            
    def register_event_handler(self, event_type: Union[str, EventType], handler: Callable) -> None:
        """Register a handler for a specific event type.
        
        Args:
            event_type: The type of event to handle.
            handler: The handler function.
        """
        if isinstance(event_type, EventType):
            event_type = event_type.value
            
        self._event_handlers[event_type] = handler
        
        # Subscribe to the event
        comm = get_agent_communication()
        comm.event_bus.subscribe(event_type, self._handle_event)
        
    def unregister_event_handler(self, event_type: Union[str, EventType]) -> None:
        """Unregister a handler for a specific event type.
        
        Args:
            event_type: The type of event to unregister.
        """
        if isinstance(event_type, EventType):
            event_type = event_type.value
            
        if event_type in self._event_handlers:
            # Unsubscribe from the event
            comm = get_agent_communication()
            comm.event_bus.unsubscribe(event_type, self._handle_event)
            del self._event_handlers[event_type]
    
    async def start(self) -> None:
        """Start the agent's message processing loop."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_messages())
        
        # Publish agent status event
        comm = get_agent_communication()
        await comm.event_bus.publish(
            EventType.AGENT_STATUS_CHANGED,
            {
                "agent_id": self.agent_id,
                "status": "started"
            }
        )
        
        logger.info(f"Agent {self.agent_id} started")
    
    async def stop(self) -> None:
        """Stop the agent's message processing loop."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        # Unsubscribe from all topics
        for topic in list(self._topic_queues.keys()):
            self.unsubscribe_from_topic(topic)
        
        # Publish agent status event
        comm = get_agent_communication()
        await comm.event_bus.publish(
            EventType.AGENT_STATUS_CHANGED,
            {
                "agent_id": self.agent_id,
                "status": "stopped"
            }
        )
        
        logger.info(f"Agent {self.agent_id} stopped")
    
    async def send_message(self, message: AgentMessage) -> None:
        """Send a message to the agent's queue.
        
        Args:
            message: The message to send.
        """
        await self._message_queue.put(message)
    
    async def _process_messages(self) -> None:
        """Process messages from the queue."""
        while self._running:
            try:
                message = await self._message_queue.get()
                await self._handle_message(message)
                self._message_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message in agent {self.agent_id}: {e}")
    
    async def _handle_message(self, message: AgentMessage) -> None:
        """Handle a message.
        
        Args:
            message: The message to handle.
        """
        if message.destination != self.agent_id and message.destination != "*":
            # Message not for this agent
            return
        
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                await self._call_handler(handler, message)
            except Exception as e:
                logger.error(f"Error in handler for {message.message_type} in agent {self.agent_id}: {e}")
                error_response = message.create_error_response(str(e))
                await self.dispatch_message(error_response)
        else:
            logger.warning(f"No handler for message type {message.message_type} in agent {self.agent_id}")
    
    async def _call_handler(self, handler: Callable[[AgentMessage], Any], message: AgentMessage) -> None:
        """Call a message handler.
        
        Args:
            handler: The handler function.
            message: The message to handle.
        """
        result = handler(message)
        if asyncio.iscoroutine(result):
            await result
    
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message and return a response.
        
        This is the main method that should be implemented by subclasses
        to define the agent's behavior.
        
        Args:
            message: The message to process.
            
        Returns:
            The response message.
        """
        pass
    
    async def dispatch_message(self, message: AgentMessage) -> None:
        """Dispatch a message to the appropriate agent.
        
        This method should be overridden by the agent system to provide
        actual message routing between agents.
        
        Args:
            message: The message to dispatch.
        """
        raise NotImplementedError("Message dispatching not implemented")
        
    async def publish_event(self, event_type: Union[str, EventType], data: Dict[str, Any]) -> None:
        """Publish an event to the event bus.
        
        Args:
            event_type: The type of event to publish.
            data: The event data.
        """
        comm = get_agent_communication()
        await comm.event_bus.publish(event_type, data)
        
    async def send_to_topic(self, topic: str, message: AgentMessage) -> None:
        """Send a message to a topic.
        
        Args:
            topic: The topic to send to.
            message: The message to send.
        """
        comm = get_agent_communication()
        await comm.message_broker.publish_to_topic(topic, message)
        
    async def send_to_queue(self, queue_name: str, message: AgentMessage) -> None:
        """Send a message to a named queue.
        
        Args:
            queue_name: The name of the queue.
            message: The message to send.
        """
        comm = get_agent_communication()
        await comm.message_broker.send_to_queue(queue_name, message)
        
    async def receive_from_queue(self, queue_name: str) -> AgentMessage:
        """Receive a message from a named queue.
        
        Args:
            queue_name: The name of the queue.
            
        Returns:
            The next message from the queue.
        """
        comm = get_agent_communication()
        return await comm.message_broker.receive_from_queue(queue_name)
        
    async def broadcast_message(self, message: AgentMessage) -> None:
        """Broadcast a message to all agents.
        
        Args:
            message: The message to broadcast.
        """
        comm = get_agent_communication()
        await comm.broadcast_message(message)
        
    async def _process_topic_messages(self, topic: str, queue: asyncio.Queue) -> None:
        """Process messages from a topic queue.
        
        Args:
            topic: The topic name.
            queue: The queue to process messages from.
        """
        while self._running:
            try:
                message = await queue.get()
                await self._handle_message(message)
                queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing topic message in agent {self.agent_id}: {e}")
                
    def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle an event from the event bus.
        
        Args:
            event: The event data.
        """
        event_type = event["type"]
        if event_type in self._event_handlers:
            try:
                handler = self._event_handlers[event_type]
                result = handler(event["data"])
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type} in agent {self.agent_id}: {e}")


class TestResponseAgent(BaseAgent):
    """Test agent for receiving responses.
    
    This agent is used internally by the agent system for request-response operations.
    """
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message.
        
        Args:
            message: The message to process.
            
        Returns:
            The response message.
        """
        return message.create_response({"result": "success"})


class AgentSystem:
    """System for managing and coordinating multiple agents.
    
    This class provides the infrastructure for agent registration,
    message routing, and lifecycle management.
    """
    
    def __init__(self, config: Config):
        """Initialize the agent system.
        
        Args:
            config: The system configuration.
        """
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        self.subscriptions: Dict[str, Set[str]] = {}
        
        # Initialize communication utilities
        self.communication = get_agent_communication()
        
        # Subscribe to agent status events
        self.communication.event_bus.subscribe(
            EventType.AGENT_STATUS_CHANGED,
            self._handle_agent_status_event
        )
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the system.
        
        Args:
            agent: The agent to register.
        """
        if agent.agent_id in self.agents:
            raise AgentError(f"Agent with ID {agent.agent_id} already registered")
        
        self.agents[agent.agent_id] = agent
        
        # Register subscriptions
        for message_type in agent.subscriptions:
            if message_type not in self.subscriptions:
                self.subscriptions[message_type] = set()
            self.subscriptions[message_type].add(agent.agent_id)
        
        # Override the agent's dispatch_message method
        agent.dispatch_message = self.dispatch_message
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the system.
        
        Args:
            agent_id: The ID of the agent to unregister.
        """
        if agent_id not in self.agents:
            raise AgentError(f"Agent with ID {agent_id} not registered")
        
        agent = self.agents[agent_id]
        
        # Remove subscriptions
        for message_type in agent.subscriptions:
            if message_type in self.subscriptions:
                self.subscriptions[message_type].discard(agent_id)
                if not self.subscriptions[message_type]:
                    del self.subscriptions[message_type]
        
        del self.agents[agent_id]
    
    async def start_all(self) -> None:
        """Start all registered agents."""
        for agent in self.agents.values():
            await agent.start()
            
        # Publish system event
        await self.communication.event_bus.publish(
            EventType.AGENT_STATUS_CHANGED,
            {
                "agent_id": "system",
                "status": "started",
                "active_agents": len(self.agents)
            }
        )
    
    async def stop_all(self) -> None:
        """Stop all registered agents."""
        for agent in self.agents.values():
            await agent.stop()
            
        # Publish system event
        await self.communication.event_bus.publish(
            EventType.AGENT_STATUS_CHANGED,
            {
                "agent_id": "system",
                "status": "stopped"
            }
        )
    
    async def _handle_agent_status_event(self, event: Dict[str, Any]) -> None:
        """Handle agent status change events.
        
        Args:
            event: The event data.
        """
        data = event["data"]
        agent_id = data.get("agent_id")
        status = data.get("status")
        
        if agent_id and status:
            logger.info(f"Agent {agent_id} status changed to {status}")
    
    async def dispatch_message(self, message: AgentMessage) -> None:
        """Dispatch a message to the appropriate agent(s).
        
        Args:
            message: The message to dispatch.
        """
        if message.destination == "*":
            # Use the broadcast mechanism
            await self.communication.broadcast_message(message)
            return
            
        # For direct messages, use the traditional approach
        if message.destination in self.agents:
            await self.agents[message.destination].send_message(message)
        else:
            # Try to send via a named queue
            try:
                await self.communication.message_broker.send_to_queue(
                    message.destination, message
                )
                logger.debug(f"Sent message to queue {message.destination}")
            except Exception as e:
                logger.warning(f"No agent or queue with ID {message.destination} found for message {message.id}: {e}")
    
    async def send_message(self, message: AgentMessage) -> None:
        """Send a message through the agent system.
        
        Args:
            message: The message to send.
        """
        await self.dispatch_message(message)
    
    async def request_response(self, message: AgentMessage, timeout: float = 30.0) -> AgentMessage:
        """Send a message and wait for a response.
        
        Args:
            message: The message to send.
            timeout: Maximum time to wait for a response in seconds.
            
        Returns:
            The response message.
            
        Raises:
            asyncio.TimeoutError: If no response is received within the timeout.
        """
        response_future = asyncio.Future()
        
        # Create a unique response topic for this request
        response_topic = f"response_{message.id}"
        response_queue = await self.communication.message_broker.subscribe_to_topic(response_topic)
        
        # Modify the message to include the response topic
        message.payload["_response_topic"] = response_topic
        
        try:
            # Send the message
            await self.send_message(message)
            
            # Wait for the response on the topic
            try:
                response_message = await asyncio.wait_for(response_queue.get(), timeout)
                response_queue.task_done()
                return response_message
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for response to message {message.id}")
                raise
        finally:
            # Clean up the temporary topic
            self.communication.message_broker.unsubscribe_from_topic(response_topic, response_queue)
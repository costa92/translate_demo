"""
WebSocket handler for the knowledge base API.

This module provides WebSocket support for streaming responses.
"""

import json
import logging
import asyncio
from typing import Dict, Set, Any, Optional, Callable, Awaitable, List

from fastapi import WebSocket, WebSocketDisconnect

from knowledge_base.core.config import Config
from knowledge_base.agents.orchestrator import OrchestratorAgent
from knowledge_base.agents.message import AgentMessage

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manager for WebSocket connections."""
    
    def __init__(self, config: Config, orchestrator: OrchestratorAgent):
        """Initialize the WebSocket manager.
        
        Args:
            config: The configuration instance.
            orchestrator: The orchestrator agent.
        """
        self.config = config
        self.orchestrator = orchestrator
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_tasks: Dict[str, asyncio.Task] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of topics
        
        # Start notification listener
        self.notification_task = None
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection.
            client_id: The client identifier.
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connection established for client: {client_id}")
        
        # Start notification listener if this is the first connection
        if len(self.active_connections) == 1 and not self.notification_task:
            await self.start_notification_listener()
    
    def disconnect(self, client_id: str) -> None:
        """Handle a WebSocket disconnection.
        
        Args:
            client_id: The client identifier.
        """
        self.active_connections.pop(client_id, None)
        
        # Cancel any running tasks for this client
        if client_id in self.connection_tasks:
            self.connection_tasks[client_id].cancel()
            self.connection_tasks.pop(client_id, None)
            
        # Remove subscriptions
        self.subscriptions.pop(client_id, None)
        
        logger.info(f"WebSocket connection closed for client: {client_id}")
        
        # Stop notification listener if no more connections
        if not self.active_connections and self.notification_task:
            self.notification_task.cancel()
            self.notification_task = None
    
    async def send_message(self, client_id: str, message: Dict[str, Any]) -> None:
        """Send a message to a client.
        
        Args:
            client_id: The client identifier.
            message: The message to send.
        """
        if client_id not in self.active_connections:
            logger.warning(f"Attempted to send message to disconnected client: {client_id}")
            return
        
        try:
            await self.active_connections[client_id].send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            self.disconnect(client_id)
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast.
        """
        for client_id in list(self.active_connections.keys()):
            await self.send_message(client_id, message)
            
    async def subscribe(self, client_id: str, topic: str) -> None:
        """Subscribe a client to a topic.
        
        Args:
            client_id: The client identifier.
            topic: The topic to subscribe to.
        """
        if client_id not in self.subscriptions:
            self.subscriptions[client_id] = set()
        
        self.subscriptions[client_id].add(topic)
        logger.info(f"Client {client_id} subscribed to topic: {topic}")
        
        # Send confirmation
        await self.send_message(client_id, {
            "type": "subscription",
            "status": "subscribed",
            "topic": topic
        })
    
    async def unsubscribe(self, client_id: str, topic: str) -> None:
        """Unsubscribe a client from a topic.
        
        Args:
            client_id: The client identifier.
            topic: The topic to unsubscribe from.
        """
        if client_id in self.subscriptions and topic in self.subscriptions[client_id]:
            self.subscriptions[client_id].remove(topic)
            logger.info(f"Client {client_id} unsubscribed from topic: {topic}")
            
            # Send confirmation
            await self.send_message(client_id, {
                "type": "subscription",
                "status": "unsubscribed",
                "topic": topic
            })
    
    async def notify_topic(self, topic: str, data: Dict[str, Any]) -> None:
        """Send a notification to all clients subscribed to a topic.
        
        Args:
            topic: The topic to notify.
            data: The notification data.
        """
        notification = {
            "type": "notification",
            "topic": topic,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send to all subscribed clients
        for client_id, topics in self.subscriptions.items():
            if topic in topics and client_id in self.active_connections:
                await self.send_message(client_id, notification)
                
    async def start_notification_listener(self) -> None:
        """Start listening for system notifications.
        
        This method sets up listeners for various system events
        and forwards them as WebSocket notifications.
        """
        # Cancel any existing task
        if self.notification_task and not self.notification_task.done():
            self.notification_task.cancel()
            
        # Create a new task
        self.notification_task = asyncio.create_task(self._notification_listener())
        
    async def _notification_listener(self) -> None:
        """Background task that listens for system notifications."""
        try:
            # Set up notification channels
            # This is a placeholder for actual implementation
            # In a real system, this would connect to message queues, event buses, etc.
            
            while True:
                # Simulate periodic system status updates
                await asyncio.sleep(30)  # Every 30 seconds
                
                # Get system status
                try:
                    status = {
                        "active_connections": len(self.active_connections),
                        "memory_usage": "Normal",
                        "cpu_usage": "Normal",
                        "timestamp": asyncio.get_event_loop().time()
                    }
                    
                    # Notify subscribers
                    await self.notify_topic("system_status", status)
                except Exception as e:
                    logger.error(f"Error getting system status: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Notification listener cancelled")
        except Exception as e:
            logger.error(f"Error in notification listener: {e}")
            
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast.
        """
        for client_id in list(self.active_connections.keys()):
            await self.send_message(client_id, message)
    
    async def handle_client(self, websocket: WebSocket, client_id: str) -> None:
        """Handle a WebSocket client connection.
        
        Args:
            websocket: The WebSocket connection.
            client_id: The client identifier.
        """
        await self.connect(websocket, client_id)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Process the message
                task = asyncio.create_task(self._process_client_message(client_id, data))
                self.connection_tasks[client_id] = task
        except WebSocketDisconnect:
            self.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error handling WebSocket client {client_id}: {e}")
            self.disconnect(client_id)
    
    async def _process_client_message(self, client_id: str, data: Dict[str, Any]) -> None:
        """Process a message from a client.
        
        Args:
            client_id: The client identifier.
            data: The message data.
        """
        try:
            # Extract message details
            request_id = data.get("request_id", "unknown")
            request_type = data.get("request_type", "query")
            payload = data.get("payload", {})
            
            # Send acknowledgment
            await self.send_message(client_id, {
                "type": "ack",
                "request_id": request_id,
                "message": "Request received"
            })
            
            # Process the request
            if request_type == "subscribe":
                # Handle subscription request
                topic = payload.get("topic")
                if topic:
                    await self.subscribe(client_id, topic)
                else:
                    await self.send_message(client_id, {
                        "type": "error",
                        "request_id": request_id,
                        "error": "Missing topic in subscription request"
                    })
            
            elif request_type == "unsubscribe":
                # Handle unsubscription request
                topic = payload.get("topic")
                if topic:
                    await self.unsubscribe(client_id, topic)
                else:
                    await self.send_message(client_id, {
                        "type": "error",
                        "request_id": request_id,
                        "error": "Missing topic in unsubscription request"
                    })
            
            elif request_type == "query" and payload.get("stream", False):
                # Handle streaming query
                await self._handle_streaming_query(client_id, request_id, payload)
            
            else:
                # Handle regular request
                response = await self.orchestrator.receive_request(
                    source=f"ws:{client_id}",
                    request_type=request_type,
                    payload=payload
                )
                
                # Send response
                await self.send_message(client_id, {
                    "type": "response",
                    "request_id": request_id,
                    "data": response
                })
        except Exception as e:
            logger.error(f"Error processing message from client {client_id}: {e}")
            
            # Send error response
            await self.send_message(client_id, {
                "type": "error",
                "request_id": data.get("request_id", "unknown"),
                "error": str(e)
            })
    
    async def _handle_streaming_query(self, client_id: str, request_id: str, payload: Dict[str, Any]) -> None:
        """Handle a streaming query request.
        
        Args:
            client_id: The client identifier.
            request_id: The request identifier.
            payload: The request payload.
        """
        try:
            # Send initial response with retrieved chunks
            chunks_response = await self.orchestrator.receive_request(
                source=f"ws:{client_id}",
                request_type="retrieve",
                payload={
                    "query": payload.get("query"),
                    "filter": payload.get("filter"),
                    "top_k": payload.get("top_k", 5)
                }
            )
            
            await self.send_message(client_id, {
                "type": "chunks",
                "request_id": request_id,
                "data": chunks_response
            })
            
            # Stream the generated response
            async for chunk in self.orchestrator.receive_request_stream(
                source=f"ws:{client_id}",
                request_type="generate",
                payload={
                    "query": payload.get("query"),
                    "chunks": chunks_response.get("chunks", []),
                    "stream": True
                }
            ):
                await self.send_message(client_id, {
                    "type": "chunk",
                    "request_id": request_id,
                    "data": {"text": chunk}
                })
            
            # Send completion message
            await self.send_message(client_id, {
                "type": "complete",
                "request_id": request_id
            })
        except Exception as e:
            logger.error(f"Error handling streaming query for client {client_id}: {e}")
            
            # Send error response
            await self.send_message(client_id, {
                "type": "error",
                "request_id": request_id,
                "error": str(e)
            })
#!/usr/bin/env python3
"""
Example WebSocket client for the knowledge base API.

This script demonstrates how to connect to the WebSocket API
and perform various operations like querying, streaming, and
subscribing to notifications.
"""

import asyncio
import json
import sys
import uuid
import websockets
from typing import Dict, Any, Optional


class KnowledgeBaseWebSocketClient:
    """WebSocket client for the knowledge base API."""
    
    def __init__(self, url: str, client_id: Optional[str] = None):
        """Initialize the WebSocket client.
        
        Args:
            url: The WebSocket URL.
            client_id: Optional client identifier. If not provided, a random UUID will be used.
        """
        self.url = url
        self.client_id = client_id or str(uuid.uuid4())
        self.websocket = None
        self.running = False
        self.response_futures = {}
        self.notification_callbacks = {}
    
    async def connect(self) -> None:
        """Connect to the WebSocket server."""
        full_url = f"{self.url}/ws/{self.client_id}"
        self.websocket = await websockets.connect(full_url)
        self.running = True
        
        # Start the message handler
        asyncio.create_task(self._handle_messages())
        
        print(f"Connected to {full_url} with client ID {self.client_id}")
    
    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.running = False
            print("Disconnected from WebSocket server")
    
    async def _handle_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        try:
            while self.running and self.websocket:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # Handle different message types
                if data.get("type") == "response":
                    # Handle response messages
                    request_id = data.get("request_id")
                    if request_id in self.response_futures:
                        self.response_futures[request_id].set_result(data.get("data"))
                
                elif data.get("type") == "chunk":
                    # Handle streaming chunks
                    request_id = data.get("request_id")
                    if request_id in self.response_futures:
                        chunk_data = data.get("data", {})
                        chunk_text = chunk_data.get("text", "")
                        print(chunk_text, end="", flush=True)
                
                elif data.get("type") == "complete":
                    # Handle stream completion
                    request_id = data.get("request_id")
                    if request_id in self.response_futures:
                        print("\nStream complete")
                        self.response_futures[request_id].set_result({"status": "complete"})
                
                elif data.get("type") == "notification":
                    # Handle notifications
                    topic = data.get("topic")
                    if topic in self.notification_callbacks:
                        callback = self.notification_callbacks[topic]
                        await callback(data.get("data", {}))
                
                elif data.get("type") == "error":
                    # Handle error messages
                    request_id = data.get("request_id")
                    error = data.get("error", "Unknown error")
                    print(f"Error: {error}")
                    
                    if request_id in self.response_futures:
                        self.response_futures[request_id].set_exception(
                            Exception(f"WebSocket error: {error}")
                        )
        
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
            self.running = False
        
        except Exception as e:
            print(f"Error handling WebSocket messages: {e}")
            self.running = False
    
    async def send_request(self, request_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the WebSocket server.
        
        Args:
            request_type: The type of request.
            payload: The request payload.
            
        Returns:
            The response data.
        """
        if not self.websocket:
            raise Exception("Not connected to WebSocket server")
        
        # Create a request ID
        request_id = str(uuid.uuid4())
        
        # Create a future for the response
        future = asyncio.Future()
        self.response_futures[request_id] = future
        
        # Send the request
        await self.websocket.send(json.dumps({
            "request_id": request_id,
            "request_type": request_type,
            "payload": payload
        }))
        
        # Wait for the response
        try:
            response = await asyncio.wait_for(future, timeout=30)
            return response
        except asyncio.TimeoutError:
            del self.response_futures[request_id]
            raise Exception("Request timed out")
    
    async def query(self, query_text: str, filter_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a query to the knowledge base.
        
        Args:
            query_text: The query text.
            filter_criteria: Optional filter criteria.
            
        Returns:
            The query response.
        """
        payload = {
            "query": query_text,
            "filter": filter_criteria,
            "stream": False
        }
        
        return await self.send_request("query", payload)
    
    async def stream_query(self, query_text: str, filter_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a streaming query to the knowledge base.
        
        Args:
            query_text: The query text.
            filter_criteria: Optional filter criteria.
            
        Returns:
            The completion status.
        """
        payload = {
            "query": query_text,
            "filter": filter_criteria,
            "stream": True
        }
        
        return await self.send_request("query", payload)
    
    async def subscribe(self, topic: str, callback) -> None:
        """Subscribe to a topic.
        
        Args:
            topic: The topic to subscribe to.
            callback: The callback function to call when a notification is received.
        """
        payload = {"topic": topic}
        await self.send_request("subscribe", payload)
        self.notification_callbacks[topic] = callback
    
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic.
        
        Args:
            topic: The topic to unsubscribe from.
        """
        payload = {"topic": topic}
        await self.send_request("unsubscribe", payload)
        self.notification_callbacks.pop(topic, None)


async def system_status_callback(data: Dict[str, Any]) -> None:
    """Callback for system status notifications.
    
    Args:
        data: The notification data.
    """
    print(f"\nSystem status update: {json.dumps(data, indent=2)}")


async def main() -> None:
    """Main function."""
    # Parse command line arguments
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <websocket_url> [client_id]")
        print(f"Example: {sys.argv[0]} ws://localhost:8000 my_client")
        return
    
    url = sys.argv[1]
    client_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Create the WebSocket client
    client = KnowledgeBaseWebSocketClient(url, client_id)
    
    try:
        # Connect to the WebSocket server
        await client.connect()
        
        # Subscribe to system status notifications
        await client.subscribe("system_status", system_status_callback)
        print("Subscribed to system status notifications")
        
        # Main interaction loop
        while True:
            print("\nOptions:")
            print("1. Send a query")
            print("2. Send a streaming query")
            print("3. Exit")
            
            choice = input("Enter your choice (1-3): ")
            
            if choice == "1":
                query_text = input("Enter your query: ")
                print("Sending query...")
                response = await client.query(query_text)
                print(f"Response: {json.dumps(response, indent=2)}")
            
            elif choice == "2":
                query_text = input("Enter your query: ")
                print("Sending streaming query...\nResponse:")
                await client.stream_query(query_text)
            
            elif choice == "3":
                break
            
            else:
                print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Disconnect from the WebSocket server
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
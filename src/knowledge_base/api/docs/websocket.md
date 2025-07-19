# WebSocket API Documentation

The WebSocket API provides real-time communication with the knowledge base system. This document describes how to use the WebSocket API for streaming responses, subscribing to notifications, and more.

## Connection

Connect to the WebSocket endpoint:

```
ws://localhost:8000/ws/{client_id}
```

Where `client_id` is a unique identifier for your client. This identifier helps track your connection and can be any string value.

## Message Format

All messages sent to the WebSocket server should follow this format:

```json
{
  "request_id": "unique-request-id",
  "request_type": "query",
  "payload": {
    // Request-specific payload
  }
}
```

- `request_id`: A unique identifier for the request. This will be included in the response to help you match responses to requests.
- `request_type`: The type of request you're making (e.g., "query", "subscribe", "unsubscribe").
- `payload`: A JSON object containing request-specific data.

## Available Operations

### Query

Send a query to the knowledge base:

```json
{
  "request_id": "query-1",
  "request_type": "query",
  "payload": {
    "query": "What is the capital of France?",
    "filter": {
      "source": "wikipedia"
    },
    "top_k": 5,
    "stream": false
  }
}
```

Parameters:
- `query`: The query text
- `filter` (optional): Filter criteria
- `top_k` (optional): Number of results to return
- `stream` (optional): Whether to stream the response

### Streaming Query

Send a streaming query to get real-time response chunks:

```json
{
  "request_id": "query-2",
  "request_type": "query",
  "payload": {
    "query": "What is the capital of France?",
    "stream": true
  }
}
```

### Subscribe to Notifications

Subscribe to a topic to receive notifications:

```json
{
  "request_id": "sub-1",
  "request_type": "subscribe",
  "payload": {
    "topic": "system_status"
  }
}
```

Available topics:
- `system_status`: System status updates
- `document_updates`: Notifications when documents are added, updated, or deleted
- `maintenance`: Maintenance task updates

### Unsubscribe from Notifications

Unsubscribe from a topic:

```json
{
  "request_id": "unsub-1",
  "request_type": "unsubscribe",
  "payload": {
    "topic": "system_status"
  }
}
```

## Response Types

The WebSocket server can send several types of messages:

### Acknowledgment

Sent immediately after receiving a request:

```json
{
  "type": "ack",
  "request_id": "query-1",
  "message": "Request received"
}
```

### Response

Sent in response to a non-streaming query:

```json
{
  "type": "response",
  "request_id": "query-1",
  "data": {
    "query": "What is the capital of France?",
    "answer": "The capital of France is Paris.",
    "chunks": [
      {
        "id": "chunk_123",
        "text": "Paris is the capital and most populous city of France.",
        "document_id": "doc_456",
        "metadata": {
          "source": "wikipedia"
        },
        "score": 0.95
      }
    ],
    "metadata": {
      "processing_time": 0.25
    }
  }
}
```

### Chunks Response

For streaming queries, first the retrieved chunks are sent:

```json
{
  "type": "chunks",
  "request_id": "query-2",
  "data": {
    "chunks": [
      {
        "id": "chunk_123",
        "text": "Paris is the capital and most populous city of France.",
        "document_id": "doc_456",
        "metadata": {
          "source": "wikipedia"
        },
        "score": 0.95
      }
    ]
  }
}
```

### Streaming Chunk

Then, for streaming queries, response chunks are sent as they're generated:

```json
{
  "type": "chunk",
  "request_id": "query-2",
  "data": {
    "text": "The capital of"
  }
}
```

```json
{
  "type": "chunk",
  "request_id": "query-2",
  "data": {
    "text": " France is"
  }
}
```

```json
{
  "type": "chunk",
  "request_id": "query-2",
  "data": {
    "text": " Paris."
  }
}
```

### Stream Complete

Sent when a streaming response is complete:

```json
{
  "type": "complete",
  "request_id": "query-2"
}
```

### Subscription Confirmation

Sent when a subscription request is processed:

```json
{
  "type": "subscription",
  "status": "subscribed",
  "topic": "system_status"
}
```

Or when unsubscribing:

```json
{
  "type": "subscription",
  "status": "unsubscribed",
  "topic": "system_status"
}
```

### Notification

Sent when an event occurs for a topic you're subscribed to:

```json
{
  "type": "notification",
  "topic": "system_status",
  "data": {
    "active_connections": 5,
    "memory_usage": "Normal",
    "cpu_usage": "Normal",
    "timestamp": 1625097600
  },
  "timestamp": 1625097600
}
```

### Error

Sent when an error occurs:

```json
{
  "type": "error",
  "request_id": "query-1",
  "error": "Invalid query format"
}
```

## Example Usage

### JavaScript Example

```javascript
// Connect to the WebSocket server
const clientId = 'client_' + Math.random().toString(36).substring(2, 15);
const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

// Handle connection open
ws.onopen = () => {
  console.log('Connected to WebSocket server');
  
  // Send a query
  ws.send(JSON.stringify({
    request_id: 'query-1',
    request_type: 'query',
    payload: {
      query: 'What is the capital of France?',
      stream: true
    }
  }));
  
  // Subscribe to system status notifications
  ws.send(JSON.stringify({
    request_id: 'sub-1',
    request_type: 'subscribe',
    payload: {
      topic: 'system_status'
    }
  }));
};

// Handle incoming messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received message:', data);
  
  // Handle different message types
  switch (data.type) {
    case 'chunk':
      process.stdout.write(data.data.text);
      break;
    case 'complete':
      console.log('\nStream complete');
      break;
    case 'notification':
      console.log(`Notification (${data.topic}):`, data.data);
      break;
    case 'error':
      console.error('Error:', data.error);
      break;
  }
};

// Handle connection close
ws.onclose = () => {
  console.log('Disconnected from WebSocket server');
};

// Handle errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

### Python Example

```python
import asyncio
import json
import uuid
import websockets

async def connect_and_query():
    # Generate a client ID
    client_id = str(uuid.uuid4())
    
    # Connect to the WebSocket server
    async with websockets.connect(f"ws://localhost:8000/ws/{client_id}") as websocket:
        print(f"Connected to WebSocket server with client ID {client_id}")
        
        # Send a query
        request_id = str(uuid.uuid4())
        await websocket.send(json.dumps({
            "request_id": request_id,
            "request_type": "query",
            "payload": {
                "query": "What is the capital of France?",
                "stream": True
            }
        }))
        
        # Process responses
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "chunk":
                print(data.get("data", {}).get("text", ""), end="", flush=True)
            elif data.get("type") == "complete":
                print("\nStream complete")
                break
            elif data.get("type") == "error":
                print(f"Error: {data.get('error')}")
                break

# Run the example
asyncio.run(connect_and_query())
```

## Error Handling

The WebSocket API uses the following error format:

```json
{
  "type": "error",
  "request_id": "query-1",
  "error": "Error message"
}
```

Common errors include:
- Invalid request format
- Missing required parameters
- Authentication or authorization failures
- Rate limiting
- Internal server errors

## Best Practices

1. **Generate unique request IDs**: Use UUIDs or another method to ensure request IDs are unique.
2. **Handle reconnection**: Implement reconnection logic in case the connection is lost.
3. **Limit subscriptions**: Only subscribe to topics you need to avoid unnecessary traffic.
4. **Process streaming responses incrementally**: For streaming responses, update your UI as chunks arrive rather than waiting for the complete response.
5. **Implement error handling**: Handle errors gracefully and consider implementing exponential backoff for retries.

## Rate Limiting

WebSocket connections and operations are subject to rate limiting:
- Maximum of 5 concurrent connections per user
- Maximum of 10 requests per second per connection
- Maximum of 100 subscriptions per connection

When rate limits are exceeded, an error message will be sent and the connection may be closed.
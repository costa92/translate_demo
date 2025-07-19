# WebSocket Support for Knowledge Base API

This module provides WebSocket support for the Knowledge Base API, enabling real-time communication between clients and the knowledge base system.

## Features

- **WebSocket Connections**: Establish persistent connections for real-time communication
- **Streaming Responses**: Stream query responses as they are generated
- **Real-time Notifications**: Subscribe to topics and receive notifications
- **Client Management**: Track active connections and handle disconnections

## Documentation

For comprehensive WebSocket API documentation, see:

- **API Documentation**: `/api-docs/README.md`
- **WebSocket-specific Documentation**: `/api-docs/websocket.md`
- **Interactive Documentation**: `/api-docs/interactive.html`
- **OpenAPI Specification**: `/api-docs/openapi.yaml`

These resources provide detailed information about message formats, available operations, and example code.

## Usage

### Server-side

The WebSocket support is automatically integrated into the Knowledge Base API server. The main entry point is the `/ws/{client_id}` endpoint, which accepts WebSocket connections.

### Client-side

Clients can connect to the WebSocket API using any WebSocket client library. Two example clients are provided:

1. **Python Client**: `examples/websocket_client.py`
2. **Browser Client**: `examples/websocket_client.html`

## Message Protocol

### Client to Server Messages

Messages sent from clients to the server should follow this format:

```json
{
  "request_id": "unique_request_id",
  "request_type": "query|subscribe|unsubscribe",
  "payload": {
    // Request-specific payload
  }
}
```

### Server to Client Messages

Messages sent from the server to clients follow these formats:

#### Acknowledgment

```json
{
  "type": "ack",
  "request_id": "original_request_id",
  "message": "Request received"
}
```

#### Response

```json
{
  "type": "response",
  "request_id": "original_request_id",
  "data": {
    // Response data
  }
}
```

#### Streaming Chunks

```json
{
  "type": "chunks",
  "request_id": "original_request_id",
  "data": {
    "chunks": [
      // Retrieved chunks
    ]
  }
}
```

```json
{
  "type": "chunk",
  "request_id": "original_request_id",
  "data": {
    "text": "Chunk text"
  }
}
```

```json
{
  "type": "complete",
  "request_id": "original_request_id"
}
```

#### Error

```json
{
  "type": "error",
  "request_id": "original_request_id",
  "error": "Error message"
}
```

#### Subscription

```json
{
  "type": "subscription",
  "status": "subscribed|unsubscribed",
  "topic": "topic_name"
}
```

#### Notification

```json
{
  "type": "notification",
  "topic": "topic_name",
  "data": {
    // Notification data
  },
  "timestamp": 1626912345.678
}
```

## Supported Request Types

### Query

Send a query to the knowledge base.

```json
{
  "request_id": "query_123",
  "request_type": "query",
  "payload": {
    "query": "What is the capital of France?",
    "filter": {
      // Optional filter criteria
    },
    "stream": true  // Set to true for streaming response
  }
}
```

### Subscribe

Subscribe to a topic to receive notifications.

```json
{
  "request_id": "sub_123",
  "request_type": "subscribe",
  "payload": {
    "topic": "system_status"
  }
}
```

### Unsubscribe

Unsubscribe from a topic.

```json
{
  "request_id": "unsub_123",
  "request_type": "unsubscribe",
  "payload": {
    "topic": "system_status"
  }
}
```

## Available Topics

- `system_status`: System status updates
- `document_updates`: Notifications about document additions or updates
- `agent_status`: Status updates from agents

## Error Handling

If an error occurs during request processing, the server will send an error message with the following format:

```json
{
  "type": "error",
  "request_id": "original_request_id",
  "error": "Error message"
}
```

## Connection Management

- Clients are identified by a unique `client_id` provided in the WebSocket URL
- If a client disconnects, any active tasks for that client will be cancelled
- The server will automatically clean up resources when clients disconnect
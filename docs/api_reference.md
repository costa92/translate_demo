# Unified Knowledge Base System API Reference

## Introduction

The Unified Knowledge Base System provides a comprehensive API for interacting with the knowledge base. This document provides detailed information about the available endpoints, request and response formats, authentication methods, and examples.

## Base URL

```
https://api.example.com/v1
```

For local development:

```
http://localhost:8000
```

## Authentication

The API supports two authentication methods:

### API Key Authentication

Include your API key in the `X-API-Key` header:

```
X-API-Key: your-api-key
```

### Bearer Token Authentication

Include your bearer token in the `Authorization` header:

```
Authorization: Bearer your-token
```

## Rate Limiting

API requests are subject to rate limiting based on your account tier. Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1625097600
```

## Error Handling

The API uses standard HTTP status codes and provides detailed error information in the response body:

```json
{
  "error": "Invalid document format",
  "details": {
    "field": "content",
    "message": "Content cannot be empty"
  },
  "code": 400
}
```

Common error codes:
- `400`: Bad Request - Invalid input
- `401`: Unauthorized - Authentication required
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server error

## API Endpoints

### Health Check

#### GET /health

Check if the API is up and running.

**Response**:

```json
{
  "status": "ok"
}
```

### Knowledge Management

#### POST /knowledge/documents

Add a new document to the knowledge base.

**Request Body**:

```json
{
  "content": "This is a sample document content.",
  "type": "text",
  "metadata": {
    "source": "user-upload",
    "author": "John Doe",
    "tags": ["sample", "documentation"]
  }
}
```

**Response**:

```json
{
  "document_id": "doc_123456",
  "chunk_ids": ["chunk_1", "chunk_2", "chunk_3"],
  "success": true
}
```

#### GET /knowledge/documents

List documents in the knowledge base.

**Parameters**:
- `limit` (optional): Maximum number of documents to return (default: 100)
- `offset` (optional): Number of documents to skip (default: 0)
- `filter` (optional): Filter expression

**Response**:

```json
{
  "documents": [
    {
      "id": "doc_123456",
      "content": "This is a sample document content.",
      "type": "text",
      "metadata": {
        "source": "user-upload",
        "author": "John Doe",
        "tags": ["sample", "documentation"]
      }
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

#### GET /knowledge/documents/{document_id}

Get a document from the knowledge base.

**Parameters**:
- `document_id`: Document ID

**Response**:

```json
{
  "id": "doc_123456",
  "content": "This is a sample document content.",
  "type": "text",
  "metadata": {
    "source": "user-upload",
    "author": "John Doe",
    "tags": ["sample", "documentation"]
  }
}
```

#### PUT /knowledge/documents/{document_id}

Update a document in the knowledge base.

**Parameters**:
- `document_id`: Document ID

**Request Body**:

```json
{
  "content": "This is an updated document content.",
  "type": "text",
  "metadata": {
    "source": "user-upload",
    "author": "John Doe",
    "tags": ["sample", "documentation", "updated"]
  }
}
```

**Response**:

```json
{
  "document_id": "doc_123456",
  "success": true
}
```

#### DELETE /knowledge/documents/{document_id}

Delete a document from the knowledge base.

**Parameters**:
- `document_id`: Document ID

**Response**:

```json
{
  "document_id": "doc_123456",
  "success": true
}
```

#### POST /knowledge/documents/bulk

Add multiple documents to the knowledge base in a single request.

**Request Body**:

```json
{
  "documents": [
    {
      "content": "Document 1 content",
      "type": "text",
      "metadata": {
        "source": "user-upload"
      }
    },
    {
      "content": "Document 2 content",
      "type": "text",
      "metadata": {
        "source": "user-upload"
      }
    }
  ]
}
```

**Response**:

```json
{
  "success_count": 2,
  "error_count": 0,
  "results": [
    {
      "document_id": "doc_123456",
      "success": true
    },
    {
      "document_id": "doc_123457",
      "success": true
    }
  ]
}
```

### Query API

#### POST /query

Query the knowledge base with natural language.

**Request Body**:

```json
{
  "query": "What is the capital of France?",
  "top_k": 5,
  "filter": {
    "source": "wikipedia"
  },
  "stream": false
}
```

**Response**:

```json
{
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
```

For streaming responses (`stream: true`), the response will be a stream of events in the format:

```
data: {"text": "The capital of"}
data: {"text": " France is"}
data: {"text": " Paris."}
data: [DONE]
```

#### POST /query/batch

Perform multiple queries in a single request.

**Request Body**:

```json
{
  "queries": [
    {
      "query": "What is the capital of France?",
      "top_k": 5
    },
    {
      "query": "What is the capital of Germany?",
      "top_k": 5
    }
  ]
}
```

**Response**:

```json
{
  "batch_id": "batch_123456"
}
```

#### GET /query/batch/{batch_id}

Get the results of a batch query.

**Parameters**:
- `batch_id`: Batch query ID

**Response**:

```json
{
  "batch_id": "batch_123456",
  "status": "completed",
  "results": [
    {
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
      ]
    },
    {
      "query": "What is the capital of Germany?",
      "answer": "The capital of Germany is Berlin.",
      "chunks": [
        {
          "id": "chunk_124",
          "text": "Berlin is the capital and largest city of Germany.",
          "document_id": "doc_457",
          "metadata": {
            "source": "wikipedia"
          },
          "score": 0.94
        }
      ]
    }
  ]
}
```

#### POST /query/similarity

Find chunks similar to the provided text.

**Request Body**:

```json
{
  "text": "Paris is a beautiful city",
  "top_k": 5,
  "filter": {
    "source": "wikipedia"
  }
}
```

**Response**:

```json
[
  {
    "id": "chunk_123",
    "text": "Paris is the capital and most populous city of France.",
    "document_id": "doc_456",
    "metadata": {
      "source": "wikipedia"
    },
    "score": 0.85
  },
  {
    "id": "chunk_125",
    "text": "Paris is known as the City of Light and is famous for its beautiful architecture.",
    "document_id": "doc_458",
    "metadata": {
      "source": "wikipedia"
    },
    "score": 0.82
  }
]
```

### Administration

#### GET /admin/health

Check the health of system components.

**Response**:

```json
{
  "status": "healthy",
  "orchestrator": "running",
  "agents": {
    "data_collection": "running",
    "knowledge_processing": "running",
    "knowledge_storage": "running",
    "knowledge_retrieval": "running",
    "knowledge_maintenance": "running",
    "rag": "running"
  },
  "version": "1.0.0"
}
```

#### GET /admin/status

Get detailed system status.

**Response**:

```json
{
  "status": "healthy",
  "uptime": 86400,
  "document_count": 1000,
  "chunk_count": 5000,
  "memory_usage": {
    "total": "2GB",
    "used": "1.5GB",
    "free": "0.5GB"
  },
  "cpu_usage": "30%",
  "storage_usage": {
    "total": "100GB",
    "used": "50GB",
    "free": "50GB"
  },
  "active_connections": 5,
  "requests_per_minute": 60
}
```

#### POST /admin/maintenance

Run maintenance tasks.

**Parameters**:
- `maintenance_type` (optional): Type of maintenance to run (default: "full")

**Response**:

```json
{
  "task_id": "task_123456"
}
```

#### GET /admin/maintenance/{task_id}

Get the status of a maintenance task.

**Parameters**:
- `task_id`: Maintenance task ID

**Response**:

```json
{
  "task_id": "task_123456",
  "status": "running",
  "progress": 50.0,
  "message": "Processing documents"
}
```

#### GET /admin/config

Get system configuration.

**Response**:

```json
{
  "system": {
    "name": "Unified Knowledge Base System",
    "version": "1.0.0"
  },
  "storage": {
    "provider": "memory",
    "connection_pool_size": 10
  },
  "embedding": {
    "provider": "sentence_transformers",
    "model": "all-MiniLM-L6-v2",
    "dimension": 384
  },
  "chunking": {
    "strategy": "recursive",
    "chunk_size": 1000,
    "chunk_overlap": 200
  },
  "retrieval": {
    "strategy": "hybrid",
    "top_k": 5,
    "reranking_enabled": true
  },
  "generation": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 1000,
    "stream": false
  },
  "api": {
    "rate_limit": 100,
    "cors_origins": ["*"]
  }
}
```

#### PATCH /admin/config

Update system configuration.

**Request Body**:

```json
{
  "retrieval": {
    "top_k": 10,
    "reranking_enabled": false
  },
  "generation": {
    "temperature": 0.5
  }
}
```

**Response**:

```json
{
  "status": "success",
  "message": "Configuration updated successfully",
  "updated_config": {
    "retrieval": {
      "top_k": 10,
      "reranking_enabled": false
    },
    "generation": {
      "temperature": 0.5
    }
  }
}
```

## WebSocket API

The WebSocket API provides real-time communication with the knowledge base system.

### Connection

Connect to the WebSocket endpoint:

```
ws://localhost:8000/ws/{client_id}
```

Where `client_id` is a unique identifier for your client.

### Message Format

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

### Available Operations

#### Query

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

#### Streaming Query

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

#### Subscribe to Notifications

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

#### Unsubscribe from Notifications

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

### Response Types

The WebSocket server can send several types of messages:

#### Acknowledgment

```json
{
  "type": "ack",
  "request_id": "query-1",
  "message": "Request received"
}
```

#### Response

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

#### Chunks Response

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

#### Streaming Chunk

```json
{
  "type": "chunk",
  "request_id": "query-2",
  "data": {
    "text": "The capital of France is Paris."
  }
}
```

#### Stream Complete

```json
{
  "type": "complete",
  "request_id": "query-2"
}
```

#### Subscription Confirmation

```json
{
  "type": "subscription",
  "status": "subscribed",
  "topic": "system_status"
}
```

#### Notification

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

#### Error

```json
{
  "type": "error",
  "request_id": "query-1",
  "error": "Invalid query format"
}
```

## Client Libraries

You can generate client libraries for various programming languages using the OpenAPI specification:

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate a Python client
openapi-generator-cli generate -i openapi.yaml -g python -o ./clients/python

# Generate a JavaScript client
openapi-generator-cli generate -i openapi.yaml -g javascript -o ./clients/javascript
```

## Examples

### Python Example

```python
import requests
import json

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Add a document
document = {
    "content": "Paris is the capital and most populous city of France.",
    "type": "text",
    "metadata": {
        "source": "wikipedia",
        "tags": ["geography", "cities", "france"]
    }
}

response = requests.post(
    f"{API_URL}/knowledge/documents",
    headers=headers,
    data=json.dumps(document)
)

print("Add Document Response:", response.json())

# Query the knowledge base
query = {
    "query": "What is the capital of France?",
    "top_k": 5
}

response = requests.post(
    f"{API_URL}/query",
    headers=headers,
    data=json.dumps(query)
)

print("Query Response:", response.json())
```

### JavaScript Example

```javascript
// Configuration
const API_URL = "http://localhost:8000";
const API_KEY = "your-api-key";

const headers = {
  "Content-Type": "application/json",
  "X-API-Key": API_KEY
};

// Add a document
const document = {
  content: "Paris is the capital and most populous city of France.",
  type: "text",
  metadata: {
    source: "wikipedia",
    tags: ["geography", "cities", "france"]
  }
};

fetch(`${API_URL}/knowledge/documents`, {
  method: "POST",
  headers: headers,
  body: JSON.stringify(document)
})
  .then(response => response.json())
  .then(data => console.log("Add Document Response:", data))
  .catch(error => console.error("Error:", error));

// Query the knowledge base
const query = {
  query: "What is the capital of France?",
  top_k: 5
};

fetch(`${API_URL}/query`, {
  method: "POST",
  headers: headers,
  body: JSON.stringify(query)
})
  .then(response => response.json())
  .then(data => console.log("Query Response:", data))
  .catch(error => console.error("Error:", error));
```

### WebSocket Example (JavaScript)

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

## Rate Limiting

API requests are subject to rate limiting based on your account tier:

- Free tier: 100 requests per hour
- Basic tier: 1,000 requests per hour
- Professional tier: 10,000 requests per hour
- Enterprise tier: Custom limits

When rate limits are exceeded, the API will return a `429 Too Many Requests` response.

## Conclusion

This API reference provides comprehensive documentation for the Unified Knowledge Base System API. For more information, please refer to the other documentation files:

- [Architecture Documentation](architecture.md)
- [Developer Guide](developer_guide.md)
- [Troubleshooting Guide](troubleshooting_guide.md)
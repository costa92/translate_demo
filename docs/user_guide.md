# Unified Knowledge Base System: User Guide

## Introduction

Welcome to the Unified Knowledge Base System! This comprehensive guide will help you understand how to use the system effectively to manage your knowledge base, retrieve information, and generate responses based on your data.

The Unified Knowledge Base System is a powerful platform that combines document storage, processing, retrieval, and generation capabilities in a cohesive system. Whether you're looking to build a question-answering system, a document search engine, or a knowledge management solution, this system provides the tools you need.

## System Overview

The Unified Knowledge Base System consists of several key components:

- **Storage Layer**: Manages document storage in various backends (Memory, Notion, Vector Databases)
- **Processing Layer**: Handles document processing, chunking, and embedding
- **Retrieval Layer**: Provides search capabilities to find relevant information
- **Generation Layer**: Generates responses based on retrieved information
- **Agent Layer**: Coordinates complex tasks through specialized agents
- **API Layer**: Provides external access through REST and WebSocket interfaces

## Getting Started

To start using the Unified Knowledge Base System, you'll need to:

1. Install the system
2. Configure your storage backend
3. Add documents to your knowledge base
4. Query your knowledge base

See the [Quick Start Tutorial](quick_start_tutorial.md) for a step-by-step guide to getting started.

## Core Concepts

### Documents and Chunks

The system works with two primary data structures:

- **Documents**: The original files or text content you add to the system
- **Chunks**: Smaller pieces of text extracted from documents for efficient retrieval

When you add a document to the system, it is automatically processed into chunks, which are then embedded and stored in your chosen vector store.

### Retrieval and Generation

The system uses a Retrieval-Augmented Generation (RAG) approach:

1. Your query is processed to find the most relevant chunks in the knowledge base
2. These chunks are used as context for generating a response
3. The response includes citations to the source documents

### Multi-Agent Architecture

The system uses specialized agents to handle different aspects of the workflow:

- **Orchestrator Agent**: Coordinates the overall workflow
- **Data Collection Agent**: Handles document collection from various sources
- **Knowledge Processing Agent**: Processes documents into chunks
- **Knowledge Storage Agent**: Manages storage operations
- **Knowledge Retrieval Agent**: Handles search and retrieval
- **Knowledge Maintenance Agent**: Performs maintenance tasks
- **RAG Agent**: Coordinates the RAG pipeline

## Common Use Cases

### Document Management

```python
# Add a document to the knowledge base
from knowledge_base import KnowledgeBase

kb = KnowledgeBase()
result = kb.add_document("path/to/document.pdf")
print(f"Added document with ID: {result.document_id}")
```

### Question Answering

```python
# Ask a question
from knowledge_base import KnowledgeBase

kb = KnowledgeBase()
result = kb.query("What is the capital of France?")
print(f"Answer: {result.answer}")
print(f"Sources: {result.sources}")
```

### Batch Processing

```python
# Process multiple documents
from knowledge_base import KnowledgeBase

kb = KnowledgeBase()
documents = ["doc1.pdf", "doc2.docx", "doc3.txt"]
results = kb.add_documents(documents)
for doc, result in zip(documents, results):
    print(f"Added {doc} with ID: {result.document_id}")
```

## Advanced Features

### Custom Embedding Models

The system supports various embedding models. You can configure your preferred model in the configuration file:

```yaml
embedding:
  provider: sentence_transformers
  model: all-MiniLM-L6-v2
```

### Retrieval Strategies

You can choose from different retrieval strategies:

- **Semantic**: Uses vector similarity search
- **Keyword**: Uses traditional keyword matching
- **Hybrid**: Combines both approaches

Configure your preferred strategy in the configuration file:

```yaml
retrieval:
  strategy: hybrid
  top_k: 5
  reranking_enabled: true
```

### Generation Providers

The system supports multiple language model providers for generation:

- OpenAI
- DeepSeek
- SiliconFlow
- Ollama

Configure your preferred provider in the configuration file:

```yaml
generation:
  provider: openai
  model: gpt-4
  temperature: 0.7
  stream: true
```

## API Usage

The system provides a comprehensive API for integration with other applications:

### REST API

```python
import requests

# Add a document
response = requests.post(
    "http://localhost:8000/api/documents",
    json={"content": "This is a test document", "type": "text"}
)
document_id = response.json()["document_id"]

# Query the knowledge base
response = requests.post(
    "http://localhost:8000/api/query",
    json={"query": "What is in the test document?"}
)
print(response.json()["answer"])
```

### WebSocket API

```javascript
const socket = new WebSocket("ws://localhost:8000/api/ws");

socket.onopen = () => {
  socket.send(JSON.stringify({
    type: "query",
    payload: {
      query: "What is the capital of France?"
    }
  }));
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "chunk") {
    console.log("Received chunk:", data.payload.text);
  } else if (data.type === "complete") {
    console.log("Complete answer:", data.payload.answer);
  }
};
```

## Troubleshooting

For common issues and their solutions, see the [Troubleshooting Guide](troubleshooting_guide.md).

## Next Steps

- Learn about [Configuration Options](configuration_guide.md)
- Explore [Best Practices](best_practices_guide.md)
- Check out the [API Reference](api_reference.md)
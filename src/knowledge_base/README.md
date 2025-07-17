# Unified Knowledge Base System

A comprehensive knowledge management, retrieval, and generation system that combines the strengths of a layered architecture with a multi-agent system.

## Overview

The Unified Knowledge Base System integrates multiple knowledge base implementations into a single, cohesive platform. It provides:

- Modular architecture with clear separation of concerns
- Pluggable components for storage, embedding, and generation
- Multi-agent coordination for complex tasks
- Comprehensive API for external integration

## Architecture

The system follows a hybrid architecture with the following key components:

- **Core Layer**: Configuration, type definitions, exception handling, and factory classes
- **Storage Layer**: Vector stores and storage providers
- **Processing Layer**: Document processing, chunking, and embedding
- **Retrieval Layer**: Semantic and keyword search with reranking
- **Generation Layer**: Response generation with multiple LLM providers
- **Agent Layer**: Specialized agents for different tasks
- **API Layer**: RESTful and WebSocket APIs

## Getting Started

```python
from knowledge_base.core.knowledge_base import KnowledgeBase
from knowledge_base.core.config import Config

# Initialize with default configuration
kb = KnowledgeBase()

# Add a document
doc_id = await kb.add_document("This is a sample document.")

# Query the knowledge base
result = await kb.query("What is in the document?")
print(result.answer)
```

## Documentation

For more detailed documentation, see the [docs](../../docs/) directory.
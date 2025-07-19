# Unified Knowledge Base System Developer Guide

## Introduction

This developer guide provides comprehensive information for developers working with the Unified Knowledge Base System. It covers setup, configuration, extension, and best practices for development.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip or poetry for package management
- Docker (optional, for containerized deployment)
- Access to LLM APIs (OpenAI, DeepSeek, etc.) if using those providers

### Installation

#### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/unified-knowledge-base.git
cd unified-knowledge-base

# Install dependencies
pip install -e .
```

#### Using poetry

```bash
# Clone the repository
git clone https://github.com/yourusername/unified-knowledge-base.git
cd unified-knowledge-base

# Install dependencies
poetry install
```

### Configuration

Create a configuration file (e.g., `config.yaml`) with the following structure:

```yaml
system:
  name: "Unified Knowledge Base System"
  version: "1.0.0"

storage:
  provider: "memory"  # Options: memory, notion, chroma, pinecone, weaviate
  connection_pool_size: 10
  # Provider-specific configuration
  memory:
    persistence_path: "./data/memory_store.json"
  notion:
    token: "your-notion-token"
    database_id: "your-database-id"

embedding:
  provider: "sentence_transformers"  # Options: sentence_transformers, openai, deepseek, siliconflow, simple
  model: "all-MiniLM-L6-v2"
  dimension: 384
  batch_size: 32
  cache_enabled: true
  cache_size: 1000

chunking:
  strategy: "recursive"  # Options: recursive, sentence, paragraph, fixed
  chunk_size: 1000
  chunk_overlap: 200

retrieval:
  strategy: "hybrid"  # Options: semantic, keyword, hybrid
  top_k: 5
  reranking_enabled: true
  semantic_weight: 0.7
  keyword_weight: 0.3

generation:
  provider: "openai"  # Options: openai, deepseek, siliconflow, ollama
  model: "gpt-4o"
  temperature: 0.7
  max_tokens: 1000
  stream: false
  # Provider-specific configuration
  openai:
    api_key: "your-openai-api-key"
  deepseek:
    api_key: "your-deepseek-api-key"
  ollama:
    base_url: "http://localhost:11434"

api:
  host: "0.0.0.0"
  port: 8000
  rate_limit: 100
  cors_origins: ["*"]
  auth_enabled: true
```

### Basic Usage

#### Creating a Knowledge Base

```python
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.knowledge_base import KnowledgeBase

# Load configuration
config = Config("config.yaml")

# Create knowledge base
kb = KnowledgeBase(config)

# Initialize knowledge base
await kb.initialize()
```

#### Adding Documents

```python
# Add a single document
document_id = await kb.add_document(
    content="Paris is the capital and most populous city of France.",
    document_type="text",
    metadata={
        "source": "wikipedia",
        "tags": ["geography", "cities", "france"]
    }
)

# Add multiple documents
documents = [
    {
        "content": "Berlin is the capital and largest city of Germany.",
        "type": "text",
        "metadata": {
            "source": "wikipedia",
            "tags": ["geography", "cities", "germany"]
        }
    },
    {
        "content": "London is the capital and largest city of England and the United Kingdom.",
        "type": "text",
        "metadata": {
            "source": "wikipedia",
            "tags": ["geography", "cities", "uk"]
        }
    }
]

document_ids = await kb.add_documents(documents)
```

#### Querying the Knowledge Base

```python
# Simple query
result = await kb.query("What is the capital of France?")
print(result.answer)

# Query with parameters
result = await kb.query(
    query="What is the capital of France?",
    top_k=3,
    filter={"source": "wikipedia"},
    stream=False
)

print(result.answer)
for chunk in result.chunks:
    print(f"- {chunk.text} (score: {chunk.score})")
```

#### Streaming Responses

```python
# Streaming query
async for chunk in kb.query_stream("What is the capital of France?"):
    print(chunk, end="", flush=True)
```

## Architecture Overview

The Unified Knowledge Base System follows a modular architecture with the following key components:

### Core Components

- **Config**: Configuration management
- **KnowledgeBase**: Main entry point for the system
- **Types**: Core data structures
- **Exceptions**: Exception hierarchy
- **Factory**: Component creation
- **Registry**: Component registration

### Storage Layer

- **BaseVectorStore**: Base interface for vector stores
- **VectorStore**: Factory for creating vector stores
- **Storage Providers**: Implementations for various storage backends

### Processing Layer

- **DocumentProcessor**: Processes documents into chunks
- **Chunker**: Splits documents into chunks
- **Embedder**: Converts text into vector representations
- **Metadata Extractor**: Extracts metadata from documents

### Retrieval Layer

- **Retriever**: Retrieves relevant chunks for a query
- **Reranker**: Improves retrieval results
- **Context Manager**: Maintains context across queries
- **Retrieval Strategies**: Different approaches to retrieval

### Generation Layer

- **Generator**: Generates responses based on retrieved information
- **Prompt Templates**: Templates for LLM prompts
- **Quality Control**: Ensures response quality
- **Citation**: Generates citations for sources

### Agent Layer

- **BaseAgent**: Base interface for agents
- **OrchestratorAgent**: Coordinates workflow between agents
- **Specialized Agents**: Agents for specific tasks

### API Layer

- **Server**: FastAPI application
- **Routes**: API endpoints
- **Middleware**: Request processing middleware
- **WebSocket**: Real-time communication

## Extending the System

### Creating a Custom Storage Provider

To create a custom storage provider, implement the `BaseVectorStore` interface:

```python
from typing import List, Dict, Any, Optional, Tuple
from src.knowledge_base.storage.base import BaseVectorStore
from src.knowledge_base.core.types import TextChunk

class CustomVectorStore(BaseVectorStore):
    """Custom vector store implementation."""
    
    def __init__(self, config):
        """Initialize the vector store."""
        super().__init__(config)
        # Custom initialization
        
    async def initialize(self) -> None:
        """Initialize the vector store."""
        # Implementation
        
    async def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """Add texts to the vector store."""
        # Implementation
        
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filter: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> List[Tuple[TextChunk, float]]:
        """Search for similar texts."""
        # Implementation
        
    async def delete(self, ids: List[str]) -> None:
        """Delete texts from the vector store."""
        # Implementation
        
    async def clear(self) -> None:
        """Clear all texts from the vector store."""
        # Implementation
```

Register your custom provider:

```python
from src.knowledge_base.core.registry import Registry
from src.knowledge_base.storage.vector_store import VectorStore

# Register your custom provider
Registry.register("vector_store", "custom", CustomVectorStore)

# Use your custom provider in configuration
config.storage.provider = "custom"
```

### Creating a Custom Embedding Provider

To create a custom embedding provider, implement the `Embedder` interface:

```python
from typing import List
from src.knowledge_base.processing.embedder import Embedder
from src.knowledge_base.core.types import TextChunk

class CustomEmbedder(Embedder):
    """Custom embedder implementation."""
    
    def __init__(self, config):
        """Initialize the embedder."""
        super().__init__(config)
        # Custom initialization
        
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text."""
        # Implementation
        
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        # Implementation
```

Register your custom embedder:

```python
from src.knowledge_base.core.registry import Registry

# Register your custom embedder
Registry.register("embedder", "custom", CustomEmbedder)

# Use your custom embedder in configuration
config.embedding.provider = "custom"
```

### Creating a Custom Chunking Strategy

To create a custom chunking strategy, implement the `Chunker` interface:

```python
from typing import List
from src.knowledge_base.processing.chunker import Chunker
from src.knowledge_base.core.types import Document, TextChunk

class CustomChunker(Chunker):
    """Custom chunking strategy."""
    
    def __init__(self, config):
        """Initialize the chunker."""
        super().__init__(config)
        # Custom initialization
        
    def chunk(self, document: Document) -> List[TextChunk]:
        """Chunk a document into text chunks."""
        # Implementation
```

Register your custom chunker:

```python
from src.knowledge_base.core.registry import Registry

# Register your custom chunker
Registry.register("chunker", "custom", CustomChunker)

# Use your custom chunker in configuration
config.chunking.strategy = "custom"
```

### Creating a Custom Generation Provider

To create a custom generation provider, implement the `GenerationProvider` interface:

```python
from typing import AsyncIterator, Union
from src.knowledge_base.generation.generator import GenerationProvider

class CustomGenerationProvider(GenerationProvider):
    """Custom generation provider."""
    
    def __init__(self, config):
        """Initialize the generation provider."""
        super().__init__(config)
        # Custom initialization
        
    async def generate(self, prompt: str) -> str:
        """Generate a response."""
        # Implementation
        
    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        """Generate a streaming response."""
        # Implementation
```

Register your custom generation provider:

```python
from src.knowledge_base.core.registry import Registry

# Register your custom generation provider
Registry.register("generation_provider", "custom", CustomGenerationProvider)

# Use your custom generation provider in configuration
config.generation.provider = "custom"
```

## Working with Agents

### Creating a Custom Agent

To create a custom agent, implement the `BaseAgent` interface:

```python
from typing import Dict, Any
from src.knowledge_base.agents.base import BaseAgent
from src.knowledge_base.agents.message import AgentMessage

class CustomAgent(BaseAgent):
    """Custom agent implementation."""
    
    def __init__(self, config):
        """Initialize the agent."""
        super().__init__(config)
        # Custom initialization
        
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message and return a response."""
        # Implementation
```

Register your custom agent:

```python
from src.knowledge_base.agents.registry import AgentRegistry

# Register your custom agent
AgentRegistry.register("custom", CustomAgent)

# Use your custom agent
orchestrator.agents["custom"] = CustomAgent(config)
```

### Agent Communication

Agents communicate using the `AgentMessage` class:

```python
from src.knowledge_base.agents.message import AgentMessage

# Create a message
message = AgentMessage(
    source="orchestrator",
    destination="custom",
    message_type="request",
    payload={
        "action": "process",
        "data": "Some data to process"
    }
)

# Send the message to the agent
response = await custom_agent.process_message(message)

# Process the response
print(response.payload)
```

## API Development

### Creating a New API Endpoint

To create a new API endpoint, add a route to the appropriate router:

```python
from fastapi import APIRouter, Depends, HTTPException
from src.knowledge_base.api.models.custom import CustomRequest, CustomResponse
from src.knowledge_base.api.dependencies import get_orchestrator

router = APIRouter(prefix="/custom", tags=["Custom"])

@router.post("/endpoint")
async def custom_endpoint(
    request: CustomRequest,
    orchestrator = Depends(get_orchestrator)
):
    """Custom endpoint."""
    try:
        result = await orchestrator.receive_request(
            source="api",
            request_type="custom",
            payload=request.dict()
        )
        return CustomResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Add your router to the API server:

```python
from src.knowledge_base.api.server import app
from src.knowledge_base.api.routes.custom import router as custom_router

app.include_router(custom_router)
```

### Adding WebSocket Support

To add WebSocket support for a new message type:

```python
from src.knowledge_base.api.websocket.handler import WebSocketHandler

# Add a new message handler
@WebSocketHandler.register_handler("custom")
async def handle_custom_message(handler, client_id, request_id, payload):
    """Handle custom messages."""
    # Implementation
    result = await handler.orchestrator.receive_request(
        source=f"websocket:{client_id}",
        request_type="custom",
        payload=payload
    )
    
    # Send response
    await handler.send_response(client_id, request_id, result)
```

## Testing

### Unit Testing

Create unit tests for your components:

```python
import pytest
from src.knowledge_base.core.config import Config
from src.knowledge_base.storage.providers.memory import MemoryVectorStore

@pytest.fixture
def config():
    """Create a test configuration."""
    return Config()

@pytest.fixture
async def memory_store(config):
    """Create a memory vector store."""
    store = MemoryVectorStore(config)
    await store.initialize()
    yield store
    await store.clear()

async def test_add_texts(memory_store):
    """Test adding texts to the memory store."""
    texts = ["Text 1", "Text 2", "Text 3"]
    ids = await memory_store.add_texts(texts)
    
    assert len(ids) == 3
    assert all(isinstance(id, str) for id in ids)
```

### Integration Testing

Create integration tests for your components:

```python
import pytest
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.knowledge_base import KnowledgeBase

@pytest.fixture
async def knowledge_base():
    """Create a knowledge base for testing."""
    config = Config()
    config.storage.provider = "memory"
    kb = KnowledgeBase(config)
    await kb.initialize()
    yield kb
    await kb.clear()

async def test_add_and_query(knowledge_base):
    """Test adding a document and querying it."""
    # Add a document
    await knowledge_base.add_document(
        content="Paris is the capital of France.",
        document_type="text",
        metadata={"source": "test"}
    )
    
    # Query the knowledge base
    result = await knowledge_base.query("What is the capital of France?")
    
    assert result.answer is not None
    assert "Paris" in result.answer
```

### End-to-End Testing

Create end-to-end tests for your API:

```python
import pytest
from fastapi.testclient import TestClient
from src.knowledge_base.api.server import app

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

def test_query_endpoint(client):
    """Test the query endpoint."""
    # Add a document
    client.post(
        "/knowledge/documents",
        json={
            "content": "Paris is the capital of France.",
            "type": "text",
            "metadata": {"source": "test"}
        },
        headers={"X-API-Key": "test-key"}
    )
    
    # Query the knowledge base
    response = client.post(
        "/query",
        json={"query": "What is the capital of France?"},
        headers={"X-API-Key": "test-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "Paris" in data["answer"]
```

## Deployment

### Docker Deployment

The project includes a multi-stage Dockerfile that optimizes the build process and reduces the final image size:

```dockerfile
# Multi-stage build for the Unified Knowledge Base System

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy only the files needed for installing dependencies
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Stage 2: Runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create a non-root user to run the application
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the API port
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["python", "-m", "src.knowledge_base.api.server"]
```

Build and run the Docker container:

```bash
# Build the image
docker build -t unified-knowledge-base .

# Run the container
docker run -p 8000:8000 unified-knowledge-base
```

### Docker Compose Deployment

The project includes a docker-compose.yml file that sets up the entire system:

```yaml
version: '3.8'

services:
  # Knowledge Base API Service
  api:
    build:
      context: .
      dockerfile: Dockerfile
    image: unified-knowledge-base:latest
    container_name: knowledge-base-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - KB_SYSTEM_LOG_LEVEL=INFO
      - KB_SYSTEM_DEBUG=false
      - KB_API_HOST=0.0.0.0
      - KB_API_PORT=8000
      - KB_API_CORS_ORIGINS=["*"]
      - KB_STORAGE_PROVIDER=memory
      # Add your API keys and other configuration here
      # - KB_GENERATION_API_KEY=your_api_key
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # Optional: Vector Database (Chroma)
  # Uncomment to enable
  # chroma:
  #   image: ghcr.io/chroma-core/chroma:latest
  #   container_name: knowledge-base-chroma
  #   restart: unless-stopped
  #   volumes:
  #     - ./data/chroma:/chroma/data
  #   ports:
  #     - "8001:8000"
  #   environment:
  #     - CHROMA_DB_IMPL=duckdb+parquet
  #     - CHROMA_PERSIST_DIRECTORY=/chroma/data

  # Optional: Ollama for local LLM support
  # Uncomment to enable
  # ollama:
  #   image: ollama/ollama:latest
  #   container_name: knowledge-base-ollama
  #   restart: unless-stopped
  #   volumes:
  #     - ./data/ollama:/root/.ollama
  #   ports:
  #     - "11434:11434"
```

Run with Docker Compose:

```bash
# Build and start the containers
docker-compose up -d

# Stop the containers
docker-compose down
```

### Using the Docker Convenience Script

The project includes a convenience script (`docker-run.sh`) to simplify Docker operations:

```bash
# Build and start the containers
./docker-run.sh --build --detach

# Stop the containers
./docker-run.sh --stop

# Restart the containers
./docker-run.sh --restart

# Stop containers and remove volumes
./docker-run.sh --clean
```

### Kubernetes Deployment

Create a Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: unified-knowledge-base
spec:
  replicas: 3
  selector:
    matchLabels:
      app: unified-knowledge-base
  template:
    metadata:
      labels:
        app: unified-knowledge-base
    spec:
      containers:
      - name: unified-knowledge-base
        image: unified-knowledge-base:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: config-volume
          mountPath: /app/config.yaml
          subPath: config.yaml
      volumes:
      - name: config-volume
        configMap:
          name: unified-knowledge-base-config
---
apiVersion: v1
kind: Service
metadata:
  name: unified-knowledge-base
spec:
  selector:
    app: unified-knowledge-base
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

Create a ConfigMap for the configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: unified-knowledge-base-config
data:
  config.yaml: |
    system:
      name: "Unified Knowledge Base System"
      version: "1.0.0"
    
    storage:
      provider: "memory"
      connection_pool_size: 10
    
    # Rest of the configuration...
```

Apply the Kubernetes resources:

```bash
kubectl apply -f deployment.yaml
kubectl apply -f configmap.yaml
```

## Best Practices

### Code Organization

- Follow the modular architecture
- Keep components small and focused
- Use interfaces for abstraction
- Implement the provider pattern for extensibility

### Error Handling

- Use the exception hierarchy
- Provide meaningful error messages
- Handle errors at the appropriate level
- Log errors for debugging

### Asynchronous Programming

- Use `async`/`await` for I/O-bound operations
- Avoid blocking the event loop
- Use proper exception handling in async code
- Consider using asyncio primitives for coordination

### Configuration Management

- Use the configuration system
- Provide sensible defaults
- Validate configuration values
- Support environment variables for sensitive information

### Testing

- Write unit tests for components
- Write integration tests for workflows
- Write end-to-end tests for API endpoints
- Use fixtures for test setup and teardown

### Documentation

- Document public interfaces
- Provide examples
- Keep documentation up-to-date
- Use docstrings for code documentation

## Conclusion

This developer guide provides comprehensive information for working with the Unified Knowledge Base System. For more information, please refer to the other documentation files:

- [Architecture Documentation](architecture.md)
- [API Reference](api_reference.md)
- [Troubleshooting Guide](troubleshooting_guide.md)
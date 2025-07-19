# Unified Knowledge Base System: Quick Start Tutorial

This tutorial will guide you through the process of setting up and using the Unified Knowledge Base System for the first time.

## Prerequisites

Before you begin, make sure you have:

- Python 3.8 or higher installed
- pip package manager
- Access to the required API keys (if using external services like OpenAI)

## Installation

### Step 1: Install the Package

```bash
pip install unified-knowledge-base
```

Or install from source:

```bash
git clone https://github.com/yourusername/unified-knowledge-base.git
cd unified-knowledge-base
pip install -e .
```

### Step 2: Create a Configuration File

Create a file named `config.yaml` with the following content:

```yaml
system:
  log_level: INFO

storage:
  provider: memory  # For a simple start, we'll use in-memory storage

embedding:
  provider: sentence_transformers
  model: all-MiniLM-L6-v2

chunking:
  strategy: recursive
  chunk_size: 1000
  chunk_overlap: 200

retrieval:
  strategy: semantic
  top_k: 5
  reranking_enabled: true

generation:
  provider: openai  # Replace with your preferred provider
  model: gpt-3.5-turbo  # Replace with your preferred model
  temperature: 0.7
  stream: true
  
api:
  host: 0.0.0.0
  port: 8000
  cors_origins: ["*"]
```

### Step 3: Set Environment Variables

If you're using external services like OpenAI, set the required API keys:

```bash
# For OpenAI
export OPENAI_API_KEY=your_api_key_here

# For DeepSeek
export DEEPSEEK_API_KEY=your_api_key_here

# For Notion
export NOTION_API_KEY=your_api_key_here
```

## Basic Usage

### Step 4: Create a Simple Script

Create a file named `example.py` with the following content:

```python
from knowledge_base import KnowledgeBase

# Initialize the knowledge base with your config
kb = KnowledgeBase(config_path="config.yaml")

# Add a document
result = kb.add_text(
    "The capital of France is Paris. Paris is known as the City of Light.",
    metadata={"source": "geography_facts.txt"}
)
print(f"Added document with ID: {result.document_id}")

# Query the knowledge base
result = kb.query("What is the capital of France?")
print(f"Query: What is the capital of France?")
print(f"Answer: {result.answer}")
print(f"Sources: {result.chunks}")
```

### Step 5: Run the Script

```bash
python example.py
```

You should see output similar to:

```
Added document with ID: doc_1234567890
Query: What is the capital of France?
Answer: The capital of France is Paris.
Sources: [TextChunk(id='chunk_1', text='The capital of France is Paris. Paris is known as the City of Light.', document_id='doc_1234567890', metadata={'source': 'geography_facts.txt'})]
```

## Starting the API Server

### Step 6: Run the API Server

```bash
python -m knowledge_base.api.server --config config.yaml
```

The API server will start on http://localhost:8000.

### Step 7: Access the API Documentation

Open your browser and navigate to:

```
http://localhost:8000/docs
```

This will show the interactive API documentation where you can test the endpoints.

## Working with Files

### Step 8: Add a PDF Document

```python
from knowledge_base import KnowledgeBase

kb = KnowledgeBase(config_path="config.yaml")

# Add a PDF document
result = kb.add_document("path/to/document.pdf")
print(f"Added document with ID: {result.document_id}")
print(f"Created {len(result.chunk_ids)} chunks")

# Query based on the PDF content
result = kb.query("What does the PDF document say about topic X?")
print(f"Answer: {result.answer}")
```

## Using the WebSocket API

### Step 9: Create a Simple WebSocket Client

Create a file named `websocket_client.py`:

```python
import asyncio
import websockets
import json

async def query():
    uri = "ws://localhost:8000/api/ws"
    async with websockets.connect(uri) as websocket:
        # Send a query
        await websocket.send(json.dumps({
            "type": "query",
            "payload": {
                "query": "What is the capital of France?"
            }
        }))
        
        # Receive streaming response
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data["type"] == "chunk":
                print(f"Chunk: {data['payload']['text']}")
            elif data["type"] == "complete":
                print(f"Complete answer: {data['payload']['answer']}")
                break

asyncio.run(query())
```

Run the client:

```bash
python websocket_client.py
```

## Next Steps

Now that you've set up the basic system, you can:

1. Configure different storage backends (see [Configuration Guide](configuration_guide.md))
2. Add more documents to your knowledge base
3. Experiment with different retrieval and generation settings
4. Integrate the API with your applications

For more advanced usage, check out the [User Guide](user_guide.md) and [Best Practices Guide](best_practices_guide.md).
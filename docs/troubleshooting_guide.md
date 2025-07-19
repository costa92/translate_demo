# Unified Knowledge Base System Troubleshooting Guide

## Introduction

This troubleshooting guide provides solutions for common issues you might encounter when working with the Unified Knowledge Base System. It covers installation problems, configuration issues, runtime errors, and performance optimization.

## Installation Issues

### Python Version Compatibility

**Issue**: Installation fails with Python version errors.

**Solution**:
- Ensure you're using Python 3.9 or higher
- Check your Python version with `python --version`
- Consider using a virtual environment with the correct Python version:

```bash
# Create a virtual environment with Python 3.9
python3.9 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Linux/macOS
venv\Scripts\activate     # On Windows
```

### Dependency Conflicts

**Issue**: Installation fails due to dependency conflicts.

**Solution**:
- Use a clean virtual environment
- Try installing with `pip install --no-deps` and then manually install dependencies
- Check for conflicting packages with `pip check`
- Consider using Poetry for better dependency management:

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
```

### C Extension Build Failures

**Issue**: Installation fails when building C extensions.

**Solution**:
- Install required build tools:
  - On Ubuntu/Debian: `sudo apt-get install build-essential python3-dev`
  - On macOS: `xcode-select --install`
  - On Windows: Install Visual C++ Build Tools
- Try installing pre-built wheels if available:

```bash
pip install --only-binary=:all: -r requirements.txt
```

## Configuration Issues

### Configuration File Not Found

**Issue**: System cannot find the configuration file.

**Solution**:
- Check the file path and ensure it's accessible
- Use absolute paths instead of relative paths
- Verify file permissions
- Create a default configuration if it doesn't exist:

```python
from src.knowledge_base.core.config import Config

# Create default configuration
config = Config()
config.save("config.yaml")
```

### Invalid Configuration Values

**Issue**: System reports invalid configuration values.

**Solution**:
- Check the configuration schema and ensure all values are valid
- Look for typos in provider names or other string values
- Ensure numeric values are within acceptable ranges
- Verify that referenced files or directories exist
- Use the validation method to check your configuration:

```python
from src.knowledge_base.core.config import Config

config = Config("config.yaml")
try:
    config.validate()
    print("Configuration is valid")
except Exception as e:
    print(f"Configuration error: {e}")
```

### Environment Variables Not Applied

**Issue**: Environment variables are not overriding configuration values.

**Solution**:
- Check environment variable naming (should be uppercase with underscores)
- Ensure environment variables are properly exported
- Verify the environment variable prefix (default is `KB_`)
- Test with a simple environment variable:

```bash
# Set environment variable
export KB_STORAGE__PROVIDER=memory

# Run your application
python -m src.knowledge_base.api.server
```

## Storage Issues

### Memory Storage Persistence Failure

**Issue**: Memory storage data is lost after restart.

**Solution**:
- Ensure persistence is enabled in configuration
- Check the persistence path is writable
- Manually save the memory store before shutdown:

```python
# Save memory store
await kb.storage.save()
```

### Notion API Connection Issues

**Issue**: Cannot connect to Notion API.

**Solution**:
- Verify your Notion API token is correct and not expired
- Check that the database ID is correct
- Ensure your integration has access to the database
- Test the connection with a simple script:

```python
import requests

headers = {
    "Authorization": f"Bearer {notion_token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

response = requests.get(
    f"https://api.notion.com/v1/databases/{database_id}",
    headers=headers
)

print(f"Status code: {response.status_code}")
print(response.json())
```

### Vector Database Connection Issues

**Issue**: Cannot connect to vector database.

**Solution**:
- Check connection string or credentials
- Verify the database is running and accessible
- Ensure required ports are open
- Test with a simple connection script:

```python
# For Chroma
import chromadb

client = chromadb.Client(
    host="localhost",
    port=8000
)

# Test connection
try:
    client.heartbeat()
    print("Connected to Chroma")
except Exception as e:
    print(f"Connection error: {e}")
```

## Embedding Issues

### Embedding Provider Not Available

**Issue**: Embedding provider is not available or fails to load.

**Solution**:
- Check if the required packages are installed
- Verify API keys for cloud providers
- Ensure the model is available and accessible
- Try a different embedding provider:

```python
# Update configuration
config.embedding.provider = "simple"  # Fallback to simple embedder
```

### Out of Memory During Embedding

**Issue**: System runs out of memory when embedding large documents.

**Solution**:
- Reduce batch size in configuration
- Process documents in smaller chunks
- Increase system memory or use swap
- Monitor memory usage and adjust accordingly:

```python
# Update configuration
config.embedding.batch_size = 8  # Smaller batch size
```

### Slow Embedding Performance

**Issue**: Embedding process is too slow.

**Solution**:
- Use a faster embedding provider if available
- Enable caching to avoid redundant embeddings
- Optimize batch size for your hardware
- Consider using a local embedding model:

```python
# Update configuration
config.embedding.provider = "sentence_transformers"
config.embedding.model = "all-MiniLM-L6-v2"  # Smaller, faster model
config.embedding.cache_enabled = True
```

## Retrieval Issues

### Poor Retrieval Quality

**Issue**: Retrieval results are not relevant to the query.

**Solution**:
- Try different retrieval strategies (semantic, keyword, hybrid)
- Adjust the semantic/keyword weights for hybrid retrieval
- Increase the number of retrieved chunks (top_k)
- Enable reranking to improve relevance:

```python
# Update configuration
config.retrieval.strategy = "hybrid"
config.retrieval.semantic_weight = 0.7
config.retrieval.keyword_weight = 0.3
config.retrieval.top_k = 10
config.retrieval.reranking_enabled = True
```

### No Results Found

**Issue**: No results are returned for queries.

**Solution**:
- Check if documents have been added to the knowledge base
- Verify that embeddings were generated correctly
- Try more general queries
- Inspect the vector store directly:

```python
# Check document count
document_count = await kb.storage.count()
print(f"Document count: {document_count}")

# Test with a simple query
results = await kb.storage.similarity_search("test", k=5)
print(f"Results: {len(results)}")
```

### Filtering Not Working

**Issue**: Metadata filtering is not working as expected.

**Solution**:
- Check metadata format and structure
- Ensure filter syntax is correct
- Verify that metadata was properly stored
- Test with a simple filter:

```python
# Test with a simple filter
results = await kb.query(
    "test",
    filter={"source": "wikipedia"}
)
print(f"Results: {len(results.chunks)}")
```

## Generation Issues

### LLM API Connection Issues

**Issue**: Cannot connect to LLM API.

**Solution**:
- Verify API key is correct and not expired
- Check API endpoint URL
- Ensure network connectivity to the API
- Test with a simple API call:

```python
# For OpenAI
import openai

openai.api_key = "your-api-key"

try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}]
    )
    print("API connection successful")
except Exception as e:
    print(f"API connection error: {e}")
```

### Generation Quality Issues

**Issue**: Generated responses are low quality or irrelevant.

**Solution**:
- Adjust generation parameters (temperature, max_tokens)
- Improve prompt templates
- Ensure retrieved context is relevant
- Try a different LLM provider or model:

```python
# Update configuration
config.generation.temperature = 0.3  # Lower temperature for more focused responses
config.generation.model = "gpt-4o"  # Use a more capable model
```

### Streaming Not Working

**Issue**: Streaming responses are not working.

**Solution**:
- Verify streaming is enabled in configuration
- Check if the LLM provider supports streaming
- Ensure client can handle streaming responses
- Test with a simple streaming example:

```python
# Enable streaming
config.generation.stream = True

# Test streaming
async for chunk in kb.query_stream("What is the capital of France?"):
    print(chunk, end="", flush=True)
```

## Agent Issues

### Agent Communication Failures

**Issue**: Agents are not communicating properly.

**Solution**:
- Check agent initialization and registration
- Verify message format and routing
- Ensure all required agents are available
- Test with direct agent communication:

```python
from src.knowledge_base.agents.message import AgentMessage

# Create a message
message = AgentMessage(
    source="test",
    destination="orchestrator",
    message_type="test",
    payload={"test": "data"}
)

# Send message directly
response = await orchestrator.process_message(message)
print(response.payload)
```

### Task Distribution Issues

**Issue**: Tasks are not being distributed to the correct agents.

**Solution**:
- Check orchestrator configuration
- Verify agent registration
- Ensure task types are correctly mapped to agents
- Monitor task distribution:

```python
# Enable debug logging for the orchestrator
import logging
logging.getLogger("src.knowledge_base.agents.orchestrator").setLevel(logging.DEBUG)
```

### Agent Initialization Failures

**Issue**: Agents fail to initialize.

**Solution**:
- Check agent dependencies
- Verify configuration for each agent
- Ensure required resources are available
- Initialize agents manually:

```python
from src.knowledge_base.agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent

# Initialize agent manually
retrieval_agent = KnowledgeRetrievalAgent(config)
await retrieval_agent.initialize()
```

## API Issues

### API Server Won't Start

**Issue**: API server fails to start.

**Solution**:
- Check port availability (another service might be using the port)
- Verify host configuration
- Ensure all dependencies are installed
- Try starting with explicit host and port:

```bash
uvicorn src.knowledge_base.api.server:app --host 0.0.0.0 --port 8000
```

### Authentication Failures

**Issue**: API authentication is failing.

**Solution**:
- Check API key or token configuration
- Verify authentication headers in requests
- Ensure authentication middleware is enabled
- Test with a known good API key:

```bash
curl -X GET "http://localhost:8000/health" -H "X-API-Key: test-key"
```

### CORS Issues

**Issue**: Browser requests are blocked by CORS.

**Solution**:
- Configure CORS origins in configuration
- Allow specific origins or use wildcard for development
- Ensure CORS middleware is enabled
- Test CORS configuration:

```python
# Update configuration
config.api.cors_origins = ["*"]  # Allow all origins (for development only)
```

### WebSocket Connection Issues

**Issue**: WebSocket connections are failing.

**Solution**:
- Check WebSocket endpoint URL
- Verify client implementation
- Ensure WebSocket support is enabled
- Test with a simple WebSocket client:

```javascript
// JavaScript WebSocket test
const ws = new WebSocket("ws://localhost:8000/ws/test-client");

ws.onopen = () => {
  console.log("Connected");
  ws.send(JSON.stringify({
    request_id: "test",
    request_type: "ping",
    payload: {}
  }));
};

ws.onmessage = (event) => {
  console.log("Received:", event.data);
};

ws.onerror = (error) => {
  console.error("Error:", error);
};
```

## Performance Issues

### Slow Query Performance

**Issue**: Queries are taking too long to process.

**Solution**:
- Enable caching for embeddings and responses
- Optimize vector store configuration
- Use a more efficient retrieval strategy
- Profile the query pipeline:

```python
import time

# Profile query performance
start_time = time.time()
result = await kb.query("What is the capital of France?")
end_time = time.time()

print(f"Query time: {end_time - start_time:.2f} seconds")
```

### High Memory Usage

**Issue**: System is using too much memory.

**Solution**:
- Reduce batch sizes for processing
- Limit the number of documents in memory
- Use more efficient storage providers
- Monitor memory usage:

```python
import psutil
import os

# Monitor memory usage
process = psutil.Process(os.getpid())
memory_info = process.memory_info()
print(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
```

### Slow Document Processing

**Issue**: Document processing is too slow.

**Solution**:
- Use smaller chunk sizes
- Process documents in parallel
- Use more efficient chunking strategies
- Profile document processing:

```python
import time

# Profile document processing
start_time = time.time()
document_id = await kb.add_document(
    content="Long document content...",
    document_type="text"
)
end_time = time.time()

print(f"Processing time: {end_time - start_time:.2f} seconds")
```

### Rate Limiting Issues

**Issue**: Hitting rate limits with external APIs.

**Solution**:
- Implement backoff and retry mechanisms
- Batch requests when possible
- Cache results to reduce API calls
- Use local alternatives when available:

```python
# Update configuration to use local alternatives
config.embedding.provider = "sentence_transformers"  # Local embedding
config.generation.provider = "ollama"  # Local LLM
```

## Logging and Debugging

### Enabling Debug Logging

To enable debug logging for troubleshooting:

```python
import logging

# Enable debug logging for all modules
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for specific modules
logging.getLogger("src.knowledge_base.core").setLevel(logging.DEBUG)
logging.getLogger("src.knowledge_base.storage").setLevel(logging.DEBUG)
logging.getLogger("src.knowledge_base.processing").setLevel(logging.DEBUG)
logging.getLogger("src.knowledge_base.retrieval").setLevel(logging.DEBUG)
logging.getLogger("src.knowledge_base.generation").setLevel(logging.DEBUG)
logging.getLogger("src.knowledge_base.agents").setLevel(logging.DEBUG)
logging.getLogger("src.knowledge_base.api").setLevel(logging.DEBUG)
```

### Logging to File

To log to a file for later analysis:

```python
import logging

# Configure file logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="knowledge_base.log",
    filemode="w"
)
```

### Using the Debug API

The system provides a debug API for troubleshooting:

```bash
# Get system status
curl -X GET "http://localhost:8000/admin/status" -H "X-API-Key: admin-key"

# Get system logs
curl -X GET "http://localhost:8000/admin/logs?level=debug&limit=100" -H "X-API-Key: admin-key"

# Get system metrics
curl -X GET "http://localhost:8000/admin/metrics" -H "X-API-Key: admin-key"
```

### Inspecting the Knowledge Base

To inspect the knowledge base for troubleshooting:

```python
# Get document count
document_count = await kb.storage.count()
print(f"Document count: {document_count}")

# Get chunk count
chunk_count = await kb.storage.count_chunks()
print(f"Chunk count: {chunk_count}")

# Get document by ID
document = await kb.get_document("doc_123456")
print(f"Document: {document}")

# Get chunks for document
chunks = await kb.get_chunks_for_document("doc_123456")
print(f"Chunks: {len(chunks)}")
```

## Common Error Messages

### "Provider not found"

**Issue**: The specified provider is not found.

**Solution**:
- Check provider name in configuration
- Ensure the provider is registered
- Verify that required packages are installed
- List available providers:

```python
from src.knowledge_base.core.registry import Registry

# List available providers
print("Vector stores:", Registry.list("vector_store"))
print("Embedders:", Registry.list("embedder"))
print("Chunkers:", Registry.list("chunker"))
print("Generation providers:", Registry.list("generation_provider"))
```

### "API key not found"

**Issue**: API key for external service is not found.

**Solution**:
- Check configuration for API key
- Set API key as environment variable
- Verify API key format
- Test with a known good API key:

```python
# Set API key in configuration
config.generation.openai.api_key = "your-api-key"

# Or set as environment variable
import os
os.environ["KB_GENERATION__OPENAI__API_KEY"] = "your-api-key"
```

### "Document not found"

**Issue**: Referenced document is not found.

**Solution**:
- Check document ID
- Verify document was added successfully
- Ensure storage provider is working correctly
- List available documents:

```python
# List documents
documents = await kb.list_documents(limit=10)
print(f"Documents: {len(documents)}")
for doc in documents:
    print(f"- {doc.id}: {doc.metadata}")
```

### "Invalid embedding dimension"

**Issue**: Embedding dimension is invalid.

**Solution**:
- Check embedding provider configuration
- Ensure embedding dimension matches the model
- Verify that embeddings are generated correctly
- Test with a known good configuration:

```python
# Update configuration
config.embedding.provider = "sentence_transformers"
config.embedding.model = "all-MiniLM-L6-v2"
config.embedding.dimension = 384  # Correct dimension for this model
```

## Maintenance Tasks

### Database Maintenance

To perform database maintenance:

```python
# Clear the knowledge base
await kb.clear()

# Compact the vector store (if supported)
if hasattr(kb.storage, "compact"):
    await kb.storage.compact()

# Rebuild indexes (if supported)
if hasattr(kb.storage, "rebuild_indexes"):
    await kb.storage.rebuild_indexes()
```

### Cache Maintenance

To manage caches:

```python
# Clear embedding cache
if hasattr(kb.processor.embedder, "clear_cache"):
    kb.processor.embedder.clear_cache()

# Clear retrieval cache
if hasattr(kb.retriever, "clear_cache"):
    kb.retriever.clear_cache()

# Clear generation cache
if hasattr(kb.generator, "clear_cache"):
    kb.generator.clear_cache()
```

### System Backup

To backup the system:

```python
# Backup memory store
if config.storage.provider == "memory":
    await kb.storage.save("backup.json")

# Backup configuration
config.save("config.backup.yaml")
```

### System Restore

To restore the system from backup:

```python
# Restore memory store
if config.storage.provider == "memory":
    await kb.storage.load("backup.json")

# Restore configuration
config = Config("config.backup.yaml")
```

## Conclusion

This troubleshooting guide covers common issues you might encounter when working with the Unified Knowledge Base System. If you encounter issues not covered in this guide, please refer to the other documentation files:

- [Architecture Documentation](architecture.md)
- [API Reference](api_reference.md)
- [Developer Guide](developer_guide.md)

For additional support, please:
- Check the issue tracker on GitHub
- Join the community forum
- Contact the development team
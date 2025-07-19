# Unified Knowledge Base System

A comprehensive knowledge management system that combines document storage, processing, retrieval, and generation capabilities in a cohesive platform. The system integrates a layered architecture with a multi-agent system to provide powerful knowledge management capabilities.

## Features

- **Multiple Storage Backends**: Support for in-memory, Notion, vector databases, and cloud storage
- **Flexible Document Processing**: Multiple chunking strategies and metadata extraction
- **Advanced Retrieval**: Semantic, keyword, and hybrid search with reranking
- **High-Quality Generation**: Support for multiple LLM providers with streaming responses
- **Multi-Agent Architecture**: Specialized agents for different aspects of knowledge management
- **Comprehensive API**: RESTful and WebSocket APIs for integration

## Documentation

### User Documentation

- [User Guide](docs/user_guide.md): Comprehensive guide to using the system
- [Quick Start Tutorial](docs/quick_start_tutorial.md): Step-by-step guide to getting started
- [Configuration Guide](docs/configuration_guide.md): Detailed information on configuration options
- [Best Practices Guide](docs/best_practices_guide.md): Recommendations for effective use
- [Troubleshooting Guide](docs/troubleshooting_guide.md): Solutions to common issues

### Technical Documentation

- [Architecture](docs/architecture.md): System architecture and design decisions
- [API Reference](docs/api_reference.md): Detailed API documentation
- [Developer Guide](docs/developer_guide.md): Guide for developers extending the system

## Installation

```bash
pip install unified-knowledge-base
```

Or install from source:

```bash
git clone https://github.com/yourusername/unified-knowledge-base.git
cd unified-knowledge-base
pip install -e .
```

## Quick Example

```python
from src.knowledge_base import KnowledgeBase
from src.knowledge_base.core.config import Config

# Initialize the knowledge base
config = Config()
kb = KnowledgeBase(config)

# Add a document
result = kb.add_document(
    content="This is a sample document for the knowledge base.",
    metadata={"title": "Sample Document", "source": "example"}
)
print(f"Added document with ID: {result.document_id}")

# Query the knowledge base
result = kb.query("What is in the sample document?")
print(f"Answer: {result.answer}")
print(f"Sources: {result.chunks}")
```

## API Server

Start the API server:

```bash
python -m src.knowledge_base.api.server
```

Access the API documentation at http://localhost:8000/docs

## Docker Deployment

The system can be easily deployed using Docker:

### Using docker-compose

```bash
# Build and start the containers
docker-compose up -d

# Stop the containers
docker-compose down
```

### Using the convenience script

```bash
# Build and start the containers
./scripts/docker_deployment.sh

# Stop the containers
docker stop knowledge-base
```

The API will be available at http://localhost:8000 with documentation at http://localhost:8000/docs

## Project Structure

```
src/knowledge_base/
├── core/               # Core components and interfaces
├── storage/            # Storage backends
├── processing/         # Document processing
├── retrieval/          # Search and retrieval
├── generation/         # Response generation
├── agents/             # Multi-agent system
└── api/                # API server
```

## Examples

Check out the `examples/` directory for more usage examples:

- `examples/quick_start.py`: Basic usage of the knowledge base
- `examples/api_server.py`: Starting the API server with custom configuration
- `examples/multi_agent_system.py`: Using the multi-agent system
- `examples/docker_deployment.sh`: Deploying with Docker

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
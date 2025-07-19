# Unified Knowledge Base System: Configuration Guide

This guide provides detailed information on configuring the Unified Knowledge Base System to meet your specific requirements.

## Configuration Overview

The system uses a YAML-based configuration file with environment variable overrides. The configuration is divided into several sections:

- **System**: General system settings
- **Storage**: Storage backend configuration
- **Embedding**: Embedding model configuration
- **Chunking**: Document chunking configuration
- **Retrieval**: Retrieval strategy configuration
- **Generation**: Text generation configuration
- **Agents**: Agent system configuration
- **API**: API server configuration

## Configuration File

The default configuration file location is `config.yaml` in the current directory. You can specify a different location using the `--config` command-line argument or the `KNOWLEDGE_BASE_CONFIG` environment variable.

### Example Configuration

```yaml
system:
  log_level: INFO
  cache_dir: ".cache"
  temp_dir: ".temp"

storage:
  provider: memory
  persistence_path: "kb_storage.pkl"
  
  # Notion-specific settings (when provider is "notion")
  notion:
    api_key: ""  # Set via NOTION_API_KEY env var
    database_id: ""
    
  # Vector database settings (when provider is "chroma", "pinecone", etc.)
  vector_db:
    host: "localhost"
    port: 8000
    collection_name: "knowledge_base"

embedding:
  provider: sentence_transformers
  model: all-MiniLM-L6-v2
  batch_size: 32
  cache_enabled: true
  
  # OpenAI-specific settings (when provider is "openai")
  openai:
    api_key: ""  # Set via OPENAI_API_KEY env var
    model: "text-embedding-ada-002"

chunking:
  strategy: recursive
  chunk_size: 1000
  chunk_overlap: 200
  min_chunk_size: 100
  max_chunk_size: 2000

retrieval:
  strategy: semantic
  top_k: 5
  reranking_enabled: true
  reranking_factor: 0.5
  cache_enabled: true
  cache_ttl: 3600

generation:
  provider: openai
  model: gpt-3.5-turbo
  temperature: 0.7
  max_tokens: 1000
  stream: true
  
  # OpenAI-specific settings
  openai:
    api_key: ""  # Set via OPENAI_API_KEY env var
    
  # DeepSeek-specific settings
  deepseek:
    api_key: ""  # Set via DEEPSEEK_API_KEY env var
    
  # SiliconFlow-specific settings
  siliconflow:
    api_key: ""  # Set via SILICONFLOW_API_KEY env var
    
  # Ollama-specific settings
  ollama:
    host: "localhost"
    port: 11434

agents:
  orchestrator:
    timeout: 60
  data_collection:
    batch_size: 10
  knowledge_processing:
    parallel_processing: true
    max_workers: 4
  knowledge_maintenance:
    schedule_interval: 86400  # 24 hours

api:
  host: "0.0.0.0"
  port: 8000
  cors_origins: ["*"]
  rate_limit: 100
  auth_enabled: false
  api_key: ""  # Set via API_KEY env var
```

## Environment Variables

You can override any configuration setting using environment variables. The format is:

```
KNOWLEDGE_BASE_{SECTION}_{KEY}
```

For example:

```bash
# Override storage provider
export KNOWLEDGE_BASE_STORAGE_PROVIDER=notion

# Override embedding model
export KNOWLEDGE_BASE_EMBEDDING_MODEL=all-mpnet-base-v2

# Override API port
export KNOWLEDGE_BASE_API_PORT=9000
```

## Storage Configuration

### Memory Storage

The simplest storage option, suitable for development and testing:

```yaml
storage:
  provider: memory
  persistence_path: "kb_storage.pkl"  # Optional, for persistence
```

### Notion Storage

For storing knowledge in Notion databases:

```yaml
storage:
  provider: notion
  notion:
    api_key: ""  # Set via NOTION_API_KEY env var
    database_id: "your_database_id"
    chunk_page_size: 100
    batch_size: 10
```

### Vector Database Storage

For efficient similarity search using vector databases:

#### Chroma

```yaml
storage:
  provider: chroma
  vector_db:
    host: "localhost"
    port: 8000
    collection_name: "knowledge_base"
    persist_directory: "./chroma_db"
```

#### Pinecone

```yaml
storage:
  provider: pinecone
  vector_db:
    api_key: ""  # Set via PINECONE_API_KEY env var
    environment: "us-west1-gcp"
    index_name: "knowledge-base"
```

#### Weaviate

```yaml
storage:
  provider: weaviate
  vector_db:
    url: "http://localhost:8080"
    api_key: ""  # Optional, set via WEAVIATE_API_KEY env var
    class_name: "KnowledgeBase"
```

### Cloud Storage

For storing documents in cloud storage:

#### Google Drive

```yaml
storage:
  provider: google_drive
  google_drive:
    credentials_file: "credentials.json"
    token_file: "token.json"
    folder_id: "your_folder_id"
```

#### OSS (Object Storage Service)

```yaml
storage:
  provider: oss
  oss:
    endpoint: "https://oss-cn-hangzhou.aliyuncs.com"
    access_key_id: ""  # Set via OSS_ACCESS_KEY_ID env var
    access_key_secret: ""  # Set via OSS_ACCESS_KEY_SECRET env var
    bucket_name: "knowledge-base"
```

## Embedding Configuration

### Sentence Transformers

```yaml
embedding:
  provider: sentence_transformers
  model: all-MiniLM-L6-v2
  batch_size: 32
  cache_enabled: true
```

### OpenAI

```yaml
embedding:
  provider: openai
  openai:
    api_key: ""  # Set via OPENAI_API_KEY env var
    model: "text-embedding-ada-002"
  batch_size: 32
  cache_enabled: true
```

### DeepSeek

```yaml
embedding:
  provider: deepseek
  deepseek:
    api_key: ""  # Set via DEEPSEEK_API_KEY env var
    model: "deepseek-embedding"
  batch_size: 32
  cache_enabled: true
```

### SiliconFlow

```yaml
embedding:
  provider: siliconflow
  siliconflow:
    api_key: ""  # Set via SILICONFLOW_API_KEY env var
    model: "siliconflow-embedding"
  batch_size: 32
  cache_enabled: true
```

## Chunking Configuration

### Recursive Chunking

```yaml
chunking:
  strategy: recursive
  chunk_size: 1000
  chunk_overlap: 200
  min_chunk_size: 100
  max_chunk_size: 2000
```

### Sentence Chunking

```yaml
chunking:
  strategy: sentence
  chunk_size: 5  # Number of sentences per chunk
  chunk_overlap: 1  # Number of overlapping sentences
```

### Paragraph Chunking

```yaml
chunking:
  strategy: paragraph
  max_paragraph_length: 1000
  chunk_overlap: 200
```

### Fixed Length Chunking

```yaml
chunking:
  strategy: fixed
  chunk_size: 1000
  chunk_overlap: 200
```

## Retrieval Configuration

### Semantic Retrieval

```yaml
retrieval:
  strategy: semantic
  top_k: 5
  reranking_enabled: true
  reranking_factor: 0.5
```

### Keyword Retrieval

```yaml
retrieval:
  strategy: keyword
  top_k: 5
  reranking_enabled: true
  reranking_factor: 0.5
```

### Hybrid Retrieval

```yaml
retrieval:
  strategy: hybrid
  top_k: 5
  semantic_weight: 0.7
  keyword_weight: 0.3
  reranking_enabled: true
  reranking_factor: 0.5
```

## Generation Configuration

### OpenAI

```yaml
generation:
  provider: openai
  model: gpt-3.5-turbo
  temperature: 0.7
  max_tokens: 1000
  stream: true
  openai:
    api_key: ""  # Set via OPENAI_API_KEY env var
```

### DeepSeek

```yaml
generation:
  provider: deepseek
  model: deepseek-chat
  temperature: 0.7
  max_tokens: 1000
  stream: true
  deepseek:
    api_key: ""  # Set via DEEPSEEK_API_KEY env var
```

### SiliconFlow

```yaml
generation:
  provider: siliconflow
  model: siliconflow-7b
  temperature: 0.7
  max_tokens: 1000
  stream: true
  siliconflow:
    api_key: ""  # Set via SILICONFLOW_API_KEY env var
```

### Ollama

```yaml
generation:
  provider: ollama
  model: llama2
  temperature: 0.7
  max_tokens: 1000
  stream: true
  ollama:
    host: "localhost"
    port: 11434
```

## Agent Configuration

```yaml
agents:
  orchestrator:
    timeout: 60
  data_collection:
    batch_size: 10
  knowledge_processing:
    parallel_processing: true
    max_workers: 4
  knowledge_maintenance:
    schedule_interval: 86400  # 24 hours
```

## API Configuration

```yaml
api:
  host: "0.0.0.0"
  port: 8000
  cors_origins: ["*"]
  rate_limit: 100
  auth_enabled: true
  api_key: ""  # Set via API_KEY env var
```

## Advanced Configuration

### Logging Configuration

```yaml
system:
  log_level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  log_file: "knowledge_base.log"
```

### Cache Configuration

```yaml
system:
  cache_dir: ".cache"
  cache_ttl: 3600  # 1 hour
  cache_max_size: 1000  # Maximum number of items in cache
```

### Performance Tuning

```yaml
system:
  max_workers: 4  # Number of worker threads
  batch_size: 32  # Default batch size for operations
  timeout: 30  # Default timeout in seconds
```

## Configuration Validation

The system validates your configuration on startup. If there are any issues, it will log errors and may fall back to default values. To validate your configuration without starting the system:

```bash
python -m knowledge_base.core.config --validate --config config.yaml
```

## Environment-Specific Configuration

You can create environment-specific configuration files:

- `config.dev.yaml`: Development environment
- `config.prod.yaml`: Production environment
- `config.test.yaml`: Testing environment

To use a specific environment configuration:

```bash
export KNOWLEDGE_BASE_ENV=prod
python -m knowledge_base.api.server
```

This will load `config.prod.yaml` instead of the default `config.yaml`.

## Configuration Best Practices

1. **Use environment variables for secrets**: Never store API keys or other secrets in the configuration file.
2. **Start with minimal configuration**: Begin with the minimal configuration needed and add settings as required.
3. **Use different configurations for different environments**: Create separate configuration files for development, testing, and production.
4. **Validate your configuration**: Always validate your configuration before deploying to production.
5. **Monitor resource usage**: Adjust batch sizes and worker counts based on your system's resources.
6. **Enable caching**: Use caching to improve performance, especially for embedding and retrieval operations.
7. **Tune chunking parameters**: Adjust chunk size and overlap based on your specific use case and document types.
#
# Docker Configuration

When running the system in Docker, you can configure it using environment variables in the `docker-compose.yml` file:

```yaml
services:
  api:
    # ... other settings ...
    environment:
      - KB_SYSTEM_LOG_LEVEL=INFO
      - KB_SYSTEM_DEBUG=false
      - KB_API_HOST=0.0.0.0
      - KB_API_PORT=8000
      - KB_API_CORS_ORIGINS=["*"]
      - KB_STORAGE_PROVIDER=memory
      # Add your API keys and other configuration here
      # - KB_GENERATION_API_KEY=your_api_key
```

### Using Configuration Files in Docker

You can also mount a configuration file into the container:

```yaml
services:
  api:
    # ... other settings ...
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./data:/app/data
```

### Environment Variables in Docker

The Docker setup uses the `KB_` prefix for environment variables instead of `KNOWLEDGE_BASE_`. For example:

- `KB_SYSTEM_LOG_LEVEL` instead of `KNOWLEDGE_BASE_SYSTEM_LOG_LEVEL`
- `KB_STORAGE_PROVIDER` instead of `KNOWLEDGE_BASE_STORAGE_PROVIDER`
- `KB_EMBEDDING_MODEL` instead of `KNOWLEDGE_BASE_EMBEDDING_MODEL`

### Docker Compose Services

The included `docker-compose.yml` file provides several services that can be enabled or disabled as needed:

1. **API Service**: The main Knowledge Base API service
2. **Chroma Service**: Vector database for efficient similarity search
3. **Ollama Service**: Local LLM support for generation

To enable optional services, uncomment their sections in the `docker-compose.yml` file.

### Docker Volumes

The Docker setup uses volumes to persist data:

```yaml
volumes:
  - ./data:/app/data  # Persists data across container restarts
```

You can customize the volume mappings to suit your needs.

### Docker Health Checks

The API service includes a health check to ensure it's running properly:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

This helps Docker automatically restart the service if it becomes unhealthy.
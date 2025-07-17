# Memory Storage Provider Guide

This guide explains how to use the MemoryVectorStore provider, including its persistence options.

## Overview

The MemoryVectorStore is an in-memory vector store implementation suitable for development, testing, and small datasets. It provides:

- Fast in-memory storage and retrieval
- Vector similarity search using cosine similarity
- Metadata filtering
- Document-based organization
- Optional persistence to disk

## Basic Usage

```python
from src.knowledge_base.core.config import Config, StorageConfig
from src.knowledge_base.storage.vector_store import VectorStore
from src.knowledge_base.core.types import Chunk
import asyncio

async def main():
    # Create configuration
    config = StorageConfig(
        provider="memory",
        max_chunks=10000
    )
    
    # Create vector store
    store = VectorStore(config)
    await store.initialize()
    
    # Add chunks
    chunks = [
        Chunk(
            id="chunk1",
            document_id="doc1",
            text="This is a test chunk",
            embedding=[0.1, 0.2, 0.3, 0.4],
            metadata={"source": "test"}
        )
    ]
    
    await store.add_chunks(chunks)
    
    # Search for similar chunks
    results = await store.search_similar([0.1, 0.2, 0.3, 0.4], top_k=5)
    
    # Close the store
    await store.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Persistence Options

The MemoryVectorStore supports persisting data to disk, which allows you to:

1. Save the current state of the vector store
2. Load the state when initializing a new instance
3. Configure automatic saving at regular intervals

### Enabling Persistence

```python
from src.knowledge_base.core.config import StorageConfig
from src.knowledge_base.storage.vector_store import VectorStore
import asyncio

async def main():
    # Create configuration with persistence enabled
    config = StorageConfig(
        provider="memory",
        max_chunks=10000,
        persistence_enabled=True,
        persistence_path="./kb_storage",
        auto_save=True,
        auto_save_interval=300  # Save every 5 minutes
    )
    
    # Create vector store
    store = VectorStore(config)
    await store.initialize()
    
    # Use the store...
    
    # Manually save data
    await store.save()
    
    # Close the store (will save data if auto_save is enabled)
    await store.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `persistence_enabled` | Enable/disable persistence | `False` |
| `persistence_path` | Directory to store persistence files | `"./kb_storage"` |
| `auto_save` | Enable/disable automatic saving | `False` |
| `auto_save_interval` | Interval between auto-saves (seconds) | `300` |

### Persistence Files

When persistence is enabled, the following files are created in the persistence directory:

- `chunks.json`: Contains all chunk data (without embeddings)
- `vectors.json`: Contains all vector embeddings
- `document_chunks.json`: Contains the document-to-chunks mapping
- `metadata_index.json`: Contains the metadata index
- `timestamp.txt`: Contains the timestamp of the last save

### Manual Save and Load

You can manually save and load data using the `save()` and `load()` methods:

```python
# Save data manually
await store.save()

# Load data manually (usually not needed as it's done during initialization)
await store.load()
```

## Performance Considerations

- The MemoryVectorStore is optimized for small to medium datasets (up to ~100,000 chunks)
- For larger datasets, consider using a dedicated vector database provider
- When using persistence, be aware that saving large datasets can be time-consuming
- The `use_numpy` option can be set to `True` to use NumPy for faster similarity calculations (requires NumPy to be installed)

## Example

See the `examples/memory_store_persistence_demo.py` file for a complete example of using the MemoryVectorStore with persistence.

## Testing

Unit tests for the MemoryVectorStore can be found in `tests/unit/storage/test_memory_vector_store.py`.
"""
Unit tests for the MemoryVectorStore class.

This module contains tests for the in-memory vector store implementation,
including persistence options.
"""

import os
import json
import shutil
import pytest
import asyncio
from typing import Dict, Any, List

from src.knowledge_base.core.types import Chunk
from src.knowledge_base.storage.providers.memory import MemoryVectorStore


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Create a test configuration."""
    return {
        "max_chunks": 1000,
        "persistence_enabled": False,
        "use_numpy": False  # Disable numpy for consistent testing
    }


@pytest.fixture
def persistence_config() -> Dict[str, Any]:
    """Create a configuration with persistence enabled."""
    return {
        "max_chunks": 1000,
        "persistence_enabled": True,
        "persistence_path": "./test_kb_storage",
        "auto_save": False,
        "use_numpy": False  # Disable numpy for consistent testing
    }


@pytest.fixture
def test_chunks() -> List[Chunk]:
    """Create test chunks."""
    return [
        Chunk(
            id="chunk1",
            document_id="doc1",
            text="This is the first test chunk",
            embedding=[0.1, 0.2, 0.3, 0.4],
            metadata={"source": "test", "page": 1}
        ),
        Chunk(
            id="chunk2",
            document_id="doc1",
            text="This is the second test chunk",
            embedding=[0.2, 0.3, 0.4, 0.5],
            metadata={"source": "test", "page": 2}
        ),
        Chunk(
            id="chunk3",
            document_id="doc2",
            text="This is a chunk from another document",
            embedding=[0.3, 0.4, 0.5, 0.6],
            metadata={"source": "other", "page": 1}
        )
    ]


@pytest.fixture
async def memory_store(test_config: Dict[str, Any]) -> MemoryVectorStore:
    """Create and initialize a memory vector store."""
    store = MemoryVectorStore(test_config)
    await store.initialize()
    return store


@pytest.fixture
async def persistence_store(persistence_config: Dict[str, Any]) -> MemoryVectorStore:
    """Create and initialize a memory vector store with persistence."""
    # Clean up any existing test data
    if os.path.exists(persistence_config["persistence_path"]):
        shutil.rmtree(persistence_config["persistence_path"])
    
    store = MemoryVectorStore(persistence_config)
    await store.initialize()
    
    yield store
    
    # Clean up after tests
    await store.close()
    if os.path.exists(persistence_config["persistence_path"]):
        shutil.rmtree(persistence_config["persistence_path"])


class TestMemoryVectorStore:
    """Tests for the MemoryVectorStore class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, memory_store: MemoryVectorStore):
        """Test that the store initializes correctly."""
        assert memory_store.is_initialized
        
        stats = await memory_store.get_stats()
        assert stats["total_chunks"] == 0
        assert stats["total_documents"] == 0
    
    @pytest.mark.asyncio
    async def test_add_chunks(self, memory_store: MemoryVectorStore, test_chunks: List[Chunk]):
        """Test adding chunks to the store."""
        result = await memory_store.add_chunks(test_chunks)
        assert result is True
        
        stats = await memory_store.get_stats()
        assert stats["total_chunks"] == 3
        assert stats["total_documents"] == 2
    
    @pytest.mark.asyncio
    async def test_get_chunk(self, memory_store: MemoryVectorStore, test_chunks: List[Chunk]):
        """Test retrieving a chunk by ID."""
        await memory_store.add_chunks(test_chunks)
        
        chunk = await memory_store.get_chunk("chunk1")
        assert chunk is not None
        assert chunk.id == "chunk1"
        assert chunk.text == "This is the first test chunk"
        
        # Test non-existent chunk
        chunk = await memory_store.get_chunk("non_existent")
        assert chunk is None
    
    @pytest.mark.asyncio
    async def test_search_similar(self, memory_store: MemoryVectorStore, test_chunks: List[Chunk]):
        """Test searching for similar vectors."""
        await memory_store.add_chunks(test_chunks)
        
        # Search with a vector similar to the first chunk
        results = await memory_store.search_similar([0.1, 0.2, 0.3, 0.4], top_k=2)
        assert len(results) == 2
        assert results[0]["chunk_id"] == "chunk1"  # Most similar should be first
        
        # Search with filters
        results = await memory_store.search_similar(
            [0.1, 0.2, 0.3, 0.4],
            filters={"source": "other"}
        )
        assert len(results) == 1
        assert results[0]["chunk_id"] == "chunk3"
    
    @pytest.mark.asyncio
    async def test_delete_chunks(self, memory_store: MemoryVectorStore, test_chunks: List[Chunk]):
        """Test deleting chunks by ID."""
        await memory_store.add_chunks(test_chunks)
        
        # Delete one chunk
        result = await memory_store.delete_chunks(["chunk1"])
        assert result is True
        
        # Verify it's deleted
        chunk = await memory_store.get_chunk("chunk1")
        assert chunk is None
        
        # Check stats
        stats = await memory_store.get_stats()
        assert stats["total_chunks"] == 2
    
    @pytest.mark.asyncio
    async def test_delete_document(self, memory_store: MemoryVectorStore, test_chunks: List[Chunk]):
        """Test deleting all chunks for a document."""
        await memory_store.add_chunks(test_chunks)
        
        # Delete document
        result = await memory_store.delete_document("doc1")
        assert result is True
        
        # Verify chunks are deleted
        chunk1 = await memory_store.get_chunk("chunk1")
        chunk2 = await memory_store.get_chunk("chunk2")
        assert chunk1 is None
        assert chunk2 is None
        
        # Check stats
        stats = await memory_store.get_stats()
        assert stats["total_chunks"] == 1
        assert stats["total_documents"] == 1
    
    @pytest.mark.asyncio
    async def test_clear(self, memory_store: MemoryVectorStore, test_chunks: List[Chunk]):
        """Test clearing all data from the store."""
        await memory_store.add_chunks(test_chunks)
        
        # Clear store
        result = await memory_store.clear()
        assert result is True
        
        # Check stats
        stats = await memory_store.get_stats()
        assert stats["total_chunks"] == 0
        assert stats["total_documents"] == 0
    
    @pytest.mark.asyncio
    async def test_persistence_save_load(self, persistence_store: MemoryVectorStore, test_chunks: List[Chunk]):
        """Test saving and loading data with persistence enabled."""
        # Add chunks
        await persistence_store.add_chunks(test_chunks)
        
        # Save data
        save_result = await persistence_store.save()
        assert save_result is True
        
        # Verify files were created
        persistence_path = persistence_store.config["persistence_path"]
        assert os.path.exists(os.path.join(persistence_path, "chunks.json"))
        assert os.path.exists(os.path.join(persistence_path, "vectors.json"))
        assert os.path.exists(os.path.join(persistence_path, "document_chunks.json"))
        assert os.path.exists(os.path.join(persistence_path, "metadata_index.json"))
        
        # Create a new store and load data
        new_store = MemoryVectorStore(persistence_store.config)
        await new_store.initialize()
        
        # Verify data was loaded
        stats = await new_store.get_stats()
        assert stats["total_chunks"] == 3
        assert stats["total_documents"] == 2
        
        # Verify chunk retrieval
        chunk = await new_store.get_chunk("chunk1")
        assert chunk is not None
        assert chunk.id == "chunk1"
        assert chunk.text == "This is the first test chunk"
        
        # Clean up
        await new_store.close()
    
    @pytest.mark.asyncio
    async def test_persistence_auto_save(self):
        """Test auto-save functionality."""
        # Create config with auto-save enabled
        config = {
            "max_chunks": 1000,
            "persistence_enabled": True,
            "persistence_path": "./test_kb_auto_save",
            "auto_save": True,
            "auto_save_interval": 0.1,  # Short interval for testing
            "use_numpy": False
        }
        
        # Clean up any existing test data
        if os.path.exists(config["persistence_path"]):
            shutil.rmtree(config["persistence_path"])
        
        # Create store
        store = MemoryVectorStore(config)
        await store.initialize()
        
        # Add chunks
        chunks = [
            Chunk(
                id="auto_chunk1",
                document_id="auto_doc1",
                text="Auto-save test chunk",
                embedding=[0.1, 0.2, 0.3, 0.4],
                metadata={"test": "auto-save"}
            )
        ]
        await store.add_chunks(chunks)
        
        # Wait for auto-save
        await asyncio.sleep(0.2)
        
        # Verify files were created
        persistence_path = config["persistence_path"]
        assert os.path.exists(os.path.join(persistence_path, "chunks.json"))
        
        # Clean up
        await store.close()
        if os.path.exists(config["persistence_path"]):
            shutil.rmtree(config["persistence_path"])
    
    @pytest.mark.asyncio
    async def test_persistence_clear(self, persistence_store: MemoryVectorStore, test_chunks: List[Chunk]):
        """Test that clearing the store also deletes persistence files."""
        # Add chunks and save
        await persistence_store.add_chunks(test_chunks)
        await persistence_store.save()
        
        # Clear store
        result = await persistence_store.clear()
        assert result is True
        
        # Verify files were deleted
        persistence_path = persistence_store.config["persistence_path"]
        assert not os.path.exists(os.path.join(persistence_path, "chunks.json"))
        
        # Check stats
        stats = await persistence_store.get_stats()
        assert stats["total_chunks"] == 0
        assert stats["total_documents"] == 0
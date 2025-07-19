"""
Unit tests for the NotionVectorStore class.

This module contains tests for the Notion vector store implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from src.knowledge_base.core.types import Chunk
from src.knowledge_base.storage.providers.notion import NotionVectorStore
from src.knowledge_base.core.exceptions import StorageError


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Create a test configuration."""
    return {
        "notion_api_key": "test_api_key",
        "notion_database_id": "test_database_id",
        "batch_size": 10,
        "retry_limit": 3,
        "retry_delay": 0.1
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
def mock_notion_client():
    """Create a mock Notion client."""
    client = MagicMock()
    
    # Mock databases.query
    query_response = {
        "results": [
            {
                "id": "page1",
                "properties": {
                    "chunk_id": {"rich_text": [{"plain_text": "chunk1"}]},
                    "document_id": {"rich_text": [{"plain_text": "doc1"}]},
                    "text": {"rich_text": [{"plain_text": "This is the first test chunk"}]},
                    "embedding": {"rich_text": [{"plain_text": "[0.1, 0.2, 0.3, 0.4]"}]},
                    "metadata": {"rich_text": [{"plain_text": '{"source": "test", "page": 1}'}]}
                }
            },
            {
                "id": "page2",
                "properties": {
                    "chunk_id": {"rich_text": [{"plain_text": "chunk2"}]},
                    "document_id": {"rich_text": [{"plain_text": "doc1"}]},
                    "text": {"rich_text": [{"plain_text": "This is the second test chunk"}]},
                    "embedding": {"rich_text": [{"plain_text": "[0.2, 0.3, 0.4, 0.5]"}]},
                    "metadata": {"rich_text": [{"plain_text": '{"source": "test", "page": 2}'}]}
                }
            }
        ],
        "has_more": False,
        "next_cursor": None
    }
    client.databases.query = AsyncMock(return_value=query_response)
    
    # Mock pages.create
    client.pages.create = AsyncMock(return_value={"id": "new_page_id"})
    
    # Mock pages.update
    client.pages.update = AsyncMock(return_value={"id": "updated_page_id"})
    
    # Mock blocks.delete
    client.blocks.delete = AsyncMock(return_value={"id": "deleted_page_id"})
    
    return client


@pytest.fixture
@patch("src.knowledge_base.storage.providers.notion.AsyncClient")
async def notion_store(mock_async_client, test_config, mock_notion_client):
    """Create and initialize a Notion vector store."""
    # Configure AsyncClient mock
    mock_async_client.return_value = mock_notion_client
    
    # Create store
    store = NotionVectorStore(test_config)
    await store.initialize()
    
    return store


class TestNotionVectorStore:
    """Tests for the NotionVectorStore class."""
    
    @pytest.mark.asyncio
    @patch("src.knowledge_base.storage.providers.notion.AsyncClient")
    async def test_initialization(self, mock_async_client, test_config, mock_notion_client):
        """Test that the store initializes correctly."""
        # Configure AsyncClient mock
        mock_async_client.return_value = mock_notion_client
        
        # Create store
        store = NotionVectorStore(test_config)
        await store.initialize()
        
        # Verify initialization
        assert store.is_initialized
        assert store.client == mock_notion_client
        mock_async_client.assert_called_once_with(auth=test_config["notion_api_key"])
    
    @pytest.mark.asyncio
    async def test_add_chunks(self, notion_store, test_chunks, mock_notion_client):
        """Test adding chunks to the store."""
        # Add chunks
        result = await notion_store.add_chunks(test_chunks)
        
        # Verify result
        assert result is True
        
        # Verify pages.create was called for each chunk
        assert mock_notion_client.pages.create.call_count == len(test_chunks)
    
    @pytest.mark.asyncio
    async def test_get_chunk(self, notion_store, mock_notion_client):
        """Test retrieving a chunk by ID."""
        # Get chunk
        chunk = await notion_store.get_chunk("chunk1")
        
        # Verify query was called
        mock_notion_client.databases.query.assert_called_once()
        
        # Verify chunk data
        assert chunk is not None
        assert chunk.id == "chunk1"
        assert chunk.document_id == "doc1"
        assert chunk.text == "This is the first test chunk"
        assert chunk.embedding == [0.1, 0.2, 0.3, 0.4]
        assert chunk.metadata == {"source": "test", "page": 1}
        
        # Test non-existent chunk
        mock_notion_client.databases.query.reset_mock()
        mock_notion_client.databases.query.return_value = {"results": [], "has_more": False}
        
        chunk = await notion_store.get_chunk("non_existent")
        assert chunk is None
    
    @pytest.mark.asyncio
    async def test_search_similar(self, notion_store, mock_notion_client):
        """Test searching for similar vectors."""
        # Search for similar chunks
        results = await notion_store.search_similar([0.1, 0.2, 0.3, 0.4], top_k=2)
        
        # Verify query was called
        mock_notion_client.databases.query.assert_called_once()
        
        # Verify results
        assert len(results) == 2
        assert results[0]["chunk_id"] == "chunk1"
        assert results[1]["chunk_id"] == "chunk2"
        
        # Test with filters
        mock_notion_client.databases.query.reset_mock()
        
        await notion_store.search_similar([0.1, 0.2, 0.3, 0.4], filters={"source": "test"})
        
        # Verify query was called with filters
        mock_notion_client.databases.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_chunks(self, notion_store, mock_notion_client):
        """Test deleting chunks by ID."""
        # Delete chunks
        result = await notion_store.delete_chunks(["chunk1", "chunk2"])
        
        # Verify result
        assert result is True
        
        # Verify query and delete were called
        assert mock_notion_client.databases.query.call_count == 2  # Once for each chunk
        assert mock_notion_client.blocks.delete.call_count == 2  # Once for each chunk
    
    @pytest.mark.asyncio
    async def test_delete_document(self, notion_store, mock_notion_client):
        """Test deleting all chunks for a document."""
        # Delete document
        result = await notion_store.delete_document("doc1")
        
        # Verify result
        assert result is True
        
        # Verify query and delete were called
        mock_notion_client.databases.query.assert_called_once()
        assert mock_notion_client.blocks.delete.call_count == 2  # Once for each chunk in doc1
    
    @pytest.mark.asyncio
    async def test_clear(self, notion_store, mock_notion_client):
        """Test clearing all data from the store."""
        # Clear store
        result = await notion_store.clear()
        
        # Verify result
        assert result is True
        
        # Verify query and delete were called
        mock_notion_client.databases.query.assert_called_once()
        assert mock_notion_client.blocks.delete.call_count == 2  # Once for each chunk
    
    @pytest.mark.asyncio
    @patch("src.knowledge_base.storage.providers.notion.AsyncClient")
    async def test_error_handling(self, mock_async_client, test_config):
        """Test error handling during initialization."""
        # Configure AsyncClient to raise an exception
        mock_async_client.side_effect = Exception("API error")
        
        # Create store
        store = NotionVectorStore(test_config)
        
        # Initialize and expect error
        with pytest.raises(StorageError):
            await store.initialize()
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, notion_store, mock_notion_client):
        """Test batch processing of chunks."""
        # Create many chunks
        many_chunks = []
        for i in range(25):  # More than batch_size
            many_chunks.append(
                Chunk(
                    id=f"chunk{i}",
                    document_id="doc1",
                    text=f"Test chunk {i}",
                    embedding=[0.1, 0.2, 0.3, 0.4],
                    metadata={"index": i}
                )
            )
        
        # Add chunks
        result = await notion_store.add_chunks(many_chunks)
        
        # Verify result
        assert result is True
        
        # Verify pages.create was called for each chunk
        assert mock_notion_client.pages.create.call_count == len(many_chunks)
    
    @pytest.mark.asyncio
    async def test_retry_logic(self, notion_store, test_chunks, mock_notion_client):
        """Test retry logic for API calls."""
        # Configure pages.create to fail once then succeed
        fail_count = [0]
        original_create = mock_notion_client.pages.create
        
        async def mock_create_with_retry(*args, **kwargs):
            if fail_count[0] < 1:
                fail_count[0] += 1
                raise Exception("Temporary API error")
            return await original_create(*args, **kwargs)
        
        mock_notion_client.pages.create = mock_create_with_retry
        
        # Add chunks
        result = await notion_store.add_chunks([test_chunks[0]])
        
        # Verify result
        assert result is True
        
        # Verify retry worked
        assert fail_count[0] == 1
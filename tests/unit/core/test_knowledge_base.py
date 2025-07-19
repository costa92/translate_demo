"""
Tests for the KnowledgeBase class in the core module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_base.core.knowledge_base import KnowledgeBase
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import Document, TextChunk, QueryResult, AddResult
from src.knowledge_base.core.exceptions import KnowledgeBaseError


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = MagicMock(spec=Config)
    config.storage.provider = "memory"
    config.embedding.provider = "sentence_transformers"
    config.chunking.strategy = "recursive"
    config.retrieval.strategy = "hybrid"
    config.generation.provider = "simple"
    return config


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = AsyncMock()
    store.initialize = AsyncMock()
    store.add_texts = AsyncMock(return_value=["chunk1", "chunk2"])
    store.similarity_search = AsyncMock(return_value=[
        (TextChunk(id="chunk1", text="Test chunk 1", document_id="doc1", metadata={}), 0.9),
        (TextChunk(id="chunk2", text="Test chunk 2", document_id="doc1", metadata={}), 0.8)
    ])
    store.delete = AsyncMock(return_value=True)
    store.clear = AsyncMock(return_value=True)
    return store


@pytest.fixture
def mock_processor():
    """Create a mock document processor."""
    processor = MagicMock()
    processor.process_document = AsyncMock(return_value=[
        TextChunk(id="chunk1", text="Test chunk 1", document_id="doc1", metadata={}),
        TextChunk(id="chunk2", text="Test chunk 2", document_id="doc1", metadata={})
    ])
    return processor


@pytest.fixture
def mock_retriever():
    """Create a mock retriever."""
    retriever = MagicMock()
    retriever.retrieve = AsyncMock(return_value=[
        TextChunk(id="chunk1", text="Test chunk 1", document_id="doc1", metadata={}),
        TextChunk(id="chunk2", text="Test chunk 2", document_id="doc1", metadata={})
    ])
    return retriever


@pytest.fixture
def mock_generator():
    """Create a mock generator."""
    generator = MagicMock()
    generator.generate = AsyncMock(return_value="Generated answer")
    return generator


@pytest.fixture
@patch("src.knowledge_base.core.knowledge_base.Factory")
def knowledge_base(mock_factory, mock_config, mock_vector_store, mock_processor, mock_retriever, mock_generator):
    """Create a KnowledgeBase instance with mocked dependencies."""
    # Configure factory mock
    mock_factory.create_component.side_effect = lambda component_type, provider, config, **kwargs: {
        "vector_store": mock_vector_store,
        "processor": mock_processor,
        "retriever": mock_retriever,
        "generator": mock_generator
    }[component_type]
    
    # Create knowledge base
    kb = KnowledgeBase(mock_config)
    return kb


class TestKnowledgeBase:
    """Tests for the KnowledgeBase class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, knowledge_base, mock_vector_store):
        """Test that the knowledge base initializes correctly."""
        await knowledge_base.initialize()
        
        # Verify vector store initialization
        mock_vector_store.initialize.assert_called_once()
        assert knowledge_base.is_initialized
    
    @pytest.mark.asyncio
    async def test_add_document(self, knowledge_base, mock_processor, mock_vector_store):
        """Test adding a document to the knowledge base."""
        # Initialize knowledge base
        await knowledge_base.initialize()
        
        # Create test document
        document = Document(id="doc1", content="Test document content", type="text", metadata={})
        
        # Add document
        result = await knowledge_base.add_document(document)
        
        # Verify document processing
        mock_processor.process_document.assert_called_once_with(document)
        
        # Verify chunks were added to vector store
        mock_vector_store.add_texts.assert_called_once()
        
        # Verify result
        assert isinstance(result, AddResult)
        assert result.document_id == "doc1"
        assert len(result.chunk_ids) == 2
        assert result.success
    
    @pytest.mark.asyncio
    async def test_query(self, knowledge_base, mock_retriever, mock_generator):
        """Test querying the knowledge base."""
        # Initialize knowledge base
        await knowledge_base.initialize()
        
        # Query knowledge base
        result = await knowledge_base.query("Test query")
        
        # Verify retrieval
        mock_retriever.retrieve.assert_called_once_with("Test query", None, None)
        
        # Verify generation
        mock_generator.generate.assert_called_once()
        
        # Verify result
        assert isinstance(result, QueryResult)
        assert result.query == "Test query"
        assert result.answer == "Generated answer"
        assert len(result.chunks) == 2
    
    @pytest.mark.asyncio
    async def test_query_with_filter(self, knowledge_base, mock_retriever):
        """Test querying with filters."""
        # Initialize knowledge base
        await knowledge_base.initialize()
        
        # Create filter
        filter_dict = {"source": "test"}
        
        # Query with filter
        await knowledge_base.query("Test query", filter=filter_dict)
        
        # Verify retrieval with filter
        mock_retriever.retrieve.assert_called_once_with("Test query", None, filter_dict)
    
    @pytest.mark.asyncio
    async def test_delete_document(self, knowledge_base, mock_vector_store):
        """Test deleting a document from the knowledge base."""
        # Initialize knowledge base
        await knowledge_base.initialize()
        
        # Delete document
        result = await knowledge_base.delete_document("doc1")
        
        # Verify deletion
        mock_vector_store.delete_document.assert_called_once_with("doc1")
        assert result
    
    @pytest.mark.asyncio
    async def test_clear(self, knowledge_base, mock_vector_store):
        """Test clearing the knowledge base."""
        # Initialize knowledge base
        await knowledge_base.initialize()
        
        # Clear knowledge base
        result = await knowledge_base.clear()
        
        # Verify clearing
        mock_vector_store.clear.assert_called_once()
        assert result
    
    @pytest.mark.asyncio
    async def test_error_handling(self, knowledge_base, mock_processor):
        """Test error handling during document processing."""
        # Initialize knowledge base
        await knowledge_base.initialize()
        
        # Configure processor to raise an exception
        mock_processor.process_document.side_effect = Exception("Processing error")
        
        # Create test document
        document = Document(id="doc1", content="Test document content", type="text", metadata={})
        
        # Add document and expect error
        result = await knowledge_base.add_document(document)
        
        # Verify error handling
        assert not result.success
        assert "Processing error" in result.error
    
    @pytest.mark.asyncio
    async def test_not_initialized_error(self, knowledge_base):
        """Test error when using knowledge base before initialization."""
        # Create test document
        document = Document(id="doc1", content="Test document content", type="text", metadata={})
        
        # Attempt operations before initialization
        with pytest.raises(KnowledgeBaseError):
            await knowledge_base.add_document(document)
        
        with pytest.raises(KnowledgeBaseError):
            await knowledge_base.query("Test query")
        
        with pytest.raises(KnowledgeBaseError):
            await knowledge_base.delete_document("doc1")
        
        with pytest.raises(KnowledgeBaseError):
            await knowledge_base.clear()
    
    @pytest.mark.asyncio
    async def test_close(self, knowledge_base, mock_vector_store):
        """Test closing the knowledge base."""
        # Initialize knowledge base
        await knowledge_base.initialize()
        
        # Close knowledge base
        await knowledge_base.close()
        
        # Verify vector store was closed
        mock_vector_store.close.assert_called_once()
        assert not knowledge_base.is_initialized
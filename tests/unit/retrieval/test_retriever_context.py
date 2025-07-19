"""
Unit tests for the retriever with context management.
"""

import unittest
import asyncio
from unittest.mock import MagicMock, patch

from src.knowledge_base.core.config import Config, RetrievalConfig
from src.knowledge_base.core.types import TextChunk, RetrievalResult, SearchQuery
from src.knowledge_base.retrieval.retriever import Retriever
from src.knowledge_base.retrieval.context_manager import ContextManager


class TestRetrieverWithContext(unittest.TestCase):
    """Test cases for the Retriever class with context management."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock config
        retrieval_config = RetrievalConfig(
            strategy="semantic",
            max_context_length=1000,
            context_window=3,
            cache_enabled=True,
            cache_ttl=3600
        )
        self.config = MagicMock(spec=Config)
        self.config.retrieval = retrieval_config
        
        # Create mock vector store
        self.vector_store = MagicMock()
        
        # Create mock strategy
        self.strategy = MagicMock()
        
        # Create test chunks
        self.chunk1 = TextChunk(
            id="chunk1",
            text="This is the first chunk",
            document_id="doc1",
            metadata={"source": "test"}
        )
        
        self.chunk2 = TextChunk(
            id="chunk2",
            text="This is the second chunk",
            document_id="doc1",
            metadata={"source": "test"}
        )
        
        # Create retriever with mocked strategy
        with patch('src.knowledge_base.retrieval.retriever.Retriever._create_strategy', return_value=self.strategy):
            with patch('src.knowledge_base.retrieval.retriever.Retriever._create_reranker', return_value=None):
                self.retriever = Retriever(self.config, self.vector_store)
    
    def test_create_conversation(self):
        """Test creating a conversation."""
        conversation_id = self.retriever.create_conversation({"user_id": "test_user"})
        self.assertIsNotNone(conversation_id)
        self.assertIn(conversation_id, self.retriever.context_manager.conversations)
    
    def test_get_conversation_context(self):
        """Test getting conversation context."""
        # Create a conversation
        conversation_id = self.retriever.create_conversation()
        
        # Add a turn manually
        turn = self.retriever.context_manager.add_query(conversation_id, "What is the capital of France?")
        self.retriever.context_manager.update_turn(
            conversation_id,
            turn.turn_id,
            answer="The capital of France is Paris."
        )
        
        # Get context
        context = self.retriever.get_conversation_context(conversation_id)
        
        self.assertEqual(len(context), 1)
        self.assertEqual(context[0]["query"], "What is the capital of France?")
        self.assertEqual(context[0]["answer"], "The capital of France is Paris?")
    
    def test_delete_conversation(self):
        """Test deleting a conversation."""
        # Create a conversation
        conversation_id = self.retriever.create_conversation()
        
        # Delete it
        success = self.retriever.delete_conversation(conversation_id)
        self.assertTrue(success)
        self.assertNotIn(conversation_id, self.retriever.context_manager.conversations)
    
    def test_retrieve_with_conversation(self):
        """Test retrieving with conversation context."""
        # Mock strategy retrieve method
        async def mock_retrieve(*args, **kwargs):
            return [(self.chunk1, 0.9), (self.chunk2, 0.8)]
        
        self.strategy.retrieve = mock_retrieve
        
        # Create a conversation
        conversation_id = self.retriever.create_conversation()
        
        # Run retrieve with conversation context
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(
            self.retriever.retrieve("What is the capital of France?", conversation_id=conversation_id)
        )
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].chunk.id, "chunk1")
        
        # Check that the turn was added to the conversation
        conversation = self.retriever.context_manager.get_conversation(conversation_id)
        self.assertEqual(len(conversation.turns), 1)
        self.assertEqual(conversation.turns[0].query, "What is the capital of France?")
        self.assertEqual(len(conversation.turns[0].sources), 2)
    
    def test_retrieve_with_conversation_cache(self):
        """Test retrieving with conversation context and cache."""
        # Mock strategy retrieve method
        async def mock_retrieve(*args, **kwargs):
            return [(self.chunk1, 0.9), (self.chunk2, 0.8)]
        
        self.strategy.retrieve = mock_retrieve
        
        # Create a conversation
        conversation_id = self.retriever.create_conversation()
        
        # Run retrieve with conversation context
        loop = asyncio.get_event_loop()
        results1 = loop.run_until_complete(
            self.retriever.retrieve("What is the capital of France?", conversation_id=conversation_id)
        )
        
        # Run the same query again (should hit cache)
        with patch.object(self.strategy, 'retrieve', side_effect=mock_retrieve) as mock_method:
            results2 = loop.run_until_complete(
                self.retriever.retrieve("What is the capital of France?", conversation_id=conversation_id)
            )
            # Strategy's retrieve should not be called again
            mock_method.assert_not_called()
        
        # Check results
        self.assertEqual(len(results2), 2)
        self.assertEqual(results2[0].chunk.id, "chunk1")
        
        # Check that only one turn was added to the conversation
        conversation = self.retriever.context_manager.get_conversation(conversation_id)
        self.assertEqual(len(conversation.turns), 2)


if __name__ == "__main__":
    unittest.main()
"""
Unit tests for the context manager module.
"""

import unittest
import tempfile
import os
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# Mock the dependencies to avoid import issues
class MockConfig:
    def __init__(self):
        self.retrieval = MockRetrievalConfig()

class MockRetrievalConfig:
    def __init__(self):
        self.max_context_length = 1000
        self.context_window = 3
        self.cache_enabled = True
        self.cache_ttl = 3600

# Import the module under test directly
import sys
import os.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.knowledge_base.retrieval.context_manager import ContextManager, Conversation, ConversationTurn

# Create mock classes for dependencies
@dataclass
class MockTextChunk:
    id: str
    text: str
    document_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MockRetrievalResult:
    chunk: MockTextChunk
    score: float
    rank: int = 0


class TestContextManager(unittest.TestCase):
    """Test cases for the ContextManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock config
        self.config = MockConfig()
        
        # Create a context manager
        self.context_manager = ContextManager(self.config)
        
        # Create a test conversation
        self.conversation = self.context_manager.create_conversation({"user_id": "test_user"})
        
        # Create some test chunks and retrieval results
        self.chunk1 = MockTextChunk(
            id="chunk1",
            text="This is the first chunk",
            document_id="doc1",
            metadata={"source": "test"}
        )
        
        self.chunk2 = MockTextChunk(
            id="chunk2",
            text="This is the second chunk",
            document_id="doc1",
            metadata={"source": "test"}
        )
        
        self.result1 = MockRetrievalResult(chunk=self.chunk1, score=0.9, rank=0)
        self.result2 = MockRetrievalResult(chunk=self.chunk2, score=0.8, rank=1)
    
    def test_create_conversation(self):
        """Test creating a new conversation."""
        conversation = self.context_manager.create_conversation({"user_id": "user1"})
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.metadata["user_id"], "user1")
        self.assertIn(conversation.id, self.context_manager.conversations)
    
    def test_get_conversation(self):
        """Test retrieving a conversation by ID."""
        # Get existing conversation
        conversation = self.context_manager.get_conversation(self.conversation.id)
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.id, self.conversation.id)
        
        # Get non-existent conversation
        conversation = self.context_manager.get_conversation("non_existent_id")
        self.assertIsNone(conversation)
    
    def test_add_query(self):
        """Test adding a query to a conversation."""
        # Add query to existing conversation
        turn = self.context_manager.add_query(self.conversation.id, "What is the capital of France?")
        self.assertIsNotNone(turn)
        self.assertEqual(turn.query, "What is the capital of France?")
        self.assertEqual(len(self.conversation.turns), 1)
        
        # Add query to non-existent conversation
        turn = self.context_manager.add_query("non_existent_id", "What is the capital of Germany?")
        self.assertIsNone(turn)
    
    def test_update_turn(self):
        """Test updating a conversation turn."""
        # Add a query
        turn = self.context_manager.add_query(self.conversation.id, "What is the capital of France?")
        
        # Update the turn
        updated_turn = self.context_manager.update_turn(
            self.conversation.id,
            turn.turn_id,
            answer="The capital of France is Paris.",
            sources=[self.result1, self.result2]
        )
        
        self.assertIsNotNone(updated_turn)
        self.assertEqual(updated_turn.answer, "The capital of France is Paris.")
        self.assertEqual(len(updated_turn.sources), 2)
        self.assertEqual(updated_turn.sources[0].chunk.id, "chunk1")
        
        # Update non-existent turn
        updated_turn = self.context_manager.update_turn(
            self.conversation.id,
            "non_existent_turn_id",
            answer="This should not work."
        )
        self.assertIsNone(updated_turn)
        
        # Update turn in non-existent conversation
        updated_turn = self.context_manager.update_turn(
            "non_existent_id",
            turn.turn_id,
            answer="This should not work either."
        )
        self.assertIsNone(updated_turn)
    
    def test_get_context_no_compression(self):
        """Test getting conversation context without compression."""
        # Add some turns
        turn1 = self.context_manager.add_query(self.conversation.id, "What is the capital of France?")
        self.context_manager.update_turn(
            self.conversation.id,
            turn1.turn_id,
            answer="The capital of France is Paris."
        )
        
        turn2 = self.context_manager.add_query(self.conversation.id, "What is the population of Paris?")
        self.context_manager.update_turn(
            self.conversation.id,
            turn2.turn_id,
            answer="The population of Paris is about 2.2 million."
        )
        
        # Get context
        context, compressed = self.context_manager.get_context(self.conversation.id)
        
        self.assertEqual(len(context), 2)
        self.assertFalse(compressed)
        self.assertEqual(context[1].query, "What is the population of Paris?")
        self.assertEqual(context[0].query, "What is the capital of France?")
    
    def test_get_context_with_compression(self):
        """Test getting conversation context with compression."""
        # Override max_context_length to force compression
        self.context_manager.max_context_length = 100
        
        # Add some turns with long content
        turn1 = self.context_manager.add_query(self.conversation.id, "What is the capital of France?" + "A" * 50)
        self.context_manager.update_turn(
            self.conversation.id,
            turn1.turn_id,
            answer="The capital of France is Paris." + "B" * 50
        )
        
        turn2 = self.context_manager.add_query(self.conversation.id, "What is the population of Paris?")
        self.context_manager.update_turn(
            self.conversation.id,
            turn2.turn_id,
            answer="The population of Paris is about 2.2 million."
        )
        
        # Get context
        context, compressed = self.context_manager.get_context(self.conversation.id)
        
        self.assertEqual(len(context), 2)
        self.assertTrue(compressed)
        self.assertEqual(context[1].query, "What is the population of Paris?")
        self.assertTrue(len(context[0].query) < 100)
        self.assertTrue("..." in context[0].query or "..." in context[0].answer)
    
    def test_context_window_limit(self):
        """Test that context window limits the number of turns."""
        # Set context window to 2
        self.context_manager.context_window = 2
        
        # Add 3 turns
        turn1 = self.context_manager.add_query(self.conversation.id, "Turn 1")
        self.context_manager.update_turn(self.conversation.id, turn1.turn_id, answer="Answer 1")
        
        turn2 = self.context_manager.add_query(self.conversation.id, "Turn 2")
        self.context_manager.update_turn(self.conversation.id, turn2.turn_id, answer="Answer 2")
        
        turn3 = self.context_manager.add_query(self.conversation.id, "Turn 3")
        self.context_manager.update_turn(self.conversation.id, turn3.turn_id, answer="Answer 3")
        
        # Get context
        context, compressed = self.context_manager.get_context(self.conversation.id)
        
        # Should only get the 2 most recent turns
        self.assertEqual(len(context), 2)
        self.assertEqual(context[0].query, "Turn 2")
        self.assertEqual(context[1].query, "Turn 3")
    
    def test_save_and_load_conversation(self):
        """Test saving and loading a conversation."""
        # Add a turn
        turn = self.context_manager.add_query(self.conversation.id, "What is the capital of France?")
        self.context_manager.update_turn(
            self.conversation.id,
            turn.turn_id,
            answer="The capital of France is Paris.",
            sources=[self.result1]
        )
        
        # Save the conversation
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        success = self.context_manager.save_conversation(self.conversation.id, temp_path)
        self.assertTrue(success)
        
        # Load the conversation
        self.context_manager.conversations = {}  # Clear existing conversations
        loaded_conversation = self.context_manager.load_conversation(temp_path)
        
        self.assertIsNotNone(loaded_conversation)
        self.assertEqual(loaded_conversation.id, self.conversation.id)
        self.assertEqual(len(loaded_conversation.turns), 1)
        self.assertEqual(loaded_conversation.turns[0].query, "What is the capital of France?")
        self.assertEqual(loaded_conversation.turns[0].answer, "The capital of France is Paris.")
        
        # Clean up
        os.unlink(temp_path)
    
    def test_delete_conversation(self):
        """Test deleting a conversation."""
        # Delete existing conversation
        success = self.context_manager.delete_conversation(self.conversation.id)
        self.assertTrue(success)
        self.assertNotIn(self.conversation.id, self.context_manager.conversations)
        
        # Delete non-existent conversation
        success = self.context_manager.delete_conversation("non_existent_id")
        self.assertFalse(success)
    
    def test_enhance_query(self):
        """Test enhancing a query with context."""
        # This is a simple test since the current implementation doesn't modify the query
        enhanced_query = self.context_manager.enhance_query(self.conversation.id, "What is its population?")
        self.assertEqual(enhanced_query, "What is its population?")


class TestConversation(unittest.TestCase):
    """Test cases for the Conversation class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.conversation = Conversation(id="test_conversation")
        
        # Create a test chunk and retrieval result
        self.chunk = MockTextChunk(
            id="chunk1",
            text="This is a test chunk",
            document_id="doc1",
            metadata={"source": "test"}
        )
        
        self.result = MockRetrievalResult(chunk=self.chunk, score=0.9, rank=0)
    
    def test_add_turn(self):
        """Test adding a turn to a conversation."""
        turn = self.conversation.add_turn("What is the capital of France?")
        self.assertIsNotNone(turn)
        self.assertEqual(turn.query, "What is the capital of France?")
        self.assertEqual(len(self.conversation.turns), 1)
    
    def test_update_turn(self):
        """Test updating a turn in a conversation."""
        # Add a turn
        turn = self.conversation.add_turn("What is the capital of France?")
        
        # Update the turn
        updated_turn = self.conversation.update_turn(
            turn.turn_id,
            answer="The capital of France is Paris.",
            sources=[self.result]
        )
        
        self.assertIsNotNone(updated_turn)
        self.assertEqual(updated_turn.answer, "The capital of France is Paris.")
        self.assertEqual(len(updated_turn.sources), 1)
        
        # Update non-existent turn
        updated_turn = self.conversation.update_turn(
            "non_existent_turn_id",
            answer="This should not work."
        )
        self.assertIsNone(updated_turn)
    
    def test_get_last_turn(self):
        """Test getting the last turn in a conversation."""
        # Empty conversation
        last_turn = self.conversation.get_last_turn()
        self.assertIsNone(last_turn)
        
        # Add some turns
        turn1 = self.conversation.add_turn("Turn 1")
        turn2 = self.conversation.add_turn("Turn 2")
        
        # Get last turn
        last_turn = self.conversation.get_last_turn()
        self.assertEqual(last_turn.query, "Turn 2")
    
    def test_get_recent_turns(self):
        """Test getting recent turns from a conversation."""
        # Add some turns
        turn1 = self.conversation.add_turn("Turn 1")
        turn2 = self.conversation.add_turn("Turn 2")
        turn3 = self.conversation.add_turn("Turn 3")
        
        # Get recent turns
        recent_turns = self.conversation.get_recent_turns(2)
        self.assertEqual(len(recent_turns), 2)
        self.assertEqual(recent_turns[0].query, "Turn 2")
        self.assertEqual(recent_turns[1].query, "Turn 3")
        
        # Get all turns
        all_turns = self.conversation.get_recent_turns(5)
        self.assertEqual(len(all_turns), 3)
        
        # Get no turns
        no_turns = self.conversation.get_recent_turns(0)
        self.assertEqual(len(no_turns), 0)
    
    def test_to_dict_and_from_dict(self):
        """Test converting a conversation to and from a dictionary."""
        # Add a turn
        turn = self.conversation.add_turn("What is the capital of France?")
        self.conversation.update_turn(
            turn.turn_id,
            answer="The capital of France is Paris.",
            sources=[self.result]
        )
        
        # Convert to dictionary
        conversation_dict = self.conversation.to_dict()
        
        # Check dictionary structure
        self.assertEqual(conversation_dict["id"], "test_conversation")
        self.assertEqual(len(conversation_dict["turns"]), 1)
        self.assertEqual(conversation_dict["turns"][0]["query"], "What is the capital of France?")
        self.assertEqual(conversation_dict["turns"][0]["answer"], "The capital of France is Paris.")
        
        # Convert back to Conversation
        new_conversation = Conversation.from_dict(conversation_dict)
        
        # Check the new conversation
        self.assertEqual(new_conversation.id, "test_conversation")
        self.assertEqual(len(new_conversation.turns), 1)
        self.assertEqual(new_conversation.turns[0].query, "What is the capital of France?")
        self.assertEqual(new_conversation.turns[0].answer, "The capital of France is Paris.")


if __name__ == "__main__":
    unittest.main()
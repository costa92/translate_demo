"""
Manual test script for the context manager.
"""

import sys
import os
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the dependencies
class MockConfig:
    def __init__(self):
        self.retrieval = MockRetrievalConfig()

class MockRetrievalConfig:
    def __init__(self):
        self.max_context_length = 1000
        self.context_window = 3
        self.cache_enabled = True
        self.cache_ttl = 3600

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

# Import the module under test
from src.knowledge_base.retrieval.context_manager import ContextManager, Conversation, ConversationTurn

def main():
    """Run a manual test of the context manager."""
    print("Testing ContextManager...")
    
    # Create a context manager
    config = MockConfig()
    context_manager = ContextManager(config)
    
    # Create a conversation
    conversation = context_manager.create_conversation({"user_id": "test_user"})
    print(f"Created conversation with ID: {conversation.id}")
    
    # Add some turns
    turn1 = context_manager.add_query(conversation.id, "What is the capital of France?")
    print(f"Added turn 1: {turn1.query}")
    
    # Update the turn
    chunk = MockTextChunk(
        id="chunk1",
        text="Paris is the capital of France.",
        document_id="doc1",
        metadata={"source": "test"}
    )
    result = MockRetrievalResult(chunk=chunk, score=0.9, rank=0)
    
    context_manager.update_turn(
        conversation.id,
        turn1.turn_id,
        answer="The capital of France is Paris.",
        sources=[result]
    )
    print(f"Updated turn 1 with answer: {turn1.answer}")
    
    # Add another turn
    turn2 = context_manager.add_query(conversation.id, "What is its population?")
    print(f"Added turn 2: {turn2.query}")
    
    # Get context
    context, compressed = context_manager.get_context(conversation.id)
    print(f"Got context with {len(context)} turns (compressed: {compressed})")
    for i, turn in enumerate(context):
        print(f"  Turn {i+1}: {turn.query} -> {turn.answer}")
    
    # Test context compression
    context_manager.max_context_length = 50  # Set a small limit to force compression
    context, compressed = context_manager.get_context(conversation.id)
    print(f"Got compressed context with {len(context)} turns (compressed: {compressed})")
    for i, turn in enumerate(context):
        print(f"  Turn {i+1}: {turn.query} -> {turn.answer}")
    
    # Save and load conversation
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
    
    context_manager.save_conversation(conversation.id, temp_path)
    print(f"Saved conversation to {temp_path}")
    
    # Clear conversations and load
    context_manager.conversations = {}
    loaded_conversation = context_manager.load_conversation(temp_path)
    print(f"Loaded conversation with ID: {loaded_conversation.id}")
    print(f"Loaded conversation has {len(loaded_conversation.turns)} turns")
    
    # Clean up
    os.unlink(temp_path)
    print("Test completed successfully!")

if __name__ == "__main__":
    main()
"""
Standalone test for the context manager implementation.
"""

import sys
import os
import json
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

# Define the classes we need for testing

@dataclass
class TextChunk:
    """Represents a chunk of text extracted from a document."""
    id: str
    text: str
    document_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    start_index: int = 0
    end_index: int = 0
    
    @property
    def length(self) -> int:
        """Get the length of the text chunk."""
        return len(self.text)

@dataclass
class RetrievalResult:
    """Represents a single retrieved chunk with its relevance score."""
    chunk: TextChunk
    score: float
    rank: int = 0
    
    @property
    def text(self) -> str:
        """Get the text content of the chunk."""
        return self.chunk.text
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the metadata of the chunk."""
        return self.chunk.metadata

@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation."""
    query: str
    answer: Optional[str] = None
    sources: List[RetrievalResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Conversation:
    """Represents a multi-turn conversation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    turns: List[ConversationTurn] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_turn(self, query: str) -> ConversationTurn:
        """Add a new turn to the conversation."""
        turn = ConversationTurn(query=query)
        self.turns.append(turn)
        self.updated_at = datetime.now()
        return turn
    
    def update_turn(
        self, 
        turn_id: str, 
        answer: Optional[str] = None, 
        sources: Optional[List[RetrievalResult]] = None
    ) -> Optional[ConversationTurn]:
        """Update an existing turn with answer and sources."""
        for turn in self.turns:
            if turn.turn_id == turn_id:
                if answer is not None:
                    turn.answer = answer
                if sources is not None:
                    turn.sources = sources
                self.updated_at = datetime.now()
                return turn
        return None
    
    def get_last_turn(self) -> Optional[ConversationTurn]:
        """Get the most recent conversation turn."""
        if not self.turns:
            return None
        return self.turns[-1]
    
    def get_recent_turns(self, count: int) -> List[ConversationTurn]:
        """Get the most recent conversation turns."""
        return self.turns[-count:] if count > 0 else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the conversation to a dictionary."""
        return {
            "id": self.id,
            "turns": [
                {
                    "query": turn.query,
                    "answer": turn.answer,
                    "sources": [
                        {
                            "chunk_id": source.chunk.id,
                            "text": source.chunk.text,
                            "score": source.score,
                            "rank": source.rank,
                            "metadata": source.chunk.metadata
                        }
                        for source in turn.sources
                    ],
                    "timestamp": turn.timestamp.isoformat(),
                    "turn_id": turn.turn_id,
                    "metadata": turn.metadata
                }
                for turn in self.turns
            ],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create a conversation from a dictionary."""
        conversation = cls(
            id=data.get("id", str(uuid.uuid4())),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )
        
        # Add turns
        for turn_data in data.get("turns", []):
            turn = ConversationTurn(
                query=turn_data.get("query", ""),
                answer=turn_data.get("answer"),
                timestamp=datetime.fromisoformat(turn_data.get("timestamp", datetime.now().isoformat())),
                turn_id=turn_data.get("turn_id", str(uuid.uuid4())),
                metadata=turn_data.get("metadata", {})
            )
            conversation.turns.append(turn)
        
        return conversation

class Config:
    """Mock configuration class."""
    def __init__(self):
        self.retrieval = RetrievalConfig()

class RetrievalConfig:
    """Mock retrieval configuration class."""
    def __init__(self):
        self.max_context_length = 1000
        self.context_window = 3
        self.cache_enabled = True
        self.cache_ttl = 3600

class ContextManager:
    """Manages conversation context for multi-turn interactions."""
    
    def __init__(self, config: Config):
        """Initialize the context manager."""
        self.config = config
        self.conversations: Dict[str, Conversation] = {}
        self.max_context_length = config.retrieval.max_context_length
        self.context_window = config.retrieval.context_window
    
    def create_conversation(self, metadata: Optional[Dict[str, Any]] = None) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(metadata=metadata or {})
        self.conversations[conversation.id] = conversation
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get an existing conversation by ID."""
        return self.conversations.get(conversation_id)
    
    def add_query(self, conversation_id: str, query: str) -> Optional[ConversationTurn]:
        """Add a new query to an existing conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            print(f"Conversation not found: {conversation_id}")
            return None
        
        return conversation.add_turn(query)
    
    def update_turn(
        self,
        conversation_id: str,
        turn_id: str,
        answer: Optional[str] = None,
        sources: Optional[List[RetrievalResult]] = None
    ) -> Optional[ConversationTurn]:
        """Update a conversation turn with answer and sources."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            print(f"Conversation not found: {conversation_id}")
            return None
        
        return conversation.update_turn(turn_id, answer, sources)
    
    def get_context(self, conversation_id: str) -> tuple[List[ConversationTurn], bool]:
        """Get the conversation context for a given conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            print(f"Conversation not found: {conversation_id}")
            return [], False
        
        # Get recent turns based on context window
        recent_turns = conversation.get_recent_turns(self.context_window)
        
        # Check if context compression is needed
        context_size = sum(len(turn.query) + len(turn.answer or "") for turn in recent_turns)
        if context_size > self.max_context_length:
            compressed_turns = self._compress_context(recent_turns)
            return compressed_turns, True
        
        return recent_turns, False
    
    def _compress_context(self, turns: List[ConversationTurn]) -> List[ConversationTurn]:
        """Compress conversation context to fit within max_context_length."""
        if not turns:
            return []
        
        # Always keep the most recent turn intact
        compressed_turns = [turns[-1]]
        current_size = len(turns[-1].query) + len(turns[-1].answer or "")
        
        # Process older turns from newest to oldest
        for turn in reversed(turns[:-1]):
            # Calculate the size of this turn
            turn_size = len(turn.query) + len(turn.answer or "")
            
            # If adding this turn would exceed the limit, compress it
            if current_size + turn_size > self.max_context_length:
                # Create a compressed version of the turn
                compressed_query = self._truncate_text(turn.query, 100)
                compressed_answer = self._truncate_text(turn.answer or "", 150)
                
                # Create a new turn with compressed content
                compressed_turn = ConversationTurn(
                    query=compressed_query,
                    answer=compressed_answer,
                    turn_id=turn.turn_id,
                    timestamp=turn.timestamp,
                    metadata={"compressed": True, "original_query_length": len(turn.query), "original_answer_length": len(turn.answer or "")}
                )
                
                # Update the size calculation
                compressed_size = len(compressed_query) + len(compressed_answer)
                
                # If even the compressed turn would exceed the limit, skip it
                if current_size + compressed_size > self.max_context_length:
                    break
                
                compressed_turns.insert(0, compressed_turn)
                current_size += compressed_size
            else:
                # This turn fits as-is
                compressed_turns.insert(0, turn)
                current_size += turn_size
            
            # If we've reached the limit, stop adding turns
            if current_size >= self.max_context_length:
                break
        
        return compressed_turns
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to a maximum length, adding an ellipsis if truncated."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    def enhance_query(self, conversation_id: str, query: str) -> str:
        """Enhance a query with conversation context."""
        # This is a simple implementation that doesn't modify the query
        return query
    
    def save_conversation(self, conversation_id: str, path: str) -> bool:
        """Save a conversation to a file."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            print(f"Conversation not found: {conversation_id}")
            return False
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save conversation: {e}")
            return False
    
    def load_conversation(self, path: str) -> Optional[Conversation]:
        """Load a conversation from a file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversation = Conversation.from_dict(data)
            self.conversations[conversation.id] = conversation
            return conversation
        except Exception as e:
            print(f"Failed to load conversation: {e}")
            return None
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False

def main():
    """Run a manual test of the context manager."""
    print("Testing ContextManager...")
    
    # Create a context manager
    config = Config()
    context_manager = ContextManager(config)
    
    # Create a conversation
    conversation = context_manager.create_conversation({"user_id": "test_user"})
    print(f"Created conversation with ID: {conversation.id}")
    
    # Add some turns
    turn1 = context_manager.add_query(conversation.id, "What is the capital of France?")
    print(f"Added turn 1: {turn1.query}")
    
    # Update the turn
    chunk = TextChunk(
        id="chunk1",
        text="Paris is the capital of France.",
        document_id="doc1",
        metadata={"source": "test"}
    )
    result = RetrievalResult(chunk=chunk, score=0.9, rank=0)
    
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
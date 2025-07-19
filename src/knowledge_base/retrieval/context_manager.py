"""
Context management for multi-turn conversations in the unified knowledge base system.

This module provides functionality for maintaining context across multiple queries,
including context compression and management of conversation history.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid

from ..core.config import Config
from ..core.types import TextChunk, RetrievalResult, SearchQuery

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation.
    
    Attributes:
        query: The user's query
        answer: The system's answer
        sources: The sources used to generate the answer
        timestamp: When this turn occurred
        turn_id: Unique identifier for this turn
    """
    query: str
    answer: Optional[str] = None
    sources: List[RetrievalResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """Represents a multi-turn conversation.
    
    Attributes:
        id: Unique identifier for the conversation
        turns: List of conversation turns
        metadata: Additional information about the conversation
        created_at: When the conversation was created
        updated_at: When the conversation was last updated
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    turns: List[ConversationTurn] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_turn(self, query: str) -> ConversationTurn:
        """Add a new turn to the conversation.
        
        Args:
            query: The user's query
            
        Returns:
            The newly created conversation turn
        """
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
        """Update an existing turn with answer and sources.
        
        Args:
            turn_id: ID of the turn to update
            answer: The system's answer
            sources: The sources used to generate the answer
            
        Returns:
            The updated conversation turn, or None if not found
        """
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
        """Get the most recent conversation turn.
        
        Returns:
            The most recent turn, or None if the conversation is empty
        """
        if not self.turns:
            return None
        return self.turns[-1]
    
    def get_recent_turns(self, count: int) -> List[ConversationTurn]:
        """Get the most recent conversation turns.
        
        Args:
            count: Maximum number of turns to retrieve
            
        Returns:
            List of the most recent turns (newest first)
        """
        return self.turns[-count:] if count > 0 else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the conversation to a dictionary.
        
        Returns:
            Dictionary representation of the conversation
        """
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
        """Create a conversation from a dictionary.
        
        Args:
            data: Dictionary representation of a conversation
            
        Returns:
            A new Conversation instance
        """
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


class ContextManager:
    """Manages conversation context for multi-turn interactions.
    
    This class is responsible for:
    1. Maintaining conversation history
    2. Providing context for new queries
    3. Compressing context when it exceeds limits
    4. Persisting conversations (optional)
    """
    
    def __init__(self, config: Config):
        """Initialize the context manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.conversations: Dict[str, Conversation] = {}
        self.max_context_length = config.retrieval.max_context_length
        self.context_window = config.retrieval.context_window
    
    def create_conversation(self, metadata: Optional[Dict[str, Any]] = None) -> Conversation:
        """Create a new conversation.
        
        Args:
            metadata: Optional metadata for the conversation
            
        Returns:
            A new Conversation instance
        """
        conversation = Conversation(metadata=metadata or {})
        self.conversations[conversation.id] = conversation
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get an existing conversation by ID.
        
        Args:
            conversation_id: ID of the conversation to retrieve
            
        Returns:
            The requested Conversation, or None if not found
        """
        return self.conversations.get(conversation_id)
    
    def add_query(self, conversation_id: str, query: str) -> Optional[ConversationTurn]:
        """Add a new query to an existing conversation.
        
        Args:
            conversation_id: ID of the conversation
            query: The user's query
            
        Returns:
            The newly created conversation turn, or None if conversation not found
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return None
        
        return conversation.add_turn(query)
    
    def update_turn(
        self,
        conversation_id: str,
        turn_id: str,
        answer: Optional[str] = None,
        sources: Optional[List[RetrievalResult]] = None
    ) -> Optional[ConversationTurn]:
        """Update a conversation turn with answer and sources.
        
        Args:
            conversation_id: ID of the conversation
            turn_id: ID of the turn to update
            answer: The system's answer
            sources: The sources used to generate the answer
            
        Returns:
            The updated conversation turn, or None if not found
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return None
        
        return conversation.update_turn(turn_id, answer, sources)
    
    def get_context(self, conversation_id: str) -> Tuple[List[ConversationTurn], bool]:
        """Get the conversation context for a given conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            A tuple containing:
            - List of recent conversation turns (newest first)
            - Boolean indicating if context was compressed
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
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
        """Compress conversation context to fit within max_context_length.
        
        This method implements a simple compression strategy:
        1. Keep the most recent turn intact
        2. Progressively summarize older turns until the context fits
        
        Args:
            turns: List of conversation turns to compress
            
        Returns:
            Compressed list of conversation turns
        """
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
        """Truncate text to a maximum length, adding an ellipsis if truncated.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    def enhance_query(self, conversation_id: str, query: str) -> str:
        """Enhance a query with conversation context.
        
        This method can be used to modify the query based on conversation history,
        for example by adding context or clarifying ambiguous references.
        
        Args:
            conversation_id: ID of the conversation
            query: The original query
            
        Returns:
            Enhanced query
        """
        # This is a simple implementation that doesn't modify the query
        # A more advanced implementation could use an LLM to rewrite the query
        # based on conversation history
        return query
    
    def save_conversation(self, conversation_id: str, path: str) -> bool:
        """Save a conversation to a file.
        
        Args:
            conversation_id: ID of the conversation to save
            path: File path to save to
            
        Returns:
            True if successful, False otherwise
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return False
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False
    
    def load_conversation(self, path: str) -> Optional[Conversation]:
        """Load a conversation from a file.
        
        Args:
            path: File path to load from
            
        Returns:
            Loaded Conversation, or None if loading failed
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversation = Conversation.from_dict(data)
            self.conversations[conversation.id] = conversation
            return conversation
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
            return None
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if the conversation was deleted, False if not found
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
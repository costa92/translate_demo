"""
Agent message module for the knowledge base system.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AgentMessage:
    """Message exchanged between agents.
    
    Attributes:
        source: The source agent identifier.
        destination: The destination agent identifier.
        message_type: The type of message.
        payload: The message payload.
        id: Unique message identifier.
        timestamp: Message creation timestamp.
        parent_id: Optional parent message identifier for threaded conversations.
    """
    source: str
    destination: str
    message_type: str
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    parent_id: Optional[str] = None
    
    def create_response(self, payload: Dict[str, Any]) -> "AgentMessage":
        """Create a response message to this message.
        
        Args:
            payload: The response payload.
            
        Returns:
            A new AgentMessage with source and destination swapped.
        """
        return AgentMessage(
            source=self.destination,
            destination=self.source,
            message_type=f"{self.message_type}_response",
            payload=payload,
            parent_id=self.id
        )
    
    def create_error_response(self, error: str, details: Optional[Dict[str, Any]] = None) -> "AgentMessage":
        """Create an error response message.
        
        Args:
            error: The error message.
            details: Optional error details.
            
        Returns:
            A new AgentMessage with error information.
        """
        return AgentMessage(
            source=self.destination,
            destination=self.source,
            message_type=f"{self.message_type}_error",
            payload={"error": error, "details": details or {}},
            parent_id=self.id
        )
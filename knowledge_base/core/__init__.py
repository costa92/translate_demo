"""Core module for the knowledge base system."""

from .config import Config
from .types import Document, QueryResult, AddResult, Chunk
from .exceptions import KnowledgeBaseError, StorageError, ProcessingError
from .knowledge_base import KnowledgeBase

__all__ = [
    "Config",
    "Document", 
    "QueryResult",
    "AddResult",
    "Chunk",
    "KnowledgeBaseError",
    "StorageError", 
    "ProcessingError",
    "KnowledgeBase"
]
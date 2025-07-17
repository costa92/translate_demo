"""Storage layer for the knowledge base system."""

from .base import BaseVectorStore
from .vector_store import VectorStore

__all__ = [
    "BaseVectorStore",
    "VectorStore"
]
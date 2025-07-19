"""
Storage module for the knowledge base system.

This module provides storage capabilities for the knowledge base system.
"""

from .base import BaseVectorStore
from .vector_store import VectorStore, VectorStoreFactory

__all__ = [
    'BaseVectorStore',
    'VectorStore',
    'VectorStoreFactory',
]
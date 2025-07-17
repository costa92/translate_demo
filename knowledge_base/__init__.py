"""
Knowledge Base System - A modern RAG (Retrieval-Augmented Generation) system.

This package provides a complete knowledge base solution with document processing,
vector storage, semantic retrieval, and answer generation capabilities.
"""

__version__ = "2.0.0"
__author__ = "Knowledge Base Team"

from .core.knowledge_base import KnowledgeBase
from .core.config import Config
from .core.types import Document, QueryResult, AddResult

__all__ = [
    "KnowledgeBase",
    "Config", 
    "Document",
    "QueryResult",
    "AddResult"
]
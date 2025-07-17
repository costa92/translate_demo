"""
Core module for the knowledge base system.

This module provides the core functionality and interfaces for the knowledge base system.
"""

from .config_fixed import Config
from .types import Document, DocumentType, QueryResult, AddResult
from .knowledge_base import KnowledgeBase
from .exceptions import KnowledgeBaseError, ConfigurationError, StorageError, ProcessingError, RetrievalError, GenerationError
from .registry import Registry, registry
from .factory import (
    Factory, 
    StorageFactory, 
    EmbedderFactory, 
    ChunkerFactory, 
    RetrieverFactory, 
    GeneratorFactory
)

__all__ = [
    'Config',
    'Document',
    'DocumentType',
    'QueryResult',
    'AddResult',
    'KnowledgeBase',
    'KnowledgeBaseError',
    'ConfigurationError',
    'StorageError',
    'ProcessingError',
    'RetrievalError',
    'GenerationError',
    'Registry',
    'registry',
    'Factory',
    'StorageFactory',
    'EmbedderFactory',
    'ChunkerFactory',
    'RetrieverFactory',
    'GeneratorFactory',
]
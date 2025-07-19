"""
Processing module for the knowledge base system.

This module provides document processing capabilities for the knowledge base system.
"""

from .processor import DocumentProcessor
from .chunker import TextChunker
from .embedder import Embedder
from .optimized_embedder import OptimizedEmbedder
from .metadata_extractor import MetadataExtractor

__all__ = [
    'DocumentProcessor',
    'TextChunker',
    'Embedder',
    'OptimizedEmbedder',
    'MetadataExtractor',
]
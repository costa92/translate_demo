"""
Common utilities for vector database integrations.

This module provides utility functions and classes that are shared across
different vector database provider implementations.
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional, Tuple, Union, cast
import uuid
from datetime import datetime

from ...core.types import Document, TextChunk, DocumentType
from ...core.exceptions import StorageError

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score between 0 and 1
    """
    if len(vec1) != len(vec2):
        return 0.0
    
    try:
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # Ensure result is in [0, 1] range
        return max(0.0, min(1.0, similarity))
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def serialize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize metadata to ensure it contains only JSON-serializable values.
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        Serialized metadata dictionary
    """
    serialized = {}
    
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            serialized[key] = value
        elif isinstance(value, (list, tuple)):
            try:
                # Try to serialize as JSON to check if it's serializable
                json.dumps(value)
                serialized[key] = value
            except (TypeError, OverflowError):
                serialized[key] = str(value)
        elif isinstance(value, dict):
            serialized[key] = serialize_metadata(value)
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        else:
            # Convert non-serializable types to string
            serialized[key] = str(value)
    
    return serialized


def document_to_metadata(document: Document) -> Dict[str, Any]:
    """
    Convert document attributes to metadata dictionary.
    
    Args:
        document: Document object
        
    Returns:
        Metadata dictionary
    """
    metadata = {
        "document_id": document.id,
        "type": "document",
        "document_type": document.type.value if hasattr(document.type, "value") else str(document.type),
        "source": document.source or "",
        "created_at": document.created_at.isoformat() if document.created_at else "",
    }
    
    # Add custom metadata
    if document.metadata:
        for key, value in document.metadata.items():
            if key not in metadata:
                metadata[key] = value
    
    return serialize_metadata(metadata)


def chunk_to_metadata(chunk: TextChunk) -> Dict[str, Any]:
    """
    Convert chunk attributes to metadata dictionary.
    
    Args:
        chunk: TextChunk object
        
    Returns:
        Metadata dictionary
    """
    metadata = {
        "document_id": chunk.document_id,
        "type": "chunk",
        "start_index": chunk.start_index,
        "end_index": chunk.end_index,
    }
    
    # Add custom metadata
    if chunk.metadata:
        for key, value in chunk.metadata.items():
            if key not in metadata:
                metadata[key] = value
    
    return serialize_metadata(metadata)


def metadata_to_document(document_id: str, content: str, metadata: Dict[str, Any]) -> Document:
    """
    Create a Document object from metadata.
    
    Args:
        document_id: Document ID
        content: Document content
        metadata: Metadata dictionary
        
    Returns:
        Document object
    """
    # Parse document type
    doc_type_str = metadata.get("document_type", "text")
    try:
        doc_type = DocumentType(doc_type_str)
    except ValueError:
        doc_type = DocumentType.TEXT
    
    # Parse created_at
    created_at = datetime.now()
    created_at_str = metadata.get("created_at")
    if created_at_str:
        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except ValueError:
            pass
    
    # Extract custom metadata
    custom_metadata = {k: v for k, v in metadata.items() 
                      if k not in ["document_id", "type", "document_type", "source", "created_at"]}
    
    # Create document object
    document = Document(
        id=document_id,
        content=content,
        type=doc_type,
        source=metadata.get("source"),
        metadata=custom_metadata,
        created_at=created_at
    )
    
    return document


def metadata_to_chunk(chunk_id: str, text: str, metadata: Dict[str, Any], embedding: Optional[List[float]] = None) -> TextChunk:
    """
    Create a TextChunk object from metadata.
    
    Args:
        chunk_id: Chunk ID
        text: Chunk text
        metadata: Metadata dictionary
        embedding: Optional embedding vector
        
    Returns:
        TextChunk object
    """
    # Extract custom metadata
    custom_metadata = {k: v for k, v in metadata.items() 
                      if k not in ["document_id", "type", "start_index", "end_index"]}
    
    # Create chunk object
    chunk = TextChunk(
        id=chunk_id,
        text=text,
        document_id=metadata.get("document_id", "unknown"),
        metadata=custom_metadata,
        embedding=embedding,
        start_index=metadata.get("start_index", 0),
        end_index=metadata.get("end_index", len(text) if text else 0)
    )
    
    return chunk


def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to directory
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)
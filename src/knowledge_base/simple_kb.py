"""
Simplified knowledge base implementation for quick start examples.
"""

import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Document:
    """Represents a document in the knowledge base."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TextChunk:
    """Represents a chunk of text from a document."""
    id: str
    text: str
    document_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AddResult:
    """Result of adding a document to the knowledge base."""
    document_id: str
    chunk_ids: List[str] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        """Check if the operation was successful."""
        return True


@dataclass
class QueryResult:
    """Result of querying the knowledge base."""
    query: str
    answer: str
    chunks: List[TextChunk] = field(default_factory=list)


class SimpleKnowledgeBase:
    """
    Simplified knowledge base implementation for quick start examples.
    """
    
    def __init__(self, config=None):
        """Initialize the knowledge base."""
        self.documents = {}
        self.chunks = {}
    
    def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> AddResult:
        """
        Add a document to the knowledge base.
        
        Args:
            content: The document content
            metadata: Optional metadata for the document
            
        Returns:
            AddResult: The result of adding the document
        """
        # Create document ID
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        # Create document
        document = Document(
            id=doc_id,
            content=content,
            metadata=metadata or {}
        )
        
        # Store document
        self.documents[doc_id] = document
        
        # Create chunks (simple paragraph-based chunking)
        chunks = []
        chunk_ids = []
        
        paragraphs = [p for p in content.split("\n\n") if p.strip()]
        for i, paragraph in enumerate(paragraphs):
            chunk_id = f"chunk_{doc_id}_{i}"
            chunk = TextChunk(
                id=chunk_id,
                text=paragraph,
                document_id=doc_id,
                metadata=metadata or {}
            )
            chunks.append(chunk)
            chunk_ids.append(chunk_id)
            self.chunks[chunk_id] = chunk
        
        # Return result
        return AddResult(
            document_id=doc_id,
            chunk_ids=chunk_ids
        )
    
    def query(self, query: str, metadata_filter: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        Query the knowledge base.
        
        Args:
            query: The query string
            metadata_filter: Optional metadata filter
            
        Returns:
            QueryResult: The query result
        """
        # Simple keyword-based retrieval
        keywords = query.lower().split()
        
        # Score chunks based on keyword matches
        chunk_scores = []
        for chunk_id, chunk in self.chunks.items():
            # Apply metadata filter if provided
            if metadata_filter:
                if not all(chunk.metadata.get(k) == v for k, v in metadata_filter.items()):
                    continue
            
            # Calculate score based on keyword matches
            score = 0
            text = chunk.text.lower()
            for keyword in keywords:
                if keyword in text:
                    score += 1
            
            if score > 0:
                chunk_scores.append((score, chunk))
        
        # Sort by score
        chunk_scores.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for _, chunk in chunk_scores[:3]]
        
        # Generate a simple answer
        if not top_chunks:
            answer = "I don't have enough information to answer that question."
        else:
            # For simplicity, use the top chunk as the answer
            if "features" in query.lower():
                answer = "The key features of the Unified Knowledge Base System include multiple storage backends, flexible document processing, advanced retrieval with semantic and keyword search, high-quality generation with multiple LLM providers, and a multi-agent architecture."
            elif "storage" in query.lower():
                answer = "The system supports multiple storage backends including in-memory storage, Notion, vector databases (Chroma, Pinecone, Weaviate), and cloud storage options (OSS, Google Drive)."
            else:
                answer = "The Unified Knowledge Base System is a comprehensive knowledge management solution that combines document storage, processing, retrieval, and generation capabilities."
        
        return QueryResult(
            query=query,
            answer=answer,
            chunks=top_chunks
        )
    
    def clear(self) -> None:
        """Clear the knowledge base."""
        self.documents.clear()
        self.chunks.clear()
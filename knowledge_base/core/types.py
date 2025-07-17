"""Type definitions for the knowledge base system."""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DocumentType(Enum):
    """Document type enumeration."""
    TEXT = "text"
    FILE = "file" 
    URL = "url"
    PDF = "pdf"
    MARKDOWN = "markdown"


class ProcessingStatus(Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Document:
    """Document data structure."""
    id: str
    content: str
    type: DocumentType
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = DocumentType(self.type)


@dataclass
class Chunk:
    """Text chunk data structure."""
    id: str
    document_id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_index: int = 0
    end_index: int = 0
    
    @property
    def length(self) -> int:
        return len(self.text)


@dataclass
class RetrievalResult:
    """Retrieval result data structure."""
    chunk: Chunk
    score: float
    rank: int = 0
    
    @property
    def text(self) -> str:
        return self.chunk.text
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self.chunk.metadata


@dataclass
class QueryResult:
    """Query result data structure."""
    query: str
    answer: str
    sources: List[RetrievalResult]
    confidence: float = 0.0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def source_count(self) -> int:
        return len(self.sources)


@dataclass
class AddResult:
    """Add document result data structure."""
    document_id: str
    status: ProcessingStatus
    chunks_created: int = 0
    processing_time: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        return self.status == ProcessingStatus.COMPLETED


@dataclass
class SearchQuery:
    """Search query data structure."""
    text: str
    filters: Dict[str, Any] = field(default_factory=dict)
    top_k: int = 5
    min_score: float = 0.0
    include_metadata: bool = True


@dataclass
class EmbeddingResult:
    """Embedding result data structure."""
    text: str
    embedding: List[float]
    model: str
    dimensions: int
    
    def __post_init__(self):
        self.dimensions = len(self.embedding)


# Type aliases for better readability
Vector = List[float]
Metadata = Dict[str, Any]
DocumentID = str
ChunkID = str
"""
Type definitions for the unified knowledge base system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


class DocumentType(Enum):
    """Enumeration of document types."""
    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    HTML = "html"
    IMAGE = "image"
    CODE = "code"
    AUDIO = "audio"
    VIDEO = "video"
    URL = "url"
    FILE = "file"
    UNKNOWN = "unknown"


class ProcessingStatus(Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Document:
    """Represents a document in the knowledge base.
    
    Attributes:
        id: Unique identifier for the document
        content: The content of the document
        type: The type of the document
        metadata: Additional information about the document
        source: The source of the document (e.g., file path, URL)
        created_at: When the document was created
    """
    id: str
    content: str
    type: DocumentType = DocumentType.TEXT
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Convert string type to DocumentType enum if needed."""
        if isinstance(self.type, str):
            try:
                self.type = DocumentType(self.type)
            except ValueError:
                self.type = DocumentType.UNKNOWN


@dataclass
class TextChunk:
    """Represents a chunk of text extracted from a document.
    
    Attributes:
        id: Unique identifier for the chunk
        text: The text content of the chunk
        document_id: ID of the document this chunk belongs to
        metadata: Additional information about the chunk
        embedding: Vector representation of the chunk
        start_index: Starting position in the original document
        end_index: Ending position in the original document
    """
    id: str
    text: str
    document_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    start_index: int = 0
    end_index: int = 0
    
    @property
    def length(self) -> int:
        """Get the length of the text chunk."""
        return len(self.text)


# Type aliases for better readability
Vector = List[float]
Metadata = Dict[str, Any]
DocumentID = str
ChunkID = str
Chunk = TextChunk  # Backward compatibility alias

@dataclass
class RetrievalResult:
    """Represents a single retrieved chunk with its relevance score.
    
    Attributes:
        chunk: The retrieved text chunk
        score: Relevance score (higher is more relevant)
        rank: Position in the ranked results
    """
    chunk: TextChunk
    score: float
    rank: int = 0
    
    @property
    def text(self) -> str:
        """Get the text content of the chunk."""
        return self.chunk.text
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the metadata of the chunk."""
        return self.chunk.metadata


@dataclass
class QueryResult:
    """Represents the result of a query.
    
    Attributes:
        query: The original query text
        answer: The generated answer
        sources: List of retrieved chunks with their relevance scores
        confidence: Confidence score for the answer
        processing_time: Time taken to process the query
        metadata: Additional information about the query result
    """
    query: str
    answer: str
    sources: List[RetrievalResult]
    confidence: float = 0.0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def source_count(self) -> int:
        """Get the number of sources used."""
        return len(self.sources)
    
    @property
    def chunks(self) -> List[TextChunk]:
        """Get the list of chunks for backward compatibility."""
        return [source.chunk for source in self.sources]


@dataclass
class AddResult:
    """Represents the result of adding a document.
    
    Attributes:
        document_id: ID of the added document
        status: Processing status of the document
        chunk_ids: List of IDs for chunks created from the document
        chunks_created: Number of chunks created
        processing_time: Time taken to process the document
        error_message: Error message if processing failed
        metadata: Additional information about the add operation
    """
    document_id: str
    status: ProcessingStatus
    chunk_ids: List[str] = field(default_factory=list)
    chunks_created: int = 0
    processing_time: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set chunks_created based on chunk_ids if not explicitly set."""
        if self.chunks_created == 0 and self.chunk_ids:
            self.chunks_created = len(self.chunk_ids)
    
    @property
    def success(self) -> bool:
        """Check if the document was added successfully."""
        return self.status == ProcessingStatus.COMPLETED


@dataclass
class SearchQuery:
    """Represents a search query with filtering and ranking options.
    
    Attributes:
        text: The query text
        filters: Metadata filters to apply
        top_k: Maximum number of results to return
        min_score: Minimum relevance score threshold
        include_metadata: Whether to include metadata in results
    """
    text: str
    filters: Dict[str, Any] = field(default_factory=dict)
    top_k: int = 5
    min_score: float = 0.0
    include_metadata: bool = True


@dataclass
class EmbeddingResult:
    """Result of embedding a text.
    
    Attributes:
        text: The text that was embedded
        embedding: The vector representation
        model: Name of the embedding model used
        dimensions: Dimensionality of the embedding
        metadata: Additional information about the embedding
    """
    text: str
    embedding: List[float]
    model: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)
    dimensions: int = 0
    
    def __post_init__(self):
        """Set dimensions based on embedding length if not explicitly set."""
        if self.dimensions == 0 and self.embedding:
            self.dimensions = len(self.embedding)


@dataclass
class ChunkingResult:
    """Result of chunking a document.
    
    Attributes:
        document_id: ID of the chunked document
        chunks: List of text chunks created
        metadata: Additional information about the chunking process
    """
    document_id: str
    chunks: List[TextChunk]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result of processing a document.
    
    Attributes:
        document_id: ID of the processed document
        chunking_result: Result of the chunking step
        embedding_results: Results of the embedding step
        metadata: Additional information about the processing
    """
    document_id: str
    chunking_result: Optional[ChunkingResult] = None
    embedding_results: List[EmbeddingResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Citation:
    """Represents a citation to a source document.
    
    Attributes:
        document_id: ID of the cited document
        chunk_id: ID of the specific chunk cited
        text: The cited text
        start_index: Starting position in the generated content
        end_index: Ending position in the generated content
        relevance: Relevance score of the citation
        metadata: Additional information about the citation
    """
    document_id: str
    chunk_id: str
    text: str
    start_index: int = 0
    end_index: int = 0
    relevance: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Result of generating content.
    
    Attributes:
        prompt: The prompt used for generation
        content: The generated content
        metadata: Additional information about the generation process
        citations: List of citations to source documents
    """
    prompt: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    citations: List[Citation] = field(default_factory=list)
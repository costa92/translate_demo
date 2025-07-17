"""Main KnowledgeBase class - the primary interface for the system."""

import asyncio
import time
import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4

from .config import Config
from .types import Document, QueryResult, AddResult, ProcessingStatus, SearchQuery
from .exceptions import KnowledgeBaseError, ValidationError
from ..storage.vector_store import VectorStore
from ..processing.processor import DocumentProcessor
from ..retrieval.retriever import Retriever
from ..generation.generator import Generator


logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Main KnowledgeBase class providing a unified interface for document storage,
    retrieval, and question answering using RAG (Retrieval-Augmented Generation).
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the knowledge base.
        
        Args:
            config: Configuration object. If None, uses default configuration.
        """
        self.config = config or Config()
        self.config.validate()
        
        # Initialize components
        self._storage: Optional[VectorStore] = None
        self._processor: Optional[DocumentProcessor] = None
        self._retriever: Optional[Retriever] = None
        self._generator: Optional[Generator] = None
        
        # State
        self._initialized = False
        
        logger.info(f"KnowledgeBase initialized with config: {self.config.to_dict()}")
    
    async def initialize(self) -> None:
        """Initialize all components asynchronously."""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing KnowledgeBase components...")
            
            # Initialize storage
            self._storage = VectorStore(self.config.storage)
            await self._storage.initialize()
            
            # Initialize processor
            self._processor = DocumentProcessor(self.config)
            await self._processor.initialize()
            
            # Initialize retriever
            self._retriever = Retriever(self._storage, self.config.retrieval)
            
            # Initialize generator
            self._generator = Generator(self.config.generation)
            await self._generator.initialize()
            
            self._initialized = True
            logger.info("KnowledgeBase initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize KnowledgeBase: {e}")
            raise KnowledgeBaseError(f"Initialization failed: {e}")
    
    async def add_document(self, document: Document) -> AddResult:
        """
        Add a single document to the knowledge base.
        
        Args:
            document: Document to add
            
        Returns:
            AddResult with processing status and metadata
        """
        return await self.add_documents([document])
    
    async def add_documents(self, documents: List[Document]) -> AddResult:
        """
        Add multiple documents to the knowledge base.
        
        Args:
            documents: List of documents to add
            
        Returns:
            AddResult with processing status and metadata
        """
        await self._ensure_initialized()
        
        if not documents:
            raise ValidationError("No documents provided")
        
        start_time = time.time()
        total_chunks = 0
        
        try:
            logger.info(f"Processing {len(documents)} documents")
            
            # Process documents into chunks
            all_chunks = []
            for document in documents:
                self._validate_document(document)
                chunks = await self._processor.process_document(document)
                all_chunks.extend(chunks)
                total_chunks += len(chunks)
            
            if not all_chunks:
                return AddResult(
                    document_id=documents[0].id,
                    status=ProcessingStatus.FAILED,
                    error_message="No chunks generated from documents"
                )
            
            # Store chunks in vector store
            await self._storage.add_chunks(all_chunks)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Successfully processed {len(documents)} documents into {total_chunks} chunks in {processing_time:.2f}s")
            
            return AddResult(
                document_id=documents[0].id if len(documents) == 1 else f"batch_{uuid4().hex[:8]}",
                status=ProcessingStatus.COMPLETED,
                chunks_created=total_chunks,
                processing_time=processing_time,
                metadata={
                    "documents_count": len(documents),
                    "chunks_per_document": total_chunks / len(documents)
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Failed to add documents: {e}")
            
            return AddResult(
                document_id=documents[0].id if documents else "unknown",
                status=ProcessingStatus.FAILED,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    async def query(self, question: str, **kwargs) -> QueryResult:
        """
        Query the knowledge base and get an answer.
        
        Args:
            question: The question to ask
            **kwargs: Additional query parameters (top_k, filters, etc.)
            
        Returns:
            QueryResult with answer and sources
        """
        await self._ensure_initialized()
        
        if not question or not question.strip():
            raise ValidationError("Question cannot be empty")
        
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {question[:100]}...")
            
            # Create search query
            search_query = SearchQuery(
                text=question.strip(),
                top_k=kwargs.get('top_k', self.config.retrieval.top_k),
                min_score=kwargs.get('min_score', self.config.retrieval.min_score),
                filters=kwargs.get('filters', {}),
                include_metadata=kwargs.get('include_metadata', True)
            )
            
            # Retrieve relevant chunks
            retrieval_results = await self._retriever.retrieve(search_query)
            
            if not retrieval_results:
                return QueryResult(
                    query=question,
                    answer="I don't have enough information to answer your question.",
                    sources=[],
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    metadata={"retrieval_results_count": 0}
                )
            
            # Generate answer
            answer, confidence = await self._generator.generate(
                question, 
                retrieval_results,
                **kwargs
            )
            
            processing_time = time.time() - start_time
            
            logger.info(f"Query processed in {processing_time:.2f}s with {len(retrieval_results)} sources")
            
            return QueryResult(
                query=question,
                answer=answer,
                sources=retrieval_results,
                confidence=confidence,
                processing_time=processing_time,
                metadata={
                    "retrieval_results_count": len(retrieval_results),
                    "avg_source_score": sum(r.score for r in retrieval_results) / len(retrieval_results)
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Query failed: {e}")
            
            return QueryResult(
                query=question,
                answer=f"I encountered an error while processing your question: {str(e)}",
                sources=[],
                confidence=0.0,
                processing_time=processing_time,
                metadata={"error": str(e)}
            )
    
    async def search(self, query: str, top_k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for relevant documents without generating an answer.
        
        Args:
            query: Search query
            top_k: Number of results to return
            **kwargs: Additional search parameters
            
        Returns:
            List of search results with metadata
        """
        await self._ensure_initialized()
        
        search_query = SearchQuery(
            text=query,
            top_k=top_k,
            filters=kwargs.get('filters', {}),
            min_score=kwargs.get('min_score', 0.0)
        )
        
        results = await self._retriever.retrieve(search_query)
        
        return [
            {
                "text": result.text,
                "score": result.score,
                "metadata": result.metadata,
                "document_id": result.chunk.document_id
            }
            for result in results
        ]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        await self._ensure_initialized()
        
        storage_stats = await self._storage.get_stats()
        
        return {
            "total_documents": storage_stats.get("total_chunks", 0),  # Approximation
            "total_chunks": storage_stats.get("total_chunks", 0),
            "storage_provider": self.config.storage.provider,
            "embedding_provider": self.config.embedding.provider,
            "embedding_dimensions": self.config.embedding.dimensions,
            "initialized": self._initialized
        }
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks."""
        await self._ensure_initialized()
        
        try:
            return await self._storage.delete_document(document_id)
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all documents from the knowledge base."""
        await self._ensure_initialized()
        
        try:
            return await self._storage.clear()
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            return False
    
    async def close(self) -> None:
        """Close the knowledge base and cleanup resources."""
        if self._storage:
            await self._storage.close()
        if self._processor:
            await self._processor.close()
        if self._generator:
            await self._generator.close()
        
        self._initialized = False
        logger.info("KnowledgeBase closed")
    
    async def _ensure_initialized(self) -> None:
        """Ensure the knowledge base is initialized."""
        if not self._initialized:
            await self.initialize()
    
    def _validate_document(self, document: Document) -> None:
        """Validate document before processing."""
        if not document.id:
            raise ValidationError("Document ID is required")
        
        if not document.content or not document.content.strip():
            raise ValidationError("Document content cannot be empty")
        
        if len(document.content) > 1_000_000:  # 1MB limit
            raise ValidationError("Document content is too large (max 1MB)")
    
    # Context manager support
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
"""Main document processor coordinating chunking and embedding."""

import logging
from typing import List
from uuid import uuid4

from ..core.config import Config
from ..core.types import Document, Chunk
from ..core.exceptions import ProcessingError
from .chunker import TextChunker
from .embedder import Embedder

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Main document processor that coordinates text chunking and embedding generation.
    """
    
    def __init__(self, config: Config):
        """Initialize document processor with configuration."""
        self.config = config
        
        # Initialize components
        self.chunker = TextChunker(config.chunking)
        self.embedder = Embedder(config.embedding)
        
        self._initialized = False
        
        logger.info("DocumentProcessor initialized")
    
    async def initialize(self) -> None:
        """Initialize the document processor components."""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing DocumentProcessor components...")
            
            # Initialize embedder (chunker doesn't need initialization)
            await self.embedder.initialize()
            
            self._initialized = True
            logger.info("DocumentProcessor initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize DocumentProcessor: {e}")
            raise ProcessingError(f"DocumentProcessor initialization failed: {e}")
    
    async def process_document(self, document: Document) -> List[Chunk]:
        """
        Process a document into chunks with embeddings.
        
        Args:
            document: Document to process
            
        Returns:
            List of processed chunks with embeddings
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.debug(f"Processing document {document.id} ({len(document.content)} chars)")
            
            # Step 1: Split document into chunks
            text_chunks = self.chunker.chunk_text(document.content)
            
            if not text_chunks:
                logger.warning(f"No chunks generated for document {document.id}")
                return []
            
            logger.debug(f"Generated {len(text_chunks)} chunks for document {document.id}")
            
            # Step 2: Create chunk objects
            chunks = []
            for i, (text, start_idx, end_idx) in enumerate(text_chunks):
                chunk_id = f"{document.id}_chunk_{i}"
                
                chunk = Chunk(
                    id=chunk_id,
                    document_id=document.id,
                    text=text,
                    start_index=start_idx,
                    end_index=end_idx,
                    metadata={
                        **document.metadata,
                        "chunk_index": i,
                        "chunk_count": len(text_chunks),
                        "document_type": document.type.value,
                        "source": document.source
                    }
                )
                chunks.append(chunk)
            
            # Step 3: Generate embeddings for all chunks
            texts = [chunk.text for chunk in chunks]
            embeddings = await self.embedder.embed_batch(texts)
            
            # Step 4: Assign embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            
            logger.debug(f"Successfully processed document {document.id} into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to process document {document.id}: {e}")
            raise ProcessingError(
                f"Document processing failed: {e}",
                document_id=document.id,
                stage="processing"
            )
    
    async def process_documents(self, documents: List[Document]) -> List[Chunk]:
        """
        Process multiple documents into chunks.
        
        Args:
            documents: List of documents to process
            
        Returns:
            List of all processed chunks
        """
        all_chunks = []
        
        for document in documents:
            try:
                chunks = await self.process_document(document)
                all_chunks.extend(chunks)
            except ProcessingError as e:
                logger.error(f"Failed to process document {document.id}: {e}")
                # Continue processing other documents
                continue
        
        logger.info(f"Processed {len(documents)} documents into {len(all_chunks)} total chunks")
        return all_chunks
    
    async def close(self) -> None:
        """Close the document processor and cleanup resources."""
        if self.embedder:
            await self.embedder.close()
        
        self._initialized = False
        logger.info("DocumentProcessor closed")
    
    @property
    def is_initialized(self) -> bool:
        """Check if the processor is initialized."""
        return self._initialized
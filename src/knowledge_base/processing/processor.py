"""
Document processor for the unified knowledge base system.

This module provides functionality for processing documents of various formats,
detecting document types, and converting between formats.
"""

import os
import logging
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Union
import re

from ..core.config import Config
from ..core.types import Document, DocumentType, TextChunk, ProcessingStatus, ChunkingResult
from ..core.exceptions import ProcessingError
from .metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Document processor that handles document type detection, format conversion,
    and coordinates the processing pipeline.
    """
    
    def __init__(self, config: Config):
        """Initialize document processor with configuration."""
        self.config = config
        
        # Initialize components
        # These will be lazily loaded when needed
        self._chunker = None
        self._embedder = None
        self._metadata_extractor = MetadataExtractor()
        
        # Initialize MIME type detection
        self._init_mime_types()
        
        # Track initialization status
        self._initialized = False
        
        logger.info("DocumentProcessor initialized")
    
    def _init_mime_types(self) -> None:
        """Initialize MIME type detection."""
        # Add additional MIME types that might not be in the default database
        mimetypes.add_type('text/markdown', '.md')
        mimetypes.add_type('text/markdown', '.markdown')
        mimetypes.add_type('text/plain', '.txt')
        mimetypes.add_type('application/json', '.json')
        mimetypes.add_type('text/csv', '.csv')
    
    async def initialize(self) -> None:
        """Initialize the document processor components."""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing DocumentProcessor components...")
            
            # Lazy-load chunker
            from .chunker import TextChunker
            self._chunker = TextChunker(self.config.chunking)
            
            # Lazy-load embedder
            from .embedder import Embedder
            self._embedder = Embedder(self.config.embedding)
            
            # Initialize embedder (chunker doesn't need initialization)
            await self._embedder.initialize()
            
            self._initialized = True
            logger.info("DocumentProcessor initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize DocumentProcessor: {e}")
            raise ProcessingError(f"DocumentProcessor initialization failed: {e}")
    
    def detect_document_type(self, content: str, filename: Optional[str] = None, 
                            mime_type: Optional[str] = None) -> DocumentType:
        """
        Detect the document type based on content, filename, or MIME type.
        
        Args:
            content: Document content
            filename: Optional filename with extension
            mime_type: Optional MIME type
            
        Returns:
            Detected DocumentType
        """
        # If MIME type is provided, use it for detection
        if mime_type:
            return self._document_type_from_mime(mime_type)
        
        # If filename is provided, use extension for detection
        if filename:
            ext = os.path.splitext(filename)[1].lower()
            
            # Check extension
            if ext in ['.txt']:
                return DocumentType.TEXT
            elif ext in ['.md', '.markdown']:
                return DocumentType.MARKDOWN
            elif ext in ['.html', '.htm']:
                return DocumentType.HTML
            elif ext in ['.pdf']:
                return DocumentType.PDF
            elif ext in ['.doc', '.docx']:
                return DocumentType.DOCX
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                return DocumentType.IMAGE
            elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.m4a']:
                return DocumentType.AUDIO
            elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.mkv']:
                return DocumentType.VIDEO
            elif ext in ['.py', '.js', '.java', '.cpp', '.cs', '.go', '.rs', '.php', '.rb', '.ts']:
                return DocumentType.CODE
        
        # Content-based detection as fallback
        return self._detect_type_from_content(content)
    
    def _document_type_from_mime(self, mime_type: str) -> DocumentType:
        """Convert MIME type to DocumentType."""
        mime_type = mime_type.lower()
        
        if mime_type.startswith('text/plain'):
            return DocumentType.TEXT
        elif mime_type.startswith('text/markdown'):
            return DocumentType.MARKDOWN
        elif mime_type.startswith('text/html'):
            return DocumentType.HTML
        elif mime_type.startswith('application/pdf'):
            return DocumentType.PDF
        elif mime_type.startswith(('application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml')):
            return DocumentType.DOCX
        elif mime_type.startswith('image/'):
            return DocumentType.IMAGE
        elif mime_type.startswith('audio/'):
            return DocumentType.AUDIO
        elif mime_type.startswith('video/'):
            return DocumentType.VIDEO
        elif mime_type.startswith(('text/x-', 'application/x-', 'application/json')):
            return DocumentType.CODE
        else:
            return DocumentType.UNKNOWN
    
    def _detect_type_from_content(self, content: str) -> DocumentType:
        """Detect document type based on content analysis."""
        # Check for HTML
        if re.search(r'<!DOCTYPE html>|<html[>\s]', content, re.IGNORECASE):
            return DocumentType.HTML
        
        # Check for Markdown
        if re.search(r'^#\s+|^##\s+|^\*\*.*\*\*|^-\s+|^```', content, re.MULTILINE):
            return DocumentType.MARKDOWN
        
        # Check for code (simplified detection)
        code_patterns = [
            r'import\s+[\w.]+|from\s+[\w.]+\s+import',  # Python
            r'function\s+\w+\s*\(|const\s+\w+\s*=|class\s+\w+\s*{',  # JavaScript/TypeScript
            r'public\s+class|private\s+\w+\(|def\s+\w+\s*\(',  # Java/C#/Python
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, content):
                return DocumentType.CODE
        
        # Default to plain text
        return DocumentType.TEXT
    
    def convert_document_format(self, document: Document, target_type: DocumentType) -> Document:
        """
        Convert a document from one format to another.
        
        Args:
            document: Source document
            target_type: Target document type
            
        Returns:
            Converted document
        """
        if document.type == target_type:
            return document
        
        # Create a new document with the same ID but different type
        converted_doc = Document(
            id=document.id,
            content=document.content,
            type=target_type,
            metadata=document.metadata.copy(),
            source=document.source
        )
        
        # Perform conversion based on source and target types
        if document.type == DocumentType.MARKDOWN and target_type == DocumentType.TEXT:
            # Strip Markdown formatting
            converted_doc.content = self._markdown_to_text(document.content)
        elif document.type == DocumentType.HTML and target_type == DocumentType.TEXT:
            # Strip HTML tags
            converted_doc.content = self._html_to_text(document.content)
        elif document.type == DocumentType.HTML and target_type == DocumentType.MARKDOWN:
            # Convert HTML to Markdown
            converted_doc.content = self._html_to_markdown(document.content)
        else:
            # For unsupported conversions, log a warning and return the original content
            logger.warning(f"Unsupported document conversion: {document.type} to {target_type}")
        
        return converted_doc
    
    def _markdown_to_text(self, content: str) -> str:
        """Convert Markdown to plain text."""
        # Remove headers
        text = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
        
        # Remove bold/italic markers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Remove links
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        
        # Remove images
        text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)
        
        # Remove horizontal rules
        text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
        
        return text
    
    def _html_to_text(self, content: str) -> str:
        """Convert HTML to plain text."""
        # Simple HTML tag removal (for complex HTML, consider using a library like BeautifulSoup)
        text = re.sub(r'<[^>]*>', '', content)
        
        # Decode HTML entities
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&apos;', "'")
        text = text.replace('&nbsp;', ' ')
        
        return text
    
    def _html_to_markdown(self, content: str) -> str:
        """Convert HTML to Markdown."""
        # This is a simplified conversion, for complex HTML consider using a library
        
        # Convert headers
        markdown = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', content)
        markdown = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', markdown)
        markdown = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', markdown)
        
        # Convert paragraphs
        markdown = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', markdown)
        
        # Convert links
        markdown = re.sub(r'<a[^>]*href="(.*?)"[^>]*>(.*?)</a>', r'[\2](\1)', markdown)
        
        # Convert emphasis
        markdown = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', markdown)
        markdown = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', markdown)
        
        # Convert lists
        markdown = re.sub(r'<ul[^>]*>(.*?)</ul>', r'\1', markdown, flags=re.DOTALL)
        markdown = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', markdown)
        
        # Remove remaining tags
        markdown = re.sub(r'<[^>]*>', '', markdown)
        
        return markdown
    
    async def process_document(self, document: Document) -> ChunkingResult:
        """
        Process a document into chunks with embeddings.
        
        Args:
            document: Document to process
            
        Returns:
            ChunkingResult containing processed chunks
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.debug(f"Processing document {document.id} ({len(document.content)} chars)")
            
            # Step 1: Extract and enhance document metadata if enabled
            if self.config.chunking.extract_metadata:
                enhanced_metadata = self._metadata_extractor.extract_document_metadata(document)
                
                # Update document with enhanced metadata
                document.metadata = enhanced_metadata
                logger.debug(f"Enhanced document metadata with {len(enhanced_metadata)} fields")
            
            # Step 2: Split document into chunks
            text_chunks = self._chunker.chunk_text(document.content)
            
            if not text_chunks:
                logger.warning(f"No chunks generated for document {document.id}")
                return ChunkingResult(document_id=document.id, chunks=[])
            
            logger.debug(f"Generated {len(text_chunks)} chunks for document {document.id}")
            
            # Step 3: Create chunk objects with enhanced metadata
            chunks = []
            for i, (text, start_idx, end_idx) in enumerate(text_chunks):
                chunk_id = f"{document.id}_chunk_{i}"
                
                # Create basic chunk
                chunk = TextChunk(
                    id=chunk_id,
                    text=text,
                    document_id=document.id,
                    metadata={
                        "chunk_index": i,
                        "chunk_count": len(text_chunks),
                        "document_type": document.type.value,
                        "source": document.source
                    },
                    start_index=start_idx,
                    end_index=end_idx
                )
                
                # Process chunk metadata based on configuration
                chunk_metadata = {}
                
                # Extract and enhance chunk metadata if enabled
                if self.config.chunking.extract_metadata:
                    chunk_metadata = self._metadata_extractor.extract_chunk_metadata(chunk, document)
                
                # Generate automatic metadata for the chunk text if enabled
                auto_metadata = {}
                if self.config.chunking.generate_automatic_metadata:
                    auto_metadata = self._metadata_extractor.generate_automatic_metadata(text)
                
                # Merge metadata (automatic metadata has lowest priority)
                merged_metadata = {**auto_metadata, **chunk_metadata, **document.metadata}
                chunk.metadata = merged_metadata
                
                chunks.append(chunk)
            
            # Step 4: Generate embeddings for all chunks
            texts = [chunk.text for chunk in chunks]
            embeddings = await self._embedder.embed_batch(texts)
            
            # Step 5: Assign embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            
            # Step 6: Prepare metadata for indexing if enabled
            if self.config.chunking.index_metadata:
                for chunk in chunks:
                    chunk.metadata = self._metadata_extractor.index_metadata(chunk.metadata)
                logger.debug(f"Indexed metadata for {len(chunks)} chunks")
            
            logger.debug(f"Successfully processed document {document.id} into {len(chunks)} chunks")
            
            return ChunkingResult(
                document_id=document.id,
                chunks=chunks,
                metadata={
                    "chunk_count": len(chunks),
                    "document_type": document.type.value,
                    "processing_time": 0.0,  # This would be calculated in a real implementation
                    "metadata_fields": list(chunks[0].metadata.keys()) if chunks else []
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to process document {document.id}: {e}")
            raise ProcessingError(
                f"Document processing failed: {e}",
                document_id=document.id,
                stage="processing"
            )
    
    async def process_documents(self, documents: List[Document]) -> List[ChunkingResult]:
        """
        Process multiple documents into chunks.
        
        Args:
            documents: List of documents to process
            
        Returns:
            List of ChunkingResults for all processed documents
        """
        results = []
        
        for document in documents:
            try:
                result = await self.process_document(document)
                results.append(result)
            except ProcessingError as e:
                logger.error(f"Failed to process document {document.id}: {e}")
                # Continue processing other documents
                continue
        
        logger.info(f"Processed {len(documents)} documents into {sum(len(r.chunks) for r in results)} total chunks")
        return results
    
    async def process_file(self, file_path: Union[str, Path], document_id: Optional[str] = None) -> Document:
        """
        Process a file into a Document object.
        
        Args:
            file_path: Path to the file
            document_id: Optional document ID (generated if not provided)
            
        Returns:
            Document object
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ProcessingError(f"File not found: {file_path}")
        
        try:
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Generate document ID if not provided
            if document_id is None:
                document_id = f"doc_{file_path.name}_{hash(content) % 10000}"
            
            # Detect document type
            doc_type = self.detect_document_type(content, filename=file_path.name, mime_type=mime_type)
            
            # Get file stats
            file_stats = file_path.stat()
            
            # Create document with basic metadata
            document = Document(
                id=document_id,
                content=content,
                type=doc_type,
                metadata={
                    "filename": file_path.name,
                    "file_size": file_stats.st_size,
                    "mime_type": mime_type or "unknown",
                    "created_time": file_stats.st_ctime,
                    "modified_time": file_stats.st_mtime,
                    "file_extension": file_path.suffix.lstrip(".").lower() if file_path.suffix else "",
                    "file_path": str(file_path.absolute())
                },
                source=str(file_path)
            )
            
            # Extract and enhance document metadata if enabled
            if self.config.chunking.extract_metadata:
                enhanced_metadata = self._metadata_extractor.extract_document_metadata(document)
                
                # Generate automatic metadata if enabled
                if self.config.chunking.generate_automatic_metadata:
                    auto_metadata = self._metadata_extractor.generate_automatic_metadata(content)
                    # Merge metadata (automatic metadata has lowest priority)
                    enhanced_metadata = {**auto_metadata, **enhanced_metadata}
                
                document.metadata = enhanced_metadata
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            raise ProcessingError(f"File processing failed: {e}", file_path=str(file_path))
    
    async def close(self) -> None:
        """Close the document processor and cleanup resources."""
        if self._embedder:
            await self._embedder.close()
        
        self._initialized = False
        logger.info("DocumentProcessor closed")
    
    @property
    def is_initialized(self) -> bool:
        """Check if the processor is initialized."""
        return self._initialized
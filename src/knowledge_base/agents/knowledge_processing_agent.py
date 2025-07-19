"""
Knowledge processing agent module for the knowledge base system.

This module implements the knowledge processing agent that is responsible for
processing documents into chunks and generating embeddings.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Union

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import AgentError, ProcessingError
from src.knowledge_base.core.types import Document, DocumentType, TextChunk, ChunkingResult
from src.knowledge_base.processing.processor import DocumentProcessor

from .base import BaseAgent
from .message import AgentMessage

logger = logging.getLogger(__name__)


class KnowledgeProcessingAgent(BaseAgent):
    """Agent responsible for processing documents into chunks with embeddings.
    
    The knowledge processing agent is responsible for:
    1. Processing documents into chunks
    2. Generating embeddings for chunks
    3. Extracting and enhancing metadata
    4. Batch processing multiple documents
    
    It acts as the central processing component in the knowledge base system,
    transforming raw documents into structured, vectorized chunks.
    """
    
    def __init__(self, config: Config, agent_id: str = "processing_agent"):
        """Initialize the knowledge processing agent.
        
        Args:
            config: The system configuration.
            agent_id: Unique identifier for this agent.
        """
        super().__init__(config, agent_id)
        
        # Register message handlers
        self.register_handler("task", self.handle_task)
        
        # Initialize document processor
        self.processor = DocumentProcessor(config)
        
        # Initialize batch processing settings
        self.batch_size = config.processing.batch_size if hasattr(config.processing, "batch_size") else 10
        self.max_concurrent_tasks = config.processing.max_concurrent_tasks if hasattr(config.processing, "max_concurrent_tasks") else 5
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
    
    async def start(self) -> None:
        """Start the agent and initialize the document processor."""
        await super().start()
        
        try:
            # Initialize the document processor
            await self.processor.initialize()
            logger.info(f"Knowledge processing agent {self.agent_id} started with initialized processor")
        except Exception as e:
            logger.error(f"Failed to initialize document processor: {e}")
            # Send error status message
            error_message = AgentMessage(
                source=self.agent_id,
                destination="*",
                message_type="agent_status",
                payload={
                    "status": "error",
                    "error": f"Failed to initialize document processor: {e}"
                }
            )
            await self.dispatch_message(error_message)
    
    async def stop(self) -> None:
        """Stop the agent and close the document processor."""
        try:
            # Close the document processor
            await self.processor.close()
            logger.info(f"Document processor closed for agent {self.agent_id}")
        except Exception as e:
            logger.error(f"Error closing document processor: {e}")
        
        await super().stop()
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message and return a response.
        
        Args:
            message: The message to process.
            
        Returns:
            The response message.
        """
        if message.message_type == "task":
            # Handle task messages through the registered handler
            await self.handle_task(message)
            return message.create_response({"status": "processing"})
        else:
            # For other message types, return a simple acknowledgment
            return message.create_response({"status": "acknowledged"})
    
    async def handle_task(self, message: AgentMessage) -> None:
        """Handle a task message.
        
        Args:
            message: The task message.
        """
        task_id = message.payload.get("task_id")
        task = message.payload.get("task")
        params = message.payload.get("params", {})
        
        if not task_id or not task:
            error_msg = "Missing task_id or task in task message"
            await self.dispatch_message(message.create_error_response(error_msg))
            return
        
        try:
            if task == "process_document":
                # Process a single document
                document = params.get("document")
                if not document:
                    raise AgentError("Missing document parameter")
                
                # Convert dict to Document object if needed
                if isinstance(document, dict):
                    document = Document(
                        id=document.get("id"),
                        content=document.get("content"),
                        type=DocumentType(document.get("type", "text")),
                        metadata=document.get("metadata", {}),
                        source=document.get("source", "")
                    )
                
                # Process the document
                result = await self.processor.process_document(document)
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "document_id": result.document_id,
                            "chunks": [self._chunk_to_dict(chunk) for chunk in result.chunks],
                            "chunk_count": len(result.chunks),
                            "metadata": result.metadata
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "process_documents":
                # Process multiple documents
                documents = params.get("documents", [])
                if not documents:
                    # Check if documents are available from collection agent
                    documents = params.get("collection", {}).get("documents", [])
                    if not documents:
                        raise AgentError("No documents to process")
                
                # Convert dicts to Document objects if needed
                doc_objects = []
                for doc in documents:
                    if isinstance(doc, dict):
                        doc_objects.append(Document(
                            id=doc.get("id"),
                            content=doc.get("content"),
                            type=DocumentType(doc.get("type", "text")),
                            metadata=doc.get("metadata", {}),
                            source=doc.get("source", "")
                        ))
                    else:
                        doc_objects.append(doc)
                
                # Process the documents in batches
                all_results = []
                for i in range(0, len(doc_objects), self.batch_size):
                    batch = doc_objects[i:i+self.batch_size]
                    batch_results = await self._process_batch(batch)
                    all_results.extend(batch_results)
                
                # Flatten chunks from all results
                all_chunks = []
                for result in all_results:
                    all_chunks.extend(result.chunks)
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "documents_processed": len(all_results),
                            "chunks_created": len(all_chunks),
                            "chunks": [self._chunk_to_dict(chunk) for chunk in all_chunks]
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            else:
                raise AgentError(f"Unsupported task: {task}")
                
        except Exception as e:
            logger.error(f"Error handling task {task} in knowledge processing agent: {e}")
            error_message = AgentMessage(
                source=self.agent_id,
                destination=message.source,
                message_type="task_error",
                payload={
                    "task_id": task_id,
                    "error": str(e),
                    "task": task
                }
            )
            await self.dispatch_message(error_message)
    
    async def _process_batch(self, documents: List[Document]) -> List[ChunkingResult]:
        """Process a batch of documents with concurrency control.
        
        Args:
            documents: List of documents to process.
            
        Returns:
            List of chunking results.
        """
        async def process_with_semaphore(doc):
            async with self.semaphore:
                return await self.processor.process_document(doc)
        
        # Process documents concurrently with semaphore limiting
        tasks = [process_with_semaphore(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing document {documents[i].id}: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    def _chunk_to_dict(self, chunk: TextChunk) -> Dict[str, Any]:
        """Convert a TextChunk to a dictionary representation.
        
        Args:
            chunk: The text chunk to convert.
            
        Returns:
            Dictionary representation of the chunk.
        """
        return {
            "id": chunk.id,
            "text": chunk.text,
            "document_id": chunk.document_id,
            "metadata": chunk.metadata,
            "embedding": chunk.embedding,
            "start_index": chunk.start_index if hasattr(chunk, "start_index") else None,
            "end_index": chunk.end_index if hasattr(chunk, "end_index") else None
        }
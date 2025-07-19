"""
RAG (Retrieval-Augmented Generation) agent module for the knowledge base system.

This module implements the RAG agent that is responsible for
generating answers to queries using retrieved information.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Union, AsyncIterator

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import AgentError, GenerationError
from src.knowledge_base.core.types import TextChunk, RetrievalResult, QueryResult
from src.knowledge_base.generation.generator import Generator
from src.knowledge_base.retrieval.retriever import Retriever
from src.knowledge_base.storage.vector_store import VectorStore

from .base import BaseAgent
from .message import AgentMessage

logger = logging.getLogger(__name__)


class RAGAgent(BaseAgent):
    """Agent responsible for retrieval-augmented generation.
    
    The RAG agent is responsible for:
    1. Coordinating the retrieval and generation process
    2. Generating answers based on retrieved information
    3. Managing the end-to-end RAG pipeline
    4. Providing streaming and non-streaming responses
    
    It acts as the central component for question answering,
    combining retrieval and generation capabilities.
    """
    
    def __init__(self, config: Config, agent_id: str = "rag_agent"):
        """Initialize the RAG agent.
        
        Args:
            config: The system configuration.
            agent_id: Unique identifier for this agent.
        """
        super().__init__(config, agent_id)
        
        # Register message handlers
        self.register_handler("task", self.handle_task)
        
        # Initialize vector store, retriever, and generator
        self.vector_store = VectorStore(config)
        self.retriever = None
        self.generator = None
        
        # Initialize streaming settings
        self.stream_chunk_size = 10  # Number of tokens per streaming chunk
    
    async def start(self) -> None:
        """Start the agent and initialize components."""
        await super().start()
        
        try:
            # Initialize the vector store
            await self.vector_store.initialize()
            
            # Initialize the retriever
            self.retriever = Retriever(self.config, self.vector_store._provider)
            
            # Initialize the generator
            self.generator = Generator(self.config)
            
            logger.info(f"RAG agent {self.agent_id} started with initialized components")
        except Exception as e:
            logger.error(f"Failed to initialize RAG agent components: {e}")
            # Send error status message
            error_message = AgentMessage(
                source=self.agent_id,
                destination="*",
                message_type="agent_status",
                payload={
                    "status": "error",
                    "error": f"Failed to initialize RAG agent components: {e}"
                }
            )
            await self.dispatch_message(error_message)
    
    async def stop(self) -> None:
        """Stop the agent and close the vector store."""
        try:
            # Close the vector store
            await self.vector_store.close()
            logger.info(f"Vector store closed for agent {self.agent_id}")
        except Exception as e:
            logger.error(f"Error closing vector store: {e}")
        
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
            if task == "generate":
                # Generate an answer for a query
                query = params.get("query")
                if not query:
                    raise AgentError("Missing query parameter")
                
                # Get optional parameters
                stream = params.get("stream", False)
                chunks = params.get("chunks")
                conversation_id = params.get("conversation_id")
                
                # If chunks are not provided, retrieve them
                if not chunks:
                    # Get chunks from retrieval agent results
                    chunks = params.get("retrieval", {}).get("chunks")
                    
                    # If still no chunks, retrieve them directly
                    if not chunks:
                        # Retrieve chunks for the query
                        retrieval_results = await self.retriever.retrieve(
                            query,
                            use_cache=True,
                            conversation_id=conversation_id
                        )
                        
                        # Convert retrieval results to chunks
                        chunks = [result.chunk for result in retrieval_results]
                else:
                    # Convert dict chunks to TextChunk objects if needed
                    chunks = [
                        TextChunk(
                            id=chunk.get("id"),
                            text=chunk.get("text"),
                            document_id=chunk.get("document_id"),
                            metadata=chunk.get("metadata", {}),
                            embedding=chunk.get("embedding")
                        ) if isinstance(chunk, dict) else chunk
                        for chunk in chunks
                    ]
                
                if not chunks:
                    # No chunks found, generate a fallback response
                    answer = "I don't have enough information to answer that question."
                    
                    # Send task completion message
                    completion_message = AgentMessage(
                        source=self.agent_id,
                        destination=message.source,
                        message_type="task_complete",
                        payload={
                            "task_id": task_id,
                            "result": {
                                "query": query,
                                "answer": answer,
                                "chunks": [],
                                "citations": []
                            }
                        }
                    )
                    
                    await self.dispatch_message(completion_message)
                    return
                
                # Generate the answer
                if stream:
                    # Handle streaming generation
                    await self._handle_streaming_generation(
                        task_id=task_id,
                        query=query,
                        chunks=chunks,
                        destination=message.source
                    )
                else:
                    # Handle non-streaming generation
                    result = await self.generator.generate(
                        query=query,
                        chunks=chunks,
                        stream=False,
                        validate=True,
                        include_citations=True
                    )
                    
                    # Format the result
                    if isinstance(result, QueryResult):
                        formatted_result = {
                            "query": query,
                            "answer": result.answer,
                            "chunks": [self._chunk_to_dict(chunk.chunk) for chunk in result.sources],
                            "citations": [
                                {
                                    "text": citation.text,
                                    "chunk_id": citation.chunk_id,
                                    "document_id": citation.document_id,
                                    "start": citation.start,
                                    "end": citation.end
                                }
                                for citation in result.citations
                            ] if hasattr(result, "citations") else []
                        }
                    else:
                        formatted_result = {
                            "query": query,
                            "answer": result,
                            "chunks": [self._chunk_to_dict(chunk) for chunk in chunks],
                            "citations": []
                        }
                    
                    # Send task completion message
                    completion_message = AgentMessage(
                        source=self.agent_id,
                        destination=message.source,
                        message_type="task_complete",
                        payload={
                            "task_id": task_id,
                            "result": formatted_result
                        }
                    )
                    
                    await self.dispatch_message(completion_message)
            
            elif task == "generate_stream":
                # Generate a streaming answer for a query
                query = params.get("query")
                if not query:
                    raise AgentError("Missing query parameter")
                
                # Get chunks and ensure they're in the right format
                chunks = params.get("chunks", [])
                
                # Convert dict chunks to TextChunk objects if needed
                chunks = [
                    TextChunk(
                        id=chunk.get("id"),
                        text=chunk.get("text"),
                        document_id=chunk.get("document_id"),
                        metadata=chunk.get("metadata", {}),
                        embedding=chunk.get("embedding")
                    ) if isinstance(chunk, dict) else chunk
                    for chunk in chunks
                ]
                
                if not chunks:
                    # No chunks found, generate a fallback response
                    error_message = AgentMessage(
                        source=self.agent_id,
                        destination=message.source,
                        message_type="task_error",
                        payload={
                            "task_id": task_id,
                            "error": "No relevant information found to answer the query",
                            "task": task
                        }
                    )
                    await self.dispatch_message(error_message)
                    return
                
                # Start the streaming generation
                # This will be handled by the generate_stream method which is called
                # directly from the orchestrator
                
                # Send a task completion message at the end
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "query": query,
                            "status": "streamed"
                        }
                    }
                )
                await self.dispatch_message(completion_message)
                
            else:
                raise AgentError(f"Unsupported task: {task}")
                
        except Exception as e:
            logger.error(f"Error handling task {task} in RAG agent: {e}")
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
    
    async def _handle_streaming_generation(
        self,
        task_id: str,
        query: str,
        chunks: List[TextChunk],
        destination: str
    ) -> None:
        """Handle streaming generation.
        
        Args:
            task_id: The task ID.
            query: The query to answer.
            chunks: The retrieved chunks.
            destination: The destination for the streaming messages.
        """
        try:
            # Start the streaming generation
            stream = await self.generator.generate(
                query=query,
                chunks=chunks,
                stream=True,
                validate=False,
                include_citations=False
            )
            
            # Send a start message
            start_message = AgentMessage(
                source=self.agent_id,
                destination=destination,
                message_type="stream_start",
                payload={
                    "task_id": task_id,
                    "query": query,
                    "chunks": [self._chunk_to_dict(chunk) for chunk in chunks]
                }
            )
            await self.dispatch_message(start_message)
            
            # Stream the chunks
            buffer = ""
            async for chunk in stream:
                buffer += chunk
                
                # Send chunks when buffer reaches a certain size
                if len(buffer) >= self.stream_chunk_size:
                    chunk_message = AgentMessage(
                        source=self.agent_id,
                        destination=destination,
                        message_type="stream_chunk",
                        payload={
                            "task_id": task_id,
                            "chunk": buffer
                        }
                    )
                    await self.dispatch_message(chunk_message)
                    buffer = ""
            
            # Send any remaining buffer
            if buffer:
                chunk_message = AgentMessage(
                    source=self.agent_id,
                    destination=destination,
                    message_type="stream_chunk",
                    payload={
                        "task_id": task_id,
                        "chunk": buffer
                    }
                )
                await self.dispatch_message(chunk_message)
            
            # Send an end message
            end_message = AgentMessage(
                source=self.agent_id,
                destination=destination,
                message_type="stream_end",
                payload={
                    "task_id": task_id,
                    "status": "completed"
                }
            )
            await self.dispatch_message(end_message)
            
            # Send a task completion message
            completion_message = AgentMessage(
                source=self.agent_id,
                destination=destination,
                message_type="task_complete",
                payload={
                    "task_id": task_id,
                    "result": {
                        "query": query,
                        "status": "streamed"
                    }
                }
            )
            await self.dispatch_message(completion_message)
            
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            
            # Send an error message
            error_message = AgentMessage(
                source=self.agent_id,
                destination=destination,
                message_type="stream_error",
                payload={
                    "task_id": task_id,
                    "error": str(e)
                }
            )
            await self.dispatch_message(error_message)
            
            # Send a task error message
            task_error_message = AgentMessage(
                source=self.agent_id,
                destination=destination,
                message_type="task_error",
                payload={
                    "task_id": task_id,
                    "error": str(e),
                    "task": "generate"
                }
            )
            await self.dispatch_message(task_error_message)
    
    async def generate_stream(self, message: AgentMessage) -> AsyncIterator[str]:
        """Generate a streaming response for a query.
        
        This method is called directly from the orchestrator to get a streaming
        response without going through the message passing system.
        
        Args:
            message: The task message containing query and chunks.
            
        Yields:
            Chunks of the generated response.
        """
        params = message.payload.get("params", {})
        query = params.get("query")
        chunks = params.get("chunks", [])
        
        if not query:
            yield "Error: Missing query parameter"
            return
        
        if not chunks:
            yield "I don't have enough information to answer that question."
            return
        
        # Convert dict chunks to TextChunk objects if needed
        chunks = [
            TextChunk(
                id=chunk.get("id"),
                text=chunk.get("text"),
                document_id=chunk.get("document_id"),
                metadata=chunk.get("metadata", {}),
                embedding=chunk.get("embedding")
            ) if isinstance(chunk, dict) else chunk
            for chunk in chunks
        ]
        
        try:
            # Generate streaming response
            stream = await self.generator.generate(
                query=query,
                chunks=chunks,
                stream=True,
                validate=False,
                include_citations=False
            )
            
            # Stream the response
            async for chunk in stream:
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield f"Error generating response: {str(e)}"
    
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
            "embedding": chunk.embedding if hasattr(chunk, "embedding") else None
        }
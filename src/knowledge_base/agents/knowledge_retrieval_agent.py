"""
Knowledge retrieval agent module for the knowledge base system.

This module implements the knowledge retrieval agent that is responsible for
retrieving relevant information from the knowledge base.
"""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional, Set, Union

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import AgentError, RetrievalError
from src.knowledge_base.core.types import SearchQuery, RetrievalResult
from src.knowledge_base.retrieval.retriever import Retriever
from src.knowledge_base.storage.vector_store import VectorStore

from .base import BaseAgent
from .message import AgentMessage

logger = logging.getLogger(__name__)


class KnowledgeRetrievalAgent(BaseAgent):
    """Agent responsible for retrieving relevant information from the knowledge base.
    
    The knowledge retrieval agent is responsible for:
    1. Processing search queries
    2. Retrieving relevant chunks from the vector store
    3. Formatting and ranking search results
    4. Managing conversation context for context-aware retrieval
    
    It acts as the search interface for the knowledge base system,
    providing relevant information based on user queries.
    """
    
    def __init__(self, config: Config, agent_id: str = "retrieval_agent"):
        """Initialize the knowledge retrieval agent.
        
        Args:
            config: The system configuration.
            agent_id: Unique identifier for this agent.
        """
        super().__init__(config, agent_id)
        
        # Register message handlers
        self.register_handler("task", self.handle_task)
        
        # Initialize vector store and retriever
        self.vector_store = VectorStore(config)
        self.retriever = None
        
        # Initialize conversation tracking
        self.active_conversations = {}
    
    async def start(self) -> None:
        """Start the agent and initialize the vector store and retriever."""
        await super().start()
        
        try:
            # Initialize the vector store
            await self.vector_store.initialize()
            
            # Initialize the retriever
            self.retriever = Retriever(self.config, self.vector_store._provider)
            
            logger.info(f"Knowledge retrieval agent {self.agent_id} started with initialized retriever")
        except Exception as e:
            logger.error(f"Failed to initialize retriever: {e}")
            # Send error status message
            error_message = AgentMessage(
                source=self.agent_id,
                destination="*",
                message_type="agent_status",
                payload={
                    "status": "error",
                    "error": f"Failed to initialize retriever: {e}"
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
            if task == "retrieve":
                # Retrieve chunks for a query
                query = params.get("query")
                if not query:
                    raise AgentError("Missing query parameter")
                
                # Get optional parameters
                filter_params = params.get("filter", {})
                top_k = params.get("top_k", self.config.retrieval.top_k if hasattr(self.config.retrieval, "top_k") else 5)
                conversation_id = params.get("conversation_id")
                
                # Create a search query
                search_query = SearchQuery(
                    text=query,
                    filters=filter_params,
                    top_k=top_k
                )
                
                # Retrieve relevant chunks
                results = await self.retriever.retrieve(
                    search_query,
                    use_cache=True,
                    conversation_id=conversation_id
                )
                
                # Format results
                formatted_results = self._format_retrieval_results(results)
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "query": query,
                            "chunks": formatted_results,
                            "count": len(results)
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "create_conversation":
                # Create a new conversation for context-aware retrieval
                metadata = params.get("metadata", {})
                
                # Create the conversation
                conversation_id = self.retriever.create_conversation(metadata)
                
                # Store the conversation ID
                self.active_conversations[conversation_id] = metadata
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "conversation_id": conversation_id,
                            "metadata": metadata
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "get_conversation_context":
                # Get the context for a conversation
                conversation_id = params.get("conversation_id")
                if not conversation_id:
                    raise AgentError("Missing conversation_id parameter")
                
                # Get the conversation context
                context = self.retriever.get_conversation_context(conversation_id)
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "conversation_id": conversation_id,
                            "context": context
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "delete_conversation":
                # Delete a conversation
                conversation_id = params.get("conversation_id")
                if not conversation_id:
                    raise AgentError("Missing conversation_id parameter")
                
                # Delete the conversation
                success = self.retriever.delete_conversation(conversation_id)
                
                # Remove from active conversations if successful
                if success and conversation_id in self.active_conversations:
                    del self.active_conversations[conversation_id]
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "conversation_id": conversation_id,
                            "success": success
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "clear_cache":
                # Clear the retrieval cache
                self.retriever.clear_cache()
                
                # Get cache stats
                cache_stats = self.retriever.get_cache_stats()
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "success": True,
                            "cache_stats": cache_stats
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            else:
                raise AgentError(f"Unsupported task: {task}")
                
        except Exception as e:
            logger.error(f"Error handling task {task} in knowledge retrieval agent: {e}")
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
    
    def _format_retrieval_results(self, results: List[RetrievalResult]) -> List[Dict[str, Any]]:
        """Format retrieval results for the response.
        
        Args:
            results: List of retrieval results.
            
        Returns:
            Formatted results as a list of dictionaries.
        """
        formatted_results = []
        
        for result in results:
            formatted_result = {
                "id": result.chunk.id,
                "text": result.chunk.text,
                "document_id": result.chunk.document_id,
                "metadata": result.chunk.metadata,
                "score": result.score,
                "rank": result.rank
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
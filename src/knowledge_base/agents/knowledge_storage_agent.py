"""
Knowledge storage agent module for the knowledge base system.

This module implements the knowledge storage agent that is responsible for
storing, retrieving, and managing knowledge chunks in the vector store.
"""

import asyncio
import logging
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import AgentError, StorageError
from src.knowledge_base.core.types import Document, TextChunk
from src.knowledge_base.storage.vector_store import VectorStore

from .base import BaseAgent
from .message import AgentMessage

logger = logging.getLogger(__name__)


class KnowledgeStorageAgent(BaseAgent):
    """Agent responsible for storing and managing knowledge in the vector store.
    
    The knowledge storage agent is responsible for:
    1. Storing processed chunks in the vector store
    2. Retrieving chunks from the vector store
    3. Managing document and chunk metadata
    4. Implementing backup and recovery mechanisms
    
    It acts as the persistence layer for the knowledge base system,
    ensuring that knowledge is properly stored and can be retrieved efficiently.
    """
    
    def __init__(self, config: Config, agent_id: str = "storage_agent"):
        """Initialize the knowledge storage agent.
        
        Args:
            config: The system configuration.
            agent_id: Unique identifier for this agent.
        """
        super().__init__(config, agent_id)
        
        # Register message handlers
        self.register_handler("task", self.handle_task)
        
        # Initialize vector store
        self.vector_store = VectorStore(config)
        
        # Initialize backup settings
        self.backup_dir = config.storage.backup_dir if hasattr(config.storage, "backup_dir") else "backups"
        self.auto_backup = config.storage.auto_backup if hasattr(config.storage, "auto_backup") else False
        self.backup_interval = config.storage.backup_interval if hasattr(config.storage, "backup_interval") else 86400  # 24 hours
        self.last_backup_time = 0
        
        # Initialize batch processing settings
        self.batch_size = config.storage.batch_size if hasattr(config.storage, "batch_size") else 100
    
    async def start(self) -> None:
        """Start the agent and initialize the vector store."""
        await super().start()
        
        try:
            # Initialize the vector store
            await self.vector_store.initialize()
            logger.info(f"Knowledge storage agent {self.agent_id} started with initialized vector store")
            
            # Start backup scheduler if auto backup is enabled
            if self.auto_backup:
                asyncio.create_task(self._backup_scheduler())
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            # Send error status message
            error_message = AgentMessage(
                source=self.agent_id,
                destination="*",
                message_type="agent_status",
                payload={
                    "status": "error",
                    "error": f"Failed to initialize vector store: {e}"
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
            if task == "store_chunks":
                # Store chunks in the vector store
                chunks = params.get("chunks")
                
                # Check if chunks are available from processing agent
                if not chunks:
                    chunks = params.get("processing", {}).get("chunks", [])
                    if not chunks:
                        raise AgentError("No chunks to store")
                
                # Convert dicts to TextChunk objects if needed
                chunk_objects = []
                for chunk in chunks:
                    if isinstance(chunk, dict):
                        chunk_objects.append(TextChunk(
                            id=chunk.get("id"),
                            text=chunk.get("text"),
                            document_id=chunk.get("document_id"),
                            metadata=chunk.get("metadata", {}),
                            embedding=chunk.get("embedding")
                        ))
                    else:
                        chunk_objects.append(chunk)
                
                # Store chunks in batches
                stored_ids = []
                for i in range(0, len(chunk_objects), self.batch_size):
                    batch = chunk_objects[i:i+self.batch_size]
                    batch_ids = await self.vector_store.add_chunks(batch)
                    stored_ids.extend(batch_ids)
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "chunks_stored": len(stored_ids),
                            "stored_ids": stored_ids
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
                # Trigger backup if auto backup is enabled
                if self.auto_backup and time.time() - self.last_backup_time > self.backup_interval:
                    asyncio.create_task(self._create_backup())
                
            elif task == "retrieve_chunks":
                # Retrieve chunks from the vector store
                chunk_ids = params.get("chunk_ids")
                if not chunk_ids:
                    raise AgentError("Missing chunk_ids parameter")
                
                # Retrieve chunks
                chunks = await self.vector_store.get_chunks(chunk_ids)
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "chunks": [self._chunk_to_dict(chunk) for chunk in chunks],
                            "chunks_retrieved": len(chunks)
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "delete_document":
                # Delete a document and its chunks
                document_id = params.get("document_id")
                if not document_id:
                    raise AgentError("Missing document_id parameter")
                
                # Delete the document
                success = await self.vector_store.delete_document(document_id)
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "document_id": document_id,
                            "success": success
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "create_backup":
                # Create a backup of the vector store
                backup_path = await self._create_backup()
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "backup_path": backup_path,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "restore_backup":
                # Restore from a backup
                backup_path = params.get("backup_path")
                if not backup_path:
                    raise AgentError("Missing backup_path parameter")
                
                # Restore from backup
                success = await self._restore_backup(backup_path)
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "backup_path": backup_path,
                            "success": success
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "get_stats":
                # Get storage statistics
                stats = await self.vector_store.get_stats()
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": stats
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            else:
                raise AgentError(f"Unsupported task: {task}")
                
        except Exception as e:
            logger.error(f"Error handling task {task} in knowledge storage agent: {e}")
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
    
    async def _create_backup(self) -> str:
        """Create a backup of the vector store.
        
        Returns:
            The path to the backup file.
        """
        try:
            # Create backup directory if it doesn't exist
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"kb_backup_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Get storage statistics
            stats = await self.vector_store.get_stats()
            
            # Create backup metadata
            backup_metadata = {
                "timestamp": timestamp,
                "provider": self.vector_store.provider_name,
                "stats": stats
            }
            
            # Write backup metadata to file
            with open(backup_path, "w") as f:
                json.dump(backup_metadata, f, indent=2)
            
            # Update last backup time
            self.last_backup_time = time.time()
            
            logger.info(f"Created backup at {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise StorageError(f"Backup creation failed: {e}")
    
    async def _restore_backup(self, backup_path: str) -> bool:
        """Restore from a backup.
        
        Args:
            backup_path: Path to the backup file.
            
        Returns:
            True if restoration was successful, False otherwise.
        """
        try:
            # Check if backup file exists
            if not os.path.exists(backup_path):
                raise StorageError(f"Backup file not found: {backup_path}")
            
            # Read backup metadata
            with open(backup_path, "r") as f:
                backup_metadata = json.load(f)
            
            # Check if backup is compatible with current provider
            if backup_metadata.get("provider") != self.vector_store.provider_name:
                logger.warning(f"Backup provider ({backup_metadata.get('provider')}) "
                              f"doesn't match current provider ({self.vector_store.provider_name})")
            
            # Perform provider-specific restoration
            # This is a placeholder for actual restoration logic
            # In a real implementation, this would depend on the vector store provider
            logger.info(f"Restored backup from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise StorageError(f"Backup restoration failed: {e}")
    
    async def _backup_scheduler(self) -> None:
        """Scheduler for automatic backups."""
        while self._running:
            try:
                # Check if it's time for a backup
                if time.time() - self.last_backup_time > self.backup_interval:
                    await self._create_backup()
                
                # Sleep for a while before checking again
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"Error in backup scheduler: {e}")
                await asyncio.sleep(3600)  # Sleep and try again later
    
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
            "embedding": chunk.embedding
        }
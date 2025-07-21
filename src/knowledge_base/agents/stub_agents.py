"""
Stub agent implementations for development purposes.
"""

import logging
from typing import Dict, Any

from src.knowledge_base.core.config import Config
from src.knowledge_base.agents.base import BaseAgent
from src.knowledge_base.agents.message import AgentMessage
from src.knowledge_base.agents.registry import register_agent, get_registry

logger = logging.getLogger(__name__)


class CollectionAgent(BaseAgent):
    """Stub implementation of the Collection Agent."""

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message.

        Args:
            message: The message to process.

        Returns:
            The response message.
        """
        logger.debug(f"CollectionAgent received message: {message.message_type}")
        return message.create_response({"status": "success"})


class ProcessingAgent(BaseAgent):
    """Stub implementation of the Processing Agent."""

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message.

        Args:
            message: The message to process.

        Returns:
            The response message.
        """
        logger.debug(f"ProcessingAgent received message: {message.message_type}")
        return message.create_response({"status": "success"})


class StorageAgent(BaseAgent):
    """Stub implementation of the Storage Agent."""

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message.

        Args:
            message: The message to process.

        Returns:
            The response message.
        """
        logger.debug(f"StorageAgent received message: {message.message_type}")
        return message.create_response({"status": "success"})


class RetrievalAgent(BaseAgent):
    """Stub implementation of the Retrieval Agent."""

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message.

        Args:
            message: The message to process.

        Returns:
            The response message.
        """
        logger.debug(f"RetrievalAgent received message: {message.message_type}")
        return message.create_response({"status": "success"})


class MaintenanceAgent(BaseAgent):
    """Stub implementation of the Maintenance Agent."""

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message.

        Args:
            message: The message to process.

        Returns:
            The response message.
        """
        logger.debug(f"MaintenanceAgent received message: {message.message_type}")
        return message.create_response({"status": "success"})


class RagAgent(BaseAgent):
    """Stub implementation of the RAG Agent."""

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message.

        Args:
            message: The message to process.

        Returns:
            The response message.
        """
        logger.debug(f"RagAgent received message: {message.message_type}")
        return message.create_response({"status": "success"})


# Register all agents
def register_stub_agents():
    """Register all stub agent implementations."""
    # Get the registry directly to avoid import issues
    registry = get_registry()

    # Register agents directly with the registry
    try:
        # Register agents with both the class name and the capitalized agent type
        # This ensures they can be found by both the orchestrator and other code
        registry.register("CollectionAgent", CollectionAgent)
        registry.register("ProcessingAgent", ProcessingAgent)
        registry.register("StorageAgent", StorageAgent)
        registry.register("RetrievalAgent", RetrievalAgent)
        registry.register("MaintenanceAgent", MaintenanceAgent)
        registry.register("RagAgent", RagAgent)

        # Also register with the names the orchestrator is looking for
        registry.register("collection", CollectionAgent)
        registry.register("processing", ProcessingAgent)
        registry.register("storage", StorageAgent)
        registry.register("retrieval", RetrievalAgent)
        registry.register("maintenance", MaintenanceAgent)
        registry.register("rag", RagAgent)

        logger.info("Registered stub agent implementations")
    except Exception as e:
        # If there's an error during registration, log it
        logger.warning(f"Error registering stub agents: {e}")


# Auto-register when this module is imported
register_stub_agents()
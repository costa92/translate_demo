"""
Agent module for the knowledge base system.
"""

from .base import AgentSystem, BaseAgent
from .message import AgentMessage
from .orchestrator import OrchestratorAgent
from .registry import (AgentRegistry, create_agent, get_registry,
                      register_agent)
from .stub_agents import (CollectionAgent, ProcessingAgent, StorageAgent,
                         RetrievalAgent, MaintenanceAgent, RagAgent)

__all__ = [
    "AgentSystem",
    "BaseAgent",
    "AgentMessage",
    "AgentRegistry",
    "get_registry",
    "register_agent",
    "create_agent",
    "OrchestratorAgent",
    "CollectionAgent",
    "ProcessingAgent",
    "StorageAgent",
    "RetrievalAgent",
    "MaintenanceAgent",
    "RagAgent"
]
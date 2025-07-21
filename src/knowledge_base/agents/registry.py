"""
Agent registry module for the knowledge base system.
"""

import importlib
import inspect
import logging
import os
import pkgutil
from typing import Dict, List, Optional, Set, Type

from knowledge_base.core.config import Config
from knowledge_base.core.exceptions import AgentError

from .base import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry for agent implementations.

    This class provides functionality for registering, discovering,
    and creating agent instances.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._agent_packages: Set[str] = set()

    def register(self, name: str, agent_class: Type[BaseAgent]) -> None:
        """Register an agent class.

        Args:
            name: The name of the agent.
            agent_class: The agent class.

        Raises:
            AgentError: If an agent with the same name is already registered.
        """
        if name in self._agent_classes:
            raise AgentError(f"Agent class '{name}' is already registered")

        self._agent_classes[name] = agent_class
        logger.debug(f"Registered agent class: {name}")

    def unregister(self, name: str) -> None:
        """Unregister an agent class.

        Args:
            name: The name of the agent.

        Raises:
            AgentError: If the agent is not registered.
        """
        if name not in self._agent_classes:
            raise AgentError(f"Agent class '{name}' is not registered")

        del self._agent_classes[name]
        logger.debug(f"Unregistered agent class: {name}")

    def get(self, name: str) -> Type[BaseAgent]:
        """Get an agent class by name.

        Args:
            name: The name of the agent.

        Returns:
            The agent class.

        Raises:
            AgentError: If the agent is not registered.
        """
        if name not in self._agent_classes:
            raise AgentError(f"Agent class '{name}' is not registered")

        return self._agent_classes[name]

    def list(self) -> List[str]:
        """List all registered agent classes.

        Returns:
            A list of agent class names.
        """
        return list(self._agent_classes.keys())

    def create(self, name: str, config: Config, agent_id: Optional[str] = None) -> BaseAgent:
        """Create an agent instance.

        Args:
            name: The name of the agent class.
            config: The system configuration.
            agent_id: Optional agent ID. If not provided, the name will be used.

        Returns:
            An instance of the agent.

        Raises:
            AgentError: If the agent is not registered.
        """
        agent_class = self.get(name)
        agent_id = agent_id or name
        return agent_class(config, agent_id)

    def register_package(self, package_name: str) -> None:
        """Register all agent classes in a package.

        This method discovers and registers all agent classes in the specified package.

        Args:
            package_name: The name of the package to scan.
        """
        if package_name in self._agent_packages:
            return

        self._agent_packages.add(package_name)

        try:
            package = importlib.import_module(package_name)
            package_path = getattr(package, "__path__", [])

            for _, module_name, is_pkg in pkgutil.iter_modules(package_path):
                full_module_name = f"{package_name}.{module_name}"

                try:
                    module = importlib.import_module(full_module_name)

                    # If it's a package, recursively register it
                    if is_pkg:
                        self.register_package(full_module_name)

                    # Find and register agent classes
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and
                            issubclass(obj, BaseAgent) and
                            obj is not BaseAgent):
                            self.register(name, obj)
                except Exception as e:
                    logger.error(f"Error loading module {full_module_name}: {e}")
        except Exception as e:
            logger.error(f"Error loading package {package_name}: {e}")

    def discover(self) -> None:
        """Discover and register all agent classes in the knowledge base package."""
        self.register_package("src.knowledge_base.agents")

        # Register TestResponseAgent for internal use
        from src.knowledge_base.agents.base import TestResponseAgent
        self.register("TestResponseAgent", TestResponseAgent)


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get the global agent registry instance.

    Returns:
        The global agent registry.
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def register_agent(name: str, agent_class: Type[BaseAgent]) -> None:
    """Register an agent class with the global registry.

    Args:
        name: The name of the agent.
        agent_class: The agent class.
    """
    get_registry().register(name, agent_class)


def create_agent(name: str, config: Config, agent_id: Optional[str] = None) -> BaseAgent:
    """Create an agent instance using the global registry.

    Args:
        name: The name of the agent class.
        config: The system configuration.
        agent_id: Optional agent ID.

    Returns:
        An instance of the agent.
    """
    return get_registry().create(name, config, agent_id)
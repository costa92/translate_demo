"""
Dependency injection for the API server.

This module provides dependency injection functions for the API server.
"""

from typing import Optional

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.monitoring import MonitoringSystem, get_monitoring_system
from src.knowledge_base.agents.orchestrator import OrchestratorAgent
from .websocket.handler import WebSocketManager

# Global variables for dependency injection
_config: Optional[Config] = None
_orchestrator: Optional[OrchestratorAgent] = None
_websocket_manager: Optional[WebSocketManager] = None
_monitoring_system: Optional[MonitoringSystem] = None


def get_config() -> Config:
    """Get the configuration instance.
    
    Returns:
        The configuration instance.
    """
    if _config is None:
        raise RuntimeError("Configuration not initialized")
    return _config


def get_orchestrator() -> OrchestratorAgent:
    """Get the orchestrator agent instance.
    
    Returns:
        The orchestrator agent instance.
    """
    if _orchestrator is None:
        raise RuntimeError("Orchestrator agent not initialized")
    return _orchestrator


def get_websocket_manager() -> WebSocketManager:
    """Get the WebSocket manager instance.
    
    Returns:
        The WebSocket manager instance.
    """
    if _websocket_manager is None:
        raise RuntimeError("WebSocket manager not initialized")
    return _websocket_manager


def get_monitoring() -> MonitoringSystem:
    """Get the monitoring system instance.
    
    Returns:
        The monitoring system instance.
    """
    global _monitoring_system
    
    if _monitoring_system is None:
        _monitoring_system = get_monitoring_system(_config)
    
    return _monitoring_system


def initialize_dependencies(config: Config) -> None:
    """Initialize dependencies.
    
    Args:
        config: The configuration instance.
    """
    global _config, _orchestrator, _websocket_manager, _monitoring_system
    
    # Store config for dependency injection
    _config = config
    
    # Initialize orchestrator agent
    _orchestrator = OrchestratorAgent(config)
    
    # Initialize monitoring system
    _monitoring_system = get_monitoring_system(config)
    
    # Initialize WebSocket manager
    _websocket_manager = WebSocketManager(config, _orchestrator)
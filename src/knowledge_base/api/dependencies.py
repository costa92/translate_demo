"""
Dependency injection for the API server.

This module provides dependency injection functions for the API server.
"""

from typing import Optional

from knowledge_base.core.config import Config
from knowledge_base.core.monitoring import MonitoringSystem, get_monitoring_system
from knowledge_base.agents.orchestrator import OrchestratorAgent
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


def get_orchestrator():
    """Get the orchestrator agent instance.
    
    Returns:
        The orchestrator agent instance.
    """
    if _orchestrator is None:
        import logging
        logging.warning("Orchestrator agent not initialized, returning None")
    return _orchestrator


def get_websocket_manager():
    """Get the WebSocket manager instance.
    
    Returns:
        The WebSocket manager instance.
    """
    if _websocket_manager is None:
        import logging
        logging.warning("WebSocket manager not initialized, returning None")
    return _websocket_manager


def get_monitoring():
    """Get the monitoring system instance.
    
    Returns:
        The monitoring system instance.
    """
    global _monitoring_system
    
    if _monitoring_system is None:
        import logging
        logging.warning("Monitoring system not initialized, returning None")
        try:
            _monitoring_system = get_monitoring_system(_config)
        except Exception as e:
            logging.warning(f"Failed to initialize monitoring system: {e}")
    
    return _monitoring_system


def initialize_dependencies(config: Config) -> None:
    """Initialize dependencies.
    
    Args:
        config: The configuration instance.
    """
    global _config, _orchestrator, _websocket_manager, _monitoring_system
    
    # Store config for dependency injection
    _config = config
    
    try:
        # Try to initialize orchestrator agent
        from knowledge_base.agents.orchestrator import OrchestratorAgent
        _orchestrator = OrchestratorAgent(config)
    except Exception as e:
        import logging
        logging.warning(f"Failed to initialize orchestrator agent: {e}")
        _orchestrator = None
    
    try:
        # Try to initialize monitoring system
        _monitoring_system = get_monitoring_system(config)
    except Exception as e:
        import logging
        logging.warning(f"Failed to initialize monitoring system: {e}")
        _monitoring_system = None
    
    try:
        # Try to initialize WebSocket manager
        _websocket_manager = WebSocketManager(config, _orchestrator)
    except Exception as e:
        import logging
        logging.warning(f"Failed to initialize WebSocket manager: {e}")
        _websocket_manager = None
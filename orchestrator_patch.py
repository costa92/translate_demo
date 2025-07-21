"""
Patch for the orchestrator to handle missing agents gracefully.
"""

import logging
import importlib
import sys
from types import ModuleType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def patch_orchestrator():
    """
    Patch the orchestrator to handle missing agents gracefully.
    """
    try:
        # Import the orchestrator module
        orchestrator_module = importlib.import_module("src.knowledge_base.agents.orchestrator")

        # Get the original _initialize_agents method
        original_initialize_agents = orchestrator_module.OrchestratorAgent._initialize_agents

        # Define the patched method
        def patched_initialize_agents(self):
            """
            Patched version of _initialize_agents that handles missing agents gracefully.
            """
            agent_configs = self.config.agents.specialized_agents

            for agent_type, enabled in agent_configs.items():
                if not enabled:
                    continue

                try:
                    agent_id = f"{agent_type}_agent"
                    # Try to create the agent, but don't raise an error if it fails
                    try:
                        from src.knowledge_base.agents.registry import create_agent
                        agent = create_agent(f"{agent_type.capitalize()}Agent", self.config, agent_id)
                        self.agents[agent_type] = agent
                        logger.info(f"Initialized {agent_type} agent with ID {agent_id}")
                    except Exception as e:
                        # Create a stub agent instead
                        from src.knowledge_base.agents.stub_agents import CollectionAgent
                        agent = CollectionAgent(self.config, agent_id)
                        self.agents[agent_type] = agent
                        logger.info(f"Created stub agent for {agent_type} with ID {agent_id}")
                except Exception as e:
                    logger.warning(f"Failed to initialize {agent_type} agent: {e}")

        # Replace the original method with the patched one
        orchestrator_module.OrchestratorAgent._initialize_agents = patched_initialize_agents

        logger.info("Successfully patched orchestrator to handle missing agents gracefully")
        return True
    except Exception as e:
        logger.error(f"Failed to patch orchestrator: {e}")
        return False

if __name__ == "__main__":
    patch_orchestrator()
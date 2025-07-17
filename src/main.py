"""
Main entry point for the unified knowledge base system.
"""

import asyncio
from knowledge_base import KnowledgeBase, Config


async def main():
    """
    Main entry point for the knowledge base system.
    """
    # Create configuration
    config = Config()
    
    # Initialize knowledge base
    kb = KnowledgeBase(config)
    await kb.initialize()
    
    # Example usage
    print("Knowledge Base System initialized successfully!")
    
    # Clean up resources
    await kb.close()


if __name__ == "__main__":
    asyncio.run(main())
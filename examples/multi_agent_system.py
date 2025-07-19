#!/usr/bin/env python
"""
Multi-agent system example for the Unified Knowledge Base System.

This example demonstrates how to use the multi-agent system for knowledge management.
"""

import asyncio
from src.knowledge_base.core.config import Config
from src.knowledge_base.agents.orchestrator import OrchestratorAgent


async def main():
    """Run the multi-agent system example."""
    # Create configuration
    config = Config()
    
    # Initialize orchestrator agent
    orchestrator = OrchestratorAgent(config)
    
    print("Unified Knowledge Base System - Multi-Agent Example")
    print("==================================================")
    
    # Start the agent system
    print("\n1. Starting agent system...")
    await orchestrator.start()
    
    # Add a document
    print("\n2. Adding a document...")
    response = await orchestrator.receive_request(
        source="example",
        request_type="add_document",
        payload={
            "content": """
            # Multi-Agent Architecture
            
            The Unified Knowledge Base System uses a multi-agent architecture with specialized agents:
            
            1. Orchestrator Agent - Coordinates the workflow
            2. Data Collection Agent - Collects data from various sources
            3. Knowledge Processing Agent - Processes documents into chunks
            4. Knowledge Storage Agent - Manages storage operations
            5. Knowledge Retrieval Agent - Handles query processing
            6. Knowledge Maintenance Agent - Performs maintenance tasks
            7. RAG Agent - Implements end-to-end RAG pipeline
            
            These agents communicate using a standardized message format and work together
            to provide comprehensive knowledge management capabilities.
            """,
            "metadata": {
                "title": "Multi-Agent Architecture",
                "format": "markdown",
                "source": "documentation"
            }
        }
    )
    
    print(f"Document added with ID: {response['document_id']}")
    print(f"Created {len(response['chunk_ids'])} chunks")
    
    # Query the knowledge base
    print("\n3. Querying the knowledge base...")
    response = await orchestrator.receive_request(
        source="example",
        request_type="query",
        payload={
            "query": "What agents are part of the system?",
            "metadata_filter": {"source": "documentation"}
        }
    )
    
    print(f"\nAnswer: {response['answer']}")
    print("\nSources:")
    for i, chunk in enumerate(response['chunks']):
        print(f"  {i+1}. {chunk['text'][:100]}...")
    
    # Get system status
    print("\n4. Getting system status...")
    response = await orchestrator.receive_request(
        source="example",
        request_type="get_status",
        payload={}
    )
    
    print("System status:")
    for component, status in response['status'].items():
        print(f"  {component}: {status}")
    
    # Stop the agent system
    print("\n5. Stopping agent system...")
    await orchestrator.stop()
    print("Agent system stopped")


if __name__ == "__main__":
    asyncio.run(main())
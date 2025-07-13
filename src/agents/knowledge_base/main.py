
"""
Main execution file for the Knowledge Base Multi-Agent System.

This script demonstrates a full end-to-end workflow and showcases the
flexibility of the storage provider system.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.agents.knowledge_base.orchestrator_agent import OrchestratorAgent
from src.agents.knowledge_base.data_collection_agent import DataCollectionAgent
from src.agents.knowledge_base.knowledge_processing_agent import KnowledgeProcessingAgent
from src.agents.knowledge_base.knowledge_storage_agent import KnowledgeStorageAgent
from src.agents.knowledge_base.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from src.agents.knowledge_base.knowledge_maintenance_agent import KnowledgeMaintenanceAgent

def run_workflow(knowledge_storage_agent: KnowledgeStorageAgent):
    """
    Runs a demonstration of the knowledge base multi-agent system with a given storage agent.
    """
    # 1. Initialize all other agents
    orchestrator = OrchestratorAgent()
    data_collection_agent = DataCollectionAgent()
    knowledge_processing_agent = KnowledgeProcessingAgent()
    knowledge_retrieval_agent = KnowledgeRetrievalAgent()
    knowledge_maintenance_agent = KnowledgeMaintenanceAgent()

    # 2. Register agents with the orchestrator
    orchestrator.register_agent("DataCollectionAgent", data_collection_agent)
    orchestrator.register_agent("KnowledgeProcessingAgent", knowledge_processing_agent)
    orchestrator.register_agent("KnowledgeStorageAgent", knowledge_storage_agent)
    orchestrator.register_agent("KnowledgeRetrievalAgent", knowledge_retrieval_agent)
    orchestrator.register_agent("KnowledgeMaintenanceAgent", knowledge_maintenance_agent)

    # 3. Step-by-step workflow simulation

    # Step 1: Collect data
    print("\n--- 1. KNOWLEDGE COLLECTION ---")
    collection_payload = {"source": "test_documents", "path": "/path/to/docs"}
    collected_docs = orchestrator.receive_request("user_request", "collect", collection_payload)
    print(f"Orchestrator received {len(collected_docs)} documents.")
    if collected_docs:
        print(f"Sample collected doc ID: {collected_docs[0].id}, Content: '{collected_docs[0].content}'")

    # Step 2: Process knowledge
    print("\n--- 2. KNOWLEDGE PROCESSING ---")
    processed_chunks = orchestrator.receive_request("data_collection", "process", collected_docs)
    print(f"Orchestrator processed documents into {len(processed_chunks)} chunks.")
    if processed_chunks:
        print(f"Sample processed chunk ID: {processed_chunks[0].id}, Vector: {processed_chunks[0].vector}")

    # Step 3: Store knowledge
    print("\n--- 3. KNOWLEDGE STORAGE ---")
    storage_success = orchestrator.receive_request("knowledge_processing", "store", processed_chunks)
    print(f"Orchestrator storage status: {'Success' if storage_success else 'Failed'}")

    # Step 4: Retrieve knowledge
    print("\n--- 4. KNOWLEDGE RETRIEVAL ---")
    retrieval_payload = {"query": "What is this document about?", "search_params": {"top_k": 1}}
    retrieved_results = orchestrator.receive_request("user_query", "retrieve", retrieval_payload)
    print(f"Orchestrator retrieved {len(retrieved_results)} results for the query.")
    if retrieved_results:
        print(f"Top answer: '{retrieved_results[0].content}' with score {retrieved_results[0].relevance_score}")


def main():
    """
    Main function to demonstrate different storage providers.
    """
    print("=========================================================")
    print("  RUNNING WORKFLOW WITH: In-Memory Storage Provider")
    print("=========================================================")
    memory_storage_agent = KnowledgeStorageAgent(provider_type='memory')
    run_workflow(memory_storage_agent)

    print("\n" + "="*57)
    print("  RUNNING WORKFLOW WITH: Notion Storage Provider (Placeholder)")
    print("="*57)
    # Example configuration for Notion
    notion_config = {
        "api_key": "YOUR_NOTION_API_KEY_HERE",
        "database_id": "YOUR_NOTION_DATABASE_ID_HERE"
    }
    notion_storage_agent = KnowledgeStorageAgent(provider_type='notion', provider_config=notion_config)
    run_workflow(notion_storage_agent)

    print("\n--- End of Demonstration ---")

if __name__ == "__main__":
    main()

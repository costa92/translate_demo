# RAG Pipeline Demonstration using OrchestratorAgent
# This demonstrates the full RAG pipeline with simplified components.

import asyncio
from agents.knowledge_base.orchestrator_agent import OrchestratorAgent

async def run_rag_demo():
    """Demonstrates the full RAG pipeline using OrchestratorAgent."""
    print("==================================================================")
    print("    RAG Pipeline Demonstration")
    print("====================================================================\n")

    # --- 1. Setup Orchestrator ---
    orchestrator = OrchestratorAgent()

    # --- 2. Add Knowledge ---
    print("--- Step 1: Adding knowledge to the system ---")
    add_knowledge_payload = {
        "sources": [
            {"type": "text", "location": "The sky is blue during the day.", "metadata": {"source": "facts.txt"}},
            {"type": "text", "location": "The grass is green in spring.", "metadata": {"source": "facts.txt"}},
            {"type": "text", "location": "NPX is used to install Gemini CLI.", "metadata": {"source": "docs.txt"}},
        ]
    }
    result = await orchestrator.receive_request(
        source="user",
        request_type="add_knowledge",
        payload=add_knowledge_payload
    )
    print(f"Knowledge added: {result}")

    # --- 3. Query the Knowledge Base ---
    print("\n--- Step 2: Querying the knowledge base ---")
    query = "What color is the sky?"
    query_payload = {
        "query": query,
        "search_params": {
            "top_k": 3
        }
    }
    query_result = await orchestrator.receive_request(
        source="user",
        request_type="query",
        payload=query_payload
    )
    print(f"Query: {query}")
    print(f"Answer: {query_result['answer']}")
    print(f"Retrieved sources: {len(query_result['retrieved_sources'])}")

    print("\n--- Demo Finished ---")

if __name__ == "__main__":
    asyncio.run(run_rag_demo())


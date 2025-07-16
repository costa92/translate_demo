# Debug RAG Pipeline to check retrieval scores

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from agents.knowledge_base.orchestrator_agent import OrchestratorAgent

async def debug_rag_demo():
    """Debug the RAG pipeline to check retrieval scores."""
    print("==================================================================")
    print("    Debug RAG Pipeline")
    print("====================================================================\n")

    llm_config = {
        'provider': 'deepseek',
        'model': 'deepseek-chat',
        'use_semantic_search': True,
        'relevance_threshold': 0.1,  # 降低阈值以便调试
    }
    # --- 1. Setup Orchestrator ---
    orchestrator = OrchestratorAgent(llm_config=llm_config)

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
    
    # Debug: Show retrieved sources with scores
    for i, source in enumerate(query_result['retrieved_sources']):
        print(f"  Source {i+1}: {source['content']} (Score: {source['relevance_score']:.3f})")

    # --- 4. Test another query ---
    print("\n--- Step 3: Testing another query ---")
    query2 = "How to install using NPX?"
    query_payload2 = {
        "query": query2,
        "search_params": {
            "top_k": 3
        }
    }
    query_result2 = await orchestrator.receive_request(
        source="user",
        request_type="query",
        payload=query_payload2
    )
    print(f"Query: {query2}")
    print(f"Answer: {query_result2['answer']}")
    print(f"Retrieved sources: {len(query_result2['retrieved_sources'])}")
    
    # Debug: Show retrieved sources with scores
    for i, source in enumerate(query_result2['retrieved_sources']):
        print(f"  Source {i+1}: {source['content']} (Score: {source['relevance_score']:.3f})")

    print("\n--- Debug Finished ---")

if __name__ == "__main__":
    asyncio.run(debug_rag_demo())
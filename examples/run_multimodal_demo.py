import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.knowledge_base.agents.orchestrator import OrchestratorAgent

async def main():
    """
    Demonstrates processing and storing multimodal data (text and images).
    """
    # Initialize the orchestrator agent
    orchestrator = OrchestratorAgent()

    # 1. Define knowledge sources, including an image
    knowledge_sources = [
        {
            "type": "text",
            "location": "This is a text document about a cat."
        },
        {
            "type": "image",
            "location": "path/to/your/cat_image.jpg" # This path is a mock
        }
    ]

    # 2. Add the knowledge to the system
    # The orchestrator will use the agents to process and store it.
    add_knowledge_payload = {
        "sources": knowledge_sources
    }
    result = await orchestrator.receive_request(
        source="user",
        request_type="add_knowledge",
        payload=add_knowledge_payload
    )

    print("--- Add Knowledge Result ---")
    print(result)

    # 3. Query the knowledge base with a multimodal query
    # (This part is a conceptual placeholder for how it might work)
    query_payload = {
        "query": "What is in the image?",
        "search_params": {
            "multimodal_query": True # A flag to indicate a multimodal query
        }
    }
    query_result = await orchestrator.receive_request(
        source="user",
        request_type="query",
        payload=query_payload
    )

    print("\n--- Query Result ---")
    print(query_result)

if __name__ == "__main__":
    asyncio.run(main())

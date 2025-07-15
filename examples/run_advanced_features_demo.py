

import asyncio
from agents.knowledge_base.orchestrator_agent import OrchestratorAgent

async def main():
    """
    Demonstrates the advanced features: Knowledge Staging and Tree of Thoughts (ToT).
    """
    print("--- Initializing Advanced Features Demo ---")

    # Initialize the orchestrator agent
    # We can pass agent-specific configurations if needed
    orchestrator = OrchestratorAgent()

    # --- 1. Demonstrate Knowledge Staging Workflow ---
    print("\n--- Step 1: Knowledge Staging Workflow ---")

    # a) Simulate finding new knowledge. This will be added to the staging area.
    print("\n1a. Maintenance agent is checking for new knowledge...")
    maintenance_payload = {"source": "some_monitored_source", "content": "a newly discovered piece of information"}
    maintenance_result = await orchestrator.receive_request("system", "maintain", maintenance_payload)
    print(f"Maintenance result: {maintenance_result}")

    # b) List items in the staging area to confirm the new chunk is there.
    storage_agent = orchestrator.agents['KnowledgeStorageAgent']
    staged_items = await storage_agent.list_staged_chunks()
    print(f"\n1b. Items currently in staging area: {staged_items}")
    assert len(staged_items) > 0, "Staging area should have items!"

    # c) Query for the new knowledge. It should NOT be found yet.
    print("\n1c. Querying for staged knowledge (should fail)...")
    query_payload_fail = {"query": "newly discovered piece of information"}
    query_result_fail = await orchestrator.receive_request("user", "query", query_payload_fail)
    print(f"Query Answer: {query_result_fail['answer']}")
    assert "I don't have relevant information" in query_result_fail['answer'], "Query should not find staged content!"

    # d) Validate and promote the chunk from staging to the main knowledge base.
    chunk_to_promote = staged_items[0]
    print(f"\n1d. Validating and promoting chunk '{chunk_to_promote}'...")
    await storage_agent.validate_and_promote(chunk_to_promote)

    # e) Query for the knowledge again. It should now be found.
    print("\n1e. Querying for promoted knowledge (should succeed)...")
    query_payload_success = {"query": "newly discovered piece of information"}
    query_result_success = await orchestrator.receive_request("user", "query", query_payload_success)
    print(f"Query Answer: {query_result_success['answer']}")
    assert "I don't have relevant information" not in query_result_success['answer'], "Query should find promoted content!"

    print("\n--- Knowledge Staging Workflow Demo Complete ---")


    # --- 2. Demonstrate Tree of Thoughts (ToT) Framework ---
    print("\n--- Step 2: Tree of Thoughts (ToT) Framework ---")

    # Add some initial data for the ToT to reason about
    add_knowledge_payload = {
        "documents": [
            {"content": "Freedonia has a 20% tax on all digital services.", "metadata": {"source": "Freedonia Tax Code"}},
            {"content": "The tax is applied to the net revenue of the company.", "metadata": {"source": "Freedonia Tax Code"}},
            {"content": "Digital service companies must report their revenue quarterly.", "metadata": {"source": "Freedonia Tax Regulations"}},
        ]
    }
    result = await orchestrator.receive_request(
        source="user",
        request_type="add_knowledge",
        payload=add_knowledge_payload
    )

    # Use the ToT framework to answer a complex query
    print("\n2a. Running a query with the ToT framework enabled...")
    tot_payload = {
        "query": "What is the total tax impact for a digital service company in Freedonia?",
        "search_params": {
            "use_tot": True,
            "max_depth": 2,
            "beam_width": 2
        }
    }
    tot_result = await orchestrator.receive_request("user", "query", tot_payload)

    print(f"\nToT Final Answer (Best Thought): {tot_result['answer']}")
    print(f"Retrieved sources for final answer: {tot_result['retrieved_sources']}")

    print("\n--- Tree of Thoughts (ToT) Demo Complete ---")


if __name__ == "__main__":
    asyncio.run(main())


"""
Example script demonstrating how to use the KnowledgeStorageAgent with different storage providers.

This script shows:
1. How to initialize the KnowledgeStorageAgent with the default 'memory' provider.
2. How to configure and initialize the agent with other providers like 'notion' or 'oss'.
3. How to perform basic operations like store and retrieve.
"""




from agents.knowledge_base.knowledge_storage_agent import KnowledgeStorageAgent
from agents.knowledge_base.knowledge_processing_agent import ProcessedKnowledgeChunk

async def run_demo_for_provider(storage_agent: KnowledgeStorageAgent):
    """Runs a simple store and retrieve demo for a given storage agent instance."""
    provider_name = storage_agent.provider.__class__.__name__
    print(f"--- Running Demo for: {provider_name} ---")

    # 1. Create some dummy data to store
    chunks_to_store = [
        ProcessedKnowledgeChunk(
            id="chunk_001",
            original_id="doc_A",
            text_content="The sky is blue.",
            vector=[0.1, 0.2, 0.8],
            category="facts",
            entities=["sky"],
            relationships=[],
            metadata={"source": "nature.txt"}
        ),
        ProcessedKnowledgeChunk(
            id="chunk_002",
            original_id="doc_B",
            text_content="The grass is green.",
            vector=[0.2, 0.8, 0.1],
            category="facts",
            entities=["grass"],
            relationships=[],
            metadata={"source": "nature.txt"}
        )
    ]
    print(f"Attempting to store {len(chunks_to_store)} chunks...")
    success = await storage_agent.store(chunks_to_store)
    print(f"Store operation successful: {success}")

    # 2. Retrieve the data
    print("\nAttempting to retrieve chunks...")
    # In a real scenario, the query_vector would come from an embedding of a user's query
    retrieved_chunks = storage_agent.retrieve(query_vector=[0.15, 0.3, 0.7], top_k=1, filters={})
    print(f"Retrieved {len(retrieved_chunks)} chunks.")
    if retrieved_chunks:
        print(f"  -> Retrieved chunk ID: {retrieved_chunks[0].id}")
        print(f"  -> Content: {retrieved_chunks[0].text_content}")

    print("--- Demo Finished ---\n")


async def main():
    """Main function to demonstrate various provider configurations."""
    print("==================================================")
    print(" KnowledgeStorageAgent Provider Demonstration")
    print("==================================================\n")

    # --- Demo 1: In-Memory Storage (Default) ---
    # No configuration needed.
    memory_agent = KnowledgeStorageAgent(provider_type='memory')
    await run_demo_for_provider(memory_agent)

    # NOTE: Skipping other provider demos to avoid configuration errors
    print("NOTE: Notion and OSS demos skipped - require valid configuration")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

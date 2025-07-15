
import asyncio
from agents.knowledge_base.orchestrator_agent import OrchestratorAgent

async def main():
    orchestrator = OrchestratorAgent()
    storage_agent = orchestrator.agents['KnowledgeStorageAgent']

    # 1. Add an item to staging
    await orchestrator.receive_request("system", "maintain", {"source": "test", "content": "test content for staging"})

    # 2. Check if it's in staging
    staged_items = await storage_agent.list_staged_chunks()
    print(f"Staged items: {staged_items}")
    assert len(staged_items) > 0

if __name__ == "__main__":
    asyncio.run(main())

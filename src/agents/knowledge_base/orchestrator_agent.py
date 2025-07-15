import asyncio
from typing import Dict, Any, List, Optional
from .data_collection_agent import DataCollectionAgent
from .knowledge_processing_agent import KnowledgeProcessingAgent
from .knowledge_storage_agent import KnowledgeStorageAgent
from .knowledge_retrieval_agent import KnowledgeRetrievalAgent
from .knowledge_maintenance_agent import KnowledgeMaintenanceAgent

class OrchestratorAgent:
    def __init__(self, 
                 storage_provider: str = 'memory',
                 storage_config: Dict[str, Any] = None,
                 llm_config: Dict[str, Any] = None):
        self.agents = {}
        self.llm_config = llm_config or {}
        
        # Initialize all agents
        self._initialize_agents(storage_provider, storage_config)
        
    def _initialize_agents(self, storage_provider: str, storage_config: Dict[str, Any]):
        """Initialize all agents and register them."""
        # Initialize storage agent first
        storage_agent = KnowledgeStorageAgent(
            provider_type=storage_provider,
            provider_config=storage_config
        )
        
        # Initialize other agents
        self.agents = {
            'DataCollectionAgent': DataCollectionAgent(),
            'KnowledgeProcessingAgent': KnowledgeProcessingAgent(),
            'KnowledgeStorageAgent': storage_agent,
            'KnowledgeRetrievalAgent': KnowledgeRetrievalAgent(storage_agent),
            'KnowledgeMaintenanceAgent': KnowledgeMaintenanceAgent(storage_agent),
        }
        
    def register_agent(self, agent_name: str, agent_instance: Any):
        """Register additional agents."""
        self.agents[agent_name] = agent_instance

    async def receive_request(self, source: str, request_type: str, payload: Dict):
        """
        Main entry point for handling requests.
        Enhanced to support complex workflows including full RAG pipeline.
        """
        try:
            if request_type == "add_knowledge":
                return await self._handle_add_knowledge(payload)
            elif request_type == "query":
                return await self._handle_query(payload)
            elif request_type == "collect":
                return await self.distribute_task("DataCollectionAgent", "collect", payload)
            elif request_type == "process":
                return await self.distribute_task("KnowledgeProcessingAgent", "process", payload)
            elif request_type == "store":
                return await self.distribute_task("KnowledgeStorageAgent", "store", payload)
            elif request_type == "retrieve":
                return await self.distribute_task("KnowledgeRetrievalAgent", "search", payload)
            elif request_type == "maintain":
                return await self.distribute_task("KnowledgeMaintenanceAgent", "check_updates", payload)
            else:
                return {"status": "error", "message": "Unknown request type"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _handle_add_knowledge(self, payload: Dict) -> Dict:
        """
        Handle full knowledge addition workflow: collect -> process -> store
        """
        sources = payload.get('sources', [])
        processing_options = payload.get('processing_options', {})
        
        all_documents = []
        
        # Step 1: Collect from all sources
        for source in sources:
            try:
                documents = await self.distribute_task("DataCollectionAgent", "collect", source)
                # Check if result is an error
                if isinstance(documents, dict) and documents.get('status') == 'error':
                    return documents
                # If successful, it should be a list of documents
                if isinstance(documents, list):
                    all_documents.extend(documents)
                else:
                    return {"status": "error", "message": f"Unexpected response from data collection: {type(documents)}"}
            except Exception as e:
                return {"status": "error", "message": f"Collection failed: {str(e)}"}
        
        if not all_documents:
            return {"status": "error", "message": "No documents collected"}
        
        # Step 2: Process documents
        try:
            processed_chunks = await self.distribute_task("KnowledgeProcessingAgent", "process", all_documents)
            if isinstance(processed_chunks, dict) and processed_chunks.get('status') == 'error':
                return processed_chunks
            if not processed_chunks:
                return {"status": "error", "message": "Processing failed"}
        except Exception as e:
            return {"status": "error", "message": f"Processing failed: {str(e)}"}
            
        # Step 3: Store processed chunks
        try:
            storage_result = await self.distribute_task("KnowledgeStorageAgent", "store", processed_chunks)
            if isinstance(storage_result, dict) and storage_result.get('status') == 'error':
                return storage_result
            if not storage_result:
                return {"status": "error", "message": "Storage failed"}
        except Exception as e:
            return {"status": "error", "message": f"Storage failed: {str(e)}"}
        
        return {
            "status": "success",
            "message": f"Successfully processed and stored {len(processed_chunks)} knowledge chunks",
            "chunks_count": len(processed_chunks),
            "sources_processed": len(sources)
        }

    async def _handle_query(self, payload: Dict) -> Dict:
        """
        Handle RAG query workflow: retrieve -> generate
        """
        query = payload.get('query', '')
        search_params = payload.get('search_params', {})
        
        if not query:
            return {"status": "error", "message": "Query is required"}
            
        # Step 1: Retrieve relevant knowledge
        try:
            search_payload = {"query": query, **search_params}
            retrieved_candidates = await self.distribute_task("KnowledgeRetrievalAgent", "search", search_payload)
            
            if not retrieved_candidates:
                return {
                    "status": "success",
                    "answer": "I don't have relevant information to answer your question.",
                    "retrieved_sources": []
                }
        except Exception as e:
            return {"status": "error", "message": f"Retrieval failed: {str(e)}"}
        
        # Step 2: Generate answer using retrieved context
        try:
            answer = self._generate_answer(query, retrieved_candidates)
            
            # Format retrieved sources
            sources = []
            for candidate in retrieved_candidates:
                sources.append({
                    "source_id": candidate.source_id,
                    "content": candidate.content[:200] + "..." if len(candidate.content) > 200 else candidate.content,
                    "relevance_score": candidate.relevance_score
                })
            
            return {
                "status": "success",
                "answer": answer,
                "retrieved_sources": sources,
                "sources_count": len(sources)
            }
        except Exception as e:
            return {"status": "error", "message": f"Answer generation failed: {str(e)}"}

    def _generate_answer(self, query: str, retrieved_candidates: List) -> str:
        """
        Generate answer using retrieved context.
        TODO: Integrate with actual LLM (OpenAI, Anthropic, etc.)
        """
        if not retrieved_candidates:
            return "I don't have relevant information to answer your question."
        
        # Simple template-based answer generation for now
        context_snippets = []
        for candidate in retrieved_candidates[:3]:  # Use top 3 results
            context_snippets.append(candidate.content[:300])  # Truncate for context
        
        context = "\n\n".join(context_snippets)
        
        # TODO: Replace with actual LLM call
        answer = f"""Based on the available information, here's what I can tell you about your question "{query}":

{context}

Please note: This is a simplified response. For more accurate answers, an LLM integration is needed."""
        
        return answer

    async def distribute_task(self, agent_name: str, task_name: str, task_params: Dict):
        """Enhanced task distribution with better error handling."""
        if agent_name not in self.agents:
            return {"status": "error", "message": f"Agent {agent_name} not found"}
            
        agent = self.agents[agent_name]
        
        if not hasattr(agent, task_name):
            return {"status": "error", "message": f"Task {task_name} not found in agent {agent_name}"}
        
        try:
            task_method = getattr(agent, task_name)
            # Check if the method is async
            if asyncio.iscoroutinefunction(task_method):
                return await task_method(task_params)
            else:
                return task_method(task_params)
        except Exception as e:
            return {"status": "error", "message": f"Task execution failed: {str(e)}"}

    def aggregate_result(self, source_agent: str, status: str, result: Dict):
        """
        Enhanced result aggregation."""
        print(f"Result from {source_agent}: {status} - {result}")
        return {"status": "aggregated", "result": result}
        
    def get_agent_status(self) -> Dict:
        """
        Get status of all registered agents."""
        return {
            "registered_agents": list(self.agents.keys()),
            "storage_provider": type(self.agents['KnowledgeStorageAgent'].provider).__name__,
            "status": "ready"
        }
import asyncio
from typing import Dict, Any, List, Optional
from .data_collection_agent import DataCollectionAgent
from .knowledge_processing_agent import KnowledgeProcessingAgent
from .knowledge_storage_agent import KnowledgeStorageAgent
from .knowledge_retrieval_agent import KnowledgeRetrievalAgent
from .knowledge_maintenance_agent import KnowledgeMaintenanceAgent
from .rag_agent import RAGAgent

class OrchestratorAgent:
    def __init__(self,
                 storage_provider: str = 'memory',
                 storage_config: Dict[str, Any] = None,
                 llm_config: Dict[str, Any] = None):
        self.agents = {}
        self.llm_config = llm_config or {}
        
        # Configuration parameters (previously hardcoded)
        self.config = {
            'relevance_threshold': self.llm_config.get('relevance_threshold', 0.3),
            'max_context_length': self.llm_config.get('max_context_length', 500),
            'top_candidates': self.llm_config.get('top_candidates', 3),
            'source_preview_length': self.llm_config.get('source_preview_length', 200),
            'enable_fallback': self.llm_config.get('enable_fallback', True),
            'default_language': self.llm_config.get('default_language', 'zh')
        }

        # Initialize all agents
        self._initialize_agents(storage_provider, storage_config)

    def _initialize_agents(self, storage_provider: str, storage_config: Dict[str, Any]):
        """Initialize all agents and register them."""
        # Check if we should use enhanced storage
        use_enhanced_storage = self.llm_config.get('use_semantic_search', True)
        
        if use_enhanced_storage:
            # Use enhanced storage with semantic search
            from .improved_rag.enhanced_storage_provider import EnhancedMemoryStorageProvider
            from .improved_rag.semantic_retriever import SimpleEmbeddingProvider, LLMEmbeddingProvider
            
            # Use simple embedding provider by default to avoid API issues
            # Can be switched to LLM embedding when API keys are available
            use_llm_embedding = self.llm_config.get('use_llm_embedding', False)
            
            if use_llm_embedding:
                try:
                    from llm_core.client import LLMClient
                    llm_provider = self.llm_config.get('provider', 'openai')
                    llm_model = self.llm_config.get('model', None)
                    llm_client = LLMClient(provider=llm_provider, model=llm_model)
                    embedding_provider = LLMEmbeddingProvider(llm_client)
                    print("Using LLM embedding provider")
                except Exception as e:
                    print(f"Failed to initialize LLM embedding provider: {e}")
                    print("Falling back to simple embedding provider")
                    embedding_provider = SimpleEmbeddingProvider()
            else:
                print("Using simple embedding provider")
                embedding_provider = SimpleEmbeddingProvider()
            
            # Initialize enhanced storage agent
            enhanced_storage = EnhancedMemoryStorageProvider(
                config=storage_config or {},
                embedding_provider=embedding_provider
            )
            storage_agent = KnowledgeStorageAgent(
                provider_type='custom',
                provider_config={},
                custom_provider=enhanced_storage
            )
        else:
            # Use original storage agent
            storage_agent = KnowledgeStorageAgent(
                provider_type=storage_provider,
                provider_config=storage_config
            )

        # Initialize RAG agent with LLM configuration
        llm_provider = self.llm_config.get('provider', 'openai')
        print("llm_provider",llm_provider)
        llm_model = self.llm_config.get('model', None)
        rag_agent = RAGAgent(llm_provider=llm_provider, model=llm_model)

        # Initialize other agents
        self.agents = {
            'DataCollectionAgent': DataCollectionAgent(),
            'KnowledgeProcessingAgent': KnowledgeProcessingAgent(),
            'KnowledgeStorageAgent': storage_agent,
            'KnowledgeRetrievalAgent': KnowledgeRetrievalAgent(storage_agent),
            'KnowledgeMaintenanceAgent': KnowledgeMaintenanceAgent(storage_agent),
            'RAGAgent': rag_agent,
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

            # Format retrieved sources with configurable preview length
            sources = []
            preview_length = self.config['source_preview_length']
            for candidate in retrieved_candidates:
                sources.append({
                    "source_id": candidate.source_id,
                    "content": candidate.content[:preview_length] + "..." if len(candidate.content) > preview_length else candidate.content,
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
        Generate answer using retrieved context with actual LLM integration.
        """
        if not retrieved_candidates:
            no_info_msg = "我没有找到相关信息来回答您的问题。" if self.config['default_language'] == 'zh' else "I don't have relevant information to answer your question."
            return no_info_msg

        # Filter candidates by configurable relevance score threshold
        relevant_threshold = self.config['relevance_threshold']
        relevant_candidates = [
            candidate for candidate in retrieved_candidates
            if candidate.relevance_score > relevant_threshold
        ]

        if not relevant_candidates:
            insufficient_info_msg = "我没有找到足够相关的信息来回答您的问题。" if self.config['default_language'] == 'zh' else "I couldn't find sufficiently relevant information to answer your question."
            return insufficient_info_msg

        # Sort by relevance score and take configurable top results
        relevant_candidates.sort(key=lambda x: x.relevance_score, reverse=True)
        top_candidates = relevant_candidates[:self.config['top_candidates']]

        # Build context from relevant candidates with configurable max length
        context_snippets = []
        for candidate in top_candidates:
            # Truncate content based on configurable max length
            max_length = self.config['max_context_length']
            content = candidate.content[:max_length] if len(candidate.content) > max_length else candidate.content
            context_snippets.append(content)

        # Use RAG agent to generate precise answer
        try:
            rag_agent = self.agents.get('RAGAgent')
            if rag_agent:
                print(f"Using RAG agent with LLM provider: {self.llm_config.get('provider', 'openai')}")
                answer = rag_agent.generate(query, context_snippets)
                return answer
            else:
                # Fallback to simple context return if RAG agent not available
                return self._intelligent_fallback(query, context_snippets)
        except Exception as e:
            print(f"RAG generation failed: {e}")
            # Fallback to intelligent answer generation
            return self._intelligent_fallback(query, context_snippets)

    def _intelligent_fallback(self, query: str, context_snippets: List[str]) -> str:
        """
        Intelligent fallback answer generation when LLM is not available.
        Removes hardcoded logic and provides context-based responses.
        """
        if not self.config['enable_fallback']:
            return "LLM服务暂时不可用，无法生成答案。" if self.config['default_language'] == 'zh' else "LLM service is temporarily unavailable."
        
        if not context_snippets:
            return "我没有找到相关信息来回答您的问题。" if self.config['default_language'] == 'zh' else "I couldn't find relevant information to answer your question."
        
        # Intelligent context-based response without hardcoded rules
        if self.config['default_language'] == 'zh':
            # For Chinese queries, provide context with explanation
            if len(context_snippets) == 1:
                return f"根据相关信息：{context_snippets[0]}"
            else:
                combined_context = " ".join(context_snippets[:2])  # Use top 2 snippets
                return f"根据相关信息：{combined_context}"
        else:
            # For English queries
            if len(context_snippets) == 1:
                return f"Based on the available information: {context_snippets[0]}"
            else:
                combined_context = " ".join(context_snippets[:2])
                return f"Based on the available information: {combined_context}"

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

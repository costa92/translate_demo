from typing import List, Dict
from .knowledge_storage_agent import KnowledgeStorageAgent
from .storage_providers.base import RetrievedChunk


class AnswerCandidate:
    def __init__(self, content: str, source_id: str, relevance_score: float, context_snippets: List[str]):
        self.content = content
        self.source_id = source_id
        self.relevance_score = relevance_score
        self.context_snippets = context_snippets


class KnowledgeRetrievalAgent:
    def __init__(self, storage_agent: KnowledgeStorageAgent):
        self.storage_agent = storage_agent

    def search(self, params: Dict) -> List[AnswerCandidate]:
        query = params.get("query")
        print(f"Searching for query: {query}")

        # Use a dummy vector for now, as we don't have a text-to-vector model yet.
        dummy_vector = [0.1, 0.2, 0.3]

        # Create filters including the query text for content-based matching
        filters = params.get("filters", {})
        if query:
            filters["query_text"] = query

        # Retrieve chunks from the storage agent
        retrieved_chunks: List[RetrievedChunk] = self.storage_agent.retrieve(
            query_vector=dummy_vector,
            top_k=params.get("top_k", 5), # Get top_k from params or default to 5
            filters=filters
        )

        # Transform retrieved chunks into answer candidates
        answer_candidates = []
        for chunk in retrieved_chunks:
            answer_candidates.append(
                AnswerCandidate(
                    content=chunk.text_content,
                    source_id=chunk.id,
                    relevance_score=chunk.score,
                    context_snippets=[chunk.text_content] # Use the content as a snippet
                )
            )

        return answer_candidates

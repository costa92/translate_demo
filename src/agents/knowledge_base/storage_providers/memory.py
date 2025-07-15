from typing import List, Dict, Any
from .base import BaseStorageProvider, RetrievedChunk

class MemoryStorageProvider(BaseStorageProvider):
    """
    A simple in-memory storage provider for demonstration and testing.
    Knowledge is lost when the application stops.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.vector_db: Dict[str, Any] = {}

    def store(self, chunks: List[Any]) -> bool:
        print(f"[MemoryProvider] Storing {len(chunks)} chunks.")
        for chunk in chunks:
            self.vector_db[chunk.id] = chunk
        return True

    def retrieve(self, query_vector: List[float], top_k: int, filters: Dict) -> List[RetrievedChunk]:
        print(f"[MemoryProvider] Retrieving top {top_k} chunks.")
        # This is a simplistic simulation. A real implementation would calculate vector similarity.
        retrieved_chunks = []
        for chunk_id, chunk in self.vector_db.items():
            # Apply filters if any (simple key-value match)
            if all(item in chunk.metadata.items() for item in filters.items()):
                retrieved_chunks.append(
                    RetrievedChunk(
                        id=chunk.id,
                        text_content=chunk.text_content,
                        score=0.9,  # Dummy score
                        metadata=chunk.metadata
                    )
                )
        return retrieved_chunks[:top_k]

    def get_all_chunk_ids(self) -> List[str]:
        print("[MemoryProvider] Fetching all chunk IDs.")
        return list(self.vector_db.keys())

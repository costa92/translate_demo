from abc import ABC, abstractmethod
from typing import List, Dict, Any
from agents.knowledge_base.knowledge_processing_agent import ProcessedKnowledgeChunk

class RetrievedChunk:
    def __init__(self, id: str, text_content: str, score: float, metadata: Dict):
        self.id = id
        self.text_content = text_content
        self.score = score
        self.metadata = metadata

class BaseStorageProvider(ABC):
    """
    Abstract base class for all knowledge storage providers.
    It defines the contract that every provider must follow.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the provider with necessary configuration.
        e.g., API keys, endpoints, database paths.
        """
        self.config = config
        print(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    def store(self, chunks: List[ProcessedKnowledgeChunk]) -> bool:
        """
        Stores a list of processed knowledge chunks in the backend.
        Returns True on success, False on failure.
        """
        pass

    @abstractmethod
    def retrieve(self, query_vector: List[float], top_k: int, filters: Dict) -> List['RetrievedChunk']:
        """
        Retrieves the top_k most relevant chunks based on a query vector.
        Can be filtered by metadata.
        """
        pass

    @abstractmethod
    def get_all_chunk_ids(self) -> List[str]:
        """
        Retrierieves all chunk IDs from the storage.
        """
        pass
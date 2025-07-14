from typing import List, Dict, Any
from agents.knowledge_base.knowledge_processing_agent import ProcessedKnowledgeChunk
from .storage_providers.base import BaseStorageProvider, RetrievedChunk
from .storage_providers.memory import MemoryStorageProvider
from .storage_providers.notion import NotionStorageProvider
from .storage_providers.oss import OSSStorageProvider
from .storage_providers.google_drive import GoogleDriveStorageProvider
from .storage_providers.google_drive_service_account import GoogleDriveServiceAccountProvider
from .storage_providers.gcs import GCSStorageProvider
from .storage_providers.onedrive import OneDriveStorageProvider

class KnowledgeStorageAgent:
    """
    Acts as a context for the storage strategy. It delegates the actual storage
    operations to a specific provider (strategy) chosen at initialization.
    """

    def __init__(self, provider_type: str = 'memory', provider_config: Dict[str, Any] = None):
        self.provider = self._create_provider(provider_type, provider_config)

    def _create_provider(self, provider_type: str, config: Dict[str, Any]) -> BaseStorageProvider:
        """Factory method to create a storage provider instance."""
        provider_map = {
            "memory": MemoryStorageProvider,
            "notion": NotionStorageProvider,
            "oss": OSSStorageProvider,
            "google_drive": GoogleDriveStorageProvider,
            "google_drive_service_account": GoogleDriveServiceAccountProvider,
            "gcs": GCSStorageProvider,
            "onedrive": OneDriveStorageProvider,
        }
        provider_class = provider_map.get(provider_type.lower())
        if not provider_class:
            raise ValueError(f"Unsupported storage provider type: {provider_type}")
        
        return provider_class(config)

    def store(self, chunks: List[ProcessedKnowledgeChunk]) -> bool:
        """
        Delegates the store operation to the chosen provider.
        """
        return self.provider.store(chunks)

    def retrieve(self, query_vector: List[float], top_k: int, filters: Dict) -> List[RetrievedChunk]:
        """
        Delegates the retrieve operation to the chosen provider.
        """
        return self.provider.retrieve(query_vector, top_k, filters)

    def get_all_chunk_ids(self) -> List[str]:
        """
        Delegates the get_all_chunk_ids operation to the chosen provider.
        """
        return self.provider.get_all_chunk_ids()
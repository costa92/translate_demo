"""
Vector store factory and main interface.

This module provides a factory for creating vector store instances based on configuration,
as well as a unified interface to different vector storage providers.
"""

import logging
from typing import List, Dict, Any, Optional, Type

from ..core.config_fixed import Config
from ..core.exceptions import StorageError, ConfigurationError
from ..core.types import Document, TextChunk
from ..core.registry import registry
from .base import BaseVectorStore

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """
    Factory class for creating vector store instances.
    
    This class provides methods for creating vector store instances based on
    configuration settings and for registering vector store providers.
    """
    
    @staticmethod
    def create(config: Config) -> BaseVectorStore:
        """
        Create a vector store based on configuration.
        
        Args:
            config: Configuration object with storage settings
            
        Returns:
            Initialized BaseVectorStore instance
            
        Raises:
            ConfigurationError: If the specified provider is unknown or configuration is invalid
        """
        provider_name = config.storage.provider
        
        try:
            # Try to get the provider from the registry
            provider_class = registry.get("storage", provider_name)
            return provider_class(config=config)
        except ValueError:
            # If not in registry, try the built-in providers
            if provider_name == "memory":
                from .providers.memory import MemoryVectorStore
                return MemoryVectorStore(config=config)
            elif provider_name == "notion":
                from .providers.notion import NotionVectorStore
                return NotionVectorStore(config=config)
            elif provider_name == "chroma":
                from .providers.chroma import ChromaVectorStore
                return ChromaVectorStore(config=config)
            elif provider_name == "pinecone":
                from .providers.pinecone import PineconeVectorStore
                return PineconeVectorStore(config=config)
            elif provider_name == "weaviate":
                from .providers.weaviate import WeaviateVectorStore
                return WeaviateVectorStore(config=config)
            elif provider_name == "gcs":
                from .providers.gcs import GCSVectorStore
                return GCSVectorStore(config=config)
            elif provider_name == "google_drive":
                from .providers.google_drive import GoogleDriveVectorStore
                return GoogleDriveVectorStore(config=config)
            elif provider_name == "google_drive_service_account":
                from .providers.google_drive_service_account import GoogleDriveServiceAccountVectorStore
                return GoogleDriveServiceAccountVectorStore(config=config)
            elif provider_name == "onedrive":
                from .providers.onedrive import OneDriveVectorStore
                return OneDriveVectorStore(config=config)
            elif provider_name == "oss":
                from .providers.oss import OSSVectorStore
                return OSSVectorStore(config=config)
            else:
                raise ConfigurationError(f"Unknown vector store provider: {provider_name}")
    
    @staticmethod
    def register_provider(name: str, provider_class: Type[BaseVectorStore]) -> None:
        """
        Register a vector store provider.
        
        Args:
            name: Name of the provider
            provider_class: Provider class implementation
            
        Example:
            >>> from my_package import MyCustomVectorStore
            >>> VectorStoreFactory.register_provider("custom", MyCustomVectorStore)
        """
        registry.register("storage", name, provider_class)
    
    @staticmethod
    def list_providers() -> List[str]:
        """
        List all registered vector store providers.
        
        Returns:
            List of provider names
        """
        # Get providers from registry
        registered_providers = registry.list("storage")
        
        # Add built-in providers if not already in the list
        built_in_providers = ["memory", "notion", "chroma", "pinecone", "weaviate", 
                             "gcs", "google_drive", "google_drive_service_account", "onedrive", "oss"]
        for provider in built_in_providers:
            if provider not in registered_providers:
                registered_providers.append(provider)
        
        return registered_providers
    
    @staticmethod
    def discover_providers() -> None:
        """
        Discover and register vector store providers from the providers package.
        
        This method scans the providers package for classes that inherit from BaseVectorStore
        and registers them with the registry.
        """
        registry.register_discovered(
            component_type="storage",
            package_path="src.knowledge_base.storage.providers",
            base_class=BaseVectorStore,
            name_attribute="provider_name"
        )


class VectorStore:
    """
    Vector store main interface.
    
    Provides a unified interface to different vector storage providers.
    """
    
    def __init__(self, config: Config):
        """Initialize vector store with configuration."""
        self.config = config
        self._provider: Optional[BaseVectorStore] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the vector store provider."""
        if self._initialized:
            return
        
        try:
            logger.info(f"Initializing vector store with provider: {self.config.storage.provider}")
            
            # Create provider instance using the factory
            self._provider = VectorStoreFactory.create(self.config)
            
            # Initialize the provider
            await self._provider.initialize()
            self._initialized = True
            
            logger.info(f"Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise StorageError(f"Vector store initialization failed: {e}")
    
    async def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """Add texts to the vector store."""
        await self._ensure_initialized()
        
        try:
            logger.debug(f"Adding {len(texts)} texts to vector store")
            return await self._provider.add_texts(texts, metadatas, ids, embeddings)
        except Exception as e:
            logger.error(f"Failed to add texts: {e}")
            raise StorageError(f"Failed to add texts: {e}", operation="add_texts")
    
    async def add_documents(
        self,
        documents: List[Document]
    ) -> List[str]:
        """Add documents to the vector store."""
        await self._ensure_initialized()
        
        try:
            logger.debug(f"Adding {len(documents)} documents to vector store")
            return await self._provider.add_documents(documents)
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise StorageError(f"Failed to add documents: {e}", operation="add_documents")
    
    async def add_chunks(
        self,
        chunks: List[TextChunk]
    ) -> List[str]:
        """Add chunks to the vector store."""
        await self._ensure_initialized()
        
        if not chunks:
            return []
        
        try:
            logger.debug(f"Adding {len(chunks)} chunks to vector store")
            return await self._provider.add_chunks(chunks)
        except Exception as e:
            logger.error(f"Failed to add chunks: {e}")
            raise StorageError(f"Failed to add chunks: {e}", operation="add_chunks")
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        await self._ensure_initialized()
        
        try:
            return await self._provider.get_document(document_id)
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise StorageError(f"Failed to get document: {e}", operation="get_document")
    
    async def get_chunk(self, chunk_id: str) -> Optional[TextChunk]:
        """Get a specific chunk by ID."""
        await self._ensure_initialized()
        
        try:
            return await self._provider.get_chunk(chunk_id)
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id}: {e}")
            raise StorageError(f"Failed to get chunk: {e}", operation="get_chunk")
    
    async def get_chunks(
        self,
        chunk_ids: List[str]
    ) -> List[TextChunk]:
        """Get multiple chunks by their IDs."""
        await self._ensure_initialized()
        
        try:
            return await self._provider.get_chunks(chunk_ids)
        except Exception as e:
            logger.error(f"Failed to get chunks: {e}")
            raise StorageError(f"Failed to get chunks: {e}", operation="get_chunks")
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filter: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        await self._ensure_initialized()
        
        try:
            logger.debug(f"Searching for {k} similar vectors")
            return await self._provider.similarity_search(
                query=query,
                k=k,
                filter=filter,
                embedding=embedding
            )
        except Exception as e:
            logger.error(f"Failed to search similar vectors: {e}")
            raise StorageError(f"Failed to search similar vectors: {e}", operation="similarity_search")
    
    async def keyword_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for texts using keyword matching."""
        await self._ensure_initialized()
        
        try:
            logger.debug(f"Performing keyword search for {k} results")
            return await self._provider.keyword_search(
                query=query,
                k=k,
                filter=filter
            )
        except Exception as e:
            logger.error(f"Failed to perform keyword search: {e}")
            raise StorageError(f"Failed to perform keyword search: {e}", operation="keyword_search")
    
    async def delete(self, ids: List[str]) -> bool:
        """Delete texts from the vector store by IDs."""
        await self._ensure_initialized()
        
        if not ids:
            return True
        
        try:
            logger.debug(f"Deleting {len(ids)} items")
            return await self._provider.delete(ids)
        except Exception as e:
            logger.error(f"Failed to delete items: {e}")
            raise StorageError(f"Failed to delete items: {e}", operation="delete")
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks belonging to a document."""
        await self._ensure_initialized()
        
        try:
            logger.debug(f"Deleting document {document_id}")
            return await self._provider.delete_document(document_id)
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise StorageError(f"Failed to delete document: {e}", operation="delete_document")
    
    async def update_metadata(
        self,
        id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Update metadata for a specific text or document."""
        await self._ensure_initialized()
        
        try:
            logger.debug(f"Updating metadata for {id}")
            return await self._provider.update_metadata(id, metadata)
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            raise StorageError(f"Failed to update metadata: {e}", operation="update_metadata")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        await self._ensure_initialized()
        
        try:
            stats = await self._provider.get_stats()
            stats["provider"] = self.config.storage.provider
            stats["initialized"] = self._initialized
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "provider": self.config.storage.provider,
                "initialized": self._initialized,
                "error": str(e)
            }
    
    async def clear(self) -> bool:
        """Clear all data from the vector store."""
        await self._ensure_initialized()
        
        try:
            logger.warning("Clearing all data from vector store")
            return await self._provider.clear()
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
            raise StorageError(f"Failed to clear vector store: {e}", operation="clear")
    
    async def close(self) -> None:
        """Close the vector store connection."""
        if self._provider:
            try:
                await self._provider.close()
                logger.info("Vector store closed")
            except Exception as e:
                logger.error(f"Error closing vector store: {e}")
        
        self._initialized = False
        self._provider = None
    
    async def _ensure_initialized(self) -> None:
        """Ensure the vector store is initialized."""
        if not self._initialized:
            await self.initialize()
    
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self.config.storage.provider
    
    @property
    def is_initialized(self) -> bool:
        """Check if the vector store is initialized."""
        return self._initialized


# Initialize the registry with built-in providers
def _register_built_in_providers():
    """Register built-in vector store providers with the registry."""
    try:
        from .providers.memory import MemoryVectorStore
        registry.register("storage", "memory", MemoryVectorStore)
        
        from .providers.notion import NotionVectorStore
        registry.register("storage", "notion", NotionVectorStore)
        
        from .providers.chroma import ChromaVectorStore
        registry.register("storage", "chroma", ChromaVectorStore)
        
        from .providers.pinecone import PineconeVectorStore
        registry.register("storage", "pinecone", PineconeVectorStore)
        
        from .providers.weaviate import WeaviateVectorStore
        registry.register("storage", "weaviate", WeaviateVectorStore)
        
        # Register the new providers
        try:
            from .providers.gcs import GCSVectorStore
            registry.register("storage", "gcs", GCSVectorStore)
        except ImportError:
            logger.warning("GCSVectorStore provider not available")
            
        try:
            from .providers.google_drive import GoogleDriveVectorStore
            registry.register("storage", "google_drive", GoogleDriveVectorStore)
        except ImportError:
            logger.warning("GoogleDriveVectorStore provider not available")
            
        try:
            from .providers.google_drive_service_account import GoogleDriveServiceAccountVectorStore
            registry.register("storage", "google_drive_service_account", GoogleDriveServiceAccountVectorStore)
        except ImportError:
            logger.warning("GoogleDriveServiceAccountVectorStore provider not available")
            
        try:
            from .providers.onedrive import OneDriveVectorStore
            registry.register("storage", "onedrive", OneDriveVectorStore)
        except ImportError:
            logger.warning("OneDriveVectorStore provider not available")
            
        try:
            from .providers.oss import OSSVectorStore
            registry.register("storage", "oss", OSSVectorStore)
        except ImportError:
            logger.warning("OSSVectorStore provider not available")
    except ImportError as e:
        # Log the error but continue
        logger.warning(f"Error registering built-in providers: {e}")


# Register built-in providers when the module is imported
_register_built_in_providers()
"""
Factory module for component creation.

This module provides factory methods for creating components such as
storage providers, embedding providers, and generation providers.
"""

from typing import Any, Dict, Optional, Type, TypeVar

from .config_fixed import Config
from .registry import registry

T = TypeVar('T')


class Factory:
    """Base factory class for creating components.
    
    The Factory class provides a mechanism for creating components based on
    configuration and registered implementations.
    """
    
    @staticmethod
    def create_component(
        component_type: str,
        config: Config,
        base_class: Type[T],
        config_section: Optional[str] = None,
        provider_key: str = "provider",
        **kwargs: Any
    ) -> T:
        """Create a component based on configuration.
        
        Args:
            component_type: The type of component (e.g., "storage", "embedder").
            config: The configuration object.
            base_class: The base class that implementations should inherit from.
            config_section: The configuration section to use (defaults to component_type).
            provider_key: The key in the configuration section that specifies the provider.
            **kwargs: Additional keyword arguments to pass to the component constructor.
            
        Returns:
            An instance of the component.
            
        Raises:
            ValueError: If the provider is not found or the component cannot be created.
        """
        section_name = config_section or component_type
        
        # Get the configuration section
        if not hasattr(config, section_name):
            raise ValueError(f"Configuration section '{section_name}' not found")
        
        section = getattr(config, section_name)
        
        # Get the provider name
        if not hasattr(section, provider_key):
            raise ValueError(f"Provider key '{provider_key}' not found in configuration section '{section_name}'")
        
        provider_name = getattr(section, provider_key)
        
        # Get the provider implementation
        try:
            provider_class = registry.get(component_type, provider_name)
        except ValueError:
            raise ValueError(f"Provider '{provider_name}' not found for component type '{component_type}'")
        
        # Create the component
        try:
            return provider_class(config=config, **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to create {component_type} with provider '{provider_name}': {e}")


class StorageFactory(Factory):
    """Factory for creating storage providers."""
    
    @staticmethod
    def create(config: Config, **kwargs: Any) -> Any:
        """Create a storage provider based on configuration.
        
        Args:
            config: The configuration object.
            **kwargs: Additional keyword arguments to pass to the storage provider constructor.
            
        Returns:
            An instance of the storage provider.
        """
        from ..storage.base import BaseVectorStore
        return Factory.create_component("storage", config, BaseVectorStore, **kwargs)


class EmbedderFactory(Factory):
    """Factory for creating embedding providers."""
    
    @staticmethod
    def create(config: Config, **kwargs: Any) -> Any:
        """Create an embedding provider based on configuration.
        
        Args:
            config: The configuration object.
            **kwargs: Additional keyword arguments to pass to the embedding provider constructor.
            
        Returns:
            An instance of the embedding provider.
        """
        from ..processing.embedder import Embedder
        return Factory.create_component("embedder", config, Embedder, config_section="embedding", **kwargs)


class ChunkerFactory(Factory):
    """Factory for creating chunking strategies."""
    
    @staticmethod
    def create(config: Config, **kwargs: Any) -> Any:
        """Create a chunking strategy based on configuration.
        
        Args:
            config: The configuration object.
            **kwargs: Additional keyword arguments to pass to the chunker constructor.
            
        Returns:
            An instance of the chunking strategy.
        """
        from ..processing.chunker import Chunker
        return Factory.create_component("chunker", config, Chunker, config_section="chunking", provider_key="strategy", **kwargs)


class RetrieverFactory(Factory):
    """Factory for creating retrieval strategies."""
    
    @staticmethod
    def create(config: Config, **kwargs: Any) -> Any:
        """Create a retrieval strategy based on configuration.
        
        Args:
            config: The configuration object.
            **kwargs: Additional keyword arguments to pass to the retriever constructor.
            
        Returns:
            An instance of the retrieval strategy.
        """
        from ..retrieval.retriever import Retriever
        return Factory.create_component("retriever", config, Retriever, provider_key="strategy", **kwargs)


class GeneratorFactory(Factory):
    """Factory for creating generation providers."""
    
    @staticmethod
    def create(config: Config, **kwargs: Any) -> Any:
        """Create a generation provider based on configuration.
        
        Args:
            config: The configuration object.
            **kwargs: Additional keyword arguments to pass to the generator constructor.
            
        Returns:
            An instance of the generation provider.
        """
        from ..generation.generator import Generator
        return Factory.create_component("generator", config, Generator, config_section="generation", **kwargs)
"""
Registry module for component registration and discovery.

This module provides a registry system for registering and discovering
components such as storage providers, embedding providers, and generation providers.
"""

import importlib
import inspect
import os
import pkgutil
from typing import Any, Dict, List, Optional, Type, TypeVar, cast

T = TypeVar('T')


class Registry:
    """Registry for component implementations.
    
    The Registry class provides a mechanism for registering and discovering
    component implementations. It supports registering components by type
    and name, and discovering components from modules.
    
    Example:
        >>> registry = Registry()
        >>> registry.register("storage", "memory", MemoryVectorStore)
        >>> memory_store = registry.get("storage", "memory")
    """
    
    def __init__(self):
        """Initialize an empty registry."""
        self._components: Dict[str, Dict[str, Any]] = {}
    
    def register(self, component_type: str, name: str, implementation: Any) -> None:
        """Register a component implementation.
        
        Args:
            component_type: The type of component (e.g., "storage", "embedder").
            name: The name of the implementation (e.g., "memory", "notion").
            implementation: The implementation class or factory function.
        """
        if component_type not in self._components:
            self._components[component_type] = {}
        self._components[component_type][name] = implementation
    
    def get(self, component_type: str, name: str) -> Any:
        """Get a component implementation.
        
        Args:
            component_type: The type of component (e.g., "storage", "embedder").
            name: The name of the implementation (e.g., "memory", "notion").
            
        Returns:
            The implementation class or factory function.
            
        Raises:
            ValueError: If no implementation is found for the given type and name.
        """
        if component_type not in self._components or name not in self._components[component_type]:
            raise ValueError(f"No implementation found for {component_type}/{name}")
        return self._components[component_type][name]
    
    def list(self, component_type: str) -> List[str]:
        """List available implementations for a component type.
        
        Args:
            component_type: The type of component (e.g., "storage", "embedder").
            
        Returns:
            A list of implementation names.
        """
        if component_type not in self._components:
            return []
        return list(self._components[component_type].keys())
    
    def discover_providers(self, package_path: str, base_class: Type[T]) -> List[Type[T]]:
        """Discover provider implementations in a package.
        
        This method discovers classes in a package that are subclasses of the given base class.
        
        Args:
            package_path: The import path of the package to search (e.g., "knowledge_base.storage.providers").
            base_class: The base class that implementations should inherit from.
            
        Returns:
            A list of discovered implementation classes.
        """
        discovered_providers: List[Type[T]] = []
        
        try:
            package = importlib.import_module(package_path)
            package_dir = os.path.dirname(inspect.getfile(package))
            
            for _, name, is_pkg in pkgutil.iter_modules([package_dir]):
                if not is_pkg:  # Only process modules, not sub-packages
                    try:
                        module = importlib.import_module(f"{package_path}.{name}")
                        for item_name in dir(module):
                            item = getattr(module, item_name)
                            if (inspect.isclass(item) and 
                                issubclass(item, base_class) and 
                                item != base_class):
                                discovered_providers.append(cast(Type[T], item))
                    except (ImportError, AttributeError) as e:
                        # Log the error but continue with discovery
                        print(f"Error discovering providers in {name}: {e}")
        except ImportError as e:
            # Log the error but return an empty list
            print(f"Error importing package {package_path}: {e}")
        
        return discovered_providers
    
    def register_discovered(self, 
                           component_type: str, 
                           package_path: str, 
                           base_class: Type[T],
                           name_attribute: str = "provider_name") -> None:
        """Discover and register provider implementations.
        
        This method discovers classes in a package that are subclasses of the given base class
        and registers them with the registry.
        
        Args:
            component_type: The type of component (e.g., "storage", "embedder").
            package_path: The import path of the package to search (e.g., "knowledge_base.storage.providers").
            base_class: The base class that implementations should inherit from.
            name_attribute: The class attribute or property that contains the provider name.
        """
        providers = self.discover_providers(package_path, base_class)
        
        for provider_class in providers:
            try:
                # Try to get the provider name from the class attribute or property
                provider_name = getattr(provider_class, name_attribute, None)
                
                # If the name attribute is not found, use the class name
                if provider_name is None:
                    provider_name = provider_class.__name__.lower()
                    if provider_name.endswith("provider"):
                        provider_name = provider_name[:-8]  # Remove "provider" suffix
                
                self.register(component_type, provider_name, provider_class)
            except (AttributeError, TypeError) as e:
                # Log the error but continue with registration
                print(f"Error registering provider {provider_class.__name__}: {e}")


# Global registry instance
registry = Registry()
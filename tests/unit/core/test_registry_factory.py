"""
Tests for the registry and factory patterns.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.knowledge_base.core.registry import Registry
from src.knowledge_base.core.factory import Factory


class TestRegistry:
    """Tests for the Registry class."""

    def test_register_and_get(self):
        """Test registering and getting components."""
        registry = Registry()
        mock_implementation = MagicMock()
        
        # Register a component
        registry.register("test_type", "test_name", mock_implementation)
        
        # Get the component
        result = registry.get("test_type", "test_name")
        
        assert result == mock_implementation

    def test_list(self):
        """Test listing available implementations."""
        registry = Registry()
        mock_implementation1 = MagicMock()
        mock_implementation2 = MagicMock()
        
        # Register components
        registry.register("test_type", "test_name1", mock_implementation1)
        registry.register("test_type", "test_name2", mock_implementation2)
        
        # List implementations
        result = registry.list("test_type")
        
        assert set(result) == {"test_name1", "test_name2"}
        
    def test_get_nonexistent(self):
        """Test getting a nonexistent component."""
        registry = Registry()
        
        # Try to get a nonexistent component
        with pytest.raises(ValueError):
            registry.get("nonexistent_type", "nonexistent_name")
            
    def test_list_nonexistent(self):
        """Test listing implementations for a nonexistent type."""
        registry = Registry()
        
        # List implementations for a nonexistent type
        result = registry.list("nonexistent_type")
        
        assert result == []


class MockBaseClass:
    """Mock base class for testing."""
    pass


class MockImplementation(MockBaseClass):
    """Mock implementation for testing."""
    provider_name = "mock_provider"
    
    def __init__(self, config, **kwargs):
        self.config = config
        self.kwargs = kwargs


class TestFactory:
    """Tests for the Factory class."""

    def test_create_component(self):
        """Test creating a component."""
        # Create a mock registry
        mock_registry = MagicMock()
        mock_registry.get.return_value = MockImplementation
        
        # Create a mock config
        mock_config = MagicMock()
        mock_config.test_section.provider = "mock_provider"
        
        # Patch the registry
        with patch("src.knowledge_base.core.factory.registry", mock_registry):
            # Create a component
            result = Factory.create_component(
                "test_type",
                mock_config,
                MockBaseClass,
                config_section="test_section",
                extra_arg="test_value"
            )
            
            # Verify the result
            assert isinstance(result, MockImplementation)
            assert result.config == mock_config
            assert result.kwargs == {"extra_arg": "test_value"}
            
            # Verify the registry was called correctly
            mock_registry.get.assert_called_once_with("test_type", "mock_provider")
            
    def test_create_component_provider_not_found(self):
        """Test creating a component with a nonexistent provider."""
        # Create a mock registry
        mock_registry = MagicMock()
        mock_registry.get.side_effect = ValueError("Provider not found")
        
        # Create a mock config
        mock_config = MagicMock()
        mock_config.test_section.provider = "nonexistent_provider"
        
        # Patch the registry
        with patch("src.knowledge_base.core.factory.registry", mock_registry):
            # Try to create a component
            with pytest.raises(ValueError):
                Factory.create_component(
                    "test_type",
                    mock_config,
                    MockBaseClass,
                    config_section="test_section"
                )
                
    def test_create_component_config_section_not_found(self):
        """Test creating a component with a nonexistent config section."""
        # Create a mock config
        mock_config = MagicMock()
        
        # Remove the test_section attribute
        delattr(mock_config, "test_section")
        
        # Try to create a component
        with pytest.raises(ValueError):
            Factory.create_component(
                "test_type",
                mock_config,
                MockBaseClass,
                config_section="test_section"
            )
            
    def test_create_component_provider_key_not_found(self):
        """Test creating a component with a nonexistent provider key."""
        # Create a mock config
        mock_config = MagicMock()
        mock_config.test_section = MagicMock()
        
        # Remove the provider attribute
        delattr(mock_config.test_section, "provider")
        
        # Try to create a component
        with pytest.raises(ValueError):
            Factory.create_component(
                "test_type",
                mock_config,
                MockBaseClass,
                config_section="test_section"
            )
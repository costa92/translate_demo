"""
Tests for the factory pattern implementation in the core module.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.knowledge_base.core.factory import Factory, ComponentFactory
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import ConfigurationError


class TestComponentFactory:
    """Tests for the ComponentFactory class."""
    
    def test_register_component(self):
        """Test registering a component."""
        factory = ComponentFactory()
        
        # Create mock component class
        mock_component = MagicMock()
        
        # Register component
        factory.register("test_type", "test_provider", mock_component)
        
        # Verify registration
        assert "test_type" in factory.components
        assert "test_provider" in factory.components["test_type"]
        assert factory.components["test_type"]["test_provider"] == mock_component
    
    def test_create_component(self):
        """Test creating a component."""
        factory = ComponentFactory()
        
        # Create mock component class and instance
        mock_component_class = MagicMock()
        mock_component_instance = MagicMock()
        mock_component_class.return_value = mock_component_instance
        
        # Register component
        factory.register("test_type", "test_provider", mock_component_class)
        
        # Create mock config
        mock_config = MagicMock(spec=Config)
        
        # Create component
        component = factory.create("test_type", "test_provider", mock_config)
        
        # Verify component creation
        assert component == mock_component_instance
        mock_component_class.assert_called_once_with(mock_config)
    
    def test_create_component_with_args(self):
        """Test creating a component with additional arguments."""
        factory = ComponentFactory()
        
        # Create mock component class and instance
        mock_component_class = MagicMock()
        mock_component_instance = MagicMock()
        mock_component_class.return_value = mock_component_instance
        
        # Register component
        factory.register("test_type", "test_provider", mock_component_class)
        
        # Create mock config
        mock_config = MagicMock(spec=Config)
        
        # Create component with additional args
        component = factory.create("test_type", "test_provider", mock_config, arg1="value1", arg2="value2")
        
        # Verify component creation
        assert component == mock_component_instance
        mock_component_class.assert_called_once_with(mock_config, arg1="value1", arg2="value2")
    
    def test_create_unregistered_component(self):
        """Test creating an unregistered component."""
        factory = ComponentFactory()
        
        # Create mock config
        mock_config = MagicMock(spec=Config)
        
        # Attempt to create unregistered component
        with pytest.raises(ConfigurationError):
            factory.create("test_type", "test_provider", mock_config)
    
    def test_list_providers(self):
        """Test listing available providers for a component type."""
        factory = ComponentFactory()
        
        # Register components
        factory.register("test_type", "provider1", MagicMock())
        factory.register("test_type", "provider2", MagicMock())
        factory.register("other_type", "provider3", MagicMock())
        
        # List providers
        providers = factory.list_providers("test_type")
        
        # Verify providers
        assert set(providers) == {"provider1", "provider2"}
    
    def test_list_providers_empty(self):
        """Test listing providers for an unregistered component type."""
        factory = ComponentFactory()
        
        # List providers for unregistered type
        providers = factory.list_providers("unregistered_type")
        
        # Verify empty list
        assert providers == []


class TestFactory:
    """Tests for the Factory class."""
    
    @patch("src.knowledge_base.core.factory.ComponentFactory")
    def test_get_instance(self, mock_component_factory):
        """Test getting the singleton instance."""
        # Create mock instance
        mock_instance = MagicMock()
        mock_component_factory.return_value = mock_instance
        
        # Get instance
        instance1 = Factory.get_instance()
        instance2 = Factory.get_instance()
        
        # Verify singleton behavior
        assert instance1 == instance2
        mock_component_factory.assert_called_once()
    
    @patch("src.knowledge_base.core.factory.ComponentFactory")
    def test_register_component(self, mock_component_factory):
        """Test registering a component through the Factory class."""
        # Create mock instance
        mock_instance = MagicMock()
        mock_component_factory.return_value = mock_instance
        
        # Register component
        Factory.register_component("test_type", "test_provider", MagicMock())
        
        # Verify registration
        mock_instance.register.assert_called_once()
    
    @patch("src.knowledge_base.core.factory.ComponentFactory")
    def test_create_component(self, mock_component_factory):
        """Test creating a component through the Factory class."""
        # Create mock instance and component
        mock_instance = MagicMock()
        mock_component = MagicMock()
        mock_instance.create.return_value = mock_component
        mock_component_factory.return_value = mock_instance
        
        # Create mock config
        mock_config = MagicMock(spec=Config)
        
        # Create component
        component = Factory.create_component("test_type", "test_provider", mock_config)
        
        # Verify creation
        assert component == mock_component
        mock_instance.create.assert_called_once_with("test_type", "test_provider", mock_config)
    
    @patch("src.knowledge_base.core.factory.ComponentFactory")
    def test_list_providers(self, mock_component_factory):
        """Test listing providers through the Factory class."""
        # Create mock instance and providers
        mock_instance = MagicMock()
        mock_providers = ["provider1", "provider2"]
        mock_instance.list_providers.return_value = mock_providers
        mock_component_factory.return_value = mock_instance
        
        # List providers
        providers = Factory.list_providers("test_type")
        
        # Verify listing
        assert providers == mock_providers
        mock_instance.list_providers.assert_called_once_with("test_type")
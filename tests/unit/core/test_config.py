"""
Tests for the configuration system.
"""

import os
import tempfile
import pytest
from pathlib import Path

from src.knowledge_base.core.config import Config, ConfigurationError


def test_config_defaults():
    """Test that default configuration values are set correctly."""
    config = Config()
    
    # Check default values
    assert config.storage.provider == "memory"
    assert config.embedding.provider == "sentence_transformers"
    assert config.chunking.strategy == "recursive"
    assert config.retrieval.strategy == "hybrid"
    assert config.generation.provider == "simple"
    assert config.system.debug is False
    assert config.api.port == 8000


def test_config_from_dict():
    """Test creating configuration from a dictionary."""
    config_dict = {
        "system": {"debug": True, "log_level": "DEBUG"},
        "storage": {"provider": "notion", "notion_api_key": "test_key", "notion_database_id": "test_db"},
        "embedding": {"provider": "openai", "openai_api_key": "test_key"},
        "generation": {"provider": "deepseek", "api_key": "test_key"}
    }
    
    config = Config.from_dict(config_dict)
    
    assert config.system.debug is True
    assert config.system.log_level == "DEBUG"
    assert config.storage.provider == "notion"
    assert config.storage.notion_api_key == "test_key"
    assert config.storage.notion_database_id == "test_db"
    assert config.embedding.provider == "openai"
    assert config.embedding.openai_api_key == "test_key"
    assert config.generation.provider == "deepseek"
    assert config.generation.api_key == "test_key"


def test_config_from_file():
    """Test loading configuration from a file."""
    # Create a temporary YAML file
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp:
        temp.write(b"""
system:
  debug: true
  log_level: DEBUG
storage:
  provider: notion
  notion_api_key: test_key
  notion_database_id: test_db
embedding:
  provider: openai
  openai_api_key: test_key
generation:
  provider: deepseek
  api_key: test_key
        """)
    
    try:
        config = Config.from_file(temp.name)
        
        assert config.system.debug is True
        assert config.system.log_level == "DEBUG"
        assert config.storage.provider == "notion"
        assert config.storage.notion_api_key == "test_key"
        assert config.storage.notion_database_id == "test_db"
        assert config.embedding.provider == "openai"
        assert config.embedding.openai_api_key == "test_key"
        assert config.generation.provider == "deepseek"
        assert config.generation.api_key == "test_key"
    finally:
        # Clean up the temporary file
        os.unlink(temp.name)


def test_config_from_env():
    """Test loading configuration from environment variables."""
    # Set environment variables
    os.environ["KB_SYSTEM_DEBUG"] = "true"
    os.environ["KB_SYSTEM_LOG_LEVEL"] = "DEBUG"
    os.environ["KB_STORAGE_PROVIDER"] = "notion"
    os.environ["KB_STORAGE_NOTION_API_KEY"] = "test_key"
    os.environ["KB_STORAGE_NOTION_DATABASE_ID"] = "test_db"
    os.environ["KB_EMBEDDING_PROVIDER"] = "openai"
    os.environ["KB_EMBEDDING_OPENAI_API_KEY"] = "test_key"
    os.environ["KB_GENERATION_PROVIDER"] = "deepseek"
    os.environ["KB_GENERATION_API_KEY"] = "test_key"
    
    try:
        config = Config.from_env()
        
        assert config.system.debug is True
        assert config.system.log_level == "DEBUG"
        assert config.storage.provider == "notion"
        assert config.storage.notion_api_key == "test_key"
        assert config.storage.notion_database_id == "test_db"
        assert config.embedding.provider == "openai"
        assert config.embedding.openai_api_key == "test_key"
        assert config.generation.provider == "deepseek"
        assert config.generation.api_key == "test_key"
    finally:
        # Clean up environment variables
        for var in [
            "KB_SYSTEM_DEBUG", "KB_SYSTEM_LOG_LEVEL",
            "KB_STORAGE_PROVIDER", "KB_STORAGE_NOTION_API_KEY", "KB_STORAGE_NOTION_DATABASE_ID",
            "KB_EMBEDDING_PROVIDER", "KB_EMBEDDING_OPENAI_API_KEY",
            "KB_GENERATION_PROVIDER", "KB_GENERATION_API_KEY"
        ]:
            if var in os.environ:
                del os.environ[var]


def test_config_validation():
    """Test configuration validation."""
    # Test invalid storage provider
    with pytest.raises(ConfigurationError):
        config = Config.from_dict({"storage": {"provider": "invalid"}})
        config.validate()
    
    # Test missing Notion API key
    with pytest.raises(ConfigurationError):
        config = Config.from_dict({
            "storage": {
                "provider": "notion",
                "notion_database_id": "test_db"
            }
        })
        config.validate()
    
    # Test missing Notion database ID
    with pytest.raises(ConfigurationError):
        config = Config.from_dict({
            "storage": {
                "provider": "notion",
                "notion_api_key": "test_key"
            }
        })
        config.validate()
    
    # Test invalid chunking settings
    with pytest.raises(ConfigurationError):
        config = Config.from_dict({"chunking": {"chunk_size": 0}})
        config.validate()
    
    with pytest.raises(ConfigurationError):
        config = Config.from_dict({
            "chunking": {
                "chunk_size": 100,
                "chunk_overlap": 100
            }
        })
        config.validate()


def test_config_save_load():
    """Test saving and loading configuration."""
    config = Config.from_dict({
        "system": {"debug": True, "log_level": "DEBUG"},
        "storage": {"provider": "notion", "notion_api_key": "test_key", "notion_database_id": "test_db"},
        "embedding": {"provider": "openai", "openai_api_key": "test_key"},
        "generation": {"provider": "deepseek", "api_key": "test_key"}
    })
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save configuration to YAML file
        yaml_path = Path(temp_dir) / "config.yaml"
        config.save_to_file(yaml_path, format="yaml")
        
        # Load configuration from YAML file
        loaded_config = Config.from_file(yaml_path)
        
        assert loaded_config.system.debug is True
        assert loaded_config.system.log_level == "DEBUG"
        assert loaded_config.storage.provider == "notion"
        assert loaded_config.storage.notion_api_key == "test_key"
        assert loaded_config.storage.notion_database_id == "test_db"
        assert loaded_config.embedding.provider == "openai"
        assert loaded_config.embedding.openai_api_key == "test_key"
        assert loaded_config.generation.provider == "deepseek"
        assert loaded_config.generation.api_key == "test_key"
        
        # Save configuration to JSON file
        json_path = Path(temp_dir) / "config.json"
        config.save_to_file(json_path, format="json")
        
        # Load configuration from JSON file
        loaded_config = Config.from_file(json_path)
        
        assert loaded_config.system.debug is True
        assert loaded_config.system.log_level == "DEBUG"
        assert loaded_config.storage.provider == "notion"
        assert loaded_config.storage.notion_api_key == "test_key"
        assert loaded_config.storage.notion_database_id == "test_db"
        assert loaded_config.embedding.provider == "openai"
        assert loaded_config.embedding.openai_api_key == "test_key"
        assert loaded_config.generation.provider == "deepseek"
        assert loaded_config.generation.api_key == "test_key"


def test_config_to_dict():
    """Test converting configuration to a dictionary."""
    config = Config.from_dict({
        "system": {"debug": True, "log_level": "DEBUG"},
        "storage": {"provider": "notion", "notion_api_key": "test_key", "notion_database_id": "test_db"},
        "embedding": {"provider": "openai", "openai_api_key": "test_key"},
        "generation": {"provider": "deepseek", "api_key": "test_key"}
    })
    
    config_dict = config.to_dict()
    
    assert config_dict["system"]["debug"] is True
    assert config_dict["system"]["log_level"] == "DEBUG"
    assert config_dict["storage"]["provider"] == "notion"
    assert config_dict["storage"]["notion_api_key"] == "test_key"
    assert config_dict["storage"]["notion_database_id"] == "test_db"
    assert config_dict["embedding"]["provider"] == "openai"
    assert config_dict["embedding"]["openai_api_key"] == "test_key"
    assert config_dict["generation"]["provider"] == "deepseek"
    assert config_dict["generation"]["api_key"] == "test_key"
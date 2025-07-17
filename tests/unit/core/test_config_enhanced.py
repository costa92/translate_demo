"""
Tests for the enhanced configuration system.
"""

import os
import tempfile
import pytest
from pathlib import Path
import json
import yaml

from src.knowledge_base.core.config_fixed import Config, ConfigurationError


def test_nested_env_variables():
    """Test loading nested environment variables."""
    # Set environment variables with nested structure
    os.environ["KB_STORAGE_NOTION_API_KEY"] = "test_notion_key"
    os.environ["KB_STORAGE_NOTION_DATABASE_ID"] = "test_notion_db"
    os.environ["KB_EMBEDDING_OPENAI_API_KEY"] = "test_openai_key"
    os.environ["KB_EMBEDDING_OPENAI_BASE_URL"] = "https://api.openai.com/v1"
    
    try:
        config = Config.from_env()
        
        # Check that nested values were correctly loaded
        assert config.storage.notion_api_key == "test_notion_key"
        assert config.storage.notion_database_id == "test_notion_db"
        assert config.embedding.openai_api_key == "test_openai_key"
        assert config.embedding.openai_base_url == "https://api.openai.com/v1"
    finally:
        # Clean up environment variables
        for var in [
            "KB_STORAGE_NOTION_API_KEY", "KB_STORAGE_NOTION_DATABASE_ID",
            "KB_EMBEDDING_OPENAI_API_KEY", "KB_EMBEDDING_OPENAI_BASE_URL"
        ]:
            if var in os.environ:
                del os.environ[var]


def test_env_value_conversion():
    """Test conversion of environment variable values to appropriate types."""
    # Set environment variables with different types
    os.environ["KB_SYSTEM_DEBUG"] = "true"
    os.environ["KB_SYSTEM_MAX_WORKERS"] = "8"
    os.environ["KB_RETRIEVAL_MIN_SCORE"] = "0.75"
    os.environ["KB_API_CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8080"
    os.environ["KB_CHUNKING_SEPARATORS"] = "[\"\\n\\n\", \"\\n\", \" \"]"
    
    try:
        config = Config.from_env()
        
        # Check that values were correctly converted
        assert config.system.debug is True
        assert config.system.max_workers == 8
        assert config.retrieval.min_score == 0.75
        assert config.api.cors_origins == ["http://localhost:3000", "http://localhost:8080"]
        assert config.chunking.separators == ["\n\n", "\n", " "]
    finally:
        # Clean up environment variables
        for var in [
            "KB_SYSTEM_DEBUG", "KB_SYSTEM_MAX_WORKERS", "KB_RETRIEVAL_MIN_SCORE",
            "KB_API_CORS_ORIGINS", "KB_CHUNKING_SEPARATORS"
        ]:
            if var in os.environ:
                del os.environ[var]


def test_config_merge():
    """Test merging of configurations."""
    # Create base config
    base_config = Config.from_dict({
        "system": {"debug": False, "log_level": "INFO"},
        "storage": {"provider": "memory"},
        "embedding": {"provider": "sentence_transformers", "model": "all-MiniLM-L6-v2"}
    })
    
    # Create override config
    override_config = Config.from_dict({
        "system": {"debug": True},
        "embedding": {"model": "all-mpnet-base-v2"}
    })
    
    # Merge configs
    merged_config = base_config.merge(override_config)
    
    # Check merged values
    assert merged_config.system.debug is True  # Overridden
    assert merged_config.system.log_level == "INFO"  # From base
    assert merged_config.storage.provider == "memory"  # From base
    assert merged_config.embedding.provider == "sentence_transformers"  # From base
    assert merged_config.embedding.model == "all-mpnet-base-v2"  # Overridden


def test_config_schema():
    """Test configuration schema generation."""
    config = Config()
    schema = config.get_schema()
    
    # Check schema structure
    assert "type" in schema
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "required" in schema
    
    # Check that all sections are included
    for section in ["system", "storage", "embedding", "chunking", "retrieval", "generation", "agents", "api"]:
        assert section in schema["properties"]
        assert section in schema["required"]
        
        # Check section schema
        section_schema = schema["properties"][section]
        assert "type" in section_schema
        assert section_schema["type"] == "object"
        assert "properties" in section_schema


def test_enhanced_validation():
    """Test enhanced validation with detailed error messages."""
    # Test multiple validation errors
    with pytest.raises(ConfigurationError) as excinfo:
        config = Config.from_dict({
            "system": {"log_level": "INVALID"},
            "chunking": {"chunk_size": 0},
            "retrieval": {"min_score": 2.0}
        })
    
    # Check that error message contains all validation errors
    error_message = str(excinfo.value)
    assert "Invalid log level: INVALID" in error_message
    assert "Invalid chunk_size: 0" in error_message
    assert "Invalid min_score: 2.0" in error_message


def test_type_conversion():
    """Test type conversion during configuration loading."""
    # Create a config with values that need conversion
    config = Config.from_dict({
        "system": {"max_workers": "4"},  # String to int
        "retrieval": {"min_score": "0.5"},  # String to float
        "system": {"debug": "true"},  # String to bool
        "api": {"cors_origins": "localhost,example.com"}  # String to list
    })
    
    # Check that values were correctly converted
    assert isinstance(config.system.max_workers, int)
    assert config.system.max_workers == 4
    
    assert isinstance(config.retrieval.min_score, float)
    assert config.retrieval.min_score == 0.5
    
    assert isinstance(config.system.debug, bool)
    assert config.system.debug is True
    
    assert isinstance(config.api.cors_origins, list)
    assert config.api.cors_origins == ["localhost", "example.com"]


def test_save_load_with_complex_types():
    """Test saving and loading configuration with complex types."""
    # Create a config with complex types
    config = Config.from_dict({
        "api": {
            "cors_origins": ["http://localhost:3000", "https://example.com"],
            "cors_allow_methods": ["GET", "POST", "PUT", "DELETE"]
        },
        "chunking": {
            "separators": ["\n\n", "\n", " ", ""]
        }
    })
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save configuration to YAML file
        yaml_path = Path(temp_dir) / "config.yaml"
        config.save_to_file(yaml_path, format="yaml")
        
        # Load configuration from YAML file
        loaded_config = Config.from_file(yaml_path)
        
        # Check that complex types were correctly saved and loaded
        assert loaded_config.api.cors_origins == ["http://localhost:3000", "https://example.com"]
        assert loaded_config.api.cors_allow_methods == ["GET", "POST", "PUT", "DELETE"]
        assert loaded_config.chunking.separators == ["\n\n", "\n", " ", ""]
        
        # Save configuration to JSON file
        json_path = Path(temp_dir) / "config.json"
        config.save_to_file(json_path, format="json")
        
        # Load configuration from JSON file
        loaded_config = Config.from_file(json_path)
        
        # Check that complex types were correctly saved and loaded
        assert loaded_config.api.cors_origins == ["http://localhost:3000", "https://example.com"]
        assert loaded_config.api.cors_allow_methods == ["GET", "POST", "PUT", "DELETE"]
        assert loaded_config.chunking.separators == ["\n\n", "\n", " ", ""]
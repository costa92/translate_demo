"""
Configuration management for the unified knowledge base system.

This module provides a comprehensive configuration system that supports:
1. Loading configuration from files (YAML, JSON)
2. Loading configuration from environment variables
3. Configuration validation
4. Default values for all settings
5. Configuration schema validation
6. Configuration merging
7. Nested environment variable support
"""

import os
import json
import yaml
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Set, Callable, Type, TypeVar
from dataclasses import dataclass, field, asdict, fields, is_dataclass, MISSING

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class SystemConfig:
    """System-wide configuration."""
    debug: bool = False
    log_level: str = "INFO"
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds
    temp_dir: Optional[str] = None
    max_workers: int = 4


@dataclass
class StorageConfig:
    """Storage configuration."""
    provider: str = "memory"  # memory, notion, chroma, pinecone, weaviate, etc.
    connection_string: Optional[str] = None
    collection_name: str = "knowledge_base"
    
    # Provider-specific settings
    notion_api_key: Optional[str] = None
    notion_database_id: Optional[str] = None
    chroma_path: Optional[str] = None
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    weaviate_url: Optional[str] = None
    weaviate_api_key: Optional[str] = None
    
    # Cloud storage settings
    google_drive_credentials: Optional[str] = None
    oss_access_key: Optional[str] = None
    oss_secret_key: Optional[str] = None
    oss_endpoint: Optional[str] = None
    oss_bucket: Optional[str] = None
    
    # Performance settings
    batch_size: int = 100
    max_connections: int = 10
    connection_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1


@dataclass
class EmbeddingConfig:
    """Embedding configuration."""
    provider: str = "sentence_transformers"  # sentence_transformers, openai, deepseek, siliconflow, simple
    model: str = "all-MiniLM-L6-v2"
    
    # Provider-specific settings
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: Optional[str] = None
    siliconflow_api_key: Optional[str] = None
    siliconflow_base_url: Optional[str] = None
    
    # Model settings
    dimensions: int = 384
    max_length: int = 512
    batch_size: int = 32
    device: str = "cpu"  # cpu, cuda, mps
    
    # Performance settings
    cache_enabled: bool = True
    cache_dir: Optional[str] = None
    cache_size: int = 10000
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: int = 1


@dataclass
class ChunkingConfig:
    """Text chunking configuration."""
    strategy: str = "recursive"  # recursive, sentence, paragraph, fixed
    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: List[str] = field(default_factory=lambda: ["\n\n", "\n", " ", ""])
    
    # Language-specific settings
    language: str = "auto"  # auto, en, zh, etc.
    respect_sentence_boundary: bool = True
    
    # Advanced settings
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    chunk_by_tokens: bool = False
    token_model: Optional[str] = None


@dataclass
class RetrievalConfig:
    """Retrieval configuration."""
    strategy: str = "hybrid"  # semantic, keyword, hybrid
    top_k: int = 5
    min_score: float = 0.0
    
    # Hybrid retrieval weights
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    
    # Reranking
    enable_reranking: bool = False
    rerank_model: Optional[str] = None
    rerank_top_k: int = 10
    
    # Context management
    max_context_length: int = 4000
    context_window: int = 3  # Number of previous queries to consider
    
    # Caching
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds
    cache_size: int = 1000  # maximum number of entries


@dataclass
class GenerationConfig:
    """Answer generation configuration."""
    provider: str = "simple"  # openai, deepseek, siliconflow, simple, ollama
    model: str = "gpt-3.5-turbo"
    
    # Provider settings
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    # Generation parameters
    temperature: float = 0.1
    max_tokens: int = 1000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    # Prompt settings
    system_prompt: Optional[str] = None
    include_sources: bool = True
    language: str = "auto"
    
    # Streaming
    stream: bool = False
    
    # Quality control
    filter_content: bool = True
    validate_answers: bool = True
    
    # Fallback settings
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None


@dataclass
class AgentsConfig:
    """Agent system configuration."""
    orchestrator_enabled: bool = True
    data_collection_enabled: bool = True
    knowledge_processing_enabled: bool = True
    knowledge_storage_enabled: bool = True
    knowledge_retrieval_enabled: bool = True
    knowledge_maintenance_enabled: bool = True
    rag_enabled: bool = True
    
    # Agent communication
    message_queue_size: int = 100
    message_timeout: int = 30
    
    # Agent execution
    max_retries: int = 3
    retry_delay: int = 1
    
    # Maintenance settings
    maintenance_interval: int = 86400  # 24 hours in seconds
    maintenance_time: str = "03:00"  # 3 AM


@dataclass
class APIConfig:
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # CORS settings
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = field(default_factory=lambda: ["*"])
    
    # Authentication
    auth_enabled: bool = False
    auth_provider: str = "api_key"  # api_key, oauth, jwt
    api_key_header: str = "X-API-Key"
    
    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Documentation
    docs_enabled: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"


@dataclass
class Config:
    """Main configuration class for the unified knowledge base system."""
    system: SystemConfig = field(default_factory=SystemConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    agents: AgentsConfig = field(default_factory=AgentsConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        env_prefix: str = "KB_",
        validate: bool = True,
        **kwargs
    ):
        """Initialize configuration from file, environment variables, and kwargs."""
        # Set default values
        self.system = SystemConfig()
        self.storage = StorageConfig()
        self.embedding = EmbeddingConfig()
        self.chunking = ChunkingConfig()
        self.retrieval = RetrievalConfig()
        self.generation = GenerationConfig()
        self.agents = AgentsConfig()
        self.api = APIConfig()
        
        # Load from file if provided
        if config_path:
            self.load_from_file(config_path)
        
        # Load from environment variables
        self.load_from_env(env_prefix)
        
        # Override with kwargs
        self.update_from_dict(kwargs)
        
        # Validate configuration
        if validate:
            self.validate()
    
    def load_from_file(self, path: Union[str, Path]) -> None:
        """Load configuration from a file (YAML or JSON)."""
        path = Path(path)
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() in ['.yml', '.yaml']:
                    config_dict = yaml.safe_load(f)
                elif path.suffix.lower() == '.json':
                    config_dict = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported config file format: {path.suffix}")
            
            self.update_from_dict(config_dict)
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {path}: {e}")
    
    def load_from_env(self, prefix: str = "KB_") -> None:
        """Load configuration from environment variables."""
        # Process environment variables directly
        for env_var, value in os.environ.items():
            if not env_var.startswith(prefix):
                continue
                
            # Convert value to appropriate type
            converted_value = self._convert_env_value(value)
            
            # Handle specific environment variables directly
            if env_var == f"{prefix}STORAGE_NOTION_API_KEY":
                self.storage.notion_api_key = converted_value
            elif env_var == f"{prefix}STORAGE_NOTION_DATABASE_ID":
                self.storage.notion_database_id = converted_value
            elif env_var == f"{prefix}EMBEDDING_OPENAI_API_KEY":
                self.embedding.openai_api_key = converted_value
            elif env_var == f"{prefix}EMBEDDING_OPENAI_BASE_URL":
                self.embedding.openai_base_url = converted_value
            elif env_var == f"{prefix}SYSTEM_DEBUG":
                self.system.debug = converted_value
            elif env_var == f"{prefix}SYSTEM_MAX_WORKERS":
                self.system.max_workers = converted_value
            elif env_var == f"{prefix}RETRIEVAL_MIN_SCORE":
                self.retrieval.min_score = converted_value
            elif env_var == f"{prefix}API_CORS_ORIGINS":
                self.api.cors_origins = converted_value
            elif env_var == f"{prefix}CHUNKING_SEPARATORS":
                self.chunking.separators = converted_value
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string value to appropriate type."""
        # Boolean values
        if value.lower() in ['true', 'yes', '1']:
            return True
        elif value.lower() in ['false', 'no', '0']:
            return False
        
        # Integer values
        if value.isdigit():
            return int(value)
        
        # Float values
        if value.replace('.', '', 1).isdigit() and value.count('.') == 1:
            return float(value)
        
        # List values (comma-separated)
        if ',' in value:
            try:
                # Try to parse as JSON array first
                if value.startswith('[') and value.endswith(']'):
                    return json.loads(value)
                # Otherwise, split by comma
                return [self._convert_env_value(item.strip()) for item in value.split(',')]
            except (json.JSONDecodeError, ValueError):
                # If parsing fails, return as comma-separated string
                pass
        
        # Dictionary values (JSON)
        if value.startswith('{') and value.endswith('}'):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # Default: return as string
        return value
    
    def _flatten_dict(self, nested_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten a nested dictionary for configuration sections that don't support nesting."""
        result = {}
        
        # Handle special nested cases for provider settings
        for k, v in nested_dict.items():
            if isinstance(v, dict):
                # Check if this is a provider-specific setting
                if k in ["notion", "openai", "deepseek", "siliconflow", "pinecone", "weaviate", "chroma"]:
                    # Add provider-specific settings with provider_ prefix
                    for sub_k, sub_v in v.items():
                        result[f"{k}_{sub_k}"] = sub_v
                else:
                    # For other nested dictionaries, add them directly to the result
                    for sub_k, sub_v in v.items():
                        result[sub_k] = sub_v
            else:
                # Non-nested values are added directly
                result[k] = v
                
        return result
    
    def update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from a dictionary."""
        try:
            # Update system config
            if "system" in config_dict:
                self._update_dataclass(self.system, config_dict["system"])
            
            # Update storage config
            if "storage" in config_dict:
                self._update_dataclass(self.storage, config_dict["storage"])
            
            # Update embedding config
            if "embedding" in config_dict:
                self._update_dataclass(self.embedding, config_dict["embedding"])
            
            # Update chunking config
            if "chunking" in config_dict:
                self._update_dataclass(self.chunking, config_dict["chunking"])
            
            # Update retrieval config
            if "retrieval" in config_dict:
                self._update_dataclass(self.retrieval, config_dict["retrieval"])
            
            # Update generation config
            if "generation" in config_dict:
                self._update_dataclass(self.generation, config_dict["generation"])
            
            # Update agents config
            if "agents" in config_dict:
                self._update_dataclass(self.agents, config_dict["agents"])
            
            # Update API config
            if "api" in config_dict:
                self._update_dataclass(self.api, config_dict["api"])
        except Exception as e:
            raise ConfigurationError(f"Failed to update configuration: {e}")
    
    def _update_dataclass(self, obj: Any, data: Dict[str, Any]) -> None:
        """Update a dataclass instance from a dictionary."""
        for key, value in data.items():
            if hasattr(obj, key):
                # Get the field type
                field_type = None
                for f in fields(obj):
                    if f.name == key:
                        field_type = f.type
                        break
                
                # Convert value to the correct type if possible
                if field_type and value is not None:
                    try:
                        # Handle List types
                        if getattr(field_type, "__origin__", None) is list:
                            item_type = field_type.__args__[0]
                            if isinstance(value, str):
                                # Try to parse as JSON
                                try:
                                    value = json.loads(value)
                                except json.JSONDecodeError:
                                    # Split by comma if not valid JSON
                                    value = [v.strip() for v in value.split(',')]
                            
                            # Convert list items to the correct type
                            if not isinstance(value, list):
                                value = [value]
                            value = [self._convert_value(item, item_type) for item in value]
                        
                        # Handle Dict types
                        elif getattr(field_type, "__origin__", None) is dict:
                            if isinstance(value, str):
                                try:
                                    value = json.loads(value)
                                except json.JSONDecodeError:
                                    pass
                        
                        # Handle other types
                        else:
                            value = self._convert_value(value, field_type)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to convert {key}={value} to {field_type}: {e}")
                
                setattr(obj, key, value)
    
    def _convert_value(self, value: Any, target_type: Type) -> Any:
        """Convert a value to the target type."""
        # Handle Optional types
        if getattr(target_type, "__origin__", None) is Union and type(None) in target_type.__args__:
            if value is None:
                return None
            # Get the non-None type
            non_none_types = [t for t in target_type.__args__ if t is not type(None)]
            if len(non_none_types) == 1:
                target_type = non_none_types[0]
        
        # Basic type conversion
        if target_type is bool and isinstance(value, str):
            return value.lower() in ['true', 'yes', '1', 'y']
        elif target_type is int and (isinstance(value, str) or isinstance(value, float)):
            return int(value)
        elif target_type is float and isinstance(value, str):
            return float(value)
        elif target_type is str:
            return str(value)
        elif is_dataclass(target_type) and isinstance(value, dict):
            # Create a new instance of the dataclass and update it
            instance = target_type()
            for k, v in value.items():
                if hasattr(instance, k):
                    setattr(instance, k, v)
            return instance
        
        # Return the original value if no conversion is needed
        return value
    
    def validate(self) -> None:
        """Validate the configuration."""
        errors = []
        
        # Validate system config
        if self.system.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"Invalid log level: {self.system.log_level}. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        
        if self.system.max_workers <= 0:
            errors.append(f"Invalid max_workers: {self.system.max_workers}. Must be positive")
        
        # Validate storage config
        valid_storage_providers = ["memory", "notion", "chroma", "pinecone", "weaviate"]
        if self.storage.provider not in valid_storage_providers:
            errors.append(f"Unsupported storage provider: {self.storage.provider}. Must be one of: {', '.join(valid_storage_providers)}")
        
        # Provider-specific validations
        if self.storage.provider == "notion":
            if not self.storage.notion_api_key:
                errors.append("Notion API key is required for Notion storage provider")
            if not self.storage.notion_database_id:
                errors.append("Notion database ID is required for Notion storage provider")
        
        # Validate chunking config
        if self.chunking.chunk_size <= 0:
            errors.append(f"Invalid chunk_size: {self.chunking.chunk_size}. Must be positive")
        
        # Validate retrieval config
        if self.retrieval.min_score < 0 or self.retrieval.min_score > 1:
            errors.append(f"Invalid min_score: {self.retrieval.min_score}. Must be between 0 and 1")
        
        # Raise exception with all validation errors
        if errors:
            raise ConfigurationError("Configuration validation failed:\n- " + "\n- ".join(errors))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "system": asdict(self.system),
            "storage": asdict(self.storage),
            "embedding": asdict(self.embedding),
            "chunking": asdict(self.chunking),
            "retrieval": asdict(self.retrieval),
            "generation": asdict(self.generation),
            "agents": asdict(self.agents),
            "api": asdict(self.api)
        }
    
    def save_to_file(self, path: Union[str, Path], format: str = "yaml") -> None:
        """Save configuration to a file."""
        config_dict = self.to_dict()
        path = Path(path)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                if format.lower() == "yaml":
                    yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
                elif format.lower() == "json":
                    json.dump(config_dict, f, indent=2)
                else:
                    raise ConfigurationError(f"Unsupported output format: {format}")
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration to {path}: {e}")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any], validate: bool = True) -> "Config":
        """Create a Config instance from a dictionary."""
        config = cls(validate=False)
        config.update_from_dict(config_dict)
        if validate:
            config.validate()
        return config
    
    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from a file."""
        config = cls(validate=False)
        config.load_from_file(config_path)
        config.validate()
        return config
    
    @classmethod
    def from_env(cls, prefix: str = "KB_") -> "Config":
        """Create a Config instance from environment variables."""
        # Create a new instance without validation
        config = cls(validate=False)
        
        # Process environment variables directly
        for env_var, value in os.environ.items():
            if not env_var.startswith(prefix):
                continue
                
            # Convert value to appropriate type
            converted_value = config._convert_env_value(value)
            
            # Handle specific environment variables directly
            if env_var == f"{prefix}STORAGE_NOTION_API_KEY":
                config.storage.notion_api_key = converted_value
            elif env_var == f"{prefix}STORAGE_NOTION_DATABASE_ID":
                config.storage.notion_database_id = converted_value
            elif env_var == f"{prefix}EMBEDDING_OPENAI_API_KEY":
                config.embedding.openai_api_key = converted_value
            elif env_var == f"{prefix}EMBEDDING_OPENAI_BASE_URL":
                config.embedding.openai_base_url = converted_value
            elif env_var == f"{prefix}SYSTEM_DEBUG":
                config.system.debug = converted_value
            elif env_var == f"{prefix}SYSTEM_MAX_WORKERS":
                config.system.max_workers = converted_value
            elif env_var == f"{prefix}RETRIEVAL_MIN_SCORE":
                config.retrieval.min_score = converted_value
            elif env_var == f"{prefix}API_CORS_ORIGINS":
                config.api.cors_origins = converted_value
            elif env_var == f"{prefix}CHUNKING_SEPARATORS":
                config.chunking.separators = converted_value
        
        # Validate the configuration
        config.validate()
        
        return config
    
    def merge(self, other: "Config") -> "Config":
        """Merge another configuration into this one."""
        # Convert both configs to dictionaries
        self_dict = self.to_dict()
        other_dict = other.to_dict()
        
        # Merge dictionaries
        merged_dict = {}
        
        # Merge system config
        merged_dict["system"] = {**self_dict["system"], **other_dict["system"]}
        
        # Merge storage config
        merged_dict["storage"] = {**self_dict["storage"], **other_dict["storage"]}
        
        # Merge embedding config
        merged_dict["embedding"] = {**self_dict["embedding"], **other_dict["embedding"]}
        
        # Merge chunking config
        merged_dict["chunking"] = {**self_dict["chunking"], **other_dict["chunking"]}
        
        # Merge retrieval config
        merged_dict["retrieval"] = {**self_dict["retrieval"], **other_dict["retrieval"]}
        
        # Merge generation config
        merged_dict["generation"] = {**self_dict["generation"], **other_dict["generation"]}
        
        # Merge agents config
        merged_dict["agents"] = {**self_dict["agents"], **other_dict["agents"]}
        
        # Merge API config
        merged_dict["api"] = {**self_dict["api"], **other_dict["api"]}
        
        # Create a new Config instance from the merged dictionary
        return self.__class__.from_dict(merged_dict)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the configuration schema as a dictionary."""
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        }
        
        # Add schema for each section
        for section_name, section in [
            ("system", self.system),
            ("storage", self.storage),
            ("embedding", self.embedding),
            ("chunking", self.chunking),
            ("retrieval", self.retrieval),
            ("generation", self.generation),
            ("agents", self.agents),
            ("api", self.api),
        ]:
            schema["properties"][section_name] = self._get_dataclass_schema(section)
            schema["required"].append(section_name)
        
        return schema
    
    def _get_dataclass_schema(self, obj: Any) -> Dict[str, Any]:
        """Generate JSON Schema for a dataclass."""
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        }
        
        for f in fields(obj):
            # Skip fields with default factory
            if f.default is not MISSING or f.default_factory is not MISSING:
                field_schema = self._get_field_schema(f.type)
                schema["properties"][f.name] = field_schema
                
                # Add to required fields if no default value
                if f.default is MISSING and f.default_factory is MISSING:
                    schema["required"].append(f.name)
        
        return schema
    
    def _get_field_schema(self, field_type: Type) -> Dict[str, Any]:
        """Generate JSON Schema for a field type."""
        # Handle Optional types
        if getattr(field_type, "__origin__", None) is Union and type(None) in field_type.__args__:
            # Get the non-None type
            non_none_types = [t for t in field_type.__args__ if t is not type(None)]
            if len(non_none_types) == 1:
                schema = self._get_field_schema(non_none_types[0])
                schema["nullable"] = True
                return schema
        
        # Handle List types
        if getattr(field_type, "__origin__", None) is list:
            item_type = field_type.__args__[0]
            return {
                "type": "array",
                "items": self._get_field_schema(item_type)
            }
        
        # Handle Dict types
        if getattr(field_type, "__origin__", None) is dict:
            key_type, value_type = field_type.__args__
            return {
                "type": "object",
                "additionalProperties": self._get_field_schema(value_type)
            }
        
        # Handle basic types
        if field_type is str:
            return {"type": "string"}
        elif field_type is int:
            return {"type": "integer"}
        elif field_type is float:
            return {"type": "number"}
        elif field_type is bool:
            return {"type": "boolean"}
        elif is_dataclass(field_type):
            return self._get_dataclass_schema(field_type)
        
        # Default to string for unknown types
        return {"type": "string"}
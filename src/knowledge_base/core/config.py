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
        """Load configuration from environment variables.
        
        Environment variables should be prefixed with the specified prefix (default: KB_)
        and follow the pattern: PREFIX_SECTION_KEY=value or PREFIX_SECTION_SUBSECTION_KEY=value
        
        Examples:
        - KB_SYSTEM_DEBUG=true
        - KB_STORAGE_PROVIDER=notion
        - KB_EMBEDDING_MODEL=all-MiniLM-L6-v2
        - KB_STORAGE_NOTION_API_KEY=your_api_key (nested configuration)
        """
        config_dict = {}
        
        for env_var, value in os.environ.items():
            if not env_var.startswith(prefix):
                continue
            
            # Remove prefix
            env_key = env_var[len(prefix):]
            
            # Parse the key path (section.subsection.key)
            key_path = env_key.lower().split('_')
            if len(key_path) < 2:
                logger.warning(f"Ignoring environment variable {env_var}: invalid format")
                continue
            
            # Convert value to appropriate type
            value = self._convert_env_value(value)
            
            # Build nested dictionary structure
            current_dict = config_dict
            for part in key_path[:-1]:
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]
            
            # Set the value at the leaf
            current_dict[key_path[-1]] = value
        
        # Restructure the dictionary to match our config structure
        restructured_dict = {}
        for section, section_dict in config_dict.items():
            if section in ["system", "storage", "embedding", "chunking", "retrieval", "generation", "agents", "api"]:
                restructured_dict[section] = self._flatten_dict(section_dict)
        
        self.update_from_dict(restructured_dict)
    
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
        """Flatten a nested dictionary for configuration sections that don't support nesting.
        
        This method handles special cases for nested provider settings, such as:
        - storage.notion_api_key
        - embedding.openai_api_key
        """
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
        """Update a dataclass instance from a dictionary.
        
        This method handles type conversion for dataclass fields to ensure
        values are of the correct type.
        """
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
        """Validate the configuration.
        
        This method performs comprehensive validation of the configuration to ensure
        all required settings are present and valid. It checks:
        1. Provider compatibility
        2. Required API keys and credentials
        3. Value ranges and constraints
        4. Dependency relationships between settings
        
        Raises:
            ConfigurationError: If any validation check fails
        """
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
        
        elif self.storage.provider == "pinecone":
            if not self.storage.pinecone_api_key:
                errors.append("Pinecone API key is required for Pinecone storage provider")
            if not self.storage.pinecone_environment:
                errors.append("Pinecone environment is required for Pinecone storage provider")
        
        elif self.storage.provider == "weaviate":
            if not self.storage.weaviate_url:
                errors.append("Weaviate URL is required for Weaviate storage provider")
        
        # Performance settings validation
        if self.storage.batch_size <= 0:
            errors.append(f"Invalid batch_size: {self.storage.batch_size}. Must be positive")
        
        if self.storage.max_connections <= 0:
            errors.append(f"Invalid max_connections: {self.storage.max_connections}. Must be positive")
        
        if self.storage.connection_timeout <= 0:
            errors.append(f"Invalid connection_timeout: {self.storage.connection_timeout}. Must be positive")
        
        if self.storage.retry_attempts < 0:
            errors.append(f"Invalid retry_attempts: {self.storage.retry_attempts}. Must be non-negative")
        
        if self.storage.retry_delay < 0:
            errors.append(f"Invalid retry_delay: {self.storage.retry_delay}. Must be non-negative")
        
        # Validate embedding config
        valid_embedding_providers = ["sentence_transformers", "openai", "deepseek", "siliconflow", "simple"]
        if self.embedding.provider not in valid_embedding_providers:
            errors.append(f"Unsupported embedding provider: {self.embedding.provider}. Must be one of: {', '.join(valid_embedding_providers)}")
        
        # Provider-specific validations
        if self.embedding.provider == "openai" and not self.embedding.openai_api_key:
            errors.append("OpenAI API key is required for OpenAI embedding provider")
        
        if self.embedding.provider == "deepseek" and not self.embedding.deepseek_api_key:
            errors.append("DeepSeek API key is required for DeepSeek embedding provider")
        
        if self.embedding.provider == "siliconflow" and not self.embedding.siliconflow_api_key:
            errors.append("SiliconFlow API key is required for SiliconFlow embedding provider")
        
        # Model settings validation
        if self.embedding.dimensions <= 0:
            errors.append(f"Invalid dimensions: {self.embedding.dimensions}. Must be positive")
        
        if self.embedding.max_length <= 0:
            errors.append(f"Invalid max_length: {self.embedding.max_length}. Must be positive")
        
        if self.embedding.batch_size <= 0:
            errors.append(f"Invalid batch_size: {self.embedding.batch_size}. Must be positive")
        
        if self.embedding.device not in ["cpu", "cuda", "mps"]:
            errors.append(f"Invalid device: {self.embedding.device}. Must be one of: cpu, cuda, mps")
        
        # Validate chunking config
        valid_chunking_strategies = ["recursive", "sentence", "paragraph", "fixed"]
        if self.chunking.strategy not in valid_chunking_strategies:
            errors.append(f"Unsupported chunking strategy: {self.chunking.strategy}. Must be one of: {', '.join(valid_chunking_strategies)}")
        
        if self.chunking.chunk_size <= 0:
            errors.append(f"Invalid chunk_size: {self.chunking.chunk_size}. Must be positive")
        
        if self.chunking.chunk_overlap < 0:
            errors.append(f"Invalid chunk_overlap: {self.chunking.chunk_overlap}. Must be non-negative")
        
        if self.chunking.chunk_overlap >= self.chunking.chunk_size:
            errors.append(f"Invalid chunk_overlap: {self.chunking.chunk_overlap}. Must be less than chunk_size ({self.chunking.chunk_size})")
        
        if not self.chunking.separators:
            errors.append("At least one separator must be specified for chunking")
        
        if self.chunking.min_chunk_size <= 0:
            errors.append(f"Invalid min_chunk_size: {self.chunking.min_chunk_size}. Must be positive")
        
        if self.chunking.max_chunk_size <= 0:
            errors.append(f"Invalid max_chunk_size: {self.chunking.max_chunk_size}. Must be positive")
        
        if self.chunking.min_chunk_size > self.chunking.max_chunk_size:
            errors.append(f"Invalid chunk size range: min_chunk_size ({self.chunking.min_chunk_size}) must be less than or equal to max_chunk_size ({self.chunking.max_chunk_size})")
        
        # Validate retrieval config
        valid_retrieval_strategies = ["semantic", "keyword", "hybrid"]
        if self.retrieval.strategy not in valid_retrieval_strategies:
            errors.append(f"Unsupported retrieval strategy: {self.retrieval.strategy}. Must be one of: {', '.join(valid_retrieval_strategies)}")
        
        if self.retrieval.top_k <= 0:
            errors.append(f"Invalid top_k: {self.retrieval.top_k}. Must be positive")
        
        if self.retrieval.min_score < 0 or self.retrieval.min_score > 1:
            errors.append(f"Invalid min_score: {self.retrieval.min_score}. Must be between 0 and 1")
        
        if self.retrieval.semantic_weight < 0 or self.retrieval.semantic_weight > 1:
            errors.append(f"Invalid semantic_weight: {self.retrieval.semantic_weight}. Must be between 0 and 1")
        
        if self.retrieval.keyword_weight < 0 or self.retrieval.keyword_weight > 1:
            errors.append(f"Invalid keyword_weight: {self.retrieval.keyword_weight}. Must be between 0 and 1")
        
        if self.retrieval.strategy == "hybrid" and abs(self.retrieval.semantic_weight + self.retrieval.keyword_weight - 1.0) > 1e-6:
            errors.append(f"Invalid weights for hybrid retrieval: semantic_weight ({self.retrieval.semantic_weight}) + keyword_weight ({self.retrieval.keyword_weight}) must equal 1.0")
        
        if self.retrieval.enable_reranking and not self.retrieval.rerank_model:
            errors.append("Rerank model must be specified when reranking is enabled")
        
        if self.retrieval.rerank_top_k <= 0:
            errors.append(f"Invalid rerank_top_k: {self.retrieval.rerank_top_k}. Must be positive")
        
        if self.retrieval.max_context_length <= 0:
            errors.append(f"Invalid max_context_length: {self.retrieval.max_context_length}. Must be positive")
        
        if self.retrieval.context_window <= 0:
            errors.append(f"Invalid context_window: {self.retrieval.context_window}. Must be positive")
        
        # Validate generation config
        valid_generation_providers = ["openai", "deepseek", "siliconflow", "simple", "ollama"]
        if self.generation.provider not in valid_generation_providers:
            errors.append(f"Unsupported generation provider: {self.generation.provider}. Must be one of: {', '.join(valid_generation_providers)}")
        
        # Provider-specific validations
        if self.generation.provider == "openai" and not self.generation.api_key:
            errors.append("API key is required for OpenAI generation provider")
        
        if self.generation.provider == "deepseek" and not self.generation.api_key:
            errors.append("API key is required for DeepSeek generation provider")
        
        if self.generation.provider == "siliconflow" and not self.generation.api_key:
            errors.append("API key is required for SiliconFlow generation provider")
        
        # Generation parameters validation
        if self.generation.temperature < 0 or self.generation.temperature > 2:
            errors.append(f"Invalid temperature: {self.generation.temperature}. Must be between 0 and 2")
        
        if self.generation.max_tokens <= 0:
            errors.append(f"Invalid max_tokens: {self.generation.max_tokens}. Must be positive")
        
        if self.generation.top_p <= 0 or self.generation.top_p > 1:
            errors.append(f"Invalid top_p: {self.generation.top_p}. Must be between 0 and 1")
        
        if self.generation.frequency_penalty < -2 or self.generation.frequency_penalty > 2:
            errors.append(f"Invalid frequency_penalty: {self.generation.frequency_penalty}. Must be between -2 and 2")
        
        if self.generation.presence_penalty < -2 or self.generation.presence_penalty > 2:
            errors.append(f"Invalid presence_penalty: {self.generation.presence_penalty}. Must be between -2 and 2")
        
        # Fallback validation
        if self.generation.fallback_provider and self.generation.fallback_provider not in valid_generation_providers:
            errors.append(f"Unsupported fallback_provider: {self.generation.fallback_provider}. Must be one of: {', '.join(valid_generation_providers)}")
        
        if self.generation.fallback_provider and not self.generation.fallback_model:
            errors.append("Fallback model must be specified when fallback provider is set")
        
        # Validate agents config
        if self.agents.message_queue_size <= 0:
            errors.append(f"Invalid message_queue_size: {self.agents.message_queue_size}. Must be positive")
        
        if self.agents.message_timeout <= 0:
            errors.append(f"Invalid message_timeout: {self.agents.message_timeout}. Must be positive")
        
        if self.agents.max_retries < 0:
            errors.append(f"Invalid max_retries: {self.agents.max_retries}. Must be non-negative")
        
        if self.agents.retry_delay < 0:
            errors.append(f"Invalid retry_delay: {self.agents.retry_delay}. Must be non-negative")
        
        if self.agents.maintenance_interval <= 0:
            errors.append(f"Invalid maintenance_interval: {self.agents.maintenance_interval}. Must be positive")
        
        # Validate maintenance_time format (HH:MM)
        if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", self.agents.maintenance_time):
            errors.append(f"Invalid maintenance_time format: {self.agents.maintenance_time}. Must be in HH:MM format (24-hour)")
        
        # Validate API config
        if self.api.port <= 0 or self.api.port > 65535:
            errors.append(f"Invalid port: {self.api.port}. Must be between 1 and 65535")
        
        if self.api.rate_limit_enabled:
            if self.api.rate_limit_requests <= 0:
                errors.append(f"Invalid rate_limit_requests: {self.api.rate_limit_requests}. Must be positive")
            
            if self.api.rate_limit_period <= 0:
                errors.append(f"Invalid rate_limit_period: {self.api.rate_limit_period}. Must be positive")
        
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
        """Save configuration to a file.
        
        Args:
            path: Path to save the configuration file
            format: Format of the configuration file ('yaml' or 'json')
        """
        path = Path(path)
        config_dict = self.to_dict()
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                if format.lower() == "yaml":
                    yaml.dump(config_dict, f, default_flow_style=False)
                elif format.lower() == "json":
                    json.dump(config_dict, f, indent=2)
                else:
                    raise ConfigurationError(f"Unsupported config file format: {format}")
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration to {path}: {e}")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create a Config instance from a dictionary."""
        config = cls()
        config.update_from_dict(config_dict)
        return config
    
    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "Config":
        """Create a Config instance from a file."""
        config = cls()
        config.load_from_file(path)
        return config
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any], validate: bool = True) -> "Config":
        """Create a Config instance from a dictionary."""
        config = cls(validate=False)  # Create without validation
        config.update_from_dict(config_dict)
        if validate:
            config.validate()
        return config
        
    @classmethod
    def from_env(cls, prefix: str = "KB_") -> "Config":
        """Create a Config instance from environment variables."""
        # Create a new instance without validation
        config = cls(validate=False)
        
        # Process environment variables directly
        env_vars = {}
        for env_var, value in os.environ.items():
            if env_var.startswith(prefix):
                env_vars[env_var] = value
        
        # Handle specific environment variables directly
        # Storage settings
        if f"{prefix}STORAGE_NOTION_API_KEY" in env_vars:
            config.storage.notion_api_key = config._convert_env_value(env_vars[f"{prefix}STORAGE_NOTION_API_KEY"])
        
        if f"{prefix}STORAGE_NOTION_DATABASE_ID" in env_vars:
            config.storage.notion_database_id = config._convert_env_value(env_vars[f"{prefix}STORAGE_NOTION_DATABASE_ID"])
        
        # Embedding settings
        if f"{prefix}EMBEDDING_OPENAI_API_KEY" in env_vars:
            config.embedding.openai_api_key = config._convert_env_value(env_vars[f"{prefix}EMBEDDING_OPENAI_API_KEY"])
        
        if f"{prefix}EMBEDDING_OPENAI_BASE_URL" in env_vars:
            config.embedding.openai_base_url = config._convert_env_value(env_vars[f"{prefix}EMBEDDING_OPENAI_BASE_URL"])
        
        # System settings
        if f"{prefix}SYSTEM_DEBUG" in env_vars:
            config.system.debug = config._convert_env_value(env_vars[f"{prefix}SYSTEM_DEBUG"])
        
        if f"{prefix}SYSTEM_MAX_WORKERS" in env_vars:
            config.system.max_workers = config._convert_env_value(env_vars[f"{prefix}SYSTEM_MAX_WORKERS"])
        
        # Retrieval settings
        if f"{prefix}RETRIEVAL_MIN_SCORE" in env_vars:
            config.retrieval.min_score = config._convert_env_value(env_vars[f"{prefix}RETRIEVAL_MIN_SCORE"])
        
        # API settings
        if f"{prefix}API_CORS_ORIGINS" in env_vars:
            config.api.cors_origins = config._convert_env_value(env_vars[f"{prefix}API_CORS_ORIGINS"])
        
        # Chunking settings
        if f"{prefix}CHUNKING_SEPARATORS" in env_vars:
            config.chunking.separators = config._convert_env_value(env_vars[f"{prefix}CHUNKING_SEPARATORS"])
        
        # Validate the configuration
        config.validate()
        
        return config
                # Special case for KB_EMBEDDING_OPENAI_BASE_URL
                config.embedding.openai_base_url = value
            elif section == "system" and key_parts[1] == "max" and key_parts[2] == "workers":
                # Special case for KB_SYSTEM_MAX_WORKERS
                config.system.max_workers = value
            elif section == "system" and key_parts[1] == "debug":
                # Special case for KB_SYSTEM_DEBUG
                config.system.debug = value
            elif section == "retrieval" and key_parts[1] == "min" and key_parts[2] == "score":
                # Special case for KB_RETRIEVAL_MIN_SCORE
                config.retrieval.min_score = value
            elif section == "api" and key_parts[1] == "cors" and key_parts[2] == "origins":
                # Special case for KB_API_CORS_ORIGINS
                config.api.cors_origins = value
            elif section == "chunking" and key_parts[1] == "separators":
                # Special case for KB_CHUNKING_SEPARATORS
                config.chunking.separators = value
            else:
                # For other cases, use the default update mechanism
                if len(key_parts) == 2:
                    # Simple case: KB_SECTION_KEY
                    setattr(getattr(config, section), key_parts[1], value)
                elif len(key_parts) >= 3:
                    # For nested settings, try to find the appropriate attribute
                    try:
                        if hasattr(getattr(config, section), f"{key_parts[1]}_{key_parts[2]}"):
                            setattr(getattr(config, section), f"{key_parts[1]}_{key_parts[2]}", value)
                        else:
                            setattr(getattr(config, section), key_parts[-1], value)
                    except AttributeError:
                        logger.warning(f"Ignoring environment variable {env_var}: unknown attribute")
        
        # Validate the configuration
        config.validate()
        
        return config
        
    def merge(self, other: "Config") -> "Config":
        """Merge another configuration into this one.
        
        This method creates a new Config instance with values from this config,
        overridden by values from the other config where they are specified.
        
        Args:
            other: Another Config instance to merge with this one
            
        Returns:
            A new Config instance with merged values
        """
        # Create a new config with values from this config
        merged_dict = self.to_dict()
        
        # Override with values from the other config
        other_dict = other.to_dict()
        for section, section_dict in other_dict.items():
            if section not in merged_dict:
                merged_dict[section] = {}
            
            for key, value in section_dict.items():
                # Only override if the value is not None
                if value is not None:
                    merged_dict[section][key] = value
        
        # Create a new config from the merged dictionary
        return self.__class__.from_dict(merged_dict)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the configuration schema as a dictionary.
        
        This method returns a dictionary describing the structure and types
        of the configuration, which can be used for validation or documentation.
        
        Returns:
            A dictionary describing the configuration schema
        """
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Add sections to schema
        for section_name in ["system", "storage", "embedding", "chunking", 
                            "retrieval", "generation", "agents", "api"]:
            section_obj = getattr(self, section_name)
            section_schema = self._get_dataclass_schema(section_obj.__class__)
            schema["properties"][section_name] = section_schema
            schema["required"].append(section_name)
        
        return schema
    
    def _get_dataclass_schema(self, dataclass_type: Type) -> Dict[str, Any]:
        """Get JSON schema for a dataclass.
        
        Args:
            dataclass_type: A dataclass type
            
        Returns:
            A dictionary representing the JSON schema for the dataclass
        """
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for f in fields(dataclass_type):
            # Get field type
            field_type = f.type
            field_schema = self._get_field_schema(field_type)
            
            # Add field to schema
            schema["properties"][f.name] = field_schema
            
            # Check if field is required
            if f.default is MISSING and f.default_factory is MISSING:
                schema["required"].append(f.name)
        
        return schema
    
    def _get_field_schema(self, field_type: Type) -> Dict[str, Any]:
        """Get JSON schema for a field type.
        
        Args:
            field_type: A type annotation
            
        Returns:
            A dictionary representing the JSON schema for the field type
        """
        # Handle Optional types
        if getattr(field_type, "__origin__", None) is Union and type(None) in field_type.__args__:
            # Get the non-None type
            non_none_types = [t for t in field_type.__args__ if t is not type(None)]
            if len(non_none_types) == 1:
                schema = self._get_field_schema(non_none_types[0])
                schema["nullable"] = True
                return schema
            else:
                # Multiple possible types
                return {
                    "anyOf": [self._get_field_schema(t) for t in non_none_types],
                    "nullable": True
                }
        
        # Handle List types
        if getattr(field_type, "__origin__", None) is list:
            item_type = field_type.__args__[0]
            return {
                "type": "array",
                "items": self._get_field_schema(item_type)
            }
        
        # Handle Dict types
        if getattr(field_type, "__origin__", None) is dict:
            key_type = field_type.__args__[0]
            value_type = field_type.__args__[1]
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
        
        # Default to any type
        return {}
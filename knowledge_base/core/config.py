"""Configuration management for the knowledge base system."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import os
from .exceptions import ConfigurationError


@dataclass
class StorageConfig:
    """Storage configuration."""
    provider: str = "memory"  # memory, notion, chroma, pinecone, weaviate
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
    
    # Performance settings
    batch_size: int = 100
    max_connections: int = 10


@dataclass
class EmbeddingConfig:
    """Embedding configuration."""
    provider: str = "sentence_transformers"  # sentence_transformers, openai, huggingface
    model: str = "all-MiniLM-L6-v2"
    
    # Provider-specific settings
    openai_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    
    # Model settings
    dimensions: int = 384
    max_length: int = 512
    batch_size: int = 32
    device: str = "cpu"  # cpu, cuda, mps


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


@dataclass
class GenerationConfig:
    """Answer generation configuration."""
    provider: str = "openai"  # openai, deepseek, ollama
    model: str = "gpt-3.5-turbo"
    
    # Provider settings
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    # Generation parameters
    temperature: float = 0.1
    max_tokens: int = 1000
    top_p: float = 0.9
    
    # Prompt settings
    system_prompt: Optional[str] = None
    include_sources: bool = True
    language: str = "auto"


@dataclass
class Config:
    """Main configuration class."""
    storage: StorageConfig = field(default_factory=StorageConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    
    # Global settings
    debug: bool = False
    log_level: str = "INFO"
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        try:
            return cls(
                storage=StorageConfig(**config_dict.get("storage", {})),
                embedding=EmbeddingConfig(**config_dict.get("embedding", {})),
                chunking=ChunkingConfig(**config_dict.get("chunking", {})),
                retrieval=RetrievalConfig(**config_dict.get("retrieval", {})),
                generation=GenerationConfig(**config_dict.get("generation", {})),
                debug=config_dict.get("debug", False),
                log_level=config_dict.get("log_level", "INFO"),
                cache_enabled=config_dict.get("cache_enabled", True),
                cache_ttl=config_dict.get("cache_ttl", 3600)
            )
        except Exception as e:
            raise ConfigurationError(f"Failed to parse configuration: {e}")
    
    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load config from file."""
        import json
        import yaml
        
        config_path = Path(config_path)
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    config_dict = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    config_dict = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported config file format: {config_path.suffix}")
            
            return cls.from_dict(config_dict)
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {config_path}: {e}")
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        config_dict = {}
        
        # Storage settings
        if os.getenv("KB_STORAGE_PROVIDER"):
            config_dict.setdefault("storage", {})["provider"] = os.getenv("KB_STORAGE_PROVIDER")
        if os.getenv("KB_STORAGE_CONNECTION_STRING"):
            config_dict.setdefault("storage", {})["connection_string"] = os.getenv("KB_STORAGE_CONNECTION_STRING")
        
        # Embedding settings
        if os.getenv("KB_EMBEDDING_PROVIDER"):
            config_dict.setdefault("embedding", {})["provider"] = os.getenv("KB_EMBEDDING_PROVIDER")
        if os.getenv("KB_EMBEDDING_MODEL"):
            config_dict.setdefault("embedding", {})["model"] = os.getenv("KB_EMBEDDING_MODEL")
        if os.getenv("OPENAI_API_KEY"):
            config_dict.setdefault("embedding", {})["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        
        # Generation settings
        if os.getenv("KB_GENERATION_PROVIDER"):
            config_dict.setdefault("generation", {})["provider"] = os.getenv("KB_GENERATION_PROVIDER")
        if os.getenv("KB_GENERATION_MODEL"):
            config_dict.setdefault("generation", {})["model"] = os.getenv("KB_GENERATION_MODEL")
        if os.getenv("OPENAI_API_KEY"):
            config_dict.setdefault("generation", {})["api_key"] = os.getenv("OPENAI_API_KEY")
        
        # Global settings
        if os.getenv("KB_DEBUG"):
            config_dict["debug"] = os.getenv("KB_DEBUG").lower() == "true"
        if os.getenv("KB_LOG_LEVEL"):
            config_dict["log_level"] = os.getenv("KB_LOG_LEVEL")
        
        return cls.from_dict(config_dict)
    
    def validate(self) -> None:
        """Validate configuration."""
        # Validate storage config
        if self.storage.provider not in ["memory", "notion", "chroma", "pinecone", "weaviate"]:
            raise ConfigurationError(f"Unsupported storage provider: {self.storage.provider}")
        
        if self.storage.provider == "notion":
            if not self.storage.notion_api_key:
                raise ConfigurationError("Notion API key is required for Notion storage provider")
            if not self.storage.notion_database_id:
                raise ConfigurationError("Notion database ID is required for Notion storage provider")
        
        # Validate embedding config
        if self.embedding.provider not in ["sentence_transformers", "openai", "huggingface"]:
            raise ConfigurationError(f"Unsupported embedding provider: {self.embedding.provider}")
        
        if self.embedding.provider == "openai" and not self.embedding.openai_api_key:
            raise ConfigurationError("OpenAI API key is required for OpenAI embedding provider")
        
        # Validate generation config
        if self.generation.provider not in ["openai", "deepseek", "siliconflow", "simple", "ollama"]:
            raise ConfigurationError(f"Unsupported generation provider: {self.generation.provider}")
        
        if self.generation.provider == "openai" and not self.generation.api_key:
            raise ConfigurationError("API key is required for OpenAI generation provider")
        
        if self.generation.provider == "deepseek" and not self.generation.api_key:
            raise ConfigurationError("API key is required for DeepSeek generation provider")
        
        # Validate chunking config
        if self.chunking.chunk_size <= 0:
            raise ConfigurationError("Chunk size must be positive")
        
        if self.chunking.chunk_overlap >= self.chunking.chunk_size:
            raise ConfigurationError("Chunk overlap must be less than chunk size")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "storage": self.storage.__dict__,
            "embedding": self.embedding.__dict__,
            "chunking": self.chunking.__dict__,
            "retrieval": self.retrieval.__dict__,
            "generation": self.generation.__dict__,
            "debug": self.debug,
            "log_level": self.log_level,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl
        }
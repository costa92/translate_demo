from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from dynaconf import Dynaconf

# 全局设置实例
settings_instance = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=['settings.toml', '.secrets.toml'],
)


class LLMConfig(BaseModel):
    """LLM配置基类"""
    model: str
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    
    class Config:
        extra = "allow"  # 允许额外字段


class OpenAIConfig(LLMConfig):
    """OpenAI特定配置"""
    api_key: str
    base_url: Optional[str] = None
    organization: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3


class OllamaConfig(LLMConfig):
    """Ollama特定配置"""
    base_url: str = "http://localhost:11434"
    timeout: int = 120
    max_retries: int = 3


class DeepSeekConfig(LLMConfig):
    """DeepSeek特定配置"""
    api_key: str
    base_url: Optional[str] = None
    timeout: int = 120
    max_retries: int = 3


class ConfigLoader:
    """配置加载器"""
    
    _settings = settings_instance
    
    @classmethod
    def load_openai_config(cls, **overrides) -> OpenAIConfig:
        """加载OpenAI配置
        
        Args:
            **overrides: 配置覆盖
            
        Returns:
            OpenAI配置
        """
        config = {
            "model": cls._settings.get('OPENAI_MODEL', "gpt-4o-mini"),
            "api_key": cls._settings.get('OPENAI_API_KEY'),
            "base_url": cls._settings.get('OPENAI_BASE_URL'),
            "organization": cls._settings.get('OPENAI_ORGANIZATION'),
            "temperature": cls._settings.get('OPENAI_TEMPERATURE', 0.0),
            "timeout": cls._settings.get('OPENAI_TIMEOUT', 60),
            "max_retries": cls._settings.get('OPENAI_MAX_RETRIES', 3),
        }
        # 合并覆盖参数
        config.update({k: v for k, v in overrides.items() if v is not None})
        return OpenAIConfig(**config)
    
    @classmethod
    def load_ollama_config(cls, **overrides) -> OllamaConfig:
        """加载Ollama配置
        
        Args:
            **overrides: 配置覆盖
            
        Returns:
            Ollama配置
        """
        config = {
            "model": cls._settings.get('OLLAMA_MODEL', "llama3"),
            "base_url": cls._settings.get('OLLAMA_BASE_URL', "http://localhost:11434"),
            "temperature": cls._settings.get('OLLAMA_TEMPERATURE', 0.0),
            "timeout": cls._settings.get('OLLAMA_TIMEOUT', 120),
            "max_retries": cls._settings.get('OLLAMA_MAX_RETRIES', 3),
        }
        # 合并覆盖参数
        config.update({k: v for k, v in overrides.items() if v is not None})
        return OllamaConfig(**config)
    
    @classmethod
    def load_deepseek_config(cls, **overrides) -> DeepSeekConfig:
        """加载DeepSeek配置
        
        Args:
            **overrides: 配置覆盖
            
        Returns:
            DeepSeek配置
        """
        config = {
            "model": cls._settings.get('DEEPSEEK_MODEL', "deepseek-chat"),
            "api_key": cls._settings.get('DEEPSEEK_API_KEY'),
            "base_url": cls._settings.get('DEEPSEEK_BASE_URL'),
            "temperature": cls._settings.get('DEEPSEEK_TEMPERATURE', 0.0),
            "timeout": cls._settings.get('DEEPSEEK_TIMEOUT', 120),
            "max_retries": cls._settings.get('DEEPSEEK_MAX_RETRIES', 3),
        }
        # 合并覆盖参数
        config.update({k: v for k, v in overrides.items() if v is not None})
        return DeepSeekConfig(**config)

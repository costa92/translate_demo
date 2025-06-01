from llm_core.base import LLM
from typing import Dict, Type, Optional, Any

class LLMFactory:
    _providers: Dict[str, Type[LLM]] = {}
    @classmethod
    def register(cls, provider_name: str):
        def decorator(provider_class: Type[LLM]):
            cls._providers[provider_name] = provider_class
            return provider_class
        return decorator
    @classmethod
    def create(cls, provider: str, model: Optional[str] = None, temperature: float = 0, **kwargs):
        if provider not in cls._providers:
            raise ValueError(f"Unsupported provider: {provider}")
        return cls._providers[provider](model, temperature, **kwargs)

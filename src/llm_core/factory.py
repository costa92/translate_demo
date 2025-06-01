from typing import Dict, Type, Optional, Any, List
from llm_core.base import LLMBase

class LLMFactory:
    """LLM工厂类，负责创建和管理LLM提供商"""
    
    _providers: Dict[str, Type[LLMBase]] = {}
    
    @classmethod
    def register(cls, provider_name: str):
        """注册LLM提供商的装饰器
        
        Args:
            provider_name: 提供商名称
            
        Returns:
            装饰器函数
        """
        def decorator(provider_class: Type[LLMBase]):
            cls._providers[provider_name] = provider_class
            return provider_class
        return decorator
    
    @classmethod
    def create(cls, provider: str, model: Optional[str] = None, temperature: float = 0, **kwargs) -> LLMBase:
        """创建LLM实例
        
        Args:
            provider: LLM提供商名称
            model: 模型名称
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            LLM实例
            
        Raises:
            ValueError: 如果提供商不支持
        """
        if provider not in cls._providers:
            available_providers = list(cls._providers.keys())
            raise ValueError(f"Unsupported provider: {provider}. Available providers: {available_providers}")
        return cls._providers[provider](model, temperature, **kwargs)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """列出所有可用的提供商
        
        Returns:
            提供商名称列表
        """
        return list(cls._providers.keys())

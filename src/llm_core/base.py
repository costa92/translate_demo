from abc import ABC, abstractmethod
from typing import Optional, Type, Dict

class LLM(ABC):
    _providers: Dict[str, Type['LLM']] = {}
    """抽象基类，定义LLM接口"""
    
    @abstractmethod
    def __init__(self, model: Optional[str] = None, temperature: float = 0):
        """初始化LLM
        
        Args:
            model: 模型名称
            temperature: 温度参数
        """
        pass
    
    @property
    @abstractmethod
    def llm(self):
        """返回实际的LLM实例"""
    
    @classmethod
    def register(cls, provider_name: str):
        """注册LLM提供商的装饰器
        
        Args:
            provider_name: 提供商名称
        """
        def decorator(provider_class: Type[LLM]):
            cls._providers[provider_name] = provider_class
            return provider_class
        return decorator
    
    @classmethod
    def create(cls, provider: str = "openai", model: Optional[str] = None, temperature: float = 0, **kwargs) -> 'LLM':
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
        print(cls._providers)
        if provider not in cls._providers:
            raise ValueError(f"Unsupported LLM provider: {provider}. Must be one of {list(cls._providers.keys())}")
        
        return cls._providers[provider](model, temperature, **kwargs)

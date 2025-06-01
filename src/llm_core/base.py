from abc import ABC, abstractmethod
from typing import Optional, Type, Dict, List, Any, Union, ClassVar, AsyncGenerator, Generator

class LLMBase(ABC):
    """LLM基类，定义所有提供商必须实现的接口"""
    
    # 类变量用于注册提供商
    _providers: ClassVar[Dict[str, Type['LLMBase']]] = {}
    
    @abstractmethod
    def __init__(self, model: Optional[str] = None, temperature: float = 0, **kwargs):
        """初始化LLM
        
        Args:
            model: 模型名称
            temperature: 温度参数
            **kwargs: 其他特定于提供商的参数
        """
        self.model = model
        self.temperature = temperature
    
    @property
    @abstractmethod
    def llm(self):
        """返回实际的LLM实例"""
        pass
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本响应
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数，如最大长度、停止条件等
            
        Returns:
            生成的文本响应
        """
        pass
    
    @abstractmethod
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """生成对话响应
        
        Args:
            messages: 对话历史，格式为[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            **kwargs: 其他参数，如最大长度、停止条件等
            
        Returns:
            包含对话响应的字典
        """
        pass
    
    @abstractmethod
    def generate_embeddings(self, texts: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """生成文本嵌入向量
        
        Args:
            texts: 单个文本或文本列表
            **kwargs: 其他特定于提供商的参数
            
        Returns:
            嵌入向量或嵌入向量列表
        """
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """获取文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            token数量
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型的信息
        
        Returns:
            包含模型信息的字典，如模型名称、最大上下文长度等
        """
        pass
    
    # 新增方法：流式响应
    @abstractmethod
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Generator[Dict[str, Any], None, None]:
        """流式生成对话响应
        
        Args:
            messages: 对话历史
            **kwargs: 其他参数
            
        Returns:
            生成器，产生对话响应片段
        """
        pass
    
    # 新增方法：函数调用
    @abstractmethod
    def function_calling(self, messages: List[Dict[str, str]], functions: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """支持函数调用的对话生成
        
        Args:
            messages: 对话历史
            functions: 函数定义列表
            **kwargs: 其他参数
            
        Returns:
            包含对话响应和函数调用的字典
        """
        pass
    
    # 新增方法：异步支持
    @abstractmethod
    async def async_generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步生成对话响应
        
        Args:
            messages: 对话历史
            **kwargs: 其他参数
            
        Returns:
            包含对话响应的字典
        """
        pass
    
    @classmethod
    def register(cls, provider_name: str):
        """注册LLM提供商的装饰器
        
        Args:
            provider_name: 提供商名称
        """
        def decorator(provider_class: Type['LLMBase']):
            cls._providers[provider_name] = provider_class
            return provider_class
        return decorator
    
    @classmethod
    def create(cls, provider: str = "openai", model: Optional[str] = None, temperature: float = 0, **kwargs) -> 'LLMBase':
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
            raise ValueError(f"Unsupported LLM provider: {provider}. Must be one of {list(cls._providers.keys())}")
        
        return cls._providers[provider](model, temperature, **kwargs)

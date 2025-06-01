from typing import Optional
from llm_core.factory import LLMFactory
from llm_core.base import LLMBase

from langchain_ollama import ChatOllama

from llm_core.config import settings_instance
# 请替换为正确的LLM基类导入


@LLMFactory.register("ollama")
class OllamaLLM(LLMBase):
    """Ollama LLM提供商实现"""
    
    def __init__(self, model: Optional[str] = None, temperature: float = 0, **kwargs):
        """初始化Ollama LLM
        
        Args:
            model: 模型名称，如果为None则使用配置中的OLLAMA_MODEL
            temperature: 温度参数
            **kwargs: 其他参数传递给ChatOllama
        """
        self.model = model or settings_instance.get('OLLAMA_MODEL', "llama3.1:8b")
        self.temperature = temperature
        self.base_url = kwargs.get('base_url') or settings_instance.get('OLLAMA_BASE_URL', "http://localhost:11434")
        self._llm = ChatOllama(
            model=self.model, 
            temperature=self.temperature, 
            base_url=self.base_url,
            **kwargs
        )
    
    @property
    def llm(self) -> ChatOllama:
        """返回ChatOllama实例"""
        return self._llm

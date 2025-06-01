from llm_core.config import settings_instance
from typing import Optional
from langchain_openai import ChatOpenAI
from llm_core.factory import LLMFactory
from llm_core.base import LLM

@LLMFactory.register("openai")
class OpenAILLM(LLM):
    """OpenAI LLM提供商实现"""
    
    def __init__(self, model: Optional[str] = None, temperature: float = 0, **kwargs):
        """初始化OpenAI LLM
        
        Args:
            model: 模型名称，如果为None则使用配置中的OPENAI_MODEL
            temperature: 温度参数
            **kwargs: 其他参数传递给ChatOpenAI
        """
        self.model = model or settings_instance.get('OPENAI_MODEL', "gpt-4o-mini")
        self.temperature = temperature
        self.api_key = kwargs.get('api_key') or settings_instance.get('OPENAI_API_KEY')
        self.base_url = kwargs.get('base_url') or settings_instance.get('OPENAI_BASE_URL')
        self._llm = ChatOpenAI(
            model=self.model, 
            temperature=self.temperature, 
            openai_api_key=self.api_key, 
            base_url=self.base_url,
            **kwargs
        )
    
    @property
    def llm(self) -> ChatOpenAI:
        """返回ChatOpenAI实例"""
        return self._llm

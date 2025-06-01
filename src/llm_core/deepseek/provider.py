from typing import Optional, Any
from llm_core.factory import LLMFactory
from llm_core.base import LLMBase
from langchain_deepseek import ChatDeepSeek
from llm_core.config import settings_instance

# 请替换为正确的LLM基类导入
@LLMFactory.register("deepseek")
class DeepSeekLLM(LLMBase):
    """DeepSeek LLM提供商实现"""
    
    def __init__(self, model: Optional[str] = None, temperature: float = 0, **kwargs):
        """初始化DeepSeek LLM
        
        Args:
            model: 模型名称，如果为None则使用配置中的DEEPSEEK_MODEL
            temperature: 温度参数
            **kwargs: 其他参数传递给ChatDeepSeek
        """
        self.model = model or settings_instance.get('DEEPSEEK_MODEL', "deepseek-r1:14b")
        self.temperature = temperature
        self.api_key = kwargs.get('api_key') or settings_instance.get('DEEPSEEK_API_KEY')
        self.base_url = kwargs.get('base_url') or settings_instance.get('DEEPSEEK_BASE_URL')
        self._llm = ChatDeepSeek(
            model=self.model, 
            temperature=self.temperature, 
            api_key=self.api_key, 
            base_url=self.base_url,
            **kwargs
        )
    
    @property
    def llm(self) -> ChatDeepSeek:
        """返回ChatDeepSeek实例"""
        return self._llm

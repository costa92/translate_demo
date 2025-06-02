from typing import Optional, Any, Dict, List, Union, Generator
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
        super().__init__(model, temperature, **kwargs)
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
        
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本响应
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
            
        Returns:
            生成的文本响应
        """
        messages = [{"role": "user", "content": prompt}]
        response = self._llm.invoke(messages)
        return response.content
    
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """生成对话响应
        
        Args:
            messages: 对话历史
            **kwargs: 其他参数
            
        Returns:
            包含对话响应的字典
        """
        response = self._llm.invoke(messages)
        return {"role": "assistant", "content": response.content}
    
    def generate_embeddings(self, texts: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """生成文本嵌入向量
        
        Args:
            texts: 单个文本或文本列表
            **kwargs: 其他参数
            
        Returns:
            嵌入向量或嵌入向量列表
        """
        # DeepSeek目前不直接支持嵌入，这里提供一个简单实现
        raise NotImplementedError("Embeddings not supported yet for DeepSeek")
    
    def get_token_count(self, text: str) -> int:
        """获取文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            token数量
        """
        # 简单估算，每4个字符约为1个token
        return len(text) // 4
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型的信息
        
        Returns:
            包含模型信息的字典
        """
        return {
            "model": self.model,
            "provider": "deepseek",
            "temperature": self.temperature,
            "api_key": f"{self.api_key[:5]}..." if self.api_key else None,
            "base_url": self.base_url
        }
    
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Generator[Dict[str, Any], None, None]:
        """流式生成对话响应
        
        Args:
            messages: 对话历史
            **kwargs: 其他参数
            
        Returns:
            生成器，产生对话响应片段
        """
        # 使用ChatDeepSeek的流式API
        response = self._llm.stream(messages)
        for chunk in response:
            yield {"role": "assistant", "content": chunk.content}
    
    def function_calling(self, messages: List[Dict[str, str]], functions: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """支持函数调用的对话生成
        
        Args:
            messages: 对话历史
            functions: 函数定义列表
            **kwargs: 其他参数
            
        Returns:
            包含对话响应和函数调用的字典
        """
        # DeepSeek支持函数调用，但这里简化实现
        response = self._llm.invoke(messages)
        return {"role": "assistant", "content": response.content, "function_call": None}
    
    async def async_generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步生成对话响应
        
        Args:
            messages: 对话历史
            **kwargs: 其他参数
            
        Returns:
            包含对话响应的字典
        """
        # 简单实现，使用ChatDeepSeek的非异步API
        response = self._llm.invoke(messages)
        return {"role": "assistant", "content": response.content}

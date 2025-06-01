from typing import Dict, List, Any, Union, Optional, Generator
import asyncio
from concurrent.futures import ThreadPoolExecutor

from llm_core.factory import LLMFactory
from llm_core.base import LLMBase
from llm_core.cache import LLMCache, cache_llm_response


class LLMClient:
    """高级LLM客户端，提供缓存和批处理功能"""
    
    def __init__(self, provider: str = "openai", model: Optional[str] = None, **kwargs):
        """初始化LLM客户端
        
        Args:
            provider: LLM提供商名称
            model: 模型名称
            **kwargs: 其他参数传递给提供商
        """
        self.provider = provider
        self.llm = LLMFactory.create(provider, model, **kwargs)
        self.cache = LLMCache()
    
    @cache_llm_response()
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """生成对话响应（带缓存）
        
        Args:
            messages: 对话历史
            **kwargs: 其他参数
            
        Returns:
            对话响应
        """
        return self.llm.generate_chat(messages, **kwargs)
    
    def stream(self, messages: List[Dict[str, str]], **kwargs) -> Generator[Dict[str, Any], None, None]:
        """流式生成对话响应
        
        Args:
            messages: 对话历史
            **kwargs: 其他参数
            
        Returns:
            生成器，产生对话响应片段
        """
        return self.llm.stream_chat(messages, **kwargs)
    
    def function_call(self, messages: List[Dict[str, str]], functions: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """支持函数调用的对话生成
        
        Args:
            messages: 对话历史
            functions: 函数定义列表
            **kwargs: 其他参数
            
        Returns:
            包含对话响应和函数调用的字典
        """
        return self.llm.function_calling(messages, functions, **kwargs)
    
    async def async_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步生成对话响应
        
        Args:
            messages: 对话历史
            **kwargs: 其他参数
            
        Returns:
            对话响应
        """
        return await self.llm.async_generate_chat(messages, **kwargs)
    
    def batch_generate(self, prompts: List[str], batch_size: int = 5, **kwargs) -> List[str]:
        """批量生成文本响应
        
        Args:
            prompts: 提示列表
            batch_size: 批处理大小
            **kwargs: 其他参数
            
        Returns:
            生成的文本响应列表
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = [executor.submit(self.llm.generate_text, prompt, **kwargs) for prompt in prompts]
            for future in futures:
                results.append(future.result())
                
        return results
    
    async def async_batch_generate(self, prompts: List[str], batch_size: int = 5, **kwargs) -> List[str]:
        """异步批量生成文本响应
        
        Args:
            prompts: 提示列表
            batch_size: 批处理大小
            **kwargs: 其他参数
            
        Returns:
            生成的文本响应列表
        """
        results = []
        semaphore = asyncio.Semaphore(batch_size)
        
        async def process_prompt(prompt):
            async with semaphore:
                response = await self.llm.async_generate_chat([{"role": "user", "content": prompt}], **kwargs)
                return response["content"]
        
        tasks = [process_prompt(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        
        return results
    
    def get_embeddings(self, texts: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """生成文本嵌入向量
        
        Args:
            texts: 单个文本或文本列表
            **kwargs: 其他参数
            
        Returns:
            嵌入向量或嵌入向量列表
        """
        return self.llm.generate_embeddings(texts, **kwargs)
    
    def get_token_count(self, text: str) -> int:
        """获取文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            token数量
        """
        return self.llm.get_token_count(text)
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型的信息
        
        Returns:
            模型信息
        """
        return self.llm.get_model_info() 

"""
LLM 核心模块
提供与各种 LLM 提供商的集成
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
import httpx

logger = logging.getLogger(__name__)

class LLMClient:
    """LLM 客户端基类"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """初始化 LLM 客户端
        
        Args:
            api_key: API 密钥
            base_url: API 基础 URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """异步生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            生成的响应
        """
        raise NotImplementedError("子类必须实现此方法")
    
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步生成对话
        
        Args:
            messages: 对话消息列表
            **kwargs: 其他参数
            
        Returns:
            生成的响应
        """
        raise NotImplementedError("子类必须实现此方法")
    
    async def stream_async(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Yields:
            生成的文本片段
        """
        raise NotImplementedError("子类必须实现此方法")
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

class OpenAIClient(LLMClient):
    """OpenAI 客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """初始化 OpenAI 客户端
        
        Args:
            api_key: OpenAI API 密钥
            base_url: OpenAI API 基础 URL
        """
        super().__init__(api_key, base_url)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    async def generate_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """异步生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            生成的响应
        """
        # 构建请求
        model = kwargs.get("model", "gpt-3.5-turbo")
        max_tokens = kwargs.get("max_tokens", 1000)
        temperature = kwargs.get("temperature", 0.1)
        
        # 构建消息
        messages = [{"role": "user", "content": prompt}]
        
        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "content": result["choices"][0]["message"]["content"],
                "model": result["model"],
                "usage": result.get("usage", {})
            }
        except Exception as e:
            logger.error(f"OpenAI API 请求失败: {e}")
            return {"content": f"生成失败: {str(e)}", "error": str(e)}
    
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步生成对话
        
        Args:
            messages: 对话消息列表
            **kwargs: 其他参数
            
        Returns:
            生成的响应
        """
        # 构建请求
        model = kwargs.get("model", "gpt-3.5-turbo")
        max_tokens = kwargs.get("max_tokens", 1000)
        temperature = kwargs.get("temperature", 0.1)
        
        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "content": result["choices"][0]["message"]["content"],
                "model": result["model"],
                "usage": result.get("usage", {})
            }
        except Exception as e:
            logger.error(f"OpenAI API 请求失败: {e}")
            return {"content": f"生成失败: {str(e)}", "error": str(e)}
    
    async def stream_async(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Yields:
            生成的文本片段
        """
        # 构建请求
        model = kwargs.get("model", "gpt-3.5-turbo")
        max_tokens = kwargs.get("max_tokens", 1000)
        temperature = kwargs.get("temperature", 0.1)
        
        # 构建消息
        messages = [{"role": "user", "content": prompt}]
        
        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                response.raise_for_status()
                
                # 处理流式响应
                buffer = ""
                async for chunk in response.aiter_text():
                    if chunk.startswith("data: "):
                        chunk = chunk[6:].strip()
                    
                    if chunk == "[DONE]":
                        break
                    
                    try:
                        if chunk:
                            data = json.loads(chunk)
                            content = data["choices"][0]["delta"].get("content", "")
                            if content:
                                buffer += content
                                yield content
                    except Exception as e:
                        logger.error(f"解析流式响应失败: {e}")
                
                # 如果没有生成任何内容，返回一个空字符串
                if not buffer:
                    yield ""
        except Exception as e:
            logger.error(f"OpenAI 流式 API 请求失败: {e}")
            yield f"生成失败: {str(e)}"

class DeepSeekClient(LLMClient):
    """DeepSeek 客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """初始化 DeepSeek 客户端
        
        Args:
            api_key: DeepSeek API 密钥
            base_url: DeepSeek API 基础 URL
        """
        super().__init__(api_key, base_url)
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    async def generate_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """异步生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            生成的响应
        """
        # 简单实现，实际上应该根据 DeepSeek 的 API 规范进行调整
        return {"content": f"DeepSeek 响应: {prompt[:20]}..."}
    
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步生成对话
        
        Args:
            messages: 对话消息列表
            **kwargs: 其他参数
            
        Returns:
            生成的响应
        """
        # 简单实现，实际上应该根据 DeepSeek 的 API 规范进行调整
        return {"content": f"DeepSeek 对话响应: {messages[-1]['content'][:20]}..."}
    
    async def stream_async(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Yields:
            生成的文本片段
        """
        # 简单实现，实际上应该根据 DeepSeek 的 API 规范进行调整
        yield "DeepSeek 流式响应: "
        for i in range(5):
            await asyncio.sleep(0.5)
            yield f"{prompt[:10]}... 片段 {i+1} "

class SimpleClient(LLMClient):
    """简单客户端，不需要外部 API"""
    
    def __init__(self):
        """初始化简单客户端"""
        super().__init__()
    
    async def generate_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """异步生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            生成的响应
        """
        # 简单实现，直接返回提示的摘要
        return {
            "content": f"基于您的查询，我找到了相关信息。请参考提供的文档片段获取更多详细信息。",
            "model": "simple",
            "usage": {"prompt_tokens": len(prompt), "completion_tokens": 50, "total_tokens": len(prompt) + 50}
        }
    
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步生成对话
        
        Args:
            messages: 对话消息列表
            **kwargs: 其他参数
            
        Returns:
            生成的响应
        """
        # 简单实现，直接返回最后一条消息的摘要
        last_message = messages[-1]["content"]
        return {
            "content": f"基于您的问题，我找到了相关信息。请参考提供的文档片段获取更多详细信息。",
            "model": "simple",
            "usage": {"prompt_tokens": len(last_message), "completion_tokens": 50, "total_tokens": len(last_message) + 50}
        }
    
    async def stream_async(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Yields:
            生成的文本片段
        """
        # 简单实现，分段返回固定响应
        response = "基于您的查询，我找到了相关信息。请参考提供的文档片段获取更多详细信息。"
        words = response.split()
        
        for word in words:
            await asyncio.sleep(0.1)
            yield word + " "

class LLMFactory:
    """LLM 工厂类"""
    
    @staticmethod
    def create(provider: str = "simple", **kwargs) -> LLMClient:
        """创建 LLM 客户端
        
        Args:
            provider: LLM 提供商
            **kwargs: 其他参数
            
        Returns:
            LLM 客户端
        """
        if provider == "openai":
            return OpenAIClient(**kwargs)
        elif provider == "deepseek":
            return DeepSeekClient(**kwargs)
        else:
            return SimpleClient()
    
    @staticmethod
    def create_client(provider: str = "simple", **kwargs) -> LLMClient:
        """创建 LLM 客户端（别名）
        
        Args:
            provider: LLM 提供商
            **kwargs: 其他参数
            
        Returns:
            LLM 客户端
        """
        return LLMFactory.create(provider, **kwargs)
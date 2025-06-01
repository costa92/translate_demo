from typing import Optional, Dict, List, Any, Union, Generator

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import OpenAI, AsyncOpenAI

from llm_core.factory import LLMFactory
from llm_core.base import LLMBase
from llm_core.config import ConfigLoader
from llm_core.exceptions import (
    AuthenticationError, RateLimitError, ModelNotFoundError, 
    ServerError, InvalidRequestError, ContextLengthExceededError
)
from llm_core.utils import retry_with_exponential_backoff, async_retry_with_exponential_backoff, get_tokenizer_for_model


@LLMFactory.register("openai")
class OpenAILLM(LLMBase):
    """OpenAI LLM提供商实现"""
    
    def __init__(self, model: Optional[str] = None, temperature: float = 0, **kwargs):
        """初始化OpenAI LLM
        
        Args:
            model: 模型名称，如果为None则使用配置中的OPENAI_MODEL
            temperature: 温度参数
            **kwargs: 其他参数
        """
        super().__init__(model, temperature, **kwargs)
        
        # 加载配置
        config_kwargs = {k: v for k, v in kwargs.items() if k in ['api_key', 'base_url', 'organization', 'timeout', 'max_retries']}
        if model:
            config_kwargs["model"] = model
        if temperature != 0:
            config_kwargs["temperature"] = temperature
            
        self.config = ConfigLoader.load_openai_config(**config_kwargs)
        
        # 设置基本属性
        self.model = self.config.model
        self.temperature = self.config.temperature
        
        # 初始化客户端
        self._client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            organization=self.config.organization,
            timeout=self.config.timeout
        )
        
        # 初始化异步客户端
        self._async_client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            organization=self.config.organization,
            timeout=self.config.timeout
        )
        
        # 初始化LangChain组件（用于兼容）
        self._llm = ChatOpenAI(
            model=self.model, 
            temperature=self.temperature, 
            openai_api_key=self.config.api_key, 
            base_url=self.config.base_url,
            **{k: v for k, v in kwargs.items() if k not in config_kwargs}
        )
        
        self._embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        # 初始化tokenizer
        self._tokenizer = get_tokenizer_for_model(self.model)
    
    @property
    def llm(self) -> ChatOpenAI:
        """返回ChatOpenAI实例"""
        return self._llm
    
    @retry_with_exponential_backoff()
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本响应
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数，如max_tokens, stop等
            
        Returns:
            生成的文本响应
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens"),
                top_p=kwargs.get("top_p"),
                presence_penalty=kwargs.get("presence_penalty"),
                frequency_penalty=kwargs.get("frequency_penalty"),
                stop=kwargs.get("stop")
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            self._handle_openai_error(e)
    
    @retry_with_exponential_backoff()
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """生成对话响应
        
        Args:
            messages: 对话历史，格式为[{"role": "user", "content": "..."}, ...]
            **kwargs: 其他参数
            
        Returns:
            包含对话响应的字典
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens"),
                top_p=kwargs.get("top_p"),
                presence_penalty=kwargs.get("presence_penalty"),
                frequency_penalty=kwargs.get("frequency_penalty"),
                stop=kwargs.get("stop"),
                response_format=kwargs.get("response_format")
            )
            
            return {
                "content": response.choices[0].message.content,
                "role": "assistant",
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            self._handle_openai_error(e)
    
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Generator[Dict[str, Any], None, None]:
        """流式生成对话响应
        
        Args:
            messages: 对话历史
            **kwargs: 其他参数
            
        Returns:
            生成器，产生对话响应片段
        """
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens"),
                top_p=kwargs.get("top_p"),
                presence_penalty=kwargs.get("presence_penalty"),
                frequency_penalty=kwargs.get("frequency_penalty"),
                stop=kwargs.get("stop"),
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "role": "assistant",
                        "model": self.model,
                        "finish_reason": chunk.choices[0].finish_reason
                    }
        except Exception as e:
            self._handle_openai_error(e)
    
    @retry_with_exponential_backoff()
    def function_calling(self, messages: List[Dict[str, str]], functions: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """支持函数调用的对话生成
        
        Args:
            messages: 对话历史
            functions: 函数定义列表
            **kwargs: 其他参数
            
        Returns:
            包含对话响应和函数调用的字典
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens"),
                tools=functions,
                tool_choice=kwargs.get("tool_choice", "auto")
            )
            
            result = {
                "content": response.choices[0].message.content,
                "role": "assistant",
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
            # 如果有函数调用
            if response.choices[0].message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tool.id,
                        "type": tool.type,
                        "function": {
                            "name": tool.function.name,
                            "arguments": tool.function.arguments
                        }
                    }
                    for tool in response.choices[0].message.tool_calls
                ]
            
            return result
        except Exception as e:
            self._handle_openai_error(e)
    
    @retry_with_exponential_backoff()
    async def async_generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """异步生成对话响应
        
        Args:
            messages: 对话历史
            **kwargs: 其他参数
            
        Returns:
            包含对话响应的字典
        """
        try:
            response = await self._async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens"),
                top_p=kwargs.get("top_p"),
                presence_penalty=kwargs.get("presence_penalty"),
                frequency_penalty=kwargs.get("frequency_penalty"),
                stop=kwargs.get("stop")
            )
            
            return {
                "content": response.choices[0].message.content,
                "role": "assistant",
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            self._handle_openai_error(e)
    
    @retry_with_exponential_backoff()
    def generate_embeddings(self, texts: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """生成文本嵌入向量
        
        Args:
            texts: 单个文本或文本列表
            **kwargs: 其他特定于提供商的参数
            
        Returns:
            嵌入向量或嵌入向量列表
        """
        try:
            if isinstance(texts, str):
                return self._embeddings.embed_query(texts)
            else:
                return self._embeddings.embed_documents(texts)
        except Exception as e:
            self._handle_openai_error(e)
    
    def get_token_count(self, text: str) -> int:
        """获取文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            token数量
        """
        return len(self._tokenizer.encode(text))
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型的信息
        
        Returns:
            包含模型信息的字典
        """
        model_info = {
            "model": self.model,
            "provider": "openai",
            "temperature": self.temperature,
        }
        
        # 根据模型名称设置不同的最大上下文长度
        context_window = 4096  # 默认值
        if "gpt-4o" in self.model:
            context_window = 128000
        elif "gpt-4-turbo" in self.model:
            context_window = 128000
        elif "gpt-4" in self.model:
            context_window = 8192
        elif "gpt-3.5-turbo-16k" in self.model:
            context_window = 16384
        elif "gpt-3.5-turbo" in self.model:
            context_window = 4096
            
        model_info["context_window"] = context_window
        
        return model_info
    
    def _handle_openai_error(self, error):
        """处理OpenAI错误并转换为自定义异常
        
        Args:
            error: 原始异常
            
        Raises:
            适当的自定义异常
        """
        import openai
        error_str = str(error)
        provider = "openai"
        
        if "authentication" in error_str.lower() or "api key" in error_str.lower():
            raise AuthenticationError("Authentication failed", provider, {"original": error_str})
        elif "rate limit" in error_str.lower():
            raise RateLimitError("Rate limit exceeded", provider, {"original": error_str})
        elif "model" in error_str.lower() and "does not exist" in error_str.lower():
            raise ModelNotFoundError(f"Model '{self.model}' not found", provider, {"original": error_str})
        elif "context length" in error_str.lower() or "token limit" in error_str.lower():
            raise ContextLengthExceededError("Context length exceeded", provider, {"original": error_str})
        elif "server" in error_str.lower() or "502" in error_str.lower() or "504" in error_str.lower():
            raise ServerError("Server error", provider, {"original": error_str})
        else:
            raise InvalidRequestError(error_str, provider, {"original": error_str})

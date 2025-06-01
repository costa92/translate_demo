from typing import Optional, Dict, Any

class LLMError(Exception):
    """LLM相关错误的基类"""
    
    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        self.provider = provider
        self.details = details or {}
        super().__init__(f"{provider} error: {message}")


class AuthenticationError(LLMError):
    """认证错误，通常是API密钥无效或过期"""
    pass


class RateLimitError(LLMError):
    """速率限制错误，通常是请求过于频繁"""
    pass


class ModelNotFoundError(LLMError):
    """模型未找到错误，通常是请求了不存在的模型"""
    pass


class ServerError(LLMError):
    """服务器错误，通常是提供商服务器出现问题"""
    pass


class InvalidRequestError(LLMError):
    """无效请求错误，通常是请求参数无效"""
    pass


class ContextLengthExceededError(LLMError):
    """上下文长度超出限制错误"""
    pass 

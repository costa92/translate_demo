import time
import random
import asyncio
import logging
from functools import wraps
from typing import Callable, TypeVar, Any, Dict, Tuple

from llm_core.exceptions import RateLimitError, ServerError

T = TypeVar('T')
logger = logging.getLogger("llm_core")


def retry_with_exponential_backoff(
    max_retries: int = 5,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple = (RateLimitError, ServerError),
):
    """指数退避重试装饰器
    
    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        exponential_base: 指数基数
        jitter: 是否添加随机波动
        retryable_exceptions: 可重试的异常类型
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        raise
                    
                    delay = initial_delay * (exponential_base ** (retries - 1))
                    if jitter:
                        delay *= random.uniform(0.8, 1.2)
                        
                    logger.warning(f"Retrying '{func.__name__}' after {delay:.2f}s due to {e}")
                    time.sleep(delay)
        return wrapper
    return decorator


async def async_retry_with_exponential_backoff(
    max_retries: int = 5,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple = (RateLimitError, ServerError),
):
    """异步指数退避重试装饰器
    
    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        exponential_base: 指数基数
        jitter: 是否添加随机波动
        retryable_exceptions: 可重试的异常类型
        
    Returns:
        异步装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        raise
                    
                    delay = initial_delay * (exponential_base ** (retries - 1))
                    if jitter:
                        delay *= random.uniform(0.8, 1.2)
                        
                    logger.warning(f"Retrying '{func.__name__}' after {delay:.2f}s due to {e}")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator


def get_tokenizer_for_model(model_name: str):
    """获取模型对应的tokenizer
    
    Args:
        model_name: 模型名称
        
    Returns:
        tokenizer实例
    """
    import tiktoken
    try:
        return tiktoken.encoding_for_model(model_name)
    except:
        # 对于未知模型，返回一个通用编码器
        return tiktoken.get_encoding("cl100k_base") 

import hashlib
import json
import time
from typing import Dict, Any, Optional, Callable, Union, List
from functools import wraps


class LLMCache:
    """LLM响应缓存"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl: 缓存生存时间（秒）
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def _get_cache_key(self, provider: str, model: str, args: Any) -> str:
        """生成缓存键
        
        Args:
            provider: 提供商名称
            model: 模型名称
            args: 缓存参数
            
        Returns:
            缓存键
        """
        # 序列化参数并计算哈希值
        key_data = {
            "provider": provider,
            "model": model,
            "args": args
        }
        serialized = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(serialized.encode()).hexdigest()
    
    def get(self, provider: str, model: str, args: Any) -> Optional[Any]:
        """获取缓存值
        
        Args:
            provider: 提供商名称
            model: 模型名称
            args: 缓存参数
            
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        key = self._get_cache_key(provider, model, args)
        if key in self.cache:
            # 检查是否过期
            cache_entry = self.cache[key]
            if time.time() - cache_entry["timestamp"] <= self.ttl:
                return cache_entry["value"]
            # 过期则删除
            del self.cache[key]
        return None
    
    def set(self, provider: str, model: str, args: Any, value: Any) -> None:
        """设置缓存值
        
        Args:
            provider: 提供商名称
            model: 模型名称
            args: 缓存参数
            value: 要缓存的值
        """
        # 如果缓存已满，删除最早的条目
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
        
        key = self._get_cache_key(provider, model, args)
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()


def cache_llm_response(cache: Optional[LLMCache] = None):
    """缓存LLM响应的装饰器
    
    Args:
        cache: LLMCache实例，如果为None则创建一个新实例
        
    Returns:
        装饰器函数
    """
    if cache is None:
        cache = LLMCache()
        
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 从kwargs中提取不应该影响缓存键的参数
            cache_kwargs = kwargs.copy()
            
            # 流式响应和不确定性较高的请求不应缓存
            if cache_kwargs.get("stream") or cache_kwargs.get("temperature", 0) > 0.1:
                return func(self, *args, **kwargs)
            
            # 获取提供商和模型信息
            provider = self.__class__.__name__
            model = getattr(self, "model", "default")
            
            # 尝试从缓存获取
            cache_key = (args, json.dumps(cache_kwargs, sort_keys=True))
            cached = cache.get(provider, model, cache_key)
            if cached is not None:
                return cached
            
            # 调用原始函数
            result = func(self, *args, **kwargs)
            
            # 缓存结果
            cache.set(provider, model, cache_key, result)
            return result
        return wrapper
    return decorator 

"""
LLM核心模块使用示例
"""
import asyncio
import logging
from typing import List

from llm_core import LLMFactory, LLMClient, LLMBase


def basic_usage_example():
    """基本用法示例"""
    print("\n=== 基本用法示例 ===")
    
    # 1. 直接使用LLMFactory创建LLM实例
    openai_llm = LLMFactory.create("openai", temperature=0.7)
    response = openai_llm.generate_text("用Python解释什么是工厂模式")
    print(f"OpenAI响应: {response[:100]}...")
    
    # 2. 使用高级客户端
    client = LLMClient(provider="openai", temperature=0)
    chat_response = client.chat([
        {"role": "user", "content": "Python的优势是什么？"}
    ])
    print(f"聊天响应: {chat_response['content'][:100]}...")


def streaming_example():
    """流式响应示例"""
    print("\n=== 流式响应示例 ===")
    
    client = LLMClient(provider="openai")
    print("流式响应内容:")
    
    # 流式生成
    for chunk in client.stream([
        {"role": "user", "content": "写一首关于编程的短诗"}
    ]):
        print(chunk["content"], end="", flush=True)
    print("\n")


def function_calling_example():
    """函数调用示例"""
    print("\n=== 函数调用示例 ===")
    
    openai_llm = LLMFactory.create("openai")
    
    # 定义一个天气查询函数
    weather_function = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取指定位置的当前天气",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "城市名称，例如：北京"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "温度单位"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    # 调用函数
    result = openai_llm.function_calling(
        [{"role": "user", "content": "北京的天气怎么样？"}],
        functions=weather_function
    )
    
    if "tool_calls" in result:
        print("检测到函数调用:")
        for tool_call in result["tool_calls"]:
            print(f"函数名: {tool_call['function']['name']}")
            print(f"参数: {tool_call['function']['arguments']}")
    else:
        print(f"普通响应: {result['content']}")


async def async_example():
    """异步用法示例"""
    print("\n=== 异步用法示例 ===")
    
    client = LLMClient(provider="openai")
    
    # 异步聊天
    response = await client.async_chat([
        {"role": "user", "content": "解释Python中的asyncio"}
    ])
    print(f"异步响应: {response['content'][:100]}...")
    
    # 异步批处理
    prompts = [
        "介绍一个关于太空的事实",
        "什么是机器学习？",
        "解释量子计算"
    ]
    
    print("开始批量处理请求...")
    batch_results = await client.async_batch_generate(prompts)
    for i, result in enumerate(batch_results):
        print(f"批量结果 {i+1}: {result[:50]}...")


def batch_processing_example():
    """批处理示例"""
    print("\n=== 批处理示例 ===")
    
    client = LLMClient(provider="openai")
    
    prompts = [
        "用一句话描述Python",
        "用一句话描述Java",
        "用一句话描述Go"
    ]
    
    print("同步批量处理...")
    results = client.batch_generate(prompts)
    
    for i, result in enumerate(results):
        print(f"结果 {i+1}: {result}")


def embeddings_example():
    """嵌入向量示例"""
    print("\n=== 嵌入向量示例 ===")
    
    client = LLMClient(provider="openai")
    
    text = "人工智能是计算机科学的一个分支"
    embedding = client.get_embeddings(text)
    
    print(f"文本: {text}")
    print(f"嵌入维度: {len(embedding)}")
    print(f"嵌入向量前5个值: {embedding[:5]}")


async def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行示例
    basic_usage_example()
    streaming_example()
    function_calling_example()
    await async_example()
    batch_processing_example()
    embeddings_example()
    
    print("\n所有示例运行完成")


if __name__ == "__main__":
    asyncio.run(main()) 

# LLM核心模块

这个模块提供了一个统一、灵活、可扩展的接口来使用各种大型语言模型（LLM）。

## 主要优化

1. **简化类层次结构**：
   - 移除了重复的`LLMInterface`接口，统一使用`LLMBase`作为唯一抽象基类
   - 定义了清晰的抽象方法和默认实现

2. **统一工厂模式**：
   - 在`LLMFactory`中实现统一的工厂模式
   - 增强了提供商注册机制，更加类型安全

3. **增强核心功能**：
   - 添加了流式响应支持（`stream_chat`方法）
   - 支持函数调用（`function_calling`方法）
   - 添加异步接口（`async_generate_chat`等）
   - 实现批量处理能力

4. **改进配置管理**：
   - 使用Pydantic模型进行类型安全的配置
   - 支持多来源配置（环境变量、配置文件、代码参数）

5. **错误处理与重试**：
   - 添加专用异常类层次结构
   - 实现指数退避重试装饰器

6. **性能优化**：
   - 实现响应缓存系统
   - 添加并发和异步处理支持

7. **高级客户端接口**：
   - 提供`LLMClient`作为高级接口，简化使用
   - 支持缓存、批处理和异步操作

## 主要组件

- **LLMBase**: 所有LLM提供商的抽象基类
- **LLMFactory**: 创建LLM实例的工厂类
- **LLMClient**: 高级客户端接口，提供缓存和批处理功能
- **LLMCache**: LLM响应缓存
- **OpenAILLM**: OpenAI LLM提供商实现
- **OllamaLLM**: Ollama LLM提供商实现
- **DeepSeekLLM**: DeepSeek LLM提供商实现

## 使用示例

```python
from llm_core import LLMFactory, LLMClient

# 直接使用工厂创建LLM实例
openai_llm = LLMFactory.create("openai", temperature=0.7)
response = openai_llm.generate_text("用Python解释什么是工厂模式")

# 使用高级客户端
client = LLMClient(provider="openai")
chat_response = client.chat([
    {"role": "user", "content": "Python的优势是什么？"}
])

# 流式生成
for chunk in client.stream([
    {"role": "user", "content": "写一首关于编程的短诗"}
]):
    print(chunk["content"], end="")

# 函数调用
result = client.function_call(
    [{"role": "user", "content": "北京的天气怎么样？"}],
    functions=[...] # 函数定义
)

# 异步聊天
async def async_example():
    response = await client.async_chat([
        {"role": "user", "content": "解释Python中的asyncio"}
    ])
    return response
```

## 设计原则

本模块的优化遵循以下SOLID原则：

- **单一职责原则**：每个类有明确的职责
- **开闭原则**：易于扩展，无需修改现有代码
- **里氏替换原则**：子类可以替换父类
- **接口隔离原则**：提供精确的接口定义
- **依赖倒置原则**：依赖抽象而非具体实现

## 未来计划

- 添加更多LLM提供商支持
- 实现模型自动切换策略
- 增加语义缓存
- 提供更丰富的性能监控 

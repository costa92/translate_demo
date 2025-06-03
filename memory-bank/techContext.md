# 技术上下文

## 核心技术栈

1. **编程语言**

   - Python 3.11+

2. **核心框架与库**

   - LangChain：用于构建 LLM 应用的框架
   - LangChain Core：核心组件
   - Click：命令行接口
   - Dynaconf：配置管理
   - gTTS：Google Text-to-Speech 语音合成

3. **LLM 提供商**

   - OpenAI (通过 langchain_openai)
   - DeepSeek (通过 langchain_deepseek)
   - Ollama (通过 langchain_ollama)

4. **开发工具**
   - Poetry：依赖管理
   - pytest：测试框架
   - pre-commit：代码质量检查

## 服务运行参数配置

- 所有服务运行参数（如 API host/port）统一由 Dynaconf settings 管理。
- 配置优先级为：环境变量 > settings.yml > 默认值。
- 推荐通过 settings.yml 或环境变量调整服务端口和 host。

## 项目结构

```
src/
├── llm_core/          # LLM核心抽象层和工厂
│   ├── base.py        # 基础抽象类
│   ├── factory.py     # 工厂类
│   ├── config.py      # 配置管理
│   ├── ollama/        # Ollama提供商实现
│   ├── deepseek/      # DeepSeek提供商实现
│   └── ...
├── tools/             # 工具集
│   ├── translate/     # 翻译工具
│   │   ├── translate.py       # 翻译函数
│   │   ├── translate_tool.py  # 翻译工具类
│   │   └── config.py          # 翻译提示词配置
│   └── tts/          # 文字转语音工具
│       └── tts_tool.py       # 语音合成工具类
├── agents/            # 智能体
│   └── TranslatorAgent.py    # 翻译智能体
└── translate_demo/    # 主应用
    ├── cmd.py         # 命令行入口
    ├── config/        # 应用配置
    └── log.py         # 日志配置
```

## 设计模式

1. **工厂模式**：使用 LLMFactory 创建不同 LLM 提供商的实例
2. **策略模式**：不同的 LLM 提供商实现相同的接口
3. **装饰器模式**：用于注册 LLM 提供商
4. **适配器模式**：统一不同 LLM 提供商的 API
5. **组合模式**：集成翻译和语音合成功能

## 开发规范

1. **代码风格**

   - 使用类型注解
   - 为函数和类提供清晰的文档字符串
   - 遵循 PEP 8 风格指南

2. **错误处理**

   - 使用专门的异常类层次结构
   - 提供有意义的错误消息
   - 实现合理的回退机制

3. **测试策略**

   - 单元测试覆盖核心功能
   - 集成测试验证不同组件的协作
   - 语音输出质量测试

4. **配置管理**
   - 使用环境变量和配置文件
   - 支持开发和生产环境的不同配置

## API 设计

1. **LLMBase 抽象类**

   - 定义所有 LLM 提供商必须实现的接口
   - 包括文本生成、聊天、嵌入等核心功能

2. **翻译 API**

   - 统一的翻译函数接口
   - 支持 LangChain 工具集成
   - 支持智能体调用

3. **语音合成 API**
   - 基于 gTTS 的语音合成接口
   - 支持多语言文本转语音
   - 可配置的输出参数（速度、音量等）
   - 临时文件自动管理

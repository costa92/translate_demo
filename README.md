# Translate Demo

一个多语言翻译演示项目，基于大型语言模型（LLM），支持多种 LLM 提供商（OpenAI、DeepSeek、Ollama 等），并集成 LangChain 工具、智能体（Agent）、命令行和语音合成功能。

## 项目目标

- 提供高质量的文本翻译，支持多语言、多 LLM 后端
- 以 LangChain 工具/Agent 形式集成，便于扩展和二次开发
- 支持命令行一键翻译和语音合成

## 技术栈

- **Python 3.11+**
- **LangChain**（核心 LLM 框架）
- **FastAPI**（可选，API 服务）
- **Click**（命令行接口）
- **Dynaconf**（配置管理）
- **gTTS**（文字转语音）
- **pytest**（测试）
- **Poetry**（依赖管理）

## 支持的 LLM 提供商

- OpenAI（GPT-3.5, GPT-4, GPT-4o 等）
- DeepSeek
- Ollama（本地大模型）

## 项目结构

```bash
src/
├── llm_core/          # LLM核心抽象层和工厂
│   ├── base.py        # 基础抽象类
│   ├── factory.py     # 工厂类
│   ├── config.py      # 配置管理
│   ├── ollama/        # Ollama实现
│   ├── deepseek/      # DeepSeek实现
│   └── ...
├── tools/             # 工具集
│   ├── translate/     # 翻译工具
│   └── text_to_speech/# 文字转语音工具
├── agents/            # 智能体
│   └── TranslatorAgent.py
└── translate_demo/    # 主应用（命令行、API等）
    ├── cmd.py         # CLI 入口
    ├── config/        # 应用配置
    └── log.py         # 日志配置
```

## 安装与依赖管理

推荐使用 Poetry：

```bash
pip install poetry
poetry install
```

或直接安装包：

```bash
pip install translate_demo
```

## 快速开始

### 1. 命令行翻译

```bash
poetry run translate
# 或
translate
```

### 2. 代码调用

```python
from llm_core import LLMFactory
from tools.translate.translate import translate

llm = LLMFactory.create("openai", model="gpt-4o", api_key="your-api-key")
result = translate(llm, "Hello, world!", "en", "zh")
print(result)
```

### 3. 异步翻译

```python
from tools.translate.translate import translate_async
import asyncio

async def main():
    llm = LLMFactory.create("openai", model="gpt-4o", api_key="your-api-key")
    result = await translate_async(llm, "Hello, world!", "en", "zh")
    print(result)

asyncio.run(main())
```

### 4. 智能体（Agent）调用

```python
from agents.TranslatorAgent import TranslatorAgent
llm = LLMFactory.create("openai", model="gpt-4o", api_key="your-api-key")
agent = TranslatorAgent(llm)
print(agent.translate("I like you, but I don't know you", "Chinese"))
```

### 5. 文字转语音

```python
from tools.text_to_speech.tts_tool import TextToSpeechTool

text = "你好，世界！"
tts_tool = TextToSpeechTool()
audio_path = tts_tool._run(text=text, language="zh", output_path="output.mp3")
print(f"音频文件已生成: {audio_path}")
```

## 配置说明

- 推荐通过环境变量或 `src/translate_demo/config/settings.yml` 配置参数。
- LLM 相关密钥可通过环境变量传递：

```bash
export OPENAI_API_KEY="your-openai-api-key"
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

- 其他参数（如模型名、host/port）可在 `settings.yml` 或环境变量中设置。

## 典型应用场景

- 文档国际化与本地化
- 跨语言交流
- 语言学习辅助
- 语音播报

## 开发规范

- 代码需类型注解，注释清晰，遵循 PEP8
- 单元测试覆盖核心逻辑，推荐使用 pytest
- 配置管理优先级：环境变量 > settings.yml > 默认值

## 项目状态

本项目处于开发阶段，已实现多 LLM 后端、LangChain 工具/Agent、命令行和 TTS 等核心功能。

## 贡献

欢迎 PR 与 Issue！

## License

MIT

## 参考文档

- [LLM：Agent](https://www.drinkingfishingseeking.com/2025/02/20/llm-agent/)
- [DeepSeek 模型微调](https://zhuanlan.zhihu.com/p/17628689019)

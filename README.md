# LLM Core

A Python package for handling different LLM providers with a unified interface.

## Features

- Unified interface for multiple LLM providers (OpenAI, Anthropic, etc.)
- Async support for better performance
- Easy to extend with new providers
- Built-in error handling and retries
- Type hints for better IDE support

## Project Structure

```
├── .editorconfig
├── .github/
│   └── workflows/
│       └── main.yml
├── .gitignore
├── .pre-commit-config.yaml
├── .pytest_cache/
├── LICENSE
├── README.md
├── __init__.py
├── __pycache__/
├── docs/
│   └── development.md
├── poetry.lock
├── pyproject.toml
├── src/
│   ├── agents/
│   ├── llm_core/
│   ├── tools/
│   └── translate_demo/
├── test_import.py
├── tests/
└── tox.ini
```

## Installation

```bash
pip install poetry
```

```bash
pip install llm-core
```

Or with Poetry:

```bash
poetry add llm-core
```

## Dependency Management

The project uses `poetry` for dependency management. Here are some useful commands:

- Install dependencies: `poetry install`
- Add a new dependency: `poetry add <package-name>`
- Update dependencies: `poetry update`

## Quick Start

```python
from llm_core import LLMFactory

# Create an OpenAI LLM instance
llm = LLMFactory.create("openai", api_key="your-api-key")

# Translate text
result = llm.translate("Hello, world!", "en", "zh")
print(result)

# Async translation
async def translate_async():
    result = await llm.translate_async("Hello, world!", "en", "zh")
    print(result)
```

## Supported Providers

- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- More coming soon...

## Configuration

You can configure the LLM providers using environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

Or pass the configuration directly when creating an instance:

```python
llm = LLMFactory.create(
    "openai",
    api_key="your-api-key",
    model="gpt-4"
)
```

## Development Guide

### Environment Setup

1. Install Dependencies:
   For detailed development instructions, please refer to [development](docs/development.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 参考文档

[LLM：Agent](https://www.drinkingfishingseeking.com/2025/02/20/llm-agent/)
[DeepSeek 模型微调](https://zhuanlan.zhihu.com/p/17628689019)

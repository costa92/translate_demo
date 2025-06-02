# 项目配置说明

本文档详细说明了 `pyproject.toml` 中的配置信息。

## 项目元数据

```toml
[tool.poetry]
name = "translate_demo"
version = "0.1.0"
description = "My Awesome Project!"
authors = ["costa <costa9293@gmail.com>"]
license = "MIT"
readme = "README.md"
```

## 包结构

项目在 `src` 目录下包含以下包：

```toml
packages = [
  {include = "llm_core", from = "src"},
  {include = "tools", from = "src"},
  {include = "agents", from = "src"},
  {include = "translate_demo", from = "src"},
]
```

## 依赖项

### 主要依赖

项目使用以下主要依赖：

- `aiohttp`: ^3.12.4 - 用于异步 HTTP 请求
- `click`: ^8.2.1 - 命令行界面工具
- `dynaconf`: ^3.2.11 - 配置管理工具
- `langchain`: ^0.3.25 - LangChain 核心功能
- `langchain-core`: ^0.3.60 - LangChain 核心组件
- `langchain-deepseek`: ^0.1.3 - DeepSeek 集成
- `langchain-ollama`: ^0.3.3 - Ollama 集成
- `langchain-openai`: ^0.3.18 - OpenAI 集成
- `ollama`: ^0.4.8 - Ollama 客户端
- `openai`: ^1.12.0 - OpenAI 客户端
- `fastapi`: ^0.115.12 - Web 框架
- `uvicorn`: ^0.34.3 - ASGI 服务器

### 开发依赖

开发工具和测试框架：

- `isort`: ^5.12.0 - 导入语句排序工具
- `mkdocs`: ^1.4.3 - 文档生成器
- `mkdocs-material`: ^8.5.11 - MkDocs 的 Material 主题
- `pre-commit`: ^3.3.2 - Git 钩子工具
- `pylint`: ^2.17.4 - 代码检查工具
- `pytest`: ^8.0.0 - 测试框架
- `pytest-cov`: ^4.1.0 - 测试覆盖率工具
- `pytest-pylint`: ^0.19.0 - Pylint 与 pytest 的集成
- `tox`: ^4.5.2 - 测试自动化工具

## 命令行脚本

项目提供了以下命令行入口点：

```toml
[tool.poetry.scripts]
translate = "translate_demo.cmd:run"
translate_demo = "translate_demo.cmdline:main"
translate_api = "translate_demo.api:main"
```

- `translate`: 主要翻译命令
- `translate_demo`: 演示命令行界面
- `translate_api`: API 服务器入口点

## 测试配置

```toml
[tool.pytest.ini_options]
python_files = "tests.py test_*.py *_tests.py"
testpaths = "tests"
```

## 代码风格

```toml
[tool.pylint.design]
max-line-length = 120
```

项目使用 120 字符作为最大行长度，以保持代码风格的一致性。

## 构建系统

项目使用 Poetry 作为构建系统：

```toml
[build-system]
build-backend = "poetry.core.masonry.api"
requires = ["poetry-core"]
```

## 使用说明

1. 安装依赖：
   ```bash
   poetry install
   ```

2. 运行测试：
   ```bash
   poetry run pytest
   ```

3. 启动翻译服务：
   ```bash
   poetry run translate
   ```

4. 启动 API 服务：
   ```bash
   poetry run translate_api
   ```

## 开发指南

1. 代码风格检查：
   ```bash
   poetry run pylint src/
   ```

2. 导入语句排序：
   ```bash
   poetry run isort src/
   ```

3. 运行所有测试：
   ```bash
   poetry run tox
   ```
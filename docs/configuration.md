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

## 知识库存储配置 (KnowledgeStorageAgent)

`KnowledgeStorageAgent` 使用可插拔的提供者（Provider）架构来支持多种存储后端。你可以在初始化 `KnowledgeStorageAgent` 时选择一个提供者并提供相应的配置。

### 初始化示例

```python
from src.agents.knowledge_base.knowledge_storage_agent import KnowledgeStorageAgent

# 示例 1: 使用默认的内存存储 (无需配置)
memory_storage = KnowledgeStorageAgent(provider_type='memory')

# 示例 2: 使用 Notion 作为后端
notion_config = {
    "api_key": "YOUR_NOTION_API_KEY",
    "database_id": "YOUR_NOTION_DATABASE_ID"
}
notion_storage = KnowledgeStorageAgent(provider_type='notion', provider_config=notion_config)

# 示例 3: 使用阿里云 OSS 作为后端
oss_config = {
    "access_key": "YOUR_OSS_ACCESS_KEY",
    "secret_key": "YOUR_OSS_SECRET_KEY",
    "endpoint": "YOUR_OSS_ENDPOINT",
    "bucket_name": "YOUR_BUCKET_NAME"
}
oss_storage = KnowledgeStorageAgent(provider_type='oss', provider_config=oss_config)
```

### 支持的提供者

| `provider_type` | 描述 | 必要配置 (`provider_config`) |
| :--- | :--- | :--- |
| `memory` | **默认**。一个简单的内存存储，程序关闭后数据会丢失。 | `None` |
| `notion` | 使用 Notion 数据库作为后端。 | `api_key`, `database_id` |
| `oss` | 使用兼容 S3 的对象存储服务（如阿里云 OSS, MinIO）。 | `access_key`, `secret_key`, `endpoint`, `bucket_name` |

### Google Cloud Storage (GCS) (`gcs`)

使用 Google Cloud Storage (GCS) 进行**集中式、高可扩展性**的存储。这是在 Google Cloud 生态中最推荐的专业存储方案。

#### 配置参数

| 参数 | 类型 | 描述 |
| :--- | :--- | :--- |
| `service_account_key_path` | `str` | **必需**。指向服务账户的 JSON 密钥文件的路径。|
| `bucket_name` | `str` | **必需**。您在 GCS 中创建的全球唯一的存储桶名称。|

> 要了解如何创建服务账户和 GCS 存储桶，请遵循我们的详细分步指南：**[如何设置 Google Cloud Storage (GCS) 用于集中存储](./gcs_setup.md)**。

### Google Drive (Service Account) (`google_drive_service_account`)

使用 Google Drive 服务账户进行**集中式、非交互式**的存储。所有用户运行应用时，文件都会被保存到**同一个共享文件夹**中，应用以自己的身份进行操作，**无需浏览器登录**。

#### 配置参数

| 参数 | 类型 | 描述 |
| :--- | :--- | :--- |
| `service_account_key_path` | `str` | **必需**。指向服务账户的 JSON 密钥文件的路径。要了解如何生成此文件并设置共享文件夹，请遵循我们的详细分步指南：**[如何为集中存储设置 Google Drive 服务账户](./google_drive_service_account_setup.md)**。 |
| `folder_name` | `str` | *可选*。您在个人 Google Drive 中创建并与服务账户共享的文件夹的名称。如果省略，将默认为 `"CentralizedKnowledgeBase"`。 |

### Google Drive (`google_drive`)

使用 Google Drive 作为知识库后端。每个知识块（chunk）都会被存储为根目录下一个指定文件夹中的一个独立的 `.json` 文件。

#### 配置参数

| 参数 | 类型 | 描述 |
| :--- | :--- | :--- |
| `credentials_path` | `str` | **必需**。指向 `credentials.json` 文件的路径。这是一个包含 API 访问密钥的敏感文件。要了解如何生成此文件，请遵循我们的详细分步指南：**[如何获取 Google Drive API 的 `credentials.json` 文件](./google_drive_setup.md)**。 |
| `token_path` | `str` | **必需**。用于存储和缓存用户授权令牌的路径，文件名为 `token.json`。**此文件是自动生成的**，在您第一次通过浏览器成功授权应用后，它会出现在您指定的路径。您只需提供一个文件名，无需手动创建。 |
| `folder_name` | `str` | *可选*。您希望在 Google Drive 中用于存储知识文件的文件夹名称。如果省略此参数，系统将默认使用 `"KnowledgeBase"` 作为文件夹名。如果该文件夹不存在，系统会自动创建。 |

#### 示例配置

```python
gdrive_config = {
    # 遵循 examples/google_drive_auth.py 的指引生成此文件
    "credentials_path": "credentials.json",

    # 首次运行后会自动创建此文件
    "token_path": "token.json",

    # （可选）自定义在 Google Drive 中使用的文件夹名称
    "folder_name": "MyProjectKnowledge"
}

gdrive_agent = KnowledgeStorageAgent(
    provider_type='google_drive',
    provider_config=gdrive_config
)
```

> **重要提示**: `credentials.json` 和 `token.json` 文件包含敏感信息。请确保已将它们添加到您的 `.gitignore` 文件中，以避免意外将它们提交到版本控制系统。

| `onedrive` | 使用 Microsoft OneDrive 作为后端。 | *需要 OAuth 凭证* |

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

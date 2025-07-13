# 项目开发说明

## 项目简介

本项目是一个基于 Python + LangChain 的多 LLM（如 DeepSeek、Ollama、OpenAI）翻译演示工具。
支持命令行一键翻译，具备多 provider 适配、异常回退、可扩展的 LLM 工厂和工具链。

## 主要开发节奏

- 2025-06-01：项目初始化，完成基础目录、依赖和 LLM 抽象层。
- 2025-06-02：重构 LLM provider，完善 DeepSeek/Ollama 支持，命令行默认切换为 DeepSeek，完善异常处理和 fallback，初始化 memory-bank 记忆库。
- 2025-06-03：添加 fastapi、uvicorn 依赖，实现异步翻译 API。

---

# Begin

## LLM Provider 适配与命令行用法

### Provider 适配

- 所有 LLM provider（如 DeepSeek、Ollama）均需实现 `LLMBase` 抽象类的全部方法（如 generate_text、generate_chat 等）。
- provider 注册采用工厂模式，便于后续扩展更多 LLM。
- DeepSeek 默认使用 `deepseek-chat` 模型，Ollama 支持本地模型。

### 命令行用法

- 入口：`poetry run translate`
- 默认调用 DeepSeek provider，支持自动 fallback。
- 支持直接调用 `translate` 工具函数，推荐用法如下：

```python
from tools.translate.translate import translate
result = translate(llm, text="I like you, but I don't know you", from_lang="English", to_lang="Chinese")
print(result)
```

---

## FastAPI 异步翻译接口

- 依赖：`fastapi`、`uvicorn` 已加入 pyproject.toml
- 启动方式：

  - 推荐：

    ```sh
    poetry run uvicorn src.translate_demo.api:app --reload
    ```

  - 或用脚本：

    ```sh
    poetry run translate_api
    ```

- 主要接口：
  - `POST /api/translate`
  - 请求参数：`{"text": str, "from_lang": str, "to_lang": str}`
  - 返回：`{"result": str}`
- 示例请求：

```sh
curl -X POST http://127.0.0.1:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "I like you, but I do not know you", "from_lang": "English", "to_lang": "Chinese"}'
```

---

## memory-bank 机制

- 项目引入 memory-bank 目录，记录项目简介、技术栈、开发进度、当前上下文等，便于团队协作和知识沉淀。
- 建议每次重要变更后同步更新 memory-bank。

---

## Init project environment

- git init
- git config
- poetry install
- git commit

## Develop

- code
- git commit
- tox

## Delivery

### Run tox

Run tox to format code style and check test.

```shell script
tox
```

### Git tag

Modify package version value, then commit.

Add tag

```shell script
git tag -a v0.1.0
```

### Build

Build this tag distribution package.

```shell script
poetry build
```

### Upload index server

Upload to pypi server, or pass `--repository https://pypi.org/simple` to specify index server.

```shell script
poetry publish
```

## Develop guide

### Pycharm Configuration

Open project use Pycharm.

#### Module can not import in src

Check menu bar, click `File` --> `Settings` --> `Project Settings` --> `Project Structure` .
Mark `src` and `tests` directory as sources.

#### Enable pytest

Click `File` --> `Settings` --> `Tools` --> `Python Integrated Tools` --> `Testing` --> `Default runner`, then select
`pytest`.

If you run test by `Unittests` before, you should delete configuration. Open `Edit Run/Debug configurations dialog` in
In the upper right corner of Pycharm window, then delete configuration.

### Others

You should confirm `src` directory in `sys.path`. You can add it by `sys.path.extend(['/tmp/demo/src'])` if it not exist.

## 如何添加新的知识库存储提供者

`KnowledgeStorageAgent` 采用了策略设计模式，可以轻松扩展以支持新的存储后端。要添加一个新的提供者（例如 `Dropbox`），请遵循以下步骤：

1. **创建提供者类**:
    - 在 `src/agents/knowledge_base/storage_providers/` 目录下，创建一个新的 Python 文件，例如 `dropbox.py`。
    - 在该文件中，创建一个继承自 `BaseStorageProvider` 的新类，例如 `DropboxStorageProvider`。

    ```python
    # src/agents/knowledge_base/storage_providers/dropbox.py
    from .base import BaseStorageProvider, RetrievedChunk
    from src.agents.knowledge_base.knowledge_processing_agent import ProcessedKnowledgeChunk

    class DropboxStorageProvider(BaseStorageProvider):
        def __init__(self, config):
            super().__init__(config)
            # 初始化 Dropbox 客户端...

        def store(self, chunks):
            # 实现将知识块上传到 Dropbox 的逻辑...
            pass

        def retrieve(self, query_vector, top_k, filters):
            # 实现从 Dropbox 检索知识的逻辑...
            pass

        def get_all_chunk_ids(self):
            # 实现获取所有知识块 ID 的逻辑...
            pass
    ```

2. **注册新的提供者**:
    - 打开 `src/agents/knowledge_base/knowledge_storage_agent.py`。
    - 在 `_create_provider` 方法的 `provider_map` 字典中，添加新的提供者。

    ```python
    # src/agents/knowledge_base/knowledge_storage_agent.py
    from .storage_providers.dropbox import DropboxStorageProvider # 1. 导入新类

    class KnowledgeStorageAgent:
        def _create_provider(self, provider_type, config):
            provider_map = {
                "memory": MemoryStorageProvider,
                "notion": NotionStorageProvider,
                "oss": OSSStorageProvider,
                "google_drive": GoogleDriveStorageProvider,
                "onedrive": OneDriveStorageProvider,
                "dropbox": DropboxStorageProvider, # 2. 在此处添加
            }
            # ...
    ```

3. **（可选）更新配置文档**:
    - 编辑 `docs/configuration.md`，在“支持的提供者”表格中添加关于 `dropbox` 的新行，说明其用途和必要的配置项。

完成以上步骤后，用户就可以在初始化 `KnowledgeStorageAgent` 时选择 `provider_type='dropbox'` 来使用你新添加的存储后端了。

## 参考

[Python 项目工程化开发指南](https://pyloong.github.io/)

## 项目结构

项目主要包含以下目录和文件：

```
/Users/costalong/code/ai/translate-demo/translate_demo/
├── .editorconfig
├── .github/
│   └── workflows/
│       └── main.yml
├── .gitignore
├── .pre-commit-config.yaml
├── .pytest_cache/
│   ├── .gitignore
│   ├── CACHEDIR.TAG
│   ├── README.md
│   └── v/
│       └── cache/
├── LICENSE
├── README.md
├── __init__.py
├── __pycache__/
│   ├── __init__.cpython-313.pyc
│   └── llm.cpython-313.pyc
├── docs/
│   └── development.md
├── poetry.lock
├── pyproject.toml
├── src/
│   ├── agents/
│   │   ├── TranslatorAgent.py
│   │   ├── __init__.py
│   │   └── __pycache__/
│   ├── llm_core/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── base.py
│   │   ├── config.py
│   │   ├── deepseek/
│   │   ├── factory.py
│   │   ├── ollama/
│   │   ├── openai/
│   │   └── providers.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   └── translate/
│   └── translate_demo/
│       ├── __init__.py
│       ├── __pycache__/
│       ├── cmd.py
│       ├── cmdline.py
│       ├── config/
│       └── log.py
├── test_import.py
├── tests/
│   ├── __init__.py
│   ├── __pycache__/
│   │   ├── __init__.cpython-313.pyc
│   │   ├── conftest.cpython-313-pytest-7.4.4.pyc
│   │   ├── conftest.cpython-313-pytest-8.3.5.pyc
│   │   ├── test_llm.cpython-313-pytest-7.4.4.pyc
│   │   └── test_llm.cpython-313-pytest-8.3.5.pyc
│   ├── conftest.py
│   ├── settings.yml
│   ├── test_llm.py
│   ├── test_llm_new.py
│   └── test_version.py
└── tox.ini
```

## 依赖管理

项目使用 `poetry` 进行依赖管理，`pyproject.toml` 文件中定义了项目的依赖和开发依赖。你可以使用以下命令来安装依赖：

```shell script
poetry install
```

如需添加新的依赖，可以使用以下命令：

```shell script
poetry add <package_name>
```

如需添加开发依赖，可以使用以下命令：

```shell script
poetry add --group dev <package_name>
```

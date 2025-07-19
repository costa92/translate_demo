# 统一知识库系统快速入门

本文档提供了统一知识库系统的快速入门指南，包括安装、配置和基本使用。

## 安装

### 方法1：使用安装脚本（推荐）

我们提供了一个简单的安装脚本，可以自动安装项目及其依赖：

```bash
# 安装开发版本
./scripts/install_dev.sh
```

### 方法2：使用 Poetry

如果你已经安装了 Poetry，可以直接使用它来安装项目：

```bash
# 安装所有依赖
poetry install

# 激活虚拟环境
poetry shell
```

### 方法3：使用 pip

你也可以使用 pip 来安装项目：

```bash
# 安装开发版本
pip install -e .
```

## 运行示例

安装完成后，你可以运行以下示例来体验统一知识库系统的功能：

### 使用示例启动器（推荐）

我们提供了一个示例启动器，你可以通过它轻松运行各种示例：

```bash
# 运行示例启动器
python examples/core_demos/run_all_demos.py
```

这将显示一个菜单，你可以选择运行不同的示例：

1. 独立示例（不依赖外部模块）
2. 最小化API服务器
3. 完整演示（API服务器 + 演示页面）
4. 打开API演示页面

### 直接运行特定示例

如果你想直接运行特定的示例，可以使用以下命令：

#### 独立示例（无依赖）

```bash
# 运行独立示例
python examples/core_demos/standalone_example.py
```

这个示例实现了一个简化版的知识库系统，展示了基本的文档添加和查询功能。

#### 最小化API服务器

```bash
# 启动最小化API服务器
python examples/core_demos/minimal_api_server.py
```

#### 完整演示

```bash
# 运行完整演示
python examples/core_demos/run_demo.py
```

这将启动最小化API服务器，并在浏览器中打开一个演示页面，你可以在其中查询知识库。

API 服务器将在 http://localhost:8000 上运行，API 文档可在 http://localhost:8000/docs 访问。

### 常见问题及解决方案

如果你在启动 API 服务器时遇到问题，可以尝试以下解决方案：

1. **ModuleNotFoundError: No module named 'src'**
   - 确保你在项目根目录运行命令
   - 尝试安装项目: `pip install -e .`
   - 使用最小化 API 服务器: `python examples/minimal_api_server.py`

2. **ModuleNotFoundError: No module named 'psutil'**
   - 安装缺少的依赖: `pip install psutil`
   - 使用最小化 API 服务器: `python examples/minimal_api_server.py`

3. **SyntaxError 或其他代码错误**
   - 使用最小化 API 服务器: `python examples/minimal_api_server.py`
   - 报告问题到项目维护者

## 基本使用

以下是一个基本的使用示例：

```python
from src.knowledge_base import KnowledgeBase

# 初始化知识库
kb = KnowledgeBase()

# 添加文档
doc_path = "path/to/document.pdf"
result = kb.add_document(doc_path)
print(f"添加文档成功，ID: {result.document_id}")

# 查询知识库
query = "这个系统有哪些主要功能？"
result = kb.query(query)
print(f"问题: {query}")
print(f"回答: {result.answer}")
```

更多详细示例，请参考 `examples/knowledge_base_example.py`。

## 配置

统一知识库系统支持多种配置选项，你可以通过以下方式配置系统：

### 1. 使用配置对象

```python
from src.knowledge_base.core.config import Config

# 创建配置对象
config = Config()

# 自定义 API 设置
config.api.host = "0.0.0.0"
config.api.port = 8000

# 自定义存储设置
config.storage.provider = "memory"

# 自定义嵌入设置
config.embedding.provider = "sentence_transformers"
config.embedding.model = "all-MiniLM-L6-v2"

# 自定义生成设置
config.generation.provider = "openai"
config.generation.model = "gpt-3.5-turbo"

# 使用配置初始化知识库
kb = KnowledgeBase(config)
```

### 2. 使用环境变量

你可以使用环境变量来配置系统，例如：

```bash
# API 设置
export KB_API_HOST="0.0.0.0"
export KB_API_PORT="8000"

# 存储设置
export KB_STORAGE_PROVIDER="memory"

# 嵌入设置
export KB_EMBEDDING_PROVIDER="sentence_transformers"
export KB_EMBEDDING_MODEL="all-MiniLM-L6-v2"

# 生成设置
export KB_GENERATION_PROVIDER="openai"
export KB_GENERATION_MODEL="gpt-3.5-turbo"
```

### 3. 使用配置文件

你可以创建一个 `.env` 文件来配置系统：

```
# API 设置
KB_API_HOST=0.0.0.0
KB_API_PORT=8000

# 存储设置
KB_STORAGE_PROVIDER=memory

# 嵌入设置
KB_EMBEDDING_PROVIDER=sentence_transformers
KB_EMBEDDING_MODEL=all-MiniLM-L6-v2

# 生成设置
KB_GENERATION_PROVIDER=openai
KB_GENERATION_MODEL=gpt-3.5-turbo
```

## 下一步

- 查看 [API 文档](api/index.md) 了解更多 API 详情
- 查看 [架构文档](architecture.md) 了解系统架构
- 查看 [存储提供商](storage_providers.md) 了解支持的存储后端
- 查看 [生成提供商](generation_providers.md) 了解支持的生成模型
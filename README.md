# 知识库 REST API 服务

这是一个基于 FastAPI 的知识库 REST API 服务，支持文档管理、智能搜索和 LLM 集成。

## 功能特点

- 📄 文档管理：添加、更新、删除、查询文档
- 🔍 智能搜索：基于语义和关键词的混合搜索
- 🤖 LLM 集成：支持多种 LLM 提供商
- 📊 批量操作：支持批量添加和删除文档
- 🔄 实时 API：支持实时查询

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

复制 `config.example.yaml` 为 `config.yaml` 并根据需要修改配置。

### 启动服务

```bash
python run_api.py
```

默认情况下，API 服务将在 `http://localhost:8000` 上运行。

### 命令行参数

- `--host`: 指定主机地址，默认为 0.0.0.0
- `--port`: 指定端口，默认为 8000
- `--debug`: 启用调试模式
- `--config`: 指定配置文件路径
- `--log-level`: 设置日志级别
- `--simple`: 使用简单模式（仅基础功能）
- `--reload`: 启用自动重载（开发模式）

## API 端点

### 文档管理

- `POST /api/v1/documents`: 添加文档
- `GET /api/v1/documents`: 列出文档
- `GET /api/v1/documents/{document_id}`: 获取文档
- `DELETE /api/v1/documents/{document_id}`: 删除文档
- `POST /api/v1/documents/batch`: 批量添加文档

### 查询

- `POST /api/v1/query`: 查询知识库
- `POST /api/v1/query/advanced`: 高级查询

### 文件上传

- `POST /api/v1/upload`: 上传文件

### 统计和管理

- `GET /api/v1/stats`: 获取统计信息
- `POST /api/v1/clear`: 清空知识库

## LLM 集成

本服务支持多种 LLM 提供商，包括：

- OpenAI
- DeepSeek
- SiliconFlow
- 本地模型

要使用 LLM 功能，请在配置文件中设置相应的 API 密钥和参数。

## 示例请求

### 添加文档

```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "这是一个测试文档",
    "title": "测试文档",
    "type": "text",
    "tags": ["测试", "示例"]
  }'
```

### 查询知识库

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "测试文档",
    "top_k": 5,
    "use_llm": true
  }'
```

## 文档

API 文档可在 `http://localhost:8000/docs` 或 `http://localhost:8000/redoc` 查看。
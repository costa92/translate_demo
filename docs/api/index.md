# 统一知识库系统 API 文档

本文档提供了统一知识库系统的 API 参考。

## 核心 API

### KnowledgeBase

`KnowledgeBase` 是统一知识库系统的主要入口点，提供了添加、查询和管理知识的功能。

```python
from src.knowledge_base import KnowledgeBase

# 初始化知识库
kb = KnowledgeBase()

# 添加文档
result = kb.add_document("path/to/document.pdf")

# 查询知识库
result = kb.query("这个系统有哪些主要功能？")
```

#### 方法

##### `__init__(config=None)`

初始化知识库。

- `config`: 可选的配置对象，用于自定义知识库的行为。

##### `add_document(path, metadata=None)`

添加文档到知识库。

- `path`: 文档路径
- `metadata`: 可选的元数据字典
- 返回: `DocumentAddResult` 对象，包含文档 ID 和状态

##### `add_text(text, metadata=None)`

添加文本到知识库。

- `text`: 文本内容
- `metadata`: 可选的元数据字典
- 返回: `DocumentAddResult` 对象，包含文档 ID 和状态

##### `query(query_text, filters=None, limit=5)`

查询知识库。

- `query_text`: 查询文本
- `filters`: 可选的过滤条件
- `limit`: 返回的结果数量
- 返回: `QueryResult` 对象，包含回答和相关文档块

##### `get_document(document_id)`

获取文档。

- `document_id`: 文档 ID
- 返回: `Document` 对象

##### `delete_document(document_id)`

删除文档。

- `document_id`: 文档 ID
- 返回: `bool` 表示操作是否成功

##### `get_storage_providers()`

获取可用的存储提供商列表。

- 返回: 存储提供商名称列表

## RESTful API

统一知识库系统提供了一组 RESTful API，可以通过 HTTP 请求访问。

### 启动 API 服务器

```python
from src.knowledge_base.api.server import run_app

# 启动 API 服务器
run_app(host="0.0.0.0", port=8000)
```

### API 端点

#### 文档管理

- `POST /documents`: 添加文档
- `GET /documents/{document_id}`: 获取文档
- `DELETE /documents/{document_id}`: 删除文档
- `GET /documents`: 获取所有文档

#### 查询

- `POST /query`: 查询知识库

#### 系统信息

- `GET /info`: 获取系统信息
- `GET /health`: 获取系统健康状态

### 示例请求

#### 添加文档

```bash
curl -X POST "http://localhost:8000/documents" \
  -H "Content-Type: application/json" \
  -d '{"text": "这是一个示例文档", "metadata": {"title": "示例"}}'
```

#### 查询知识库

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "这个系统有哪些主要功能？"}'
```

## WebSocket API

统一知识库系统还提供了 WebSocket API，支持实时通信和流式响应。

### 连接 WebSocket

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");

ws.onopen = () => {
  console.log("连接已建立");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("收到消息:", data);
};

ws.onclose = () => {
  console.log("连接已关闭");
};
```

### 发送查询

```javascript
ws.send(JSON.stringify({
  type: "query",
  data: {
    query: "这个系统有哪些主要功能？"
  }
}));
```

## 完整 API 文档

要生成完整的 API 文档，请运行以下命令：

```bash
python scripts/generate_api_docs.py
```

生成的文档将保存在 `docs/api/` 目录中。
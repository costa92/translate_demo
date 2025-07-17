# Notion 存储提供商使用指南

## 概述

Notion 存储提供商允许您将知识库的向量数据和元数据存储在 Notion 数据库中。这为您提供了一个可视化的界面来查看、管理和组织您的知识库内容。

## 特性

- ✅ **完整的 CRUD 操作**: 支持添加、查询、更新和删除操作
- ✅ **向量相似性搜索**: 在内存中计算余弦相似度
- ✅ **丰富的元数据支持**: 存储和查询文档元数据
- ✅ **可视化界面**: 通过 Notion 界面直观查看数据
- ✅ **多语言支持**: 支持中英文内容存储
- ✅ **灵活的数据结构**: 支持自定义属性和标签

## 前置条件

### 1. 创建 Notion 集成

1. 访问 [Notion Developers](https://www.notion.so/my-integrations)
2. 点击 "New integration"
3. 填写集成信息：
   - Name: Knowledge Base Integration
   - Associated workspace: 选择您的工作区
   - Type: Internal
4. 点击 "Submit" 创建集成
5. 复制生成的 "Internal Integration Token"（这就是您的 API 密钥）

### 2. 创建父页面

1. 在 Notion 中创建一个新页面作为数据库的父页面
2. 复制页面 URL 中的页面 ID（URL 中最后一个 `/` 后面的部分）

### 3. 设置数据库

使用我们提供的设置脚本自动创建数据库：

```bash
python setup_notion_database.py
```

或者手动设置：

1. 在父页面中创建一个新的数据库
2. 添加以下属性：
   - `Chunk ID` (Title)
   - `Document ID` (Text)
   - `Text` (Text)
   - `Start Index` (Number)
   - `End Index` (Number)
   - `Embedding` (Text)
   - `Metadata` (Text)
   - `Created` (Date)
   - `Document Type` (Select)
   - `Source` (URL)
   - `Tags` (Multi-select)

## 配置

### 环境变量配置

```bash
export NOTION_API_KEY="your_notion_api_key"
export NOTION_DATABASE_ID="your_database_id"
```

### 配置文件配置

```json
{
  "storage": {
    "provider": "notion",
    "notion_api_key": "your_notion_api_key",
    "notion_database_id": "your_database_id",
    "batch_size": 100,
    "max_connections": 10
  }
}
```

### Python 代码配置

```python
from knowledge_base.core.config import Config, StorageConfig

config = Config(
    storage=StorageConfig(
        provider="notion",
        notion_api_key="your_notion_api_key",
        notion_database_id="your_database_id"
    )
)
```

## 使用示例

### 基本使用

```python
import asyncio
from knowledge_base.core.knowledge_base import KnowledgeBase
from knowledge_base.core.config import Config, StorageConfig
from knowledge_base.core.types import Document, DocumentType

async def main():
    # 配置知识库
    config = Config(
        storage=StorageConfig(
            provider="notion",
            notion_api_key="your_api_key",
            notion_database_id="your_database_id"
        )
    )
    
    # 初始化知识库
    kb = KnowledgeBase(config)
    await kb.initialize()
    
    # 添加文档
    document = Document(
        id="doc_001",
        content="这是一个测试文档，用于演示 Notion 存储功能。",
        type=DocumentType.TEXT,
        metadata={"source": "example.txt", "language": "zh"}
    )
    
    result = await kb.add_document(document)
    print(f"添加文档成功，创建了 {result.chunks_created} 个块")
    
    # 查询
    query_result = await kb.query("什么是测试文档？")
    print(f"查询结果: {query_result.answer}")
    print(f"置信度: {query_result.confidence}")
    
    # 关闭知识库
    await kb.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 直接使用存储提供商

```python
import asyncio
from knowledge_base.storage.providers.notion import NotionVectorStore
from knowledge_base.core.types import Chunk

async def main():
    # 初始化存储
    config = {
        "notion_api_key": "your_api_key",
        "notion_database_id": "your_database_id"
    }
    
    store = NotionVectorStore(config)
    await store.initialize()
    
    # 创建测试块
    chunk = Chunk(
        id="test_001",
        document_id="doc_001",
        text="这是一个测试文本块",
        embedding=[0.1, 0.2, 0.3] * 128,  # 384维向量
        metadata={"source": "test.txt"}
    )
    
    # 添加块
    await store.add_chunks([chunk])
    
    # 搜索相似块
    query_vector = [0.15, 0.25, 0.35] * 128
    results = await store.search_similar(query_vector, top_k=5)
    
    for result in results:
        print(f"相似度: {result['score']:.3f}")
        print(f"文本: {result['chunk'].text}")
    
    # 关闭存储
    await store.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 数据库结构

### 核心属性

| 属性名 | 类型 | 描述 |
|--------|------|------|
| Chunk ID | Title | 文本块的唯一标识符 |
| Document ID | Text | 所属文档的标识符 |
| Text | Text | 文本块的实际内容 |
| Start Index | Number | 在原文档中的起始位置 |
| End Index | Number | 在原文档中的结束位置 |
| Embedding | Text | 向量嵌入（JSON 格式） |
| Metadata | Text | 元数据（JSON 格式） |
| Created | Date | 创建时间 |

### 扩展属性

| 属性名 | 类型 | 描述 |
|--------|------|------|
| Document Type | Select | 文档类型（Text, PDF, Markdown, URL） |
| Source | URL | 源文件或 URL |
| Tags | Multi-select | 标签分类 |

## 性能考虑

### 优势

- **可视化管理**: 通过 Notion 界面直观管理数据
- **灵活查询**: 支持复杂的过滤和排序
- **协作友好**: 团队成员可以直接查看和编辑数据
- **备份简单**: Notion 自动备份数据

### 限制

- **向量搜索性能**: 需要将所有数据加载到内存中进行相似性计算
- **API 限制**: 受 Notion API 速率限制约束
- **存储限制**: 文本字段有长度限制（2000字符）
- **并发限制**: 不适合高并发场景

### 优化建议

1. **分批处理**: 使用较小的批次大小避免超时
2. **缓存策略**: 实现本地缓存减少 API 调用
3. **混合架构**: 考虑将向量搜索委托给专门的向量数据库
4. **定期清理**: 定期清理不需要的数据以提高性能

## 测试

### 运行存储测试

```bash
# 设置环境变量
export NOTION_API_KEY="your_api_key"
export NOTION_DATABASE_ID="your_database_id"

# 运行存储测试
python test_notion_storage.py
```

### 运行 RAG 集成测试

```bash
# 运行完整的 RAG 集成测试
python test_notion_rag_integration.py
```

## 故障排除

### 常见错误

1. **认证失败**
   ```
   Error: Cannot access Notion database: 401 - Unauthorized
   ```
   - 检查 API 密钥是否正确
   - 确保集成有访问数据库的权限

2. **数据库不存在**
   ```
   Error: Cannot access Notion database: 404 - Not Found
   ```
   - 检查数据库 ID 是否正确
   - 确保数据库存在且集成有访问权限

3. **属性不匹配**
   ```
   Error: Failed to create Notion page: 400 - Bad Request
   ```
   - 检查数据库属性配置是否正确
   - 确保所有必需的属性都存在

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **检查数据库结构**
   ```python
   # 使用 Notion API 检查数据库结构
   response = await client.get(f"/databases/{database_id}")
   print(json.dumps(response.json(), indent=2))
   ```

3. **验证数据**
   ```python
   # 查询数据库内容
   response = await client.post(f"/databases/{database_id}/query")
   print(f"Found {len(response.json()['results'])} pages")
   ```

## 最佳实践

1. **权限管理**: 只给集成必要的权限
2. **数据备份**: 定期导出重要数据
3. **监控使用**: 监控 API 使用量和性能
4. **错误处理**: 实现完善的错误处理和重试机制
5. **数据验证**: 在存储前验证数据格式和完整性

## 扩展功能

### 自定义属性

您可以根据需要添加自定义属性：

```python
# 在数据库中添加自定义属性
custom_properties = {
    "Priority": {"select": {"options": [{"name": "High", "color": "red"}]}},
    "Category": {"multi_select": {"options": [{"name": "Technical", "color": "blue"}]}},
    "Last Updated": {"date": {}}
}
```

### 批量操作

```python
# 批量添加文档
documents = [...]  # 文档列表
for batch in chunks(documents, batch_size=10):
    await kb.add_documents(batch)
```

### 数据迁移

```python
# 从其他存储迁移到 Notion
async def migrate_to_notion(source_store, notion_store):
    chunks = await source_store.get_all_chunks()
    await notion_store.add_chunks(chunks)
```

## 总结

Notion 存储提供商为知识库系统提供了一个独特的可视化存储解决方案。虽然在性能方面可能不如专门的向量数据库，但它在可视化管理、协作和灵活性方面具有独特优势。

选择 Notion 存储适合以下场景：
- 需要可视化管理知识库内容
- 团队协作和内容审核
- 原型开发和小规模应用
- 与现有 Notion 工作流集成

对于高性能和大规模应用，建议考虑专门的向量数据库解决方案。
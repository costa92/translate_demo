# 知识库多智能体系统

基于设计文档实现的知识库多智能体系统，支持知识收集、处理、存储、检索和维护。

## 系统架构

### 智能体组件

1. **协调智能体 (OrchestratorAgent)** - 系统总指挥，负责任务分发和结果聚合
2. **数据收集智能体 (DataCollectionAgent)** - 从多种源收集数据（文件、HTTP、文本）
3. **知识处理智能体 (KnowledgeProcessingAgent)** - 文本分块、向量化、实体抽取
4. **知识存储智能体 (KnowledgeStorageAgent)** - 策略模式存储，支持多种后端
5. **知识检索智能体 (KnowledgeRetrievalAgent)** - 语义搜索和相似度匹配
6. **知识维护智能体 (KnowledgeMaintenanceAgent)** - 知识更新和质量维护

### 存储提供者

- **✅ 内存存储 (MemoryStorageProvider)** - 开发测试用，即开即用
- **✅ Notion存储 (NotionStorageProvider)** - 完整实现，支持团队协作
- **✅ OSS存储 (OSSStorageProvider)** - 完整实现，支持生产环境
- **✅ Google Drive存储** - 个人和团队协作，需要OAuth配置
- **⚠️ 其他存储** - OneDrive（占位符实现）

## 快速开始

### 1. 系统测试

```bash
# 测试基本功能
python src/agents/knowledge_base/test_system.py
```

### 2. 启动API服务器

```bash
# 启动FastAPI服务器
python -m src.agents.knowledge_base.api_server

# 或者使用uvicorn
uvicorn src.agents.knowledge_base.api_server:app --reload
```

### 3. 测试API接口

```bash
# 在另一个终端中测试API
python src/agents/knowledge_base/test_api.py
```

### 4. 存储提供者演示

```bash
# 演示不同存储提供者的使用
python src/agents/knowledge_base/storage_demo.py
```

### 5. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## API 端点

### 知识库管理

- `POST /api/v1/knowledge` - 添加知识到知识库
- `GET /api/v1/tasks/{task_id}` - 查询任务状态

### 问答查询

- `POST /api/v1/chat/query` - RAG问答查询

### 系统状态

- `GET /health` - 健康检查
- `GET /status` - 系统状态
- `GET /api/v1/debug/agents` - 调试智能体信息
- `GET /api/v1/debug/storage` - 调试存储信息

## 使用示例

### 添加知识

```python
import requests

# 添加文本知识
response = requests.post("http://localhost:8000/api/v1/knowledge", json={
    "sources": [
        {
            "type": "text",
            "location": "人工智能是计算机科学的一个分支...",
            "metadata": {"topic": "AI"}
        }
    ]
})
```

### 查询知识

```python
# 查询知识
response = requests.post("http://localhost:8000/api/v1/chat/query", json={
    "query": "什么是人工智能？"
})
```

### 程序化使用

```python
from src.agents.knowledge_base.orchestrator_agent import OrchestratorAgent

# 内存存储（默认）
orchestrator = OrchestratorAgent(storage_provider='memory')

# Notion存储
notion_config = {
    "notion_token": "secret_xxxxxxxxxxxx",
    "database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
orchestrator = OrchestratorAgent(
    storage_provider='notion',
    storage_config=notion_config
)

# OSS存储
oss_config = {
    "endpoint": "https://oss-cn-beijing.aliyuncs.com",
    "access_key_id": "your_access_key_id",
    "access_key_secret": "your_access_key_secret",
    "bucket_name": "your_bucket_name",
    "prefix": "knowledge_base/"
}
orchestrator = OrchestratorAgent(
    storage_provider='oss',
    storage_config=oss_config
)

# 添加知识
result = orchestrator.receive_request("user", "add_knowledge", {
    "sources": [
        {"type": "text", "location": "知识内容..."}
    ]
})

# 查询知识
result = orchestrator.receive_request("user", "query", {
    "query": "你的问题"
})
```

## 存储提供者配置

### Notion存储配置

1. **创建Notion集成**：
   - 访问 https://www.notion.so/my-integrations
   - 创建新的集成并获取Integration Token

2. **设置数据库**：
   - 创建新的数据库
   - 添加以下属性：
     - `chunk_id` (标题)
     - `content` (富文本)
     - `category` (选择)
     - `metadata` (富文本)
   - 将集成添加到数据库权限中

3. **获取Database ID**：
   - 从数据库URL中提取ID
   - 格式：`https://www.notion.so/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### OSS存储配置

1. **安装依赖**：
   ```bash
   pip install oss2
   ```

2. **创建OSS Bucket**：
   - 在阿里云控制台创建Bucket
   - 配置访问权限
   - 获取Endpoint地址

3. **获取访问凭证**：
   - 创建AccessKey ID和Secret
   - 配置适当的OSS权限

### Google Drive存储配置

1. **创建Google Cloud项目**：
   - 启用Google Drive API
   - 创建OAuth2凭证
   - 下载credentials.json

2. **配置权限**：
   - 设置适当的OAuth2作用域
   - 首次使用需要授权

## 当前实现状态

### ✅ 已完成

- [x] 基础智能体架构
- [x] 内存存储提供者（完整实现）
- [x] Notion存储提供者（完整实现）
- [x] OSS存储提供者（完整实现）
- [x] Google Drive存储提供者（完整实现）
- [x] 文本分块和基础向量化
- [x] 完整的RAG问答流程
- [x] FastAPI接口层
- [x] 基础测试脚本
- [x] 存储提供者演示

### ⚠️ 部分完成

- [x] 知识处理智能体（使用哈希向量，需要真实embedding）
- [x] 知识检索智能体（需要真实向量搜索）

### ❌ 待实现

- [ ] 真实的embedding模型集成
- [ ] 向量相似度搜索
- [ ] LLM集成用于答案生成
- [ ] OneDrive存储提供者（完整实现）
- [ ] 任务状态跟踪
- [ ] 高级推理策略（CoT、ToT等）
- [ ] 记忆管理机制

## 下一步计划

1. **集成真实的embedding模型**（如OpenAI、Sentence Transformers）
2. **添加向量数据库**（如Pinecone、Weaviate、Chroma）
3. **集成LLM**用于答案生成
4. **实现完整的存储提供者**
5. **添加记忆管理**
6. **实现高级推理策略**

## 技术栈

- **后端**: Python, FastAPI, Pydantic
- **存储**: 多种策略模式存储后端
- **API**: RESTful API with OpenAPI documentation
- **测试**: 内置测试脚本

## 贡献指南

1. 查看`docs/consolidated_design.md`了解完整设计
2. 运行测试确保基本功能正常
3. 参考现有代码模式添加新功能
4. 遵循接口规范确保兼容性
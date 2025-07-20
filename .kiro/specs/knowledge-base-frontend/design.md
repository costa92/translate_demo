# 知识库前端设计文档

## 概述

本文档描述了知识库前端的设计，该前端使用 React 设计封装的方式实现，并与后端 API 进行交互。前端代码将放置在 front 目录中，并使用 API 路由进行接口调用。

## 架构

知识库前端采用组件化架构，将功能封装在可重用的组件中。整体架构如下：

```
front/
├── public/
│   ├── index.html
│   └── ...
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Header.js
│   │   │   ├── Footer.js
│   │   │   └── ...
│   │   ├── documents/
│   │   │   ├── DocumentList.js
│   │   │   ├── DocumentItem.js
│   │   │   ├── AddDocumentForm.js
│   │   │   └── ...
│   │   ├── search/
│   │   │   ├── SearchBar.js
│   │   │   ├── SearchResults.js
│   │   │   ├── ResultItem.js
│   │   │   └── ...
│   │   └── conversation/
│   │       ├── ConversationHistory.js
│   │       ├── MessageItem.js
│   │       ├── InputBox.js
│   │       └── ...
│   ├── pages/
│   │   ├── HomePage.js
│   │   ├── DocumentsPage.js
│   │   ├── SearchPage.js
│   │   └── ...
│   ├── services/
│   │   ├── api.js
│   │   ├── documentService.js
│   │   ├── searchService.js
│   │   └── ...
│   ├── utils/
│   │   ├── formatters.js
│   │   ├── validators.js
│   │   └── ...
│   ├── contexts/
│   │   ├── AuthContext.js
│   │   ├── ThemeContext.js
│   │   └── ...
│   ├── hooks/
│   │   ├── useDocuments.js
│   │   ├── useSearch.js
│   │   └── ...
│   ├── App.js
│   ├── index.js
│   └── ...
├── package.json
└── ...
```

## 组件和接口

### 组件

#### 1. 文档组件

- **DocumentList**: 显示文档列表，支持分页和排序。
- **DocumentItem**: 显示单个文档的摘要信息。
- **AddDocumentForm**: 用于添加新文档的表单。
- **DocumentDetail**: 显示文档的详细信息。

#### 2. 搜索组件

- **SearchBar**: 搜索输入框和过滤选项。
- **SearchResults**: 显示搜索结果列表。
- **ResultItem**: 显示单个搜索结果项。
- **FilterPanel**: 提供元数据过滤选项。

#### 3. 对话组件

- **ConversationHistory**: 显示对话历史。
- **MessageItem**: 显示单个消息（用户查询或系统回答）。
- **InputBox**: 用户输入新查询的框。
- **ConversationControls**: 提供开始新对话等控制选项。

### 接口

#### 1. 文档接口

- **GET /api/documents**: 获取文档列表。
  - 参数：page, limit, sort, order
  - 返回：文档列表和分页信息

- **POST /api/documents**: 添加新文档。
  - 参数：title, content, source, metadata
  - 返回：新添加的文档信息

- **GET /api/documents/:id**: 获取单个文档的详细信息。
  - 参数：id
  - 返回：文档详细信息

#### 2. 搜索接口

- **POST /api/search**: 执行搜索查询。
  - 参数：query, metadata_filter, page, limit
  - 返回：搜索结果列表和分页信息

#### 3. 对话接口

- **POST /api/conversation**: 开始新对话或继续现有对话。
  - 参数：query, conversation_id (可选)
  - 返回：系统回答和更新的对话历史

## 数据模型

### 文档模型

```typescript
interface Document {
  id: string;
  title: string;
  content: string;
  source: string;
  date: string;
  metadata: Record<string, any>;
  chunk_ids: string[];
}
```

### 文本块模型

```typescript
interface TextChunk {
  chunk_id: string;
  text: string;
  metadata: Record<string, any>;
  document_id: string;
}
```

### 查询结果模型

```typescript
interface QueryResult {
  query: string;
  answer: string;
  chunks: TextChunk[];
  metadata: Record<string, any>;
}
```

### 对话模型

```typescript
interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface Conversation {
  conversation_id: string;
  messages: Message[];
  metadata: Record<string, any>;
}
```

## 用户界面设计

### 主页

主页将提供知识库的概述和主要功能入口：

- 顶部导航栏，包含链接到文档页面、搜索页面等
- 搜索框，允许用户直接从主页开始搜索
- 最近添加的文档列表
- 功能卡片，链接到添加文档、浏览文档等功能

### 文档页面

文档页面将显示知识库中的所有文档：

- 文档列表，显示标题、来源和日期
- 排序和过滤选项
- 分页控件
- "添加文档"按钮

### 搜索页面

搜索页面将允许用户查询知识库：

- 搜索框和搜索按钮
- 元数据过滤选项
- 搜索结果列表
- 对话历史（如果在对话模式下）

### 文档详情页面

文档详情页面将显示单个文档的完整内容：

- 文档标题和元数据
- 完整文档内容
- 相关文档链接

## 错误处理

前端将实现以下错误处理策略：

1. 网络错误：当 API 请求失败时，显示适当的错误消息。
2. 表单验证错误：在提交表单之前验证输入，并显示具体的错误消息。
3. 空结果处理：当搜索没有结果时，显示友好的空状态消息。
4. 加载状态：在数据加载过程中显示加载指示器。

## 响应式设计

前端将使用响应式设计，确保在不同设备上的良好体验：

1. 使用 CSS Grid 和 Flexbox 进行布局。
2. 使用媒体查询适应不同屏幕尺寸。
3. 在移动设备上优化交互元素的大小和间距。
4. 实现适当的触摸手势支持。

## 安全考虑

前端将实现以下安全措施：

1. 输入验证：验证所有用户输入，防止 XSS 攻击。
2. CSRF 保护：在 API 请求中包含 CSRF 令牌。
3. 敏感数据处理：不在客户端存储敏感数据。
4. 错误消息：不向用户显示详细的技术错误信息。
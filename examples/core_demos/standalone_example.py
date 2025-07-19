#!/usr/bin/env python
"""
统一知识库系统独立示例

这个示例不依赖于项目的导入，可以独立运行。
"""

import sys
import os
import json
from typing import List, Dict, Any, Optional


class SimpleKnowledgeBase:
    """简单知识库实现"""
    
    def __init__(self):
        """初始化知识库"""
        self.documents = []
    
    def add_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """添加文本到知识库"""
        doc_id = f"doc_{len(self.documents) + 1}"
        document = {
            "id": doc_id,
            "content": text,
            "metadata": metadata or {}
        }
        self.documents.append(document)
        
        return {
            "document_id": doc_id,
            "success": True
        }
    
    def query(self, query_text: str) -> Dict[str, Any]:
        """查询知识库"""
        # 简化版：根据查询返回预定义的回答
        if "是什么" in query_text or "什么是" in query_text:
            answer = "统一知识库系统是一个综合性的知识管理平台，它结合了文档存储、处理、检索和生成功能。系统采用分层架构，支持多种存储后端，并提供灵活的文档处理功能。"
            relevant_docs = [doc for doc in self.documents if "简介" in doc.get("metadata", {}).get("title", "")]
        elif "组件" in query_text or "架构" in query_text:
            answer = "统一知识库系统采用模块化设计，主要包括核心组件、存储组件、处理组件、检索组件、生成组件、代理组件和API组件。"
            relevant_docs = [doc for doc in self.documents if "架构" in doc.get("metadata", {}).get("title", "")]
        elif "场景" in query_text or "用途" in query_text or "适用" in query_text:
            answer = "统一知识库系统适用于多种场景，包括企业知识管理、个人知识管理、客户支持、研究辅助和教育培训等。"
            relevant_docs = [doc for doc in self.documents if "场景" in doc.get("metadata", {}).get("title", "")]
        else:
            answer = f"我理解你的问题是关于统一知识库系统的，但我需要更具体的信息才能给你准确的回答。你可以问我关于系统是什么、系统架构或适用场景的问题。"
            relevant_docs = self.documents[:1]  # 默认返回第一个文档
        
        # 创建返回的文档块
        chunks = []
        for doc in relevant_docs:
            chunks.append({
                "text": doc["content"],
                "metadata": doc["metadata"]
            })
        
        return {
            "answer": answer,
            "chunks": chunks
        }
    
    def get_storage_providers(self) -> List[str]:
        """获取可用的存储提供商"""
        return ["memory", "file", "vector_db", "notion", "google_drive", "onedrive"]


def main():
    """运行独立示例"""
    print("初始化简单知识库...")
    kb = SimpleKnowledgeBase()
    
    # 添加一些示例文档
    print("添加示例文档...")
    documents = [
        {
            "title": "统一知识库系统简介",
            "content": """
            统一知识库系统是一个综合性的知识管理平台，它结合了文档存储、处理、检索和生成功能。
            系统采用分层架构，支持多种存储后端，包括内存存储、Notion、向量数据库和云存储。
            系统还提供灵活的文档处理功能，支持多种分块策略和元数据提取。
            """
        },
        {
            "title": "系统架构",
            "content": """
            统一知识库系统采用模块化设计，主要包括以下组件：
            1. 核心组件：提供基础接口和配置管理
            2. 存储组件：负责文档的存储和检索
            3. 处理组件：负责文档的处理和分块
            4. 检索组件：负责文档的搜索和排序
            5. 生成组件：负责基于检索结果生成回答
            6. 代理组件：提供多代理协作功能
            7. API组件：提供RESTful和WebSocket接口
            """
        },
        {
            "title": "使用场景",
            "content": """
            统一知识库系统适用于多种场景，包括：
            1. 企业知识管理：整合企业内部文档，提供智能检索和问答功能
            2. 个人知识管理：管理个人笔记和资料，提供智能助手功能
            3. 客户支持：基于产品文档提供自动化客户支持
            4. 研究辅助：整合研究论文和资料，辅助研究工作
            5. 教育培训：基于教材和课程资料提供个性化学习辅助
            """
        }
    ]
    
    for i, doc in enumerate(documents):
        result = kb.add_text(doc["content"], metadata={"title": doc["title"]})
        print(f"  文档 {i+1} 添加成功，ID: {result['document_id']}")
    
    # 查询知识库
    print("\n查询知识库...")
    queries = [
        "统一知识库系统是什么？",
        "系统的主要组件有哪些？",
        "这个系统适用于哪些场景？"
    ]
    
    for i, query in enumerate(queries):
        print(f"\n问题 {i+1}: {query}")
        result = kb.query(query)
        print(f"回答: {result['answer']}")
        print("来源:")
        for j, chunk in enumerate(result["chunks"]):
            print(f"  {j+1}. {chunk['metadata']['title']}")
            print(f"     {chunk['text'][:100]}...")
    
    # 显示可用的存储提供商
    print("\n可用的存储提供商:")
    providers = kb.get_storage_providers()
    for provider in providers:
        print(f"  - {provider}")
    
    # 保存查询结果到文件
    print("\n保存查询结果到文件...")
    with open("query_results.json", "w", encoding="utf-8") as f:
        result = kb.query("统一知识库系统的架构")
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("  结果已保存到 query_results.json")


if __name__ == "__main__":
    main()
#!/usr/bin/env python
"""
简化版知识库

这是一个简化版的知识库实现，用于示例脚本。
在实际应用中，应使用完整的知识库实现。
"""

import uuid
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class TextChunk:
    """文本块"""
    chunk_id: str
    text: str
    metadata: Dict[str, Any]


@dataclass
class AddDocumentResult:
    """添加文档结果"""
    document_id: str
    chunk_ids: List[str]


@dataclass
class QueryResult:
    """查询结果"""
    query: str
    answer: str
    chunks: List[TextChunk]
    metadata: Dict[str, Any]


class KnowledgeBase:
    """简化版知识库"""
    
    def __init__(self):
        """初始化知识库"""
        self.documents = {}
        self.chunks = {}
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> AddDocumentResult:
        """添加文档到知识库"""
        document_id = str(uuid.uuid4())
        
        # 简单的文本分块（按段落）
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        
        chunk_ids = []
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
                
            chunk_id = f"{document_id}_{i}"
            chunk = TextChunk(
                chunk_id=chunk_id,
                text=paragraph,
                metadata={**metadata, "paragraph_index": i}
            )
            
            self.chunks[chunk_id] = chunk
            chunk_ids.append(chunk_id)
        
        self.documents[document_id] = {
            "content": content,
            "metadata": metadata,
            "chunk_ids": chunk_ids
        }
        
        return AddDocumentResult(document_id=document_id, chunk_ids=chunk_ids)
    
    def query(self, query: str, metadata_filter: Optional[Dict[str, Any]] = None) -> QueryResult:
        """查询知识库"""
        # 简单的关键词匹配
        query_words = set(query.lower().replace("？", "").replace("?", "").split())
        
        # 调试信息
        print(f"查询: {query}")
        print(f"查询词: {query_words}")
        if metadata_filter:
            print(f"应用元数据过滤: {metadata_filter}")
        
        # 打印所有可用的文档块
        print("\n可用的文档块:")
        for chunk_id, chunk in self.chunks.items():
            print(f"- ID: {chunk_id}, 元数据: {chunk.metadata}")
            print(f"  内容: {chunk.text[:50]}...")
            
        # 计算每个文本块的相关性分数
        chunk_scores = []
        for chunk_id, chunk in self.chunks.items():
            # 如果有元数据过滤，检查是否匹配
            if metadata_filter:
                match = True
                for key, value in metadata_filter.items():
                    if key not in chunk.metadata or chunk.metadata[key] != value:
                        match = False
                        break
                
                if not match:
                    continue
                
                # 调试信息
                print(f"元数据匹配: {chunk.metadata}")
                print(f"文本内容: {chunk.text[:100]}...")
            
            # 计算相关性分数
            chunk_text = chunk.text.lower()
            
            # 改进的相关性计算
            score = 0
            
            # 1. 完整查询匹配
            if query.lower() in chunk_text:
                score += 10
                
            # 2. 关键词匹配
            for word in query_words:
                if len(word) > 2:  # 忽略太短的词
                    if word in chunk_text:
                        score += 1
                        
            # 3. 特殊关键词匹配（更高权重）
            important_keywords = ["评估", "deepseek", "chat", "coder", "模型", "性能", "维度", "天空", "颜色", "自然语言处理", "nlp", "机器学习", "深度学习", "npx", "安装", "gemini"]
            for keyword in important_keywords:
                if keyword in query.lower() and keyword in chunk_text:
                    score += 3
            
            # 4. 元数据标题匹配
            if "title" in chunk.metadata:
                title = chunk.metadata["title"].lower()
                if any(word in title for word in query_words if len(word) > 2):
                    score += 5
            
            # 5. 语义相似度（简化版）
            # 检查一些常见的同义词
            synonyms = {
                "天空": ["蓝色", "白天"],
                "颜色": ["蓝色", "绿色", "无色"],
                "自然语言处理": ["nlp", "语言", "处理"],
                "安装": ["使用", "执行", "运行"]
            }
            
            for word in query_words:
                if word in synonyms:
                    for synonym in synonyms[word]:
                        if synonym in chunk_text:
                            score += 2
                            print(f"同义词匹配: {word} -> {synonym}")
            
            # 6. 基于位置的加权
            # 如果关键词出现在文本的开头，给予更高的权重
            first_50_chars = chunk_text[:50]
            for word in query_words:
                if len(word) > 2 and word in first_50_chars:
                    score += 2
            
            if score > 0:
                print(f"文档块 {chunk_id} 相关性分数: {score}")
                chunk_scores.append((score, chunk))
        
        # 按相关性排序
        chunk_scores.sort(key=lambda x: x[0], reverse=True)
        
        # 获取最相关的文本块
        relevant_chunks = [chunk for _, chunk in chunk_scores[:5]]
        
        return QueryResult(
            query=query,
            answer="",  # 初始为空，由调用者填充
            chunks=relevant_chunks,
            metadata={"total_chunks": len(relevant_chunks)}
        )
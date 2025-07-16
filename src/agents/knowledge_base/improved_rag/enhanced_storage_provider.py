"""
增强的存储提供商 - 支持向量化和语义检索
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from ..storage_providers.base import BaseStorageProvider, RetrievedChunk, ProcessedKnowledgeChunk
from .semantic_retriever import SemanticRetriever, EmbeddingProvider, SimpleEmbeddingProvider


class EnhancedStorageProvider(BaseStorageProvider):
    """增强的存储提供商基类，支持语义检索"""
    
    def __init__(self, config: Dict[str, Any] = None, embedding_provider: EmbeddingProvider = None):
        super().__init__(config or {})
        self.embedding_provider = embedding_provider or SimpleEmbeddingProvider()
        self.semantic_retriever = SemanticRetriever(self.embedding_provider)
        
        # 存储嵌入向量
        self.embeddings_db: Dict[str, List[float]] = {}
    
    async def store(self, chunks: List[ProcessedKnowledgeChunk]) -> bool:
        """存储chunks并生成嵌入向量"""
        # 调用原有的存储逻辑
        result = self._store_chunks(chunks)
        
        if result:
            # 生成并存储嵌入向量
            for chunk in chunks:
                try:
                    embedding = self.embedding_provider.embed_text(chunk.text_content)
                    self.embeddings_db[chunk.id] = embedding
                except Exception as e:
                    print(f"Failed to generate embedding for chunk {chunk.id}: {e}")
        
        return result
    
    @abstractmethod
    def _store_chunks(self, chunks: List[ProcessedKnowledgeChunk]) -> bool:
        """子类实现具体的存储逻辑"""
        pass
    
    def retrieve(self, query_vector: List[float], top_k: int, filters: Dict) -> List[RetrievedChunk]:
        """增强的检索方法，支持语义检索"""
        query_text = filters.get('query_text', '') if filters else ''
        
        if not query_text:
            # 如果没有查询文本，使用原有的向量检索
            return self._vector_retrieve(query_vector, top_k, filters)
        
        # 获取所有chunks
        all_chunks = self._get_all_chunks()
        
        if not all_chunks:
            return []
        
        # 应用元数据过滤器
        filtered_chunks = self._apply_metadata_filters(all_chunks, filters)
        
        # 使用语义检索
        retrieval_method = filters.get('retrieval_method', 'hybrid')  # 'semantic', 'keyword', 'hybrid'
        
        if retrieval_method == 'semantic':
            results = self.semantic_retriever.retrieve_semantic(query_text, filtered_chunks, top_k)
        elif retrieval_method == 'keyword':
            results = self.semantic_retriever._keyword_retrieve(query_text, filtered_chunks)[:top_k]
        else:  # hybrid
            results = self.semantic_retriever.hybrid_retrieve(query_text, filtered_chunks, top_k)
        
        # 转换为RetrievedChunk对象
        retrieved_chunks = []
        for score, chunk in results:
            retrieved_chunks.append(
                RetrievedChunk(
                    id=chunk.id,
                    text_content=chunk.text_content,
                    score=score,
                    metadata=chunk.metadata
                )
            )
        
        return retrieved_chunks
    
    @abstractmethod
    def _vector_retrieve(self, query_vector: List[float], top_k: int, filters: Dict) -> List[RetrievedChunk]:
        """子类实现向量检索逻辑"""
        pass
    
    @abstractmethod
    def _get_all_chunks(self) -> List[ProcessedKnowledgeChunk]:
        """子类实现获取所有chunks的逻辑"""
        pass
    
    def _apply_metadata_filters(self, chunks: List[ProcessedKnowledgeChunk], filters: Dict) -> List[ProcessedKnowledgeChunk]:
        """应用元数据过滤器"""
        if not filters:
            return chunks
        
        filtered_chunks = []
        for chunk in chunks:
            metadata_match = True
            for key, value in filters.items():
                if key not in ['query_text', 'retrieval_method']:
                    if not (key in chunk.metadata and chunk.metadata[key] == value):
                        metadata_match = False
                        break
            
            if metadata_match:
                filtered_chunks.append(chunk)
        
        return filtered_chunks


class EnhancedMemoryStorageProvider(EnhancedStorageProvider):
    """增强的内存存储提供商"""
    
    def __init__(self, config: Dict[str, Any] = None, embedding_provider: EmbeddingProvider = None):
        super().__init__(config, embedding_provider)
        self.vector_db: Dict[str, ProcessedKnowledgeChunk] = {}
        self.staged_chunks: Dict[str, ProcessedKnowledgeChunk] = {}
    
    def _store_chunks(self, chunks: List[ProcessedKnowledgeChunk]) -> bool:
        """存储chunks到内存"""
        print(f"[EnhancedMemoryProvider] Storing {len(chunks)} chunks with embeddings.")
        
        for chunk in chunks:
            print(f"[EnhancedMemoryProvider] Storing chunk: {chunk.id}")
            if chunk.metadata.get('stage', False):
                print(f"[EnhancedMemoryProvider] Staging chunk: {chunk.id}")
                self.staged_chunks[chunk.id] = chunk
            else:
                print(f"[EnhancedMemoryProvider] Storing chunk to DB: {chunk.id}")
                self.vector_db[chunk.id] = chunk
        
        return True
    
    def _vector_retrieve(self, query_vector: List[float], top_k: int, filters: Dict) -> List[RetrievedChunk]:
        """基于向量的检索（简化实现）"""
        # 这里可以实现真正的向量相似度计算
        # 目前返回空列表，让语义检索处理
        return []
    
    def _get_all_chunks(self) -> List[ProcessedKnowledgeChunk]:
        """获取所有chunks"""
        return list(self.vector_db.values())
    
    def get_all_chunk_ids(self) -> List[str]:
        """获取所有chunk IDs"""
        print("[EnhancedMemoryProvider] Fetching all chunk IDs.")
        return list(self.vector_db.keys())
    
    async def list_staged_chunks(self) -> List[str]:
        """列出暂存的chunks"""
        print("[EnhancedMemoryProvider] Listing staged chunks.")
        return list(self.staged_chunks.keys())
    
    async def validate_and_promote(self, chunk_id: str) -> bool:
        """将chunk从暂存区移动到主数据库"""
        print(f"[EnhancedMemoryProvider] Promoting chunk {chunk_id}.")
        if chunk_id in self.staged_chunks:
            chunk = self.staged_chunks.pop(chunk_id)
            self.vector_db[chunk.id] = chunk
            # 同时生成嵌入向量
            try:
                embedding = self.embedding_provider.embed_text(chunk.text_content)
                self.embeddings_db[chunk.id] = embedding
            except Exception as e:
                print(f"Failed to generate embedding for promoted chunk {chunk_id}: {e}")
            return True
        return False
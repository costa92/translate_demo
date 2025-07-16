"""
语义检索器 - 使用向量化实现真正的语义搜索
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import math


class EmbeddingProvider(ABC):
    """嵌入向量提供商抽象基类"""
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """将文本转换为嵌入向量"""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为嵌入向量"""
        pass


class SimpleEmbeddingProvider(EmbeddingProvider):
    """简单的嵌入向量提供商 - 用于演示"""
    
    def __init__(self):
        # 简单的词汇表，实际应用中应该使用预训练的embedding模型
        self.vocab = {
            # 中文词汇
            '太阳': [0.8, 0.2, 0.1, 0.3, 0.5],
            '温度': [0.7, 0.3, 0.2, 0.4, 0.6],
            '表面': [0.6, 0.4, 0.3, 0.2, 0.7],
            '水': [0.5, 0.6, 0.4, 0.3, 0.2],
            '分子式': [0.4, 0.7, 0.5, 0.6, 0.3],
            'h2o': [0.5, 0.6, 0.4, 0.3, 0.2],
            '光速': [0.9, 0.1, 0.2, 0.8, 0.4],
            '公里': [0.3, 0.5, 0.7, 0.2, 0.6],
            'dna': [0.2, 0.8, 0.6, 0.4, 0.7],
            '脱氧': [0.2, 0.8, 0.6, 0.4, 0.7],
            '核糖': [0.2, 0.8, 0.6, 0.4, 0.7],
            '核酸': [0.2, 0.8, 0.6, 0.4, 0.7],
            
            # 数学词汇
            '圆': [0.1, 0.2, 0.9, 0.3, 0.4],
            '面积': [0.1, 0.3, 0.8, 0.4, 0.5],
            '半径': [0.1, 0.2, 0.9, 0.3, 0.4],
            '勾股定理': [0.2, 0.1, 0.7, 0.8, 0.3],
            '直角三角形': [0.2, 0.1, 0.7, 0.8, 0.3],
            '二次方程': [0.3, 0.2, 0.6, 0.9, 0.2],
            '求解': [0.4, 0.3, 0.5, 0.8, 0.3],
            '复利': [0.6, 0.7, 0.2, 0.3, 0.8],
            '本金': [0.6, 0.7, 0.2, 0.3, 0.8],
            '年利率': [0.6, 0.7, 0.2, 0.3, 0.8],
            
            # 物理词汇
            '速度': [0.8, 0.3, 0.1, 0.2, 0.9],
            '距离': [0.7, 0.4, 0.2, 0.3, 0.8],
            '时间': [0.9, 0.2, 0.1, 0.4, 0.7],
            '牛顿': [0.5, 0.1, 0.3, 0.9, 0.6],
            '质量': [0.4, 0.2, 0.4, 0.8, 0.7],
            '加速度': [0.6, 0.1, 0.2, 0.9, 0.5],
            '电功率': [0.3, 0.4, 0.6, 0.7, 0.9],
            '电压': [0.3, 0.4, 0.6, 0.7, 0.9],
            '电流': [0.3, 0.4, 0.6, 0.7, 0.9],
            '动能': [0.7, 0.2, 0.3, 0.8, 0.6],
            
            # 统计词汇
            '平均数': [0.2, 0.9, 0.4, 0.1, 0.3],
            '总和': [0.2, 0.9, 0.4, 0.1, 0.3],
            '标准差': [0.1, 0.8, 0.5, 0.2, 0.4],
            '离散程度': [0.1, 0.8, 0.5, 0.2, 0.4],
            '概率': [0.4, 0.6, 0.3, 0.5, 0.8],
            '有利结果': [0.4, 0.6, 0.3, 0.5, 0.8],
            '硬币': [0.5, 0.5, 0.2, 0.6, 0.7],
            '正面': [0.5, 0.5, 0.2, 0.6, 0.7],
            '条件概率': [0.3, 0.7, 0.4, 0.4, 0.9],
            
            # 逻辑词汇
            '肯定前件': [0.9, 0.4, 0.1, 0.6, 0.2],
            '否定后件': [0.9, 0.4, 0.1, 0.6, 0.2],
            '德摩根定律': [0.8, 0.3, 0.2, 0.7, 0.1],
            '三段论': [0.7, 0.5, 0.3, 0.8, 0.2],
            '大前提': [0.7, 0.5, 0.3, 0.8, 0.2],
            '小前提': [0.7, 0.5, 0.3, 0.8, 0.2],
            '结论': [0.7, 0.5, 0.3, 0.8, 0.2],
            '苏格拉底': [0.7, 0.5, 0.3, 0.8, 0.2],
            '推理': [0.8, 0.4, 0.2, 0.7, 0.3],
            '有效': [0.8, 0.4, 0.2, 0.7, 0.3],
            '逻辑': [0.8, 0.4, 0.2, 0.7, 0.3],
            '前提': [0.7, 0.5, 0.3, 0.8, 0.2],
            '成立': [0.7, 0.5, 0.3, 0.8, 0.2],
            '条件': [0.7, 0.5, 0.3, 0.8, 0.2],
            
            # 同义词和相关词汇
            '恒星': [0.8, 0.2, 0.1, 0.3, 0.5],  # 与太阳相似
            '星球': [0.8, 0.2, 0.1, 0.3, 0.5],  # 与太阳相似
            '热度': [0.7, 0.3, 0.2, 0.4, 0.6],  # 与温度相似
            '分子': [0.4, 0.7, 0.5, 0.6, 0.3],  # 与分子式相似
            '组成': [0.4, 0.7, 0.5, 0.6, 0.3],  # 与分子式相似
            '化学': [0.4, 0.7, 0.5, 0.6, 0.3],  # 与分子式相似
            '符号': [0.4, 0.7, 0.5, 0.6, 0.3],  # 与分子式相似
            '氢': [0.5, 0.6, 0.4, 0.3, 0.2],    # 与水相似
            '氧': [0.5, 0.6, 0.4, 0.3, 0.2],    # 与水相似
            '原子': [0.5, 0.6, 0.4, 0.3, 0.2],  # 与水相似
            '构成': [0.5, 0.6, 0.4, 0.3, 0.2],  # 与水相似
            '大小': [0.1, 0.3, 0.8, 0.4, 0.5],  # 与面积相似
            '计算': [0.1, 0.3, 0.8, 0.4, 0.5],  # 与面积相似
            '公式': [0.1, 0.3, 0.8, 0.4, 0.5],  # 与面积相似
            '运动': [0.8, 0.3, 0.1, 0.2, 0.9],  # 与速度相似
            '路程': [0.7, 0.4, 0.2, 0.3, 0.8],  # 与距离相似
        }
        self.embedding_dim = 5
    
    def embed_text(self, text: str) -> List[float]:
        """将文本转换为嵌入向量"""
        text_lower = text.lower()
        
        # 提取文本中的关键词
        words = []
        for word in self.vocab.keys():
            if word in text_lower:
                words.append(word)
        
        if not words:
            # 如果没有匹配的词汇，返回零向量
            return [0.0] * self.embedding_dim
        
        # 计算平均向量
        embeddings = [self.vocab[word] for word in words]
        avg_embedding = []
        for i in range(self.embedding_dim):
            avg_embedding.append(sum(emb[i] for emb in embeddings) / len(embeddings))
        
        return avg_embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为嵌入向量"""
        return [self.embed_text(text) for text in texts]


class LLMEmbeddingProvider(EmbeddingProvider):
    """使用LLM的嵌入向量提供商"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def embed_text(self, text: str) -> List[float]:
        """使用LLM生成嵌入向量"""
        try:
            return self.llm_client.get_embeddings(text)
        except Exception as e:
            print(f"LLM embedding failed: {e}")
            # 回退到简单提供商
            simple_provider = SimpleEmbeddingProvider()
            return simple_provider.embed_text(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        try:
            return self.llm_client.get_embeddings(texts)
        except Exception as e:
            print(f"LLM batch embedding failed: {e}")
            # 回退到简单提供商
            simple_provider = SimpleEmbeddingProvider()
            return simple_provider.embed_batch(texts)


class SemanticRetriever:
    """语义检索器 - 使用向量相似度进行检索"""
    
    def __init__(self, embedding_provider: EmbeddingProvider):
        self.embedding_provider = embedding_provider
    
    def calculate_similarity(self, query_embedding: List[float], chunk_embedding: List[float]) -> float:
        """计算余弦相似度"""
        if not query_embedding or not chunk_embedding:
            return 0.0
        
        if len(query_embedding) != len(chunk_embedding):
            return 0.0
        
        # 计算点积
        dot_product = sum(a * b for a, b in zip(query_embedding, chunk_embedding))
        
        # 计算向量的模长
        query_norm = math.sqrt(sum(a * a for a in query_embedding))
        chunk_norm = math.sqrt(sum(b * b for b in chunk_embedding))
        
        if query_norm == 0 or chunk_norm == 0:
            return 0.0
        
        # 计算余弦相似度
        similarity = dot_product / (query_norm * chunk_norm)
        return max(0.0, similarity)  # 确保相似度非负
    
    def retrieve_semantic(self, query: str, chunks: List[Any], top_k: int = 5) -> List[tuple]:
        """基于语义相似度检索"""
        # 生成查询的嵌入向量
        query_embedding = self.embedding_provider.embed_text(query)
        
        # 计算每个chunk的相似度
        similarities = []
        for chunk in chunks:
            chunk_embedding = self.embedding_provider.embed_text(chunk.text_content)
            similarity = self.calculate_similarity(query_embedding, chunk_embedding)
            similarities.append((similarity, chunk))
        
        # 按相似度排序并返回top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        return similarities[:top_k]
    
    def hybrid_retrieve(self, query: str, chunks: List[Any], top_k: int = 5, 
                       semantic_weight: float = 0.7, keyword_weight: float = 0.3) -> List[tuple]:
        """混合检索：结合语义相似度和关键词匹配"""
        # 语义检索
        semantic_results = self.retrieve_semantic(query, chunks, len(chunks))
        
        # 关键词检索（简化版）
        keyword_results = self._keyword_retrieve(query, chunks)
        
        # 合并分数
        final_scores = {}
        for similarity, chunk in semantic_results:
            chunk_id = chunk.id
            final_scores[chunk_id] = {
                'chunk': chunk,
                'semantic_score': similarity,
                'keyword_score': 0.0
            }
        
        for keyword_score, chunk in keyword_results:
            chunk_id = chunk.id
            if chunk_id in final_scores:
                final_scores[chunk_id]['keyword_score'] = keyword_score
            else:
                final_scores[chunk_id] = {
                    'chunk': chunk,
                    'semantic_score': 0.0,
                    'keyword_score': keyword_score
                }
        
        # 计算最终分数
        final_results = []
        for chunk_id, scores in final_scores.items():
            final_score = (scores['semantic_score'] * semantic_weight + 
                          scores['keyword_score'] * keyword_weight)
            final_results.append((final_score, scores['chunk']))
        
        # 排序并返回top_k
        final_results.sort(key=lambda x: x[0], reverse=True)
        return final_results[:top_k]
    
    def _keyword_retrieve(self, query: str, chunks: List[Any]) -> List[tuple]:
        """简单的关键词检索"""
        query_lower = query.lower()
        results = []
        
        for chunk in chunks:
            chunk_text = chunk.text_content.lower()
            
            # 简单的关键词匹配分数
            query_words = query_lower.split()
            matching_words = sum(1 for word in query_words if word in chunk_text)
            
            if matching_words > 0:
                score = matching_words / len(query_words)
                results.append((score, chunk))
        
        return results
"""Simple generator provider for basic answer generation."""
import logging
from typing import Dict, Any, List
from ...core.config import GenerationConfig

logger = logging.getLogger(__name__)


class SimpleGenerator:
    """
    Simple generator that provides basic answer generation without LLM.
    """
    
    def __init__(self, config: GenerationConfig):
        """Initialize simple generator."""
        self.config = config
        logger.info("SimpleGenerator initialized")
    
    async def initialize(self) -> None:
        """Initialize the simple generator (no-op)."""
        logger.info("Simple generator initialized successfully")
    
    async def generate(self, query: str, context: List[str], **kwargs) -> Dict[str, Any]:
        """
        Generate answer using simple context-based approach.
        
        Args:
            query: User query
            context: List of context texts
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with generated answer and metadata
        """
        if not context:
            return self._no_context_response(query)
        
        # Use the first (best) context as the answer base
        best_context = context[0]
        
        # Detect language
        is_chinese = any('\u4e00' <= char <= '\u9fff' for char in query)
        
        # Calculate simple confidence based on context length and query overlap
        confidence = self._calculate_confidence(query, best_context)
        
        if is_chinese:
            if confidence > 0.7:
                answer = f"根据相关信息：{best_context}"
            elif confidence > 0.3:
                answer = f"可能相关的信息：{best_context}"
            else:
                answer = f"找到一些信息，但相关性较低：{best_context}"
        else:
            if confidence > 0.7:
                answer = f"Based on the relevant information: {best_context}"
            elif confidence > 0.3:
                answer = f"Possibly relevant information: {best_context}"
            else:
                answer = f"Found some information with low relevance: {best_context}"
        
        return {
            "text": answer,
            "confidence": confidence,
            "model": "simple",
            "provider": "simple"
        }
    
    def _calculate_confidence(self, query: str, context: str) -> float:
        """Calculate confidence score based on query-context similarity."""
        if not query or not context:
            return 0.0
        
        # Simple word overlap calculation
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())
        
        if not query_words:
            return 0.0
        
        # Calculate overlap ratio
        overlap = len(query_words.intersection(context_words))
        confidence = overlap / len(query_words)
        
        # Boost confidence if context is substantial
        if len(context) > 100:
            confidence += 0.1
        
        # Penalize very short contexts
        if len(context) < 20:
            confidence *= 0.5
        
        return min(1.0, max(0.1, confidence))
    
    def _no_context_response(self, query: str) -> Dict[str, Any]:
        """Generate response when no context is available."""
        is_chinese = any('\u4e00' <= char <= '\u9fff' for char in query)
        
        if is_chinese:
            answer = "抱歉，我没有找到相关信息来回答您的问题。"
        else:
            answer = "I'm sorry, I couldn't find relevant information to answer your question."
        
        return {
            "text": answer,
            "confidence": 0.0,
            "model": "simple",
            "provider": "simple"
        }
    
    async def close(self) -> None:
        """Close the simple generator (no-op)."""
        logger.info("Simple generator closed")
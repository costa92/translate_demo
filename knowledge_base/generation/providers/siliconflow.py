"""SiliconFlow LLM provider for answer generation."""
import logging
import httpx
import json
from typing import Dict, Any, List, Optional
from ...core.config import GenerationConfig
from ...core.exceptions import GenerationError

logger = logging.getLogger(__name__)


class SiliconFlowGenerator:
    """
    SiliconFlow LLM provider for answer generation.
    """
    
    def __init__(self, config: GenerationConfig):
        """Initialize SiliconFlow generator."""
        self.config = config
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.siliconflow.cn/v1"
        self.model = config.model or "Qwen/Qwen2.5-7B-Instruct"
        self._client = None
        self._initialized = False
        
        if not self.api_key:
            raise GenerationError("SiliconFlow API key is required")
        
        logger.info(f"SiliconFlowGenerator initialized with model: {self.model}")
    
    async def initialize(self) -> None:
        """Initialize the SiliconFlow client."""
        if self._initialized:
            return
        
        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=60.0
            )
            self._initialized = True
            logger.info("SiliconFlow generator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SiliconFlow generator: {e}")
            raise GenerationError(f"SiliconFlow initialization failed: {e}")
    
    async def generate(self, query: str, context: List[str], **kwargs) -> Dict[str, Any]:
        """
        Generate answer using SiliconFlow LLM.
        
        Args:
            query: User query
            context: List of context texts
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with generated answer and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Build system prompt with context
            context_text = "\n\n".join(context)
            
            # Detect language
            is_chinese = any('\u4e00' <= char <= '\u9fff' for char in query)
            
            if is_chinese:
                system_prompt = f"""你是一个知识库助手。请根据提供的上下文信息准确回答用户的问题。

上下文信息:
{context_text}

要求：
1. 基于上下文信息回答，不要编造信息
2. 如果上下文信息不足以回答问题，请明确说明
3. 回答要简洁明确，直接针对问题
4. 可以引用上下文中的具体内容"""
            else:
                system_prompt = f"""You are a knowledge base assistant. Please answer the user's question accurately based on the provided context information.

Context Information:
{context_text}

Requirements:
1. Answer based on the context information, do not make up information
2. If the context information is insufficient to answer the question, please state clearly
3. Keep answers concise and direct to the question
4. You may quote specific content from the context"""
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            # Call SiliconFlow API
            response = await self._client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "top_p": getattr(self.config, "top_p", 0.9),
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                raise GenerationError(f"SiliconFlow API request failed: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if "choices" not in result or not result["choices"]:
                raise GenerationError("Invalid SiliconFlow API response format")
            
            answer = result["choices"][0]["message"]["content"].strip()
            
            # Calculate confidence based on context relevance
            confidence = self._calculate_confidence(answer, context)
            
            return {
                "text": answer,
                "confidence": confidence,
                "model": self.model,
                "provider": "siliconflow",
                "usage": result.get("usage", {})
            }
            
        except httpx.RequestError as e:
            logger.error(f"Network error during generation: {e}")
            raise GenerationError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise GenerationError(f"Answer generation failed: {e}")
    
    def _calculate_confidence(self, answer: str, context: List[str]) -> float:
        """Calculate confidence score based on answer and context."""
        # Simple heuristic confidence calculation
        if not answer or not context:
            return 0.0
        
        # Check if answer contains content from context
        confidence = 0.5  # Base confidence
        
        # Check for context references
        for ctx in context:
            # Find significant phrases (3+ words) from context in answer
            ctx_phrases = self._extract_phrases(ctx)
            for phrase in ctx_phrases:
                if phrase in answer:
                    confidence += 0.1
                    break
        
        # Check for uncertainty markers
        uncertainty_phrases = [
            "I don't have enough information",
            "insufficient context",
            "cannot determine",
            "not mentioned in the context",
            "没有足够的信息",
            "上下文中没有提到",
            "无法确定"
        ]
        
        for phrase in uncertainty_phrases:
            if phrase in answer:
                confidence -= 0.2
                break
        
        return min(1.0, max(0.1, confidence))
    
    def _extract_phrases(self, text: str, min_words: int = 3) -> List[str]:
        """Extract significant phrases from text."""
        words = text.split()
        phrases = []
        
        for i in range(len(words) - min_words + 1):
            phrase = " ".join(words[i:i+min_words])
            if len(phrase) > 10:  # Only phrases with reasonable length
                phrases.append(phrase)
        
        return phrases[:10]  # Limit number of phrases
    
    async def close(self) -> None:
        """Close the SiliconFlow client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._initialized = False
        logger.info("SiliconFlow generator closed")
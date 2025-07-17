"""Answer generation implementation."""

import logging
from typing import List, Tuple, Optional, Dict, Any
from ..core.config import GenerationConfig
from ..core.types import RetrievalResult
from ..core.exceptions import GenerationError

logger = logging.getLogger(__name__)


class Generator:
    """
    Answer generator that creates responses based on retrieved context.
    """
    
    def __init__(self, config: GenerationConfig):
        """Initialize generator with configuration."""
        self.config = config
        self.provider = None
        self._initialized = False
        
        logger.info(f"Generator initialized with provider: {config.provider}")
    
    async def initialize(self) -> None:
        """Initialize the generator provider."""
        if self._initialized:
            return
        
        try:
            logger.info(f"Initializing generator provider: {self.config.provider}")
            
            if self.config.provider == "simple":
                from .providers.simple import SimpleGenerator
                self.provider = SimpleGenerator(self.config)
            elif self.config.provider == "deepseek":
                from .providers.deepseek import DeepSeekGenerator
                self.provider = DeepSeekGenerator(self.config)
            elif self.config.provider == "siliconflow":
                from .providers.siliconflow import SiliconFlowGenerator
                self.provider = SiliconFlowGenerator(self.config)
            else:
                # Fallback to simple provider for unsupported providers
                logger.warning(f"Unsupported provider {self.config.provider}, using simple provider")
                from .providers.simple import SimpleGenerator
                self.provider = SimpleGenerator(self.config)
            
            if hasattr(self.provider, 'initialize'):
                await self.provider.initialize()
            
            self._initialized = True
            logger.info(f"Generator provider '{self.config.provider}' initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize generator: {e}")
            # Fallback to simple provider
            try:
                from .providers.simple import SimpleGenerator
                self.provider = SimpleGenerator(self.config)
                self._initialized = True
                logger.info("Fallback to simple provider successful")
            except Exception as fallback_error:
                logger.error(f"Fallback initialization failed: {fallback_error}")
                raise GenerationError(f"Generator initialization failed: {e}")
    
    async def generate(
        self, 
        query: str, 
        retrieval_results: List[RetrievalResult],
        **kwargs
    ) -> Tuple[str, float]:
        """
        Generate an answer based on query and retrieved context.
        
        Args:
            query: User query
            retrieval_results: Retrieved context chunks
            **kwargs: Additional generation parameters
            
        Returns:
            Tuple of (answer, confidence_score)
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Convert retrieval results to context strings
            if retrieval_results and hasattr(retrieval_results[0], 'text'):
                # If we have RetrievalResult objects
                context = [result.text for result in retrieval_results]
            else:
                # If we already have strings (for testing)
                context = retrieval_results if isinstance(retrieval_results, list) else []
            
            # Use the provider to generate answer
            result = await self.provider.generate(query, context, **kwargs)
            
            # Extract answer and confidence from result
            answer = result.get("text", "")
            confidence = result.get("confidence", 0.0)
            
            logger.debug(f"Generated answer with confidence {confidence:.2f}")
            return answer, confidence
                
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return self._error_response(query, str(e))
    

    
    def _error_response(self, query: str, error_msg: str) -> Tuple[str, float]:
        """Generate error response."""
        is_chinese = any('\u4e00' <= char <= '\u9fff' for char in query)
        
        if is_chinese:
            answer = f"处理您的问题时遇到错误：{error_msg}"
        else:
            answer = f"An error occurred while processing your question: {error_msg}"
        
        return answer, 0.0
    
    async def close(self) -> None:
        """Close the generator and cleanup resources."""
        if self.provider and hasattr(self.provider, 'close'):
            await self.provider.close()
        self.provider = None
        self._initialized = False
        logger.info("Generator closed")
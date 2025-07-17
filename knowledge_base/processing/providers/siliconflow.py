"""SiliconFlow embedding provider."""

import asyncio
import logging
import httpx
from typing import List, Dict, Any
from ...core.config import EmbeddingConfig
from ...core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class SiliconFlowEmbedder:
    """
    SiliconFlow embedding provider.
    Supports various embedding models through SiliconFlow API.
    """
    
    def __init__(self, config: EmbeddingConfig):
        """Initialize SiliconFlow embedder."""
        self.config = config
        self.api_key = config.api_key or config.additional_params.get("siliconflow_api_key")
        self.base_url = config.additional_params.get("base_url", "https://api.siliconflow.cn/v1")
        self.model = config.model_name or "BAAI/bge-large-zh-v1.5"
        self._client = None
        self._initialized = False
        
        if not self.api_key:
            raise EmbeddingError("SiliconFlow API key is required")
        
        logger.info(f"SiliconFlowEmbedder initialized with model: {self.model}")
    
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
                timeout=30.0
            )
            
            # Test the connection
            await self._test_connection()
            
            self._initialized = True
            logger.info("SiliconFlow embedder initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SiliconFlow embedder: {e}")
            raise EmbeddingError(f"SiliconFlow initialization failed: {e}")
    
    async def _test_connection(self) -> None:
        """Test the API connection."""
        try:
            response = await self._client.post(
                "/embeddings",
                json={
                    "model": self.model,
                    "input": ["test"],
                    "encoding_format": "float"
                }
            )
            
            if response.status_code != 200:
                raise EmbeddingError(f"API test failed: {response.status_code} - {response.text}")
            
            result = response.json()
            if "data" not in result or not result["data"]:
                raise EmbeddingError("Invalid API response format")
            
            # Update dimensions from actual response
            self.config.dimensions = len(result["data"][0]["embedding"])
            logger.info(f"SiliconFlow API test successful, dimensions: {self.config.dimensions}")
            
        except httpx.RequestError as e:
            raise EmbeddingError(f"Network error during API test: {e}")
        except Exception as e:
            raise EmbeddingError(f"API test failed: {e}")
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not self._initialized:
            await self.initialize()
        
        if not text or not text.strip():
            return [0.0] * self.config.dimensions
        
        try:
            # Truncate text if too long
            if len(text) > self.config.max_length:
                text = text[:self.config.max_length]
            
            response = await self._client.post(
                "/embeddings",
                json={
                    "model": self.model,
                    "input": [text],
                    "encoding_format": "float"
                }
            )
            
            if response.status_code != 200:
                raise EmbeddingError(f"API request failed: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if "data" not in result or not result["data"]:
                raise EmbeddingError("Invalid API response format")
            
            embedding = result["data"][0]["embedding"]
            
            # Normalize if configured
            if self.config.normalize:
                embedding = self._normalize_vector(embedding)
            
            return embedding
            
        except httpx.RequestError as e:
            logger.error(f"Network error during embedding: {e}")
            raise EmbeddingError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingError(f"Embedding generation failed: {e}")
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self._initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        if not valid_texts:
            return [[0.0] * self.config.dimensions] * len(texts)
        
        try:
            # Truncate texts if too long
            truncated_texts = []
            for text in valid_texts:
                if len(text) > self.config.max_length:
                    text = text[:self.config.max_length]
                truncated_texts.append(text)
            
            # Process in batches to avoid API limits
            batch_size = min(self.config.batch_size, 100)  # SiliconFlow batch limit
            all_embeddings = []
            
            for i in range(0, len(truncated_texts), batch_size):
                batch = truncated_texts[i:i + batch_size]
                
                response = await self._client.post(
                    "/embeddings",
                    json={
                        "model": self.model,
                        "input": batch,
                        "encoding_format": "float"
                    }
                )
                
                if response.status_code != 200:
                    raise EmbeddingError(f"Batch API request failed: {response.status_code} - {response.text}")
                
                result = response.json()
                
                if "data" not in result or not result["data"]:
                    raise EmbeddingError("Invalid batch API response format")
                
                batch_embeddings = [item["embedding"] for item in result["data"]]
                
                # Normalize if configured
                if self.config.normalize:
                    batch_embeddings = [self._normalize_vector(emb) for emb in batch_embeddings]
                
                all_embeddings.extend(batch_embeddings)
                
                # Add small delay between batches to respect rate limits
                if i + batch_size < len(truncated_texts):
                    await asyncio.sleep(0.1)
            
            # Map back to original texts (handle empty texts)
            result_embeddings = []
            valid_idx = 0
            
            for text in texts:
                if text and text.strip():
                    result_embeddings.append(all_embeddings[valid_idx])
                    valid_idx += 1
                else:
                    result_embeddings.append([0.0] * self.config.dimensions)
            
            logger.info(f"Generated embeddings for {len(texts)} texts using SiliconFlow")
            return result_embeddings
            
        except httpx.RequestError as e:
            logger.error(f"Network error during batch embedding: {e}")
            raise EmbeddingError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise EmbeddingError(f"Batch embedding generation failed: {e}")
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize a vector to unit length."""
        import math
        
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude == 0:
            return vector
        
        return [x / magnitude for x in vector]
    
    async def close(self) -> None:
        """Close the SiliconFlow client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        
        self._initialized = False
        logger.info("SiliconFlow embedder closed")
    
    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return self.config.dimensions
"""
Ollama generation provider for the knowledge base system.
"""

import asyncio
import json
from typing import AsyncIterator, Dict, List, Optional

import httpx

from ...core.config import Config
from ...core.exceptions import GenerationError
from ..generator import GenerationProvider


class OllamaProvider(GenerationProvider):
    """Ollama generation provider."""

    def __init__(self, config: Config):
        """Initialize the Ollama generation provider.

        Args:
            config: The system configuration.
        """
        super().__init__(config)
        self.api_base = getattr(self.config.generation, "ollama_api_base", "http://localhost:11434")
        self.model = getattr(self.config.generation, "ollama_model", "llama2")
        self.temperature = getattr(self.config.generation, "temperature", 0.7)
        self.max_tokens = getattr(self.config.generation, "max_tokens", 1000)
        self.headers = {"Content-Type": "application/json"}

    async def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt.

        Args:
            prompt: The prompt to generate a response for.

        Returns:
            The generated response.

        Raises:
            GenerationError: If generation fails.
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "stream": False,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/api/generate",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise GenerationError(f"Ollama API error: {response.status_code} - {response.text}")
                
                result = response.json()
                return result["response"]
        except Exception as e:
            raise GenerationError(f"Ollama generation failed: {str(e)}") from e

    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        """Generate a streaming response for the given prompt.

        Args:
            prompt: The prompt to generate a response for.

        Returns:
            An async iterator of response chunks.

        Raises:
            GenerationError: If generation fails.
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "stream": True,
            }
            
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/api/generate",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise GenerationError(f"Ollama API error: {response.status_code} - {error_text.decode()}")
                    
                    # Process the streaming response
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                yield chunk["response"]
                            if chunk.get("done", False):
                                break
                        except Exception:
                            # Skip malformed chunks
                            continue
        except Exception as e:
            raise GenerationError(f"Ollama streaming generation failed: {str(e)}") from e
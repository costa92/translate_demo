"""
DeepSeek generation provider for the knowledge base system.
"""

import asyncio
from typing import AsyncIterator, Dict, List, Optional

import httpx

from ...core.config import Config
from ...core.exceptions import GenerationError
from ..generator import GenerationProvider


class DeepSeekProvider(GenerationProvider):
    """DeepSeek generation provider."""

    def __init__(self, config: Config):
        """Initialize the DeepSeek generation provider.

        Args:
            config: The system configuration.
        """
        super().__init__(config)
        self.api_key = self.config.generation.deepseek_api_key
        self.api_base = getattr(self.config.generation, "deepseek_api_base", "https://api.deepseek.com")
        self.model = getattr(self.config.generation, "deepseek_model", "deepseek-chat")
        self.temperature = getattr(self.config.generation, "temperature", 0.7)
        self.max_tokens = getattr(self.config.generation, "max_tokens", 1000)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

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
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/v1/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise GenerationError(f"DeepSeek API error: {response.status_code} - {response.text}")
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            raise GenerationError(f"DeepSeek generation failed: {str(e)}") from e

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
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": True,
            }
            
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/v1/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise GenerationError(f"DeepSeek API error: {response.status_code} - {error_text.decode()}")
                    
                    # Process the streaming response
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if line and line.startswith("data:"):
                            data = line[5:].strip()
                            if data == "[DONE]":
                                break
                            
                            try:
                                chunk = json.loads(data)
                                if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except Exception as e:
                                # Skip malformed chunks
                                continue
        except Exception as e:
            raise GenerationError(f"DeepSeek streaming generation failed: {str(e)}") from e
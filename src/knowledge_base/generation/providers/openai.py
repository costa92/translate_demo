"""
OpenAI generation provider for the knowledge base system.
"""

import asyncio
from typing import AsyncIterator, Optional

import openai
from openai import AsyncOpenAI

from ...core.config import Config
from ...core.exceptions import GenerationError
from ..generator import GenerationProvider


class OpenAIProvider(GenerationProvider):
    """OpenAI generation provider."""

    def __init__(self, config: Config):
        """Initialize the OpenAI generation provider.

        Args:
            config: The system configuration.
        """
        super().__init__(config)
        self.api_key = self.config.generation.openai_api_key
        self.model = self.config.generation.openai_model or "gpt-3.5-turbo"
        self.temperature = getattr(self.config.generation, "temperature", 0.7)
        self.max_tokens = getattr(self.config.generation, "max_tokens", 1000)
        self.client = AsyncOpenAI(api_key=self.api_key)

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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise GenerationError(f"OpenAI generation failed: {str(e)}") from e

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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise GenerationError(f"OpenAI streaming generation failed: {str(e)}") from e
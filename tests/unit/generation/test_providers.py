"""
Tests for the generation providers.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import GenerationError
from src.knowledge_base.generation.providers.openai import OpenAIProvider
from src.knowledge_base.generation.providers.deepseek import DeepSeekProvider
from src.knowledge_base.generation.providers.siliconflow import SiliconFlowProvider
from src.knowledge_base.generation.providers.ollama import OllamaProvider
from src.knowledge_base.generation.providers.simple import SimpleProvider


class TestOpenAIProvider:
    """Tests for the OpenAIProvider class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = MagicMock(spec=Config)
        config.generation = MagicMock()
        config.generation.openai_api_key = "test_key"
        config.generation.openai_model = "gpt-3.5-turbo"
        config.generation.temperature = 0.7
        config.generation.max_tokens = 1000
        return config
    
    @pytest.fixture
    def provider(self, config):
        """Create a test provider."""
        with patch("openai.AsyncOpenAI"):
            provider = OpenAIProvider(config)
            return provider
    
    @pytest.mark.asyncio
    async def test_generate(self, provider):
        """Test the generate method."""
        # Mock the OpenAI client response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        response = await provider.generate("Test prompt")
        
        assert response == "Test response"
        provider.client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_error(self, provider):
        """Test error handling in generate method."""
        provider.client.chat.completions.create = AsyncMock(side_effect=Exception("Test error"))
        
        with pytest.raises(GenerationError):
            await provider.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_stream(self, provider):
        """Test the generate_stream method."""
        # Mock streaming response chunks
        mock_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Test "))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="stream "))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="response"))])
        ]
        
        # Create an async generator to return the mock chunks
        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk
        
        provider.client.chat.completions.create = AsyncMock(return_value=mock_stream())
        
        # Collect all chunks from the stream
        result = []
        async for chunk in provider.generate_stream("Test prompt"):
            result.append(chunk)
        
        assert result == ["Test ", "stream ", "response"]
        provider.client.chat.completions.create.assert_called_once()


class TestSimpleProvider:
    """Tests for the SimpleProvider class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = MagicMock(spec=Config)
        config.generation = MagicMock()
        config.generation.simple_delay = 0.01  # Use a small delay for tests
        return config
    
    @pytest.fixture
    def provider(self, config):
        """Create a test provider."""
        return SimpleProvider(config)
    
    @pytest.mark.asyncio
    async def test_generate(self, provider):
        """Test the generate method."""
        response = await provider.generate("Test prompt")
        
        assert "Test prompt" in response or "simple response" in response.lower()
    
    @pytest.mark.asyncio
    async def test_generate_with_question(self, provider):
        """Test the generate method with a question in the prompt."""
        prompt = "Context: Some context\n\nQuestion: What is the answer?"
        response = await provider.generate(prompt)
        
        assert "What is the answer?" in response or "simple response" in response.lower()
    
    @pytest.mark.asyncio
    async def test_generate_stream(self, provider):
        """Test the generate_stream method."""
        # Collect all chunks from the stream
        result = []
        async for chunk in provider.generate_stream("Test prompt"):
            result.append(chunk)
        
        # Join the chunks and check the result
        full_response = "".join(result)
        assert "Test prompt" in full_response or "simple response" in full_response.lower()


# Note: For the HTTP-based providers (DeepSeek, SiliconFlow, Ollama),
# we would typically use a mocked httpx client to test their behavior.
# These tests are more complex and would require more setup.
# For brevity, we'll just include basic initialization tests for now.

class TestHttpProviders:
    """Basic tests for HTTP-based providers."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = MagicMock(spec=Config)
        config.generation = MagicMock()
        config.generation.deepseek_api_key = "test_key"
        config.generation.deepseek_api_base = "https://api.deepseek.com"
        config.generation.siliconflow_api_key = "test_key"
        config.generation.siliconflow_api_base = "https://api.siliconflow.com"
        config.generation.ollama_api_base = "http://localhost:11434"
        config.generation.ollama_model = "llama2"
        return config
    
    def test_deepseek_init(self, config):
        """Test DeepSeekProvider initialization."""
        provider = DeepSeekProvider(config)
        assert provider.api_key == "test_key"
        assert "api.deepseek.com" in provider.api_base
    
    def test_siliconflow_init(self, config):
        """Test SiliconFlowProvider initialization."""
        provider = SiliconFlowProvider(config)
        assert provider.api_key == "test_key"
        assert "api.siliconflow.com" in provider.api_base
    
    def test_ollama_init(self, config):
        """Test OllamaProvider initialization."""
        provider = OllamaProvider(config)
        assert provider.api_base == "http://localhost:11434"
        assert provider.model == "llama2"  # Default model
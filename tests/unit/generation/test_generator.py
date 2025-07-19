"""
Tests for the Generator class.
"""

import asyncio
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import TextChunk
from src.knowledge_base.core.exceptions import GenerationError
from src.knowledge_base.generation.generator import Generator, GenerationProvider
from src.knowledge_base.generation.prompt_template import PromptTemplate, PromptTemplateManager


class TestGenerationProvider(GenerationProvider):
    """Test implementation of GenerationProvider."""
    
    def __init__(self, config, response="Test response", stream_response=None):
        super().__init__(config)
        self.response = response
        self.stream_response = stream_response or ["Test ", "stream ", "response"]
        
    async def generate(self, prompt):
        return self.response
        
    async def generate_stream(self, prompt):
        for chunk in self.stream_response:
            yield chunk


class TestGenerator:
    """Tests for the Generator class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = Config()
        config.generation.provider = "test"
        config.generation.stream = False
        return config
    
    @pytest.fixture
    def generator(self, config):
        """Create a test generator."""
        with patch.object(Generator, '_create_provider') as mock_create:
            mock_create.return_value = TestGenerationProvider(config)
            generator = Generator(config)
            return generator
    
    @pytest.mark.asyncio
    async def test_generate(self, generator):
        """Test the generate method."""
        query = "Test query"
        chunks = [TextChunk(
            id=str(uuid.uuid4()),
            text="Test chunk",
            document_id=str(uuid.uuid4()),
            metadata={}
        )]
        
        response = await generator.generate(query, chunks)
        
        assert response == "Test response"
    
    @pytest.mark.asyncio
    async def test_generate_stream(self, generator):
        """Test the generate method with streaming."""
        query = "Test query"
        chunks = [TextChunk(
            id=str(uuid.uuid4()),
            text="Test chunk",
            document_id=str(uuid.uuid4()),
            metadata={}
        )]
        
        stream = await generator.generate(query, chunks, stream=True)
        
        # Collect all chunks from the stream
        result = []
        async for chunk in stream:
            result.append(chunk)
        
        assert result == ["Test ", "stream ", "response"]
    
    @pytest.mark.asyncio
    async def test_generate_error(self, generator):
        """Test error handling in generate method."""
        query = "Test query"
        chunks = [TextChunk(
            id=str(uuid.uuid4()),
            text="Test chunk",
            document_id=str(uuid.uuid4()),
            metadata={}
        )]
        
        # Make the provider's generate method raise an exception
        generator.provider.generate = AsyncMock(side_effect=ValueError("Test error"))
        
        with pytest.raises(GenerationError):
            await generator.generate(query, chunks)
    
    def test_create_provider_unknown(self, config):
        """Test creating an unknown provider."""
        config.generation.provider = "unknown"
        
        with pytest.raises(ValueError):
            Generator(config)
    
    def test_create_prompt(self, generator):
        """Test creating a prompt."""
        # Reset the mock for prompt_template and template_id
        if hasattr(generator.config.generation, "prompt_template"):
            delattr(generator.config.generation, "prompt_template")
        if hasattr(generator.config.generation, "template_id"):
            delattr(generator.config.generation, "template_id")
            
        query = "Test query"
        chunks = [
            TextChunk(
                id=str(uuid.uuid4()),
                text="Chunk 1",
                document_id=str(uuid.uuid4()),
                metadata={}
            ),
            TextChunk(
                id=str(uuid.uuid4()),
                text="Chunk 2",
                document_id=str(uuid.uuid4()),
                metadata={}
            )
        ]
        
        # Call the actual method, not the mock
        prompt = generator._create_prompt(query, chunks)
        
        assert "Test query" in prompt
        assert "Chunk 1" in prompt
        assert "Chunk 2" in prompt
    
    def test_create_prompt_with_direct_template(self, generator):
        """Test creating a prompt with a direct template string."""
        generator.config.generation.prompt_template = "Q: {query}\nC: {context}"
        
        query = "Test query"
        chunks = [TextChunk(
            id=str(uuid.uuid4()),
            text="Test chunk",
            document_id=str(uuid.uuid4()),
            metadata={}
        )]
        
        prompt = generator._create_prompt(query, chunks)
        
        assert prompt == "Q: Test query\nC: Test chunk"
        
    def test_create_prompt_with_template_id(self, generator):
        """Test creating a prompt with a template ID."""
        # Add a custom template to the template manager
        generator.template_manager.add_template("custom_template", "Custom: {query}\nData: {context}")
        
        # Set the template ID in the config
        generator.config.generation.template_id = "custom_template"
        
        query = "Test query"
        chunks = [TextChunk(
            id=str(uuid.uuid4()),
            text="Test chunk",
            document_id=str(uuid.uuid4()),
            metadata={}
        )]
        
        prompt = generator._create_prompt(query, chunks)
        
        assert prompt == "Custom: Test query\nData: Test chunk"
        
    def test_create_prompt_with_nonexistent_template_id(self, generator):
        """Test creating a prompt with a nonexistent template ID."""
        # Set a nonexistent template ID in the config
        generator.config.generation.template_id = "nonexistent_template"
        
        query = "Test query"
        chunks = [TextChunk(
            id=str(uuid.uuid4()),
            text="Test chunk",
            document_id=str(uuid.uuid4()),
            metadata={}
        )]
        
        # Should fall back to default_rag template
        prompt = generator._create_prompt(query, chunks)
        
        assert "Test query" in prompt
        assert "Test chunk" in prompt
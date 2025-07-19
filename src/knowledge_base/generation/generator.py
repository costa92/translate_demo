"""
Generator module for the knowledge base system.

This module provides the base Generator class and related functionality
for generating responses based on retrieved information.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from ..core.config import Config
from ..core.exceptions import GenerationError
from ..core.types import TextChunk, RetrievalResult, QueryResult
from .prompt_template import PromptTemplate, PromptTemplateManager
from .quality_control import AnswerValidator
from .citation import SourceAttributor


class GenerationProvider(ABC):
    """Base interface for generation providers."""

    def __init__(self, config: Config):
        """Initialize the generation provider.

        Args:
            config: The system configuration.
        """
        self.config = config

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt.

        Args:
            prompt: The prompt to generate a response for.

        Returns:
            The generated response.
        """
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        """Generate a streaming response for the given prompt.

        Args:
            prompt: The prompt to generate a response for.

        Returns:
            An async iterator of response chunks.
        """
        pass


class Generator:
    """Generates responses based on retrieved information."""

    def __init__(self, config: Config):
        """Initialize the generator.

        Args:
            config: The system configuration.
        """
        self.config = config
        self.provider = self._create_provider()
        self.template_manager = PromptTemplateManager(config)
        self.validator = AnswerValidator(config)
        self.source_attributor = SourceAttributor(config)

    def _create_provider(self) -> GenerationProvider:
        """Create a generation provider based on configuration.

        Returns:
            The configured generation provider.

        Raises:
            ValueError: If the configured provider is unknown.
        """
        provider_name = self.config.generation.provider
        if provider_name == "openai":
            from .providers.openai import OpenAIProvider
            return OpenAIProvider(self.config)
        elif provider_name == "deepseek":
            from .providers.deepseek import DeepSeekProvider
            return DeepSeekProvider(self.config)
        elif provider_name == "siliconflow":
            from .providers.siliconflow import SiliconFlowProvider
            return SiliconFlowProvider(self.config)
        elif provider_name == "ollama":
            from .providers.ollama import OllamaProvider
            return OllamaProvider(self.config)
        elif provider_name == "simple":
            from .providers.simple import SimpleProvider
            return SimpleProvider(self.config)
        else:
            raise ValueError(f"Unknown generation provider: {provider_name}")

    async def generate(
        self,
        query: str,
        chunks: List[TextChunk],
        stream: Optional[bool] = None,
        validate: Optional[bool] = None,
        include_citations: Optional[bool] = None
    ) -> Union[str, AsyncIterator[str], QueryResult]:
        """Generate a response based on a query and retrieved chunks.

        Args:
            query: The user query.
            chunks: The retrieved text chunks.
            stream: Whether to stream the response. If None, uses the config setting.
            validate: Whether to validate the response. If None, uses the config setting.
            include_citations: Whether to include citations. If None, uses the config setting.

        Returns:
            The generated response, an async iterator of response chunks, or a QueryResult with citations.

        Raises:
            GenerationError: If generation fails.
        """
        try:
            prompt = self._create_prompt(query, chunks)
            stream_response = stream if stream is not None else self.config.generation.stream
            validate_response = validate if validate is not None else getattr(self.config.generation, "validate", True)
            add_citations = include_citations if include_citations is not None else getattr(self.config.generation, "include_citations", True)

            if stream_response:
                # Streaming responses can't be validated or have citations added in advance
                return self.provider.generate_stream(prompt)
            else:
                answer = await self.provider.generate(prompt)
                
                # Apply quality control if enabled
                if validate_response:
                    answer = await self.validator.validate_and_improve(query, answer, chunks)
                
                # Add citations if enabled
                if add_citations:
                    # Convert chunks to RetrievalResult objects for citation
                    sources = [
                        RetrievalResult(chunk=chunk, score=1.0, rank=i)
                        for i, chunk in enumerate(chunks)
                    ]
                    return self.source_attributor.create_attributed_result(query, answer, sources)
                else:
                    return answer
        except Exception as e:
            raise GenerationError(f"Failed to generate response: {str(e)}") from e

    def _create_prompt(self, query: str, chunks: List[TextChunk]) -> str:
        """Create a prompt for the generation model.

        Args:
            query: The user query.
            chunks: The retrieved text chunks.

        Returns:
            The formatted prompt.
        """
        context = "\n\n".join([chunk.text for chunk in chunks])
        
        # Check if a specific template ID is specified in the config
        template_id = getattr(self.config.generation, "template_id", "default_rag")
        
        # For backward compatibility, check if prompt_template is directly specified
        direct_template = getattr(self.config.generation, "prompt_template", None)
        if direct_template:
            # Create a one-time template if directly specified
            template = PromptTemplate(direct_template)
            return template.format(query=query, context=context)
        
        # Use the template manager to format the template
        try:
            return self.template_manager.format_template(
                template_id, 
                query=query, 
                context=context
            )
        except GenerationError:
            # Fallback to default template if the specified one is not found
            return self.template_manager.format_template("default_rag", query=query, context=context)
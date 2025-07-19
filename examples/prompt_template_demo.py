"""
Demo for the prompt template system.

This script demonstrates how to use the prompt template system
for generating responses with different templates.
"""

import asyncio
import os
from pathlib import Path

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import TextChunk
from src.knowledge_base.generation.generator import Generator
from src.knowledge_base.generation.prompt_template import PromptTemplate, PromptTemplateManager


async def main():
    """Run the demo."""
    # Create a configuration
    config = Config()
    
    # Set up a simple provider for demonstration
    config.generation.provider = "simple"
    
    # Create a generator
    generator = Generator(config)
    
    # Create some sample chunks
    chunks = [
        TextChunk(
            id="1",
            text="Paris is the capital of France.",
            document_id="doc1",
            metadata={"source": "geography.txt"}
        ),
        TextChunk(
            id="2",
            text="France is a country in Western Europe.",
            document_id="doc1",
            metadata={"source": "geography.txt"}
        )
    ]
    
    # Example 1: Using the default template
    print("Example 1: Using the default template")
    query = "What is the capital of France?"
    response = await generator.generate(query, chunks)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()
    
    # Example 2: Using a direct template
    print("Example 2: Using a direct template")
    config.generation.prompt_template = """
Question: {query}

Information:
{context}

Please answer the question based on the information provided:
"""
    response = await generator.generate(query, chunks)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()
    
    # Example 3: Using a custom template from the template manager
    print("Example 3: Using a custom template from the template manager")
    # Reset the direct template
    config.generation.prompt_template = None
    
    # Add a custom template
    generator.template_manager.add_template(
        "qa_template",
        """
Q: {query}
---
Context:
{context}
---
A:
"""
    )
    
    # Set the template ID
    config.generation.template_id = "qa_template"
    
    response = await generator.generate(query, chunks)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()
    
    # Example 4: Saving and loading templates
    print("Example 4: Saving and loading templates")
    
    # Create a temporary directory for templates
    os.makedirs("temp", exist_ok=True)
    template_file = Path("temp/templates.json")
    
    # Add another template
    generator.template_manager.add_template(
        "concise",
        "Answer this question briefly: {query}\nBased on: {context}"
    )
    
    # Save templates
    generator.template_manager.save_templates(template_file)
    print(f"Templates saved to {template_file}")
    
    # Create a new configuration with the template directory
    new_config = Config()
    new_config.generation.provider = "simple"
    new_config.generation.template_directory = "temp"
    
    # Create a new generator
    new_generator = Generator(new_config)
    
    # Use the loaded template
    new_config.generation.template_id = "concise"
    response = await new_generator.generate(query, chunks)
    print(f"Query: {query}")
    print(f"Response: {response}")


if __name__ == "__main__":
    asyncio.run(main())
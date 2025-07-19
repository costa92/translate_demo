#!/usr/bin/env python
"""
Example script demonstrating the quality control mechanisms.

This script shows how to use the quality control mechanisms in the unified knowledge base system.
"""

import asyncio
import logging
from typing import List

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import TextChunk
from src.knowledge_base.generation.generator import Generator
from src.knowledge_base.generation.quality_control import (
    ContentFilter, ContentFilterLevel, QualityAssessment,
    SimpleQualityAssessor, AnswerValidator
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demonstrate_content_filtering():
    """Demonstrate content filtering."""
    logger.info("Demonstrating content filtering...")
    
    # Create configuration
    config = Config()
    
    # Create content filter with different levels
    for level in ["none", "low", "medium", "high"]:
        config.generation.filter_level = level
        content_filter = ContentFilter(config)
        
        # Test with harmless content
        content = "The capital of France is Paris."
        filtered, reason = content_filter.filter_content(content)
        logger.info(f"Filter level: {level}, Content: '{content}'")
        logger.info(f"  Filtered: {filtered}, Reason: {reason}")
        
        # Test with potentially harmful content
        content = "Here's how to hack into a computer system..."
        filtered, reason = content_filter.filter_content(content)
        logger.info(f"Filter level: {level}, Content: '{content}'")
        logger.info(f"  Filtered: {filtered}, Reason: {reason}")
        
        logger.info("-" * 50)


async def demonstrate_quality_assessment():
    """Demonstrate quality assessment."""
    logger.info("Demonstrating quality assessment...")
    
    # Create configuration
    config = Config()
    
    # Create simple quality assessor
    assessor = SimpleQualityAssessor(config)
    
    # Test with good answer
    query = "What is the capital of France?"
    answer = "The capital of France is Paris. It is known for its iconic landmarks like the Eiffel Tower."
    assessment = assessor.assess_quality(query, answer)
    logger.info(f"Query: '{query}'")
    logger.info(f"Answer: '{answer}'")
    logger.info(f"Assessment: {assessment}")
    
    # Test with short answer
    answer = "Paris."
    assessment = assessor.assess_quality(query, answer)
    logger.info(f"Query: '{query}'")
    logger.info(f"Answer: '{answer}'")
    logger.info(f"Assessment: {assessment}")
    
    # Test with uncertain answer
    answer = "I'm not sure what the capital of France is."
    assessment = assessor.assess_quality(query, answer)
    logger.info(f"Query: '{query}'")
    logger.info(f"Answer: '{answer}'")
    logger.info(f"Assessment: {assessment}")
    
    # Test with irrelevant answer
    answer = "The weather is nice today."
    assessment = assessor.assess_quality(query, answer)
    logger.info(f"Query: '{query}'")
    logger.info(f"Answer: '{answer}'")
    logger.info(f"Assessment: {assessment}")
    
    logger.info("-" * 50)


async def demonstrate_answer_validation():
    """Demonstrate answer validation."""
    logger.info("Demonstrating answer validation...")
    
    # Create configuration
    config = Config()
    
    # Create answer validator
    validator = AnswerValidator(config)
    
    # Test with good answer
    query = "What is the capital of France?"
    answer = "The capital of France is Paris. It is known for its iconic landmarks like the Eiffel Tower."
    is_valid, assessment = await validator.validate_answer(query, answer)
    logger.info(f"Query: '{query}'")
    logger.info(f"Answer: '{answer}'")
    logger.info(f"Valid: {is_valid}, Assessment: {assessment}")
    
    # Test with short answer
    answer = "Paris."
    is_valid, assessment = await validator.validate_answer(query, answer)
    logger.info(f"Query: '{query}'")
    logger.info(f"Answer: '{answer}'")
    logger.info(f"Valid: {is_valid}, Assessment: {assessment}")
    
    logger.info("-" * 50)


async def demonstrate_generator_with_quality_control():
    """Demonstrate generator with quality control."""
    logger.info("Demonstrating generator with quality control...")
    
    # Create configuration
    config = Config()
    config.generation.provider = "simple"  # Use simple provider for demonstration
    
    # Create generator
    generator = Generator(config)
    
    # Create sample chunks
    chunks = [
        TextChunk(
            id="1",
            text="Paris is the capital of France. It is known for its iconic landmarks like the Eiffel Tower.",
            document_id="doc1",
            metadata={"source": "geography.txt"}
        ),
        TextChunk(
            id="2",
            text="France is a country in Western Europe. Its capital is Paris.",
            document_id="doc1",
            metadata={"source": "geography.txt"}
        )
    ]
    
    # Generate answer with quality control
    query = "What is the capital of France?"
    logger.info(f"Query: '{query}'")
    logger.info("Generating answer with quality control...")
    answer = await generator.generate(query, chunks, validate=True)
    logger.info(f"Answer: '{answer}'")
    
    # Generate answer without quality control
    logger.info("Generating answer without quality control...")
    answer = await generator.generate(query, chunks, validate=False)
    logger.info(f"Answer: '{answer}'")
    
    logger.info("-" * 50)


async def main():
    """Run the demonstration."""
    logger.info("Starting quality control demonstration...")
    
    await demonstrate_content_filtering()
    await demonstrate_quality_assessment()
    await demonstrate_answer_validation()
    await demonstrate_generator_with_quality_control()
    
    logger.info("Quality control demonstration completed.")


if __name__ == "__main__":
    asyncio.run(main())
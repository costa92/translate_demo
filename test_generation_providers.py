#!/usr/bin/env python3
"""Test script for generation providers."""

import asyncio
import logging
import os
from knowledge_base.core.config import GenerationConfig
from knowledge_base.generation.generator import Generator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_simple_provider():
    """Test simple generation provider."""
    print("\n=== Testing Simple Provider ===")
    
    config = GenerationConfig(
        provider="simple",
        temperature=0.7,
        max_tokens=500
    )
    
    generator = Generator(config)
    
    try:
        await generator.initialize()
        
        # Test with context
        query = "What is machine learning?"
        context = [
            "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.",
            "It involves algorithms that can identify patterns in data and make predictions or classifications."
        ]
        
        answer, confidence = await generator.generate(query, context)
        print(f"Query: {query}")
        print(f"Answer: {answer}")
        print(f"Confidence: {confidence:.2f}")
        
        # Test without context
        query2 = "What is quantum computing?"
        answer2, confidence2 = await generator.generate(query2, [])
        print(f"\nQuery: {query2}")
        print(f"Answer: {answer2}")
        print(f"Confidence: {confidence2:.2f}")
        
    finally:
        await generator.close()


async def test_deepseek_provider():
    """Test DeepSeek generation provider."""
    print("\n=== Testing DeepSeek Provider ===")
    
    # Skip if no API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Skipping DeepSeek test - no API key found")
        return
    
    config = GenerationConfig(
        provider="deepseek",
        api_key=api_key,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=500
    )
    
    generator = Generator(config)
    
    try:
        await generator.initialize()
        
        # Test with context
        query = "What is machine learning?"
        context = [
            "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.",
            "It involves algorithms that can identify patterns in data and make predictions or classifications."
        ]
        
        answer, confidence = await generator.generate(query, context)
        print(f"Query: {query}")
        print(f"Answer: {answer}")
        print(f"Confidence: {confidence:.2f}")
        
    except Exception as e:
        print(f"DeepSeek test failed: {e}")
    finally:
        await generator.close()


async def test_siliconflow_provider():
    """Test SiliconFlow generation provider."""
    print("\n=== Testing SiliconFlow Provider ===")
    
    # Skip if no API key
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("Skipping SiliconFlow test - no API key found")
        return
    
    config = GenerationConfig(
        provider="siliconflow",
        api_key=api_key,
        model="THUDM/chatglm3-6b",
        temperature=0.7,
        max_tokens=500
    )
    
    generator = Generator(config)
    
    try:
        await generator.initialize()
        
        # Test with context
        query = "什么是机器学习？"
        context = [
            "机器学习是人工智能的一个分支，它使计算机能够从数据中学习并做出决策，而无需明确编程。",
            "它涉及能够识别数据中的模式并进行预测或分类的算法。"
        ]
        
        answer, confidence = await generator.generate(query, context)
        print(f"Query: {query}")
        print(f"Answer: {answer}")
        print(f"Confidence: {confidence:.2f}")
        
    except Exception as e:
        print(f"SiliconFlow test failed: {e}")
    finally:
        await generator.close()


async def main():
    """Run all generation provider tests."""
    print("Testing Generation Providers")
    print("=" * 50)
    
    await test_simple_provider()
    await test_deepseek_provider()
    await test_siliconflow_provider()
    
    print("\n" + "=" * 50)
    print("Generation provider tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
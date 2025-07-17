#!/usr/bin/env python3
"""
Test script for the new knowledge base architecture.
"""

import asyncio
import logging
from knowledge_base import KnowledgeBase, Config, Document
from knowledge_base.core.types import DocumentType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_functionality():
    """Test basic knowledge base functionality."""
    print("=== Testing New Knowledge Base Architecture ===")
    
    # Create configuration
    config = Config()
    config.storage.provider = "memory"
    config.embedding.provider = "sentence_transformers"  # Will fallback to simple implementation
    config.generation.provider = "ollama"  # Use ollama which doesn't require API key for testing
    
    # Initialize knowledge base
    async with KnowledgeBase(config) as kb:
        print(f"✓ Knowledge base initialized with {config.storage.provider} storage")
        
        # Test adding documents
        documents = [
            Document(
                id="doc1",
                content="Python是一种高级编程语言，由Guido van Rossum于1991年首次发布。Python设计哲学强调代码的可读性和简洁性。",
                type=DocumentType.TEXT,
                metadata={"topic": "programming", "language": "python"}
            ),
            Document(
                id="doc2", 
                content="FastAPI是一个现代、快速（高性能）的Web框架，用于构建Python API。它基于标准Python类型提示，支持异步编程。",
                type=DocumentType.TEXT,
                metadata={"topic": "web_framework", "language": "python"}
            ),
            Document(
                id="doc3",
                content="机器学习是人工智能的一个分支，它使用算法和统计模型来让计算机系统能够有效地执行特定任务，而无需明确的指令。",
                type=DocumentType.TEXT,
                metadata={"topic": "machine_learning", "language": "chinese"}
            )
        ]
        
        # Add documents
        print(f"\n📝 Adding {len(documents)} documents...")
        result = await kb.add_documents(documents)
        
        if result.success:
            print(f"✓ Successfully added documents: {result.chunks_created} chunks created in {result.processing_time:.2f}s")
        else:
            print(f"✗ Failed to add documents: {result.error_message}")
            return
        
        # Test queries
        queries = [
            "什么是Python？",
            "FastAPI有什么特点？", 
            "机器学习是什么？",
            "编程语言的设计哲学"
        ]
        
        print(f"\n🔍 Testing queries...")
        for query in queries:
            print(f"\nQuery: {query}")
            
            # Test search first
            search_results = await kb.search(query, top_k=2)
            print(f"Search results: {len(search_results)} found")
            
            # Test full query
            result = await kb.query(query)
            
            if result.sources:
                print(f"Answer: {result.answer[:100]}...")
                print(f"Sources: {len(result.sources)} chunks, confidence: {result.confidence:.2f}")
                print(f"Processing time: {result.processing_time:.2f}s")
            else:
                print(f"No relevant information found")
        
        # Test statistics
        print(f"\n📊 Knowledge base statistics:")
        stats = await kb.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")


async def test_error_handling():
    """Test error handling."""
    print(f"\n=== Testing Error Handling ===")
    
    config = Config()
    config.generation.provider = "ollama"  # Use ollama to avoid API key requirement
    
    async with KnowledgeBase(config) as kb:
        # Test empty query
        try:
            result = await kb.query("")
            print(f"✗ Empty query should fail but got: {result.answer}")
        except Exception as e:
            print(f"✓ Empty query correctly failed: {type(e).__name__}")
        
        # Test invalid document
        try:
            invalid_doc = Document(id="", content="", type=DocumentType.TEXT)
            result = await kb.add_document(invalid_doc)
            print(f"✗ Invalid document should fail but got: {result.status}")
        except Exception as e:
            print(f"✓ Invalid document correctly failed: {type(e).__name__}")


async def main():
    """Main test function."""
    try:
        await test_basic_functionality()
        await test_error_handling()
        print(f"\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Test script for Notion storage provider.
Tests all CRUD operations and vector similarity search.
"""

import asyncio
import logging
import os
import json
from typing import List, Dict, Any
from datetime import datetime

from knowledge_base.core.config import StorageConfig
from knowledge_base.storage.providers.notion import NotionVectorStore
from knowledge_base.core.types import Chunk

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotionStorageTester:
    """Test Notion storage provider functionality."""
    
    def __init__(self, api_key: str, database_id: str):
        """Initialize tester with Notion credentials."""
        self.api_key = api_key
        self.database_id = database_id
        
        # Create storage config
        self.config = StorageConfig(
            provider="notion",
            notion_api_key=api_key,
            notion_database_id=database_id
        )
        
        self.store = None
    
    async def setup(self) -> None:
        """Setup the storage provider."""
        logger.info("Setting up Notion storage provider...")
        
        self.store = NotionVectorStore(self.config.__dict__)
        await self.store.initialize()
        
        logger.info("Notion storage provider initialized successfully")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.store:
            await self.store.close()
            logger.info("Notion storage provider closed")
    
    def create_test_chunks(self) -> List[Chunk]:
        """Create test chunks for testing."""
        return [
            Chunk(
                id="test_chunk_001",
                document_id="test_doc_001",
                text="Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including object-oriented, functional, and procedural programming.",
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 77,  # 385 dimensions
                metadata={
                    "source": "test_document.txt",
                    "language": "en",
                    "topic": "programming",
                    "created_at": datetime.now().isoformat()
                },
                start_index=0,
                end_index=180
            ),
            Chunk(
                id="test_chunk_002",
                document_id="test_doc_001", 
                text="机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习和改进。常见的机器学习算法包括线性回归、决策树和神经网络。",
                embedding=[0.2, 0.3, 0.4, 0.5, 0.6] * 77,  # 385 dimensions
                metadata={
                    "source": "test_document.txt",
                    "language": "zh",
                    "topic": "machine_learning",
                    "created_at": datetime.now().isoformat()
                },
                start_index=181,
                end_index=280
            ),
            Chunk(
                id="test_chunk_003",
                document_id="test_doc_002",
                text="Vector databases are specialized database systems designed to store and retrieve high-dimensional vectors efficiently. They are particularly useful for similarity search and recommendation systems.",
                embedding=[0.3, 0.4, 0.5, 0.6, 0.7] * 77,  # 385 dimensions
                metadata={
                    "source": "vector_db_guide.md",
                    "language": "en", 
                    "topic": "databases",
                    "created_at": datetime.now().isoformat()
                },
                start_index=0,
                end_index=200
            )
        ]
    
    async def test_add_chunks(self) -> bool:
        """Test adding chunks to Notion."""
        logger.info("\n=== Testing Add Chunks ===")
        
        try:
            test_chunks = self.create_test_chunks()
            
            logger.info(f"Adding {len(test_chunks)} test chunks...")
            success = await self.store.add_chunks(test_chunks)
            
            if success:
                logger.info("✅ Successfully added chunks to Notion")
                return True
            else:
                logger.error("❌ Failed to add chunks to Notion")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error adding chunks: {e}")
            return False
    
    async def test_get_chunk(self) -> bool:
        """Test retrieving a specific chunk."""
        logger.info("\n=== Testing Get Chunk ===")
        
        try:
            chunk_id = "test_chunk_001"
            logger.info(f"Retrieving chunk: {chunk_id}")
            
            chunk = await self.store.get_chunk(chunk_id)
            
            if chunk:
                logger.info(f"✅ Successfully retrieved chunk: {chunk.id}")
                logger.info(f"   Text: {chunk.text[:50]}...")
                logger.info(f"   Document ID: {chunk.document_id}")
                logger.info(f"   Metadata: {chunk.metadata}")
                return True
            else:
                logger.error(f"❌ Chunk {chunk_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error retrieving chunk: {e}")
            return False
    
    async def test_search_similar(self) -> bool:
        """Test vector similarity search."""
        logger.info("\n=== Testing Similarity Search ===")
        
        try:
            # Create a query vector similar to the first test chunk
            query_vector = [0.15, 0.25, 0.35, 0.45, 0.55] * 77  # 385 dimensions
            
            logger.info("Performing similarity search...")
            results = await self.store.search_similar(
                query_vector=query_vector,
                top_k=3,
                min_score=0.0
            )
            
            logger.info(f"✅ Found {len(results)} similar chunks:")
            for i, result in enumerate(results, 1):
                chunk = result["chunk"]
                score = result["score"]
                logger.info(f"   {i}. Chunk {chunk.id} (score: {score:.3f})")
                logger.info(f"      Text: {chunk.text[:50]}...")
            
            return len(results) > 0
            
        except Exception as e:
            logger.error(f"❌ Error in similarity search: {e}")
            return False
    
    async def test_get_stats(self) -> bool:
        """Test getting storage statistics."""
        logger.info("\n=== Testing Get Stats ===")
        
        try:
            stats = await self.store.get_stats()
            
            logger.info("✅ Storage statistics:")
            for key, value in stats.items():
                logger.info(f"   {key}: {value}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return False
    
    async def test_delete_chunk(self) -> bool:
        """Test deleting a specific chunk."""
        logger.info("\n=== Testing Delete Chunk ===")
        
        try:
            chunk_id = "test_chunk_003"
            logger.info(f"Deleting chunk: {chunk_id}")
            
            success = await self.store.delete_chunks([chunk_id])
            
            if success:
                logger.info(f"✅ Successfully deleted chunk: {chunk_id}")
                
                # Verify deletion
                chunk = await self.store.get_chunk(chunk_id)
                if chunk is None:
                    logger.info("✅ Chunk deletion verified")
                    return True
                else:
                    logger.error("❌ Chunk still exists after deletion")
                    return False
            else:
                logger.error(f"❌ Failed to delete chunk: {chunk_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting chunk: {e}")
            return False
    
    async def test_delete_document(self) -> bool:
        """Test deleting all chunks from a document."""
        logger.info("\n=== Testing Delete Document ===")
        
        try:
            document_id = "test_doc_001"
            logger.info(f"Deleting all chunks from document: {document_id}")
            
            success = await self.store.delete_document(document_id)
            
            if success:
                logger.info(f"✅ Successfully deleted document: {document_id}")
                return True
            else:
                logger.error(f"❌ Failed to delete document: {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting document: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        logger.info("🚀 Starting Notion Storage Tests")
        logger.info("=" * 50)
        
        test_results = {}
        
        # Run tests
        test_results["add_chunks"] = await self.test_add_chunks()
        test_results["get_chunk"] = await self.test_get_chunk()
        test_results["search_similar"] = await self.test_search_similar()
        test_results["get_stats"] = await self.test_get_stats()
        test_results["delete_chunk"] = await self.test_delete_chunk()
        test_results["delete_document"] = await self.test_delete_document()
        
        # Generate summary
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result)
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": passed_tests / total_tests * 100,
            "test_results": test_results
        }
        
        logger.info("\n" + "=" * 50)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success rate: {summary['success_rate']:.1f}%")
        
        # Show individual test results
        logger.info("\n📋 Individual Test Results:")
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")
        
        return summary


async def main():
    """Main test function."""
    print("🧪 Notion Storage Provider Test Suite")
    print("=" * 50)
    
    # Get configuration
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not api_key:
        api_key = input("Enter your Notion API key: ").strip()
    
    if not database_id:
        database_id = input("Enter your Notion database ID: ").strip()
    
    if not api_key or not database_id:
        print("❌ API key and database ID are required!")
        return
    
    # Run tests
    tester = NotionStorageTester(api_key, database_id)
    
    try:
        await tester.setup()
        results = await tester.run_all_tests()
        
        # Save results to file
        with open("notion_storage_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Test results saved to: notion_storage_test_results.json")
        
        if results["success_rate"] == 100:
            print("🎉 All tests passed! Notion storage is working correctly.")
        else:
            print(f"⚠️  {results['failed_tests']} test(s) failed. Check the logs for details.")
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        logger.error(f"Test execution failed: {e}")
    
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
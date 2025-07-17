#!/usr/bin/env python3
"""
Complete RAG integration test with Notion storage.
Tests the full pipeline: document processing -> Notion storage -> retrieval -> generation.
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, List

from knowledge_base.core.knowledge_base import KnowledgeBase
from knowledge_base.core.config import Config, StorageConfig, EmbeddingConfig, ChunkingConfig, RetrievalConfig, GenerationConfig
from knowledge_base.core.types import Document, DocumentType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotionRAGTester:
    """Test complete RAG system with Notion storage."""
    
    def __init__(self, notion_api_key: str, notion_database_id: str):
        """Initialize tester with Notion credentials."""
        self.notion_api_key = notion_api_key
        self.notion_database_id = notion_database_id
        
        self.test_documents = [
            {
                "id": "notion_doc_001",
                "content": "Notion is an all-in-one workspace that combines note-taking, project management, and database functionality. It allows users to create pages with rich content including text, images, tables, and embedded media. Notion's flexibility makes it popular among individuals and teams for organizing information and collaborating on projects.",
                "metadata": {"source": "notion_guide.md", "category": "productivity", "language": "en"}
            },
            {
                "id": "notion_doc_002", 
                "content": "向量数据库是专门设计用于存储和检索高维向量的数据库系统。它们在相似性搜索、推荐系统和机器学习应用中发挥重要作用。常见的向量数据库包括Pinecone、Weaviate和Chroma等。",
                "metadata": {"source": "vector_db_intro.md", "category": "technology", "language": "zh"}
            },
            {
                "id": "notion_doc_003",
                "content": "Knowledge base systems help organizations capture, organize, and share institutional knowledge. They typically include features for document management, search capabilities, and collaborative editing. Modern knowledge bases often incorporate AI-powered features like semantic search and automated content generation.",
                "metadata": {"source": "kb_overview.txt", "category": "knowledge_management", "language": "en"}
            }
        ]
        
        self.test_queries = [
            {
                "query": "What is Notion?",
                "expected_language": "en",
                "expected_topics": ["notion", "workspace", "productivity"]
            },
            {
                "query": "什么是向量数据库？",
                "expected_language": "zh",
                "expected_topics": ["向量数据库", "相似性搜索"]
            },
            {
                "query": "How do knowledge base systems work?",
                "expected_language": "en", 
                "expected_topics": ["knowledge base", "document management"]
            },
            {
                "query": "Tell me about collaborative tools",
                "expected_language": "en",
                "expected_topics": ["collaboration", "tools"]
            }
        ]
    
    async def setup_knowledge_base(self) -> KnowledgeBase:
        """Setup knowledge base with Notion storage."""
        logger.info("Setting up knowledge base with Notion storage...")
        
        config = Config(
            storage=StorageConfig(
                provider="notion",
                notion_api_key=self.notion_api_key,
                notion_database_id=self.notion_database_id
            ),
            embedding=EmbeddingConfig(
                provider="sentence_transformers",
                model="all-MiniLM-L6-v2"
            ),
            chunking=ChunkingConfig(
                chunk_size=300,
                chunk_overlap=50
            ),
            retrieval=RetrievalConfig(
                strategy="semantic",
                top_k=3,
                min_score=0.1
            ),
            generation=GenerationConfig(
                provider="simple",
                temperature=0.7,
                max_tokens=500
            )
        )
        
        kb = KnowledgeBase(config)
        await kb.initialize()
        
        logger.info("Knowledge base initialized successfully")
        return kb
    
    async def add_test_documents(self, kb: KnowledgeBase) -> bool:
        """Add test documents to the knowledge base."""
        logger.info("Adding test documents to knowledge base...")
        
        try:
            for doc_data in self.test_documents:
                document = Document(
                    id=doc_data["id"],
                    content=doc_data["content"],
                    type=DocumentType.TEXT,
                    metadata=doc_data["metadata"]
                )
                
                result = await kb.add_document(document)
                logger.info(f"Added document {doc_data['id']}: {result.chunks_created} chunks created")
            
            logger.info(f"Successfully added {len(self.test_documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    async def test_queries(self, kb: KnowledgeBase) -> List[Dict[str, Any]]:
        """Test queries against the knowledge base."""
        logger.info("Testing queries against knowledge base...")
        
        results = []
        
        for test_case in self.test_queries:
            query = test_case["query"]
            logger.info(f"\nQuery: {query}")
            
            try:
                # Perform query
                query_result = await kb.query(query)
                
                result = {
                    "query": query,
                    "answer": query_result.answer,
                    "confidence": query_result.confidence,
                    "source_count": len(query_result.sources),
                    "processing_time": query_result.processing_time,
                    "sources": [
                        {
                            "chunk_id": source.chunk_id,
                            "score": source.score,
                            "text_preview": source.text[:100] + "..." if len(source.text) > 100 else source.text,
                            "metadata": source.metadata
                        }
                        for source in query_result.sources
                    ],
                    "success": True,
                    "error": None,
                    "expected_language": test_case["expected_language"],
                    "expected_topics": test_case["expected_topics"]
                }
                
                logger.info(f"Answer: {query_result.answer[:100]}...")
                logger.info(f"Confidence: {query_result.confidence:.2f}")
                logger.info(f"Sources: {len(query_result.sources)}")
                logger.info(f"Processing time: {query_result.processing_time:.3f}s")
                
            except Exception as e:
                result = {
                    "query": query,
                    "answer": None,
                    "confidence": 0.0,
                    "source_count": 0,
                    "processing_time": 0.0,
                    "sources": [],
                    "success": False,
                    "error": str(e),
                    "expected_language": test_case["expected_language"],
                    "expected_topics": test_case["expected_topics"]
                }
                logger.error(f"Query failed: {e}")
            
            results.append(result)
        
        return results
    
    async def test_storage_operations(self, kb: KnowledgeBase) -> Dict[str, Any]:
        """Test storage-specific operations."""
        logger.info("Testing storage operations...")
        
        try:
            # Get storage statistics
            stats = await kb._storage.get_stats()
            logger.info(f"Storage stats: {stats}")
            
            # Test chunk retrieval
            # Note: This would require knowing specific chunk IDs from the storage
            
            return {
                "stats_retrieved": True,
                "stats": stats,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Storage operations failed: {e}")
            return {
                "stats_retrieved": False,
                "stats": {},
                "error": str(e)
            }
    
    async def run_integration_test(self) -> Dict[str, Any]:
        """Run the complete integration test."""
        logger.info("🚀 Starting Notion RAG Integration Test")
        logger.info("=" * 60)
        
        kb = None
        
        try:
            # Setup knowledge base
            kb = await self.setup_knowledge_base()
            
            # Add documents
            docs_added = await self.add_test_documents(kb)
            
            if not docs_added:
                raise Exception("Failed to add test documents")
            
            # Test queries
            query_results = await self.test_queries(kb)
            
            # Test storage operations
            storage_results = await self.test_storage_operations(kb)
            
            # Generate summary
            successful_queries = sum(1 for r in query_results if r["success"])
            total_queries = len(query_results)
            
            summary = {
                "test_type": "notion_rag_integration",
                "timestamp": asyncio.get_event_loop().time(),
                "setup_successful": True,
                "documents_added": len(self.test_documents),
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "query_success_rate": successful_queries / total_queries * 100 if total_queries > 0 else 0,
                "average_confidence": sum(r["confidence"] for r in query_results if r["success"]) / max(1, successful_queries),
                "average_processing_time": sum(r["processing_time"] for r in query_results if r["success"]) / max(1, successful_queries),
                "average_source_count": sum(r["source_count"] for r in query_results if r["success"]) / max(1, successful_queries),
                "query_results": query_results,
                "storage_results": storage_results
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            return {
                "test_type": "notion_rag_integration",
                "timestamp": asyncio.get_event_loop().time(),
                "setup_successful": False,
                "error": str(e),
                "query_results": [],
                "storage_results": {}
            }
        
        finally:
            if kb:
                await kb.close()
                logger.info("Knowledge base closed")


async def main():
    """Main test function."""
    print("🧪 Notion RAG Integration Test Suite")
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
    
    # Run integration test
    tester = NotionRAGTester(api_key, database_id)
    
    try:
        results = await tester.run_integration_test()
        
        # Save results to file
        with open("notion_rag_integration_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 NOTION RAG INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        if results.get("setup_successful", False):
            print(f"✅ Setup: Successful")
            print(f"📄 Documents added: {results.get('documents_added', 0)}")
            print(f"🔍 Total queries: {results.get('total_queries', 0)}")
            print(f"✅ Successful queries: {results.get('successful_queries', 0)}")
            print(f"📈 Success rate: {results.get('query_success_rate', 0):.1f}%")
            print(f"🎯 Average confidence: {results.get('average_confidence', 0):.2f}")
            print(f"⏱️  Average processing time: {results.get('average_processing_time', 0):.3f}s")
            print(f"📚 Average sources per query: {results.get('average_source_count', 0):.1f}")
            
            if results.get("query_success_rate", 0) == 100:
                print("\n🎉 All tests passed! Notion RAG integration is working perfectly.")
            else:
                print(f"\n⚠️  Some queries failed. Check the detailed results for more information.")
        else:
            print(f"❌ Setup failed: {results.get('error', 'Unknown error')}")
        
        print(f"\n📄 Detailed results saved to: notion_rag_integration_results.json")
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        logger.error(f"Test execution failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())